
import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import onnxruntime as ort
from PIL import Image
from tokenizers import Tokenizer


# ============================================================
# MODEL PATHS AND CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).parent / "models"

# DistilBERT
MODEL_DIR = BASE_DIR / "distilbert"
MODEL_PATH = MODEL_DIR / "model_quantized.onnx"
MAX_LENGTH = 128

# YOLOv8n
YOLO_DIR = BASE_DIR / "yolo"
YOLO_PATH = YOLO_DIR / "yolov8n.onnx"
YOLO_SIZE = 640
YOLO_CONFIDENCE = 0.25
YOLO_IOU = 0.45

# TinyLlama
LLAMA_DIR = BASE_DIR / "tinyllama"
LLAMA_PATH = LLAMA_DIR / "TinyLlama-1.1B-Chat-v1.0-Q2_K.gguf"
LLAMA_CONTEXT_SIZE = 256
LLAMA_THREADS = 2
LLAMA_MAX_TOKENS = 64


# ============================================================
# YOLO COCO LABELS
# ============================================================

COCO_LABELS = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus",
    "train", "truck", "boat", "traffic light", "fire hydrant",
    "stop sign", "parking meter", "bench", "bird", "cat", "dog",
    "horse", "sheep", "cow", "elephant", "bear", "zebra",
    "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase",
    "frisbee", "skis", "snowboard", "sports ball", "kite",
    "baseball bat", "baseball glove", "skateboard", "surfboard",
    "tennis racket", "bottle", "wine glass", "cup", "fork", "knife",
    "spoon", "bowl", "banana", "apple", "sandwich", "orange",
    "broccoli", "carrot", "hot dog", "pizza", "donut", "cake",
    "chair", "couch", "potted plant", "bed", "dining table",
    "toilet", "tv", "laptop", "mouse", "remote", "keyboard",
    "cell phone", "microwave", "oven", "toaster", "sink",
    "refrigerator", "book", "clock", "vase", "scissors",
    "teddy bear", "hair drier", "toothbrush",
]


# ============================================================
# MODEL 1: DISTILBERT SENTIMENT ANALYSIS
# ============================================================

@lru_cache(maxsize=1)
def load_model():
    """Load and cache the DistilBERT ONNX model and tokenizer."""

    if not MODEL_PATH.is_file():
        raise RuntimeError(f"ONNX model not found: {MODEL_PATH}")

    tokenizer = Tokenizer.from_file(
        str(MODEL_DIR / "tokenizer.json")
    )

    tokenizer.enable_truncation(max_length=MAX_LENGTH)
    tokenizer.enable_padding(
        length=MAX_LENGTH,
        pad_id=tokenizer.token_to_id("[PAD]") or 0,
    )

    session = ort.InferenceSession(
        str(MODEL_PATH),
        providers=["CPUExecutionProvider"],
    )

    with open(MODEL_DIR / "config.json", encoding="utf-8") as file:
        config = json.load(file)

    labels = config.get(
        "id2label",
        {"0": "NEGATIVE", "1": "POSITIVE"},
    )

    return tokenizer, session, labels


def bert_model(text="This platform is working great!"):
    """Classify text sentiment using DistilBERT on CPU."""

    if not isinstance(text, str) or not text.strip():
        raise ValueError("Text must be a non-empty string.")

    tokenizer, session, labels = load_model()
    encoded = tokenizer.encode(text)

    inputs = {}

    for item in session.get_inputs():
        if item.name == "input_ids":
            inputs[item.name] = np.asarray(
                [encoded.ids], dtype=np.int64
            )

        elif item.name == "attention_mask":
            inputs[item.name] = np.asarray(
                [encoded.attention_mask], dtype=np.int64
            )

        elif item.name == "token_type_ids":
            inputs[item.name] = np.asarray(
                [encoded.type_ids], dtype=np.int64
            )

    logits = session.run(None, inputs)[0][0]

    shifted = logits - np.max(logits)
    probabilities = np.exp(shifted)
    probabilities /= np.sum(probabilities)

    index = int(np.argmax(probabilities))

    return {
        "model": "DistilBERT-SST-2-ONNX",
        "task": "sentiment-analysis",
        "label": labels.get(
            str(index),
            labels.get(index, str(index)),
        ),
        "confidence": round(float(probabilities[index]), 4),
        "input_text": text,
        "runtime": "ONNX Runtime CPU",
    }


