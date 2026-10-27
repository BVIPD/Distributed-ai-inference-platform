# Distributed Multi-Model AI Inference Fabric

A cloud-native platform for serving heterogeneous AI models through a common API gateway, adaptive scheduling, containerized inference workers, and Kubernetes orchestration.

## 1. Project Overview

This project provides a unified inference platform for three AI workloads:

- **DistilBERT:** Sentiment classification using ONNX Runtime.
- **YOLOv8n:** Object detection using ONNX Runtime.
- **TinyLlama 1.1B:** Text generation using llama.cpp.

The FastAPI gateway accepts inference requests and routes them through the scheduling layer to inference workers. Redis provides queue and result support, while Kubernetes manages application deployments and autoscaling.

Prometheus and Grafana support monitoring and visualization.

## 2. Architecture

```text
                         Client
                           |
                           v
                   FastAPI API Gateway
                           |
                           v
                    Adaptive Scheduler
                           |
                           v
                      Worker Router
                           |
              +------------+------------+
              |            |            |
              v            v            v
           DistilBERT     YOLOv8n     TinyLlama
             ONNX          ONNX       llama.cpp
              |            |            |
              +------------+------------+
                           |
                           v
                   Inference Response

                Kubernetes Orchestration
                           |
              +------------+------------+
              |            |            |
              v            v            v
           Deployments   Services      HPA

              +------------+------------+
              |                         |
              v                         v
           Prometheus                Grafana

                     Redis
              Queue/result support
```

## 3. Technology Stack

| Component | Technology |
|---|---|
| API gateway | Python, FastAPI, Uvicorn |
| Sentiment classification | DistilBERT, ONNX Runtime |
| Object detection | YOLOv8n, ONNX Runtime |
| Text generation | TinyLlama, llama.cpp |
| Scheduling | Adaptive scheduling and worker routing |
| Queue and results | Redis |
| Containerization | Docker |
| Orchestration | Kubernetes |
| Autoscaling | Kubernetes Horizontal Pod Autoscaler |
| Monitoring | Prometheus and Grafana |

## 4. Repository Structure

```text
.
├── development_v3/
│   ├── main.py
│   ├── router.py
│   ├── scheduler.py
│   ├── models.py
│   ├── model_registry.py
│   ├── worker_api.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── kubernetes-v3.1.yaml
│   ├── worker-deployment-final.yaml
│   ├── redis.yaml
│   ├── prometheus.yaml
│   ├── grafana.yaml
│   ├── hpa-final-evidence.yaml
│   ├── metrics-server-patch.yaml
│   ├── PHASE4_REPORT.md
│   ├── benchmark_v3.py
│   ├── benchmark_v3_repeated.py
│   ├── scheduler_v3_evaluation.py
│   ├── scheduler_v3_overhead.py
│   └── models/
├── main.py
├── router.py
├── scheduler.py
├── models.py
├── benchmark.py
├── benchmark_results.csv
├── scheduler_experiment.py
├── scheduler_independent_eval.py
├── deployment.yaml
├── Dockerfile
├── requirements.txt
└── .gitignore
```

The root-level files preserve the original prototype. The `development_v3/` directory contains the newer inference implementation and supporting deployment and monitoring configuration.

## 5. Prerequisites

- Docker Desktop with Kubernetes enabled.
- `kubectl` configured for the intended Kubernetes cluster.
- Python 3.10 for local development.
- Sufficient RAM and disk space for the selected model artifacts.

TinyLlama inference can be memory-intensive. Check available system resources before running multiple inference replicas.

## 6. Model Artifacts

Model weights are excluded from the Git repository because of their size and licensing considerations.

The development implementation uses model artifacts such as:

- DistilBERT ONNX model.
- YOLOv8n ONNX model.
- TinyLlama GGUF model.

Obtain compatible artifacts from their respective publishers, verify their licenses, and place them at the paths expected by the application.

## 7. Local Development

From the repository root, activate the existing virtual environment and start the development application:

```powershell
.\venv\Scripts\Activate.ps1
cd .\development_v3
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8002
```

The local application uses port `8002` in this example. Ensure required dependencies and model artifacts are available before testing inference.

### API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Application information |
| GET | `/health` | Health status |
| GET | `/models` | List registered models |
| GET | `/models/{model_id}` | Retrieve model information |
| POST | `/infer` | Submit an inference request |

