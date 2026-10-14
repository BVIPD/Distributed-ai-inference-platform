
import os
import random

SUPPORTED_MODELS = {"yolo", "llama", "bert"}


def get_workers():
    """Return comma-separated worker IDs from WORKER_IDS."""
    configured = os.getenv("WORKER_IDS", "worker-1")
    workers = list(dict.fromkeys(
        worker.strip()
        for worker in configured.split(",")
        if worker.strip()
    ))
    if not workers:
        raise RuntimeError("Configure at least one worker in WORKER_IDS.")
    return workers


def get_system_state(workers=None):
    """
    Generate synthetic metrics for scheduler experiments.
    These are NOT live worker resource measurements.
    """
    workers = workers or get_workers()
    return {
        worker: {
            "queue_length": random.randint(1, 10),
            "resource_usage": random.randint(1, 10),
            "node_load": random.randint(1, 10),
        }
        for worker in workers
    }


def adaptive_scheduler(priority=1):
    priority = max(1, min(int(priority), 10))
    workers = get_workers()
    states = get_system_state(workers)
    scores = {}

    for worker, state in states.items():
        queue = state["queue_length"]
        resource = state["resource_usage"]
        load = state["node_load"]
        scores[worker] = round(
            0.45 * queue
            + 0.30 * resource
            + 0.25 * load
            - 0.05 * priority * queue,
            3,
        )

    selected_worker = min(scores, key=scores.get)
    return {
        "selected_worker": selected_worker,
        "score": scores[selected_worker],
        "worker_scores": scores,
        "worker_states": states,
        "metrics_source": "synthetic",
    }


def schedule(model, priority=1):
    requested_model = str(model).strip().lower()
    if requested_model not in SUPPORTED_MODELS:
        raise ValueError("Unsupported model. Choose yolo, llama, or bert.")

    try:
        priority = int(priority)
    except (TypeError, ValueError):
        raise ValueError("Priority must be an integer from 1 to 10.")

    if not 1 <= priority <= 10:
        raise ValueError("Priority must be an integer from 1 to 10.")

    return {
        "model": requested_model,
        "priority": priority,
        **adaptive_scheduler(priority),
    }
