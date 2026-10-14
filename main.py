
from fastapi import FastAPI, HTTPException
from router import route_request

app = FastAPI()


@app.get("/")
def home():
    return {"message": "AI Inference Platform Running"}


@app.post("/infer")
def infer(model: str, priority: int = 1):
    try:
        return route_request(model, priority)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