# ============================================================
# MODEL 2: YOLOV8N OBJECT DETECTION
# ============================================================

@lru_cache(maxsize=1)
def load_yolo_model():
    """Load and cache the YOLOv8n ONNX model."""

    if not YOLO_PATH.is_file():
        raise RuntimeError(
            f"YOLO ONNX model not found: {YOLO_PATH}"
        )

    session = ort.InferenceSession(
        str(YOLO_PATH),
        providers=["CPUExecutionProvider"],
    )

    input_info = session.get_inputs()[0]

    if input_info.shape != [1, 3, YOLO_SIZE, YOLO_SIZE]:
        raise RuntimeError(
            f"Unexpected YOLO input shape: {input_info.shape}"
        )

    return session


def _nms(boxes, scores, threshold):
    """Apply non-maximum suppression to bounding boxes."""

    if len(boxes) == 0:
        return []

    boxes = np.asarray(boxes, dtype=np.float32)
    scores = np.asarray(scores, dtype=np.float32)

    x1, y1, x2, y2 = boxes.T

    areas = (
        np.maximum(0, x2 - x1)
        * np.maximum(0, y2 - y1)
    )

    order = scores.argsort()[::-1]
    kept = []

    while order.size:
        current = int(order[0])
        kept.append(current)

        if order.size == 1:
            break

        rest = order[1:]

        xx1 = np.maximum(x1[current], x1[rest])
        yy1 = np.maximum(y1[current], y1[rest])
        xx2 = np.minimum(x2[current], x2[rest])
        yy2 = np.minimum(y2[current], y2[rest])

        intersection = (
            np.maximum(0, xx2 - xx1)
            * np.maximum(0, yy2 - yy1)
        )

        union = areas[current] + areas[rest] - intersection
        iou = intersection / np.maximum(union, 1e-7)

        order = rest[iou <= threshold]

    return kept


