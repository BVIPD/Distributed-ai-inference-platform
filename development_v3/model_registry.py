from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models"

MODEL_REGISTRY = {
    "bert": {
        "model_id": "bert",
        "name": "DistilBERT-SST-2-ONNX",
        "task": "sentiment-analysis",
        "runtime": "ONNX Runtime CPU",
        "input_type": "text",
        "artifact": MODEL_DIR / "distilbert" / "model_quantized.onnx",
    },
    "yolo": {
        "model_id": "yolo",
        "name": "YOLOv8n-ONNX",
        "task": "object-detection",
        "runtime": "ONNX Runtime CPU",
        "input_type": "image",
        "artifact": MODEL_DIR / "yolo" / "yolov8n.onnx",
    },
    "llama": {
        "model_id": "llama",
        "name": "TinyLlama-1.1B-Chat-Q2_K",
        "task": "text-generation",
        "runtime": "llama.cpp CPU",
        "input_type": "text",
        "artifact": MODEL_DIR / "tinyllama" / "TinyLlama-1.1B-Chat-v1.0-Q2_K.gguf",
    },
}


def _serialize(entry):
    artifact = entry["artifact"]

    return {
        key: value
        for key, value in entry.items()
        if key != "artifact"
    } | {
        "artifact_path": str(artifact),
        "artifact_exists": artifact.is_file(),
        "status": (
            "artifact_available"
            if artifact.is_file()
            else "artifact_missing"
        ),
    }


def list_models():
    """List registered models without loading inference runtimes."""
    return [
        _serialize(entry)
        for entry in MODEL_REGISTRY.values()
    ]


def get_model(model_id):
    """Get registered model metadata by model ID."""
    model_id = str(model_id).strip().lower()

    if model_id not in MODEL_REGISTRY:
        raise ValueError(
            f"Unknown model '{model_id}'. "
            f"Available models: {', '.join(sorted(MODEL_REGISTRY))}"
        )

    return _serialize(MODEL_REGISTRY[model_id])
