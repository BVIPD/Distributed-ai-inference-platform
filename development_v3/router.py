import json
import os
import urllib.error
import urllib.request

from scheduler import schedule


def get_worker_urls():
    """
    Read worker endpoints from WORKER_URLS as comma-separated ID=URL pairs.
    Fall back to the existing single-worker configuration.
    """
    configured = os.getenv("WORKER_URLS", "").strip()
    if not configured:
        return {
            "worker-1": os.getenv(
                "WORKER_1_URL",
                "http://ai-inference-worker1:8000",
            )
        }

    worker_urls = {}
    for entry in configured.split(","):
        if "=" not in entry:
            raise RuntimeError(
                "WORKER_URLS entries must use worker-id=http://host:port format."
            )
        worker_id, url = entry.split("=", 1)
        worker_id = worker_id.strip()
        url = url.strip().rstrip("/")
        if not worker_id or not url.startswith(("http://", "https://")):
            raise RuntimeError(
                "Each WORKER_URLS entry requires a worker ID and HTTP(S) URL."
            )
        worker_urls[worker_id] = url

    if not worker_urls:
        raise RuntimeError("Configure at least one worker endpoint.")
    return worker_urls


def route_request(model, priority=1, text=None, image_base64=None):
    decision = schedule(model, priority)
    selected_model = decision["model"]
    worker_id = decision["selected_worker"]

    worker_urls = get_worker_urls()
    worker_url = worker_urls.get(worker_id)
    if not worker_url:
        raise RuntimeError(
            f"No endpoint configured for selected worker {worker_id}. "
            "Check WORKER_IDS and WORKER_URLS."
        )

    payload = {
        "model": selected_model,
        "text": text,
        "image_base64": image_base64,
    }

    request = urllib.request.Request(
        f"{worker_url}/execute",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            worker_response = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Worker {worker_id} returned HTTP {exc.code}: {detail}"
        ) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(
            f"Worker {worker_id} is unreachable or timed out: {exc}"
        ) from exc

    return {
        "result": worker_response["result"],
        "model": selected_model,
        "selected_worker": worker_response.get("worker_id", worker_id),
        "scheduling_score": decision["score"],
        "worker_scores": decision["worker_scores"],
        "metrics_source": decision["metrics_source"],
        "execution_status": worker_response.get(
            "execution_status", "completed"
        ),
    }
