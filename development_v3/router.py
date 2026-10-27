import json
import os
import threading
import time
import urllib.error
import urllib.request
import uuid

import redis

from scheduler import schedule

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
QUEUE_NAME = "inference:queue"
RESULT_PREFIX = "inference:result:"
RESULT_TTL = 180
REQUEST_TIMEOUT = 125

_redis_client = None
_consumer_thread = None
_stop_event = threading.Event()


def get_redis():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=5,
        )
    return _redis_client


def start_queue_consumer():
    global _consumer_thread
    client = get_redis()
    client.ping()

    if _consumer_thread and _consumer_thread.is_alive():
        return

    _stop_event.clear()
    _consumer_thread = threading.Thread(
        target=_consume_queue,
        name="inference-queue-consumer",
        daemon=True,
    )
    _consumer_thread.start()


def stop_queue_consumer():
    _stop_event.set()


def _consume_queue():
    client = get_redis()

    while not _stop_event.is_set():
        try:
            item = client.brpop(QUEUE_NAME, timeout=1)
            if not item:
                continue

            _, raw_job = item
            job = json.loads(raw_job)
            request_id = job["request_id"]
            result_key = RESULT_PREFIX + request_id

            try:
                result = _route_request_direct(
                    model=job["model"],
                    priority=job["priority"],
                    text=job.get("text"),
                    image_base64=job.get("image_base64"),
                )
                response = {"ok": True, "result": result}

            except Exception as exc:
                response = {
                    "ok": False,
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                }

            client.set(
                result_key,
                json.dumps(response),
                ex=RESULT_TTL,
            )

        except redis.RedisError:
            time.sleep(1)
        except (ValueError, KeyError, TypeError, json.JSONDecodeError):
            # Discard malformed queue messages rather than killing the consumer.
            continue


def enqueue_inference(model, priority=1, text=None, image_base64=None):
    request_id = uuid.uuid4().hex
    client = get_redis()

    job = {
        "request_id": request_id,
        "model": model,
        "priority": priority,
        "text": text,
        "image_base64": image_base64,
    }

    try:
        client.lpush(QUEUE_NAME, json.dumps(job))
    except redis.RedisError as exc:
        raise RuntimeError(f"Redis queue is unavailable: {exc}") from exc

    result_key = RESULT_PREFIX + request_id
    deadline = time.monotonic() + REQUEST_TIMEOUT

    while time.monotonic() < deadline:
        try:
            raw_result = client.get(result_key)
        except redis.RedisError as exc:
            raise RuntimeError(f"Unable to retrieve inference result: {exc}") from exc

        if raw_result:
            response = json.loads(raw_result)

            if response.get("ok"):
                return response["result"]

            error_type = response.get("error_type", "RuntimeError")
            error_message = response.get("error", "Inference failed")

            if error_type == "ValueError":
                raise ValueError(error_message)

            raise RuntimeError(error_message)

        time.sleep(0.1)

    raise TimeoutError(
        "Timed out waiting for the inference result. "
        "The request may still be processing."
    )


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


def _route_request_direct(model, priority=1, text=None, image_base64=None):
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


def route_request(model, priority=1, text=None, image_base64=None):
    """
    Public inference entry point. All requests pass through Redis.
    """
    return enqueue_inference(
        model=model,
        priority=priority,
        text=text,
        image_base64=image_base64,
    )
