import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, make_asgi_app
from pydantic import BaseModel, Field, model_validator

from model_registry import get_model, list_models
from router import (
    get_redis,
    route_request,
    start_queue_consumer,
    stop_queue_consumer,
)


# ---------------------------------------------------------------------
# Prometheus metrics
# ---------------------------------------------------------------------

HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["app", "method", "endpoint", "status"],
)

HTTP_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["app", "method", "endpoint"],
)

INFERENCE_REQUESTS = Counter(
    "inference_requests_total",
    "Inference requests by model and outcome",
    ["model", "status"],
)

INFERENCE_DURATION = Histogram(
    "inference_duration_seconds",
    "End-to-end inference request duration in seconds",
    ["model"],
)


# ---------------------------------------------------------------------
# Application lifecycle
# ---------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_queue_consumer()
    try:
        yield
    finally:
        stop_queue_consumer()


# ---------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------

app = FastAPI(
    title="Distributed Multi-Model AI Inference Fabric",
    description=(
        "Cloud-native multi-model inference gateway with Redis-backed "
        "request routing, model registry, and Prometheus monitoring."
    ),
    version="3.2.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------
# CORS configuration
# Allows the local and deployed project websites to access the API.
# ---------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8080",
        "http://localhost:8080",
        "https://tourmaline-gelato-f80707.netlify.app",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


# ---------------------------------------------------------------------
# Request schema
# ---------------------------------------------------------------------

class InferenceRequest(BaseModel):
    model: str = Field(
        ...,
        description="Registered model identifier: bert, yolo, or llama.",
    )

    priority: int = Field(
        default=1,
        ge=1,
        le=10,
        description="Scheduling priority from 1 to 10.",
    )

    text: str | None = None
    image_base64: str | None = None

    @model_validator(mode="after")
    def validate_input(self):
        normalized_model = self.model.strip().lower()

        if not normalized_model:
            raise ValueError("Model identifier cannot be empty.")

        if normalized_model in {"bert", "llama"}:
            if not self.text or not self.text.strip():
                raise ValueError(
                    f"Model '{normalized_model}' requires non-empty text."
                )

        if normalized_model == "yolo":
            if not self.image_base64:
                raise ValueError(
                    "Model 'yolo' requires image_base64."
                )

        return self


# ---------------------------------------------------------------------
# HTTP request metrics middleware
# ---------------------------------------------------------------------

@app.middleware("http")
async def collect_http_metrics(request: Request, call_next):
    start = time.perf_counter()
    status = "500"
    endpoint = request.url.path

    try:
        response = await call_next(request)
        status = str(response.status_code)
        return response

    finally:
        if endpoint != "/metrics" and not endpoint.startswith("/metrics/"):
            HTTP_REQUESTS.labels(
                "gateway",
                request.method,
                endpoint,
                status,
            ).inc()

            HTTP_DURATION.labels(
                "gateway",
                request.method,
                endpoint,
            ).observe(time.perf_counter() - start)


# ---------------------------------------------------------------------
# Root and health endpoints
# ---------------------------------------------------------------------

@app.get("/", tags=["Platform"])
def home():
    return {
        "message": "Distributed Multi-Model AI Inference Fabric",
        "version": app.version,
        "status": "running",
        "endpoints": {
            "health": "/health",
            "models": "/models",
            "inference": "/infer",
            "metrics": "/metrics",
            "documentation": "/docs",
        },
    }


@app.get("/health", tags=["Platform"])
def health():
    try:
        get_redis().ping()
        redis_status = "ok"
    except Exception:
        redis_status = "unavailable"

    registered_models = list_models()

    available_models = sum(
        1 for model in registered_models if model["artifact_exists"]
    )

    return {
        "status": "ok" if redis_status == "ok" else "degraded",
        "redis": redis_status,
        "model_registry": {
            "registered": len(registered_models),
            "artifacts_available": available_models,
        },
    }


# ---------------------------------------------------------------------
# Model registry endpoints
# ---------------------------------------------------------------------

@app.get("/models", tags=["Model Registry"])
def models():
    registered_models = list_models()

    return {
        "count": len(registered_models),
        "models": registered_models,
    }


@app.get("/models/{model_id}", tags=["Model Registry"])
def model_details(model_id: str):
    try:
        return get_model(model_id)

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


# ---------------------------------------------------------------------
# Inference endpoint
# ---------------------------------------------------------------------

@app.post("/infer", tags=["Inference"])
def infer(request: InferenceRequest):
    model = request.model.strip().lower()
    start = time.perf_counter()
    status = "error"

    try:
        # Reject unknown models before enqueueing a request.
        get_model(model)

        result = route_request(
            model=model,
            priority=request.priority,
            text=request.text,
            image_base64=request.image_base64,
        )

        status = "success"
        return result

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except NotImplementedError as exc:
        raise HTTPException(
            status_code=501,
            detail=str(exc),
        ) from exc

    except TimeoutError as exc:
        raise HTTPException(
            status_code=504,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    finally:
        INFERENCE_REQUESTS.labels(model, status).inc()

        INFERENCE_DURATION.labels(model).observe(
            time.perf_counter() - start
        )


# ---------------------------------------------------------------------
# Prometheus metrics endpoint
# ---------------------------------------------------------------------

app.mount("/metrics", make_asgi_app())