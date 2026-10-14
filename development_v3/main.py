
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from router import route_request

app = FastAPI(
    title="Distributed Multi-Model AI Inference Fabric",
    version="3.0.0",
)


class InferenceRequest(BaseModel):
    model: str
    priority: int = Field(default=1, ge=1, le=10)
    text: str | None = None
    image_base64: str | None = None


@app.get("/")
def home():
    return {
        "message": "AI Inference Platform Development v3",
        "status": "development",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/infer")
def infer(request: InferenceRequest):
    try:
        return route_request(
            model=request.model,
            priority=request.priority,
            text=request.text,
            image_base64=request.image_base64,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
