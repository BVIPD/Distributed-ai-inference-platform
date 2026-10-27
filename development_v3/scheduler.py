import json
import os
import threading
import urllib.parse
import urllib.request

SUPPORTED_MODELS = {"yolo", "llama", "bert"}

PROMETHEUS_URL = os.getenv(
    "PROMETHEUS_URL",
    "http://prometheus:9090",
).rstrip("/")

# Worker resource limits from the Kubernetes deployment.
WORKER_CPU_LIMIT_CORES = float(
    os.getenv("WORKER_CPU_LIMIT_CORES", "2")
)
WORKER_MEMORY_LIMIT_BYTES = float(
    os.getenv("WORKER_MEMORY_LIMIT_BYTES", str(3 * 1024**3))
)

PROMETHEUS_TIMEOUT_SECONDS = float(
    os.getenv("PROMETHEUS_TIMEOUT_SECONDS", "1")
)

_fallback_lock = threading.Lock()
_fallback_index = 0


def get_workers():
    """Read configured worker IDs from WORKER_IDS."""
    configured = os.getenv("WORKER_IDS", "worker-1")

    workers = list(dict.fromkeys(
        item.strip()
        for item in configured.split(",")
        if item.strip()
    ))

    if not workers:
        raise RuntimeError(
            "Configure at least one worker in WORKER_IDS."
        )

    return workers


def _prometheus_query(expression):
    """Execute an instant query against Prometheus."""
    params = urllib.parse.urlencode({"query": expression})
    url = f"{PROMETHEUS_URL}/api/v1/query?{params}"

    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json"},
    )

    with urllib.request.urlopen(
        request,
        timeout=PROMETHEUS_TIMEOUT_SECONDS,
    ) as response:
        payload = json.loads(response.read().decode("utf-8"))

    if payload.get("status") != "success":
        raise RuntimeError("Prometheus query was unsuccessful.")

    results = payload.get("data", {}).get("result", [])

    if not results:
        return None

    return float(results[0]["value"][1])


def _worker_metric(expression):
    """Return a metric value or None when unavailable."""
    try:
        return _prometheus_query(expression)
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        RuntimeError,
    ):
        return None


def get_system_state(workers=None):
    """
    Collect live worker measurements from Prometheus.

    Queue length is deliberately not fabricated: the current
    Prometheus metrics do not establish a measured queue length.
    """
    workers = workers or get_workers()
    states = {}

    for worker in workers:
        job = worker.replace("\\", "\\\\").replace('"', '\\"')
        worker_id = worker.replace("\\", "\\\\").replace('"', '\\"')

        cpu_cores = _worker_metric(
            f'rate(process_cpu_seconds_total{{job="{job}"}}[1m])'
        )

        memory_bytes = _worker_metric(
            f'process_resident_memory_bytes{{job="{job}"}}'
        )

        average_latency_seconds = _worker_metric(
            "sum(rate(worker_inference_duration_seconds_sum"
            f'{{worker_id="{worker_id}"}}[5m]))'
            " / "
            "clamp_min(sum(rate(worker_inference_duration_seconds_count"
            f'{{worker_id="{worker_id}"}}[5m])), 1e-9)'
        )

        request_rate = _worker_metric(
            "sum(rate(worker_inference_requests_total"
            f'{{worker_id="{worker_id}"}}[1m]))'
        )

        cpu_available = cpu_cores is not None
        memory_available = memory_bytes is not None

        cpu_percent = (
            min(100.0, max(0.0, cpu_cores
                           / WORKER_CPU_LIMIT_CORES * 100.0))
            if cpu_available and WORKER_CPU_LIMIT_CORES > 0
            else None
        )

        memory_percent = (
            min(100.0, max(0.0, memory_bytes
                           / WORKER_MEMORY_LIMIT_BYTES * 100.0))
            if memory_available and WORKER_MEMORY_LIMIT_BYTES > 0
            else None
        )

        latency_ms = (
            max(0.0, average_latency_seconds * 1000.0)
            if average_latency_seconds is not None
            else None
        )

        states[worker] = {
            "cpu_usage_percent": (
                round(cpu_percent, 2)
                if cpu_percent is not None else None
            ),
            "memory_usage_percent": (
                round(memory_percent, 2)
                if memory_percent is not None else None
            ),
            "average_inference_latency_ms": (
                round(latency_ms, 2)
                if latency_ms is not None else None
            ),
            "request_rate_per_second": (
                round(max(0.0, request_rate), 4)
                if request_rate is not None else None
            ),
            "metrics_available": (
                cpu_available and memory_available
            ),
        }

    return states


def _fallback_decision(workers, priority, states):
    """
    Use deterministic round-robin routing when live telemetry
    is unavailable. This does not pretend the metrics are real.
    """
    global _fallback_index

    with _fallback_lock:
        selected = workers[_fallback_index % len(workers)]
        _fallback_index += 1

    return {
        "selected_worker": selected,
        "score": None,
        "worker_scores": {},
        "worker_states": states,
        "metrics_source": "round_robin_fallback",
    }


def adaptive_scheduler(priority=1):
    priority = max(1, min(int(priority), 10))
    workers = get_workers()
    states = get_system_state(workers)

    # Only workers with measured CPU and memory are eligible for
    # telemetry-based scoring.
    available_workers = [
        worker
        for worker in workers
        if states[worker]["metrics_available"]
    ]

    if not available_workers:
        return _fallback_decision(workers, priority, states)

    scores = {}

    # Higher priority increases the influence of inference latency.
    latency_weight = 0.15 + 0.02 * (priority - 1)
    cpu_weight = 0.40
    memory_weight = 0.25
    request_weight = 0.35 - latency_weight

    for worker in available_workers:
        state = states[worker]

        cpu = state["cpu_usage_percent"] / 10.0
        memory = state["memory_usage_percent"] / 10.0

        latency_ms = state["average_inference_latency_ms"]
        request_rate = state["request_rate_per_second"]

        # Missing latency/rate data receives a neutral value rather
        # than being misrepresented as a measured zero.
        latency_score = (
            min(10.0, latency_ms / 200.0)
            if latency_ms is not None
            else 5.0
        )

        request_score = (
            min(10.0, request_rate)
            if request_rate is not None
            else 5.0
        )

        scores[worker] = round(
            cpu_weight * cpu
            + memory_weight * memory
            + latency_weight * latency_score
            + request_weight * request_score,
            3,
        )

    selected_worker = min(scores, key=scores.get)

    return {
        "selected_worker": selected_worker,
        "score": scores[selected_worker],
        "worker_scores": scores,
        "worker_states": states,
        "metrics_source": "prometheus",
    }


def schedule(model, priority=1):
    requested_model = str(model).strip().lower()

    if requested_model not in SUPPORTED_MODELS:
        raise ValueError(
            "Unsupported model. Choose yolo, llama, or bert."
        )

    try:
        priority = int(priority)
    except (TypeError, ValueError):
        raise ValueError(
            "Priority must be an integer from 1 to 10."
        ) from None

    if not 1 <= priority <= 10:
        raise ValueError(
            "Priority must be an integer from 1 to 10."
        )

    return {
        "model": requested_model,
        "priority": priority,
        **adaptive_scheduler(priority),
    }