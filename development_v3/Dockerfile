FROM python:3.10-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV OMP_NUM_THREADS=2

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py router.py scheduler.py models.py model_registry.py worker_api.py ./
COPY models/ ./models/

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
