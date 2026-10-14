
from scheduler import schedule
from models import yolo_model, llama_model, bert_model


MODEL_FUNCTIONS = {
    "yolo": yolo_model,
    "llama": llama_model,
    "bert": bert_model,
}


def route_request(model, priority=1):
    decision = schedule(model, priority)

    selected_model = decision["model"]
    result = MODEL_FUNCTIONS[selected_model]()

    return {
        "result": result,
        "model": selected_model,
        "selected_worker": decision["selected_worker"],
        "scheduling_score": decision["score"],
        "worker_scores": decision["worker_scores"],
    }