Request fields depend on the selected model and the API implementation.

## 8. Docker Deployment

Build the development image from the `development_v3` directory:

```powershell
cd .\development_v3
docker build -t ai-inference-platform:dev3.3 .
```

Ensure the image and its required model artifacts are available to the target container runtime.

The current Kubernetes manifest references the `ai-inference-platform:dev3.3` image. Verify that this image is compatible with the gateway and worker configuration before deploying it to all components.

## 9. Kubernetes Deployment

Check the current Kubernetes context:

```powershell
kubectl config current-context
```

From the repository root, review the manifest and apply it to the intended cluster:

```powershell
kubectl apply -f .\development_v3\kubernetes-v3.1.yaml
```

Additional manifests provide configuration for Redis, Prometheus, Grafana, worker deployments, and autoscaling. Review each manifest before applying it, especially when resources with the same names already exist.

Check deployment status:

```powershell
kubectl get deployments
kubectl get pods
kubectl get services
kubectl get hpa
```

### Access the API

For a local Docker Desktop Kubernetes environment, forward the gateway service port:

```powershell
kubectl port-forward service/ai-inference-gateway-v3 8001:8000
```

Keep the port-forward process running. From another terminal, test the endpoints:

```powershell
Invoke-RestMethod http://127.0.0.1:8001/health
Invoke-RestMethod http://127.0.0.1:8001/models
```

The gateway is then accessible at `http://127.0.0.1:8001` from the local machine.

### Monitoring

The repository includes Prometheus and Grafana manifests under `development_v3/`.

Use these commands when the corresponding services are deployed:

```powershell
kubectl port-forward service/prometheus 9090:9090
kubectl port-forward service/grafana 3000:3000
```

Keep each port-forward process running while accessing its service.

Prometheus collects configured application and worker metrics. Grafana provides dashboards for visualizing configured metrics.

## 10. Validation Results

The following capabilities were validated during development:

- The Kubernetes gateway returned a healthy status.
- The model registry reported three registered models and three available artifacts.
- DistilBERT completed a sentiment classification request.
- YOLOv8n completed an object detection request.
- TinyLlama generated text using CPU inference.
- Prometheus reported the gateway and both worker targets as healthy.
- Kubernetes worker deployments and the Horizontal Pod Autoscaler were configured.
- A previous controlled load test recorded successful requests and observed worker autoscaling.

These results reflect the development environment and should not be interpreted as a guarantee of performance on other systems.

### Historical Model Benchmark

The following results were recorded during earlier sequential benchmark runs:

| Model | Mean latency (ms) | Median latency (ms) | P95 latency (ms) |
|---|---:|---:|---:|
| DistilBERT | 74.77 | 73.21 | 102.89 |
| YOLOv8n | 178.75 | 162.95 | 272.01 |
| TinyLlama | 1930.22 | 1953.18 | 2781.89 |

These are historical measurements, not results from a fresh benchmark. Actual latency depends on hardware, input size, model configuration, concurrency, and system load.

### Scheduler Evaluation

The project includes evaluation scripts for round-robin, queue-based, resource-based, and adaptive scheduling strategies.

Some comparisons use synthetic scenarios and proxy-cost calculations. These results are useful for studying scheduler behavior, but they must not be interpreted as live hardware measurements or proof that one scheduling strategy always performs best.

Refer to `development_v3/PHASE4_REPORT.md` and the evaluation scripts for the methodology and additional results.

## 11. Limitations and Future Work

Potential improvements include:

- Running repeated, statistically controlled benchmarks under concurrent load.
- Comparing scheduling strategies across multiple workload distributions.
- Improving resource-aware scheduling using reliable live measurements.
- Evaluating autoscaling response time and sustained throughput.
- Expanding monitoring dashboards and operational observability.
- Testing failure recovery and queue behavior under worker restarts.
- Improving deployment portability across Kubernetes environments.

## 12. Reproducibility

Record the Docker image tag, model artifact versions, Kubernetes configuration, and benchmark conditions when reproducing results.

Keep historical benchmarks, synthetic scheduler evaluations, and current live telemetry clearly distinguished in reports.

## 13. License

Add the project's chosen license before distributing or reusing the implementation. Verify the licenses of the underlying models and dependencies separately.