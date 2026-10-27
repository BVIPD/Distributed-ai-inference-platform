import base64
import binascii
import os
import tempfile
import time
from io import BytesIO

from fastapi import FastAPI, HTTPException, Request
from prometheus_client import Counter, Histogram, make_asgi_app
from pydantic import BaseModel
from PIL import Image, UnidentifiedImageError

from models import bert_model, llama_model, yolo_model

app = FastAPI(title="AI Inference Worker", version="1.3.0")

WORKER_ID = os.getenv("WORKER_ID", "worker-1")
SUPPORTED_MODELS = {"bert", "yolo", "llama"}

WORKER_INFERENCES = Counter(
    "worker_inference_requests_total",
    "Inference requests processed by this worker",
    ["worker_id", "model", "status"],
)

WORKER_INFERENCE_DURATION = Histogram(
    "worker_inference_duration_seconds",
    "Worker-side inference duration in seconds",
    ["worker_id", "model"],
)


class WorkerRequest(BaseModel):
    model: str
    text: str | None = None
    image_base64: str | None = None


@app.get("/health")
def health():
    return {
        "status": "ok",
        "worker_id": WORKER_ID,
        "supported_models": sorted(SUPPORTED_MODELS),
    }


@app.post("/execute")
def execute(request: WorkerRequest):
    model = request.model.strip().lower()
    start = time.perf_counter()
    status = "error"

    try:
        if model not in SUPPORTED_MODELS:
            raise HTTPException(
                status_code=400,
                detail="Supported models: bert, yolo, llama.",
            )

        if model == "bert":
            result = bert_model(
                request.text or "This platform is working great!"
            )

        elif model == "llama":
            result = llama_model(
                request.text or "Explain cloud computing in one sentence."
            )

        else:
            if not request.image_base64:
                raise HTTPException(
                    status_code=400,
                    detail="image_base64 is required for YOLO inference.",
                )

            try:
                image_bytes = base64.b64decode(
                    request.image_base64,
                    validate=True,
                )

                with Image.open(BytesIO(image_bytes)) as image:
                    image.verify()

            except (
                binascii.Error,
                ValueError,
                UnidentifiedImageError,
                OSError,
            ) as exc:
                raise HTTPException(
                    status_code=400,
                    detail="image_base64 must contain a valid encoded image.",
                ) from exc

            image_path = None

            try:
                with tempfile.NamedTemporaryFile(
                    suffix=".img",
                    delete=False,
                ) as temporary:
                    temporary.write(image_bytes)
                    image_path = temporary.name

                result = yolo_model(image_path)

            finally:
                if image_path and os.path.exists(image_path):
                    os.unlink(image_path)

        status = "success"

        return {
            "worker_id": WORKER_ID,
            "result": result,
            "execution_status": "completed",
        }

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    finally:
        WORKER_INFERENCES.labels(WORKER_ID, model, status).inc()
        WORKER_INFERENCE_DURATION.labels(
            WORKER_ID,
            model,
        ).observe(time.perf_counter() - start)


app.mount("/metrics", make_asgi_app())