def yolo_model(image_path):
    """Detect objects in an image using YOLOv8n on CPU."""

    if not isinstance(image_path, str) or not image_path.strip():
        raise ValueError("A non-empty image_path is required.")

    path = Path(image_path)

    if not path.is_file():
        raise ValueError(f"Image file not found: {image_path}")

    try:
        with Image.open(path) as source:
            image = source.convert("RGB")
            original_width, original_height = image.size

            if original_width <= 0 or original_height <= 0:
                raise ValueError("Image dimensions must be positive.")

            scale = min(
                YOLO_SIZE / original_width,
                YOLO_SIZE / original_height,
            )

            resized_width = round(original_width * scale)
            resized_height = round(original_height * scale)

            resized = image.resize(
                (resized_width, resized_height),
                Image.Resampling.BILINEAR,
            )

            canvas = Image.new(
                "RGB",
                (YOLO_SIZE, YOLO_SIZE),
                (114, 114, 114),
            )

            pad_x = (YOLO_SIZE - resized_width) // 2
            pad_y = (YOLO_SIZE - resized_height) // 2

            canvas.paste(resized, (pad_x, pad_y))

            tensor = np.asarray(
                canvas, dtype=np.float32
            ) / 255.0

            tensor = np.transpose(tensor, (2, 0, 1))[None, ...]

    except (OSError, ValueError) as exc:
        raise ValueError(f"Could not read image: {exc}") from exc

    session = load_yolo_model()

    output = session.run(
        None,
        {session.get_inputs()[0].name: tensor},
    )[0]

    if output.ndim != 3 or output.shape[0] != 1:
        raise RuntimeError(
            f"Unexpected YOLO output shape: {output.shape}"
        )

    predictions = output[0]

    if predictions.shape[0] == 84:
        predictions = predictions.T
    elif predictions.shape[1] != 84:
        raise RuntimeError(
            f"Expected 84 values per YOLO prediction, got {output.shape}"
        )

    centers = predictions[:, :2]
    sizes = predictions[:, 2:4]
    class_scores = predictions[:, 4:]

    class_ids = np.argmax(class_scores, axis=1)
    confidences = class_scores[
        np.arange(len(class_scores)), class_ids
    ]

    candidates = np.flatnonzero(
        confidences >= YOLO_CONFIDENCE
    )

    boxes = []
    scores = []
    ids = []

    for idx in candidates:
        cx, cy = centers[idx]
        width, height = sizes[idx]

        x1 = (cx - width / 2 - pad_x) / scale
        y1 = (cy - height / 2 - pad_y) / scale
        x2 = (cx + width / 2 - pad_x) / scale
        y2 = (cy + height / 2 - pad_y) / scale

        x1 = float(np.clip(x1, 0, original_width))
        y1 = float(np.clip(y1, 0, original_height))
        x2 = float(np.clip(x2, 0, original_width))
        y2 = float(np.clip(y2, 0, original_height))

        if x2 <= x1 or y2 <= y1:
            continue

        boxes.append([x1, y1, x2, y2])
        scores.append(float(confidences[idx]))
        ids.append(int(class_ids[idx]))

    kept = []

    for class_id in sorted(set(ids)):
        indices = [
            i for i, value in enumerate(ids)
            if value == class_id
        ]

        selected = _nms(
            [boxes[i] for i in indices],
            [scores[i] for i in indices],
            YOLO_IOU,
        )

        kept.extend(indices[i] for i in selected)

    kept.sort(key=lambda i: scores[i], reverse=True)

    detections = [
        {
            "label": (
                COCO_LABELS[ids[i]]
                if 0 <= ids[i] < len(COCO_LABELS)
                else str(ids[i])
            ),
            "class_id": ids[i],
            "confidence": round(scores[i], 4),
            "bbox_xyxy": [
                round(value, 2) for value in boxes[i]
            ],
        }
        for i in kept
    ]

    return {
        "model": "YOLOv8n-ONNX",
        "task": "object-detection",
        "runtime": "ONNX Runtime CPU",
        "image_width": original_width,
        "image_height": original_height,
        "detection_count": len(detections),
        "detections": detections,
    }


# ============================================================
# MODEL 3: TINYLLAMA TEXT GENERATION
# ============================================================

@lru_cache(maxsize=1)
def load_llama_model():
    """Load and cache TinyLlama only when text generation is requested."""

    if not LLAMA_PATH.is_file():
        raise RuntimeError(
            f"TinyLlama GGUF model not found: {LLAMA_PATH}"
        )

    try:
        from llama_cpp import Llama
    except ImportError as exc:
        raise RuntimeError(
            "llama-cpp-python is not installed. "
            "Install the project requirements."
        ) from exc

    return Llama(
        model_path=str(LLAMA_PATH),
        n_ctx=LLAMA_CONTEXT_SIZE,
        n_batch=32,
        n_threads=LLAMA_THREADS,
        n_gpu_layers=0,
        verbose=False,
    )


def llama_model(text="Explain cloud computing in one sentence."):
    """Generate a concise response using TinyLlama on CPU."""

    if not isinstance(text, str) or not text.strip():
        raise ValueError("Text prompt must be a non-empty string.")

    model = load_llama_model()

    result = model.create_chat_completion(
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant. "
                    "Answer concisely."
                ),
            },
            {
                "role": "user",
                "content": text.strip(),
            },
        ],
        max_tokens=LLAMA_MAX_TOKENS,
        temperature=0.2,
    )

    answer = result["choices"][0]["message"]["content"]

    return {
        "model": "TinyLlama-1.1B-Chat-Q2_K",
        "task": "text-generation",
        "response": (answer or "").strip(),
        "runtime": "llama.cpp CPU",
    }
