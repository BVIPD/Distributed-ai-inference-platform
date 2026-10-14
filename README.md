# Distributed Multi-Model AI Inference Fabric

A cloud-native platform for serving heterogeneous AI models through a common API gateway, a scheduling layer, containerized inference workers, and Kubernetes orchestration.

## Project overview

The platform integrates three inference workloads:

- **DistilBERT:** text sentiment classification using ONNX Runtime.
- **YOLOv8n:** object detection using ONNX Runtime.
- **TinyLlama 1.1B:** CPU-based text generation using llama.cpp.

A gateway accepts inference requests, the scheduler selects a configured worker, and the worker executes the requested model.

## Architecture

```text
Client
  |
  v
FastAPI Gateway
  |
  v
Adaptive Scheduler
  |
  v
Worker Router
  |
  v
Inference Worker
  |------ DistilBERT (ONNX)
  |------ YOLOv8n (ONNX)
  |------ TinyLlama (llama.cpp)
  |
  v
Inference Response

Kubernetes manages the gateway and worker deployments.
Horizontal Pod Autoscaling is configured for the worker.
```

## Technology stack

- Python 3.10
- FastAPI and Uvicorn
- ONNX Runtime and NumPy
- Hugging Face tokenizers
- llama-cpp-python
- Docker
- Kubernetes and Horizontal Pod Autoscaling
- PowerShell for local development and testing

## Repository structure

```text
.
├── development_v3/
│   ├── main.py
│   ├── router.py
│   ├── scheduler.py
│   ├── models.py
│   ├── worker_api.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── kubernetes-v3.yaml
│   ├── kubernetes-v3.1.yaml
│   ├── benchmark_v3.py
│   ├── benchmark_v3_repeated.py
│   ├── scheduler_v3_evaluation.py
│   ├── scheduler_v3_overhead.py
│   ├── PHASE4_REPORT.md
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

The original prototype is preserved separately from the v3 development implementation.

## Prerequisites

- Docker Desktop with Kubernetes enabled
- `kubectl` configured for the intended cluster
- Python 3.10 for local development
- Sufficient RAM and disk space for the selected model artifacts

TinyLlama inference can be memory-intensive. Avoid running multiple model replicas on a resource-constrained machine without checking available memory.

## Model artifacts

Model weights are not included in this Git repository because of their size and licensing considerations. Obtain compatible artifacts from their official model publishers and place them at the expected paths.

Expected layout:

```text
development_v3/models/
├── distilbert/
│   ├── config.json
│   ├── model_quantized.onnx
│   ├── tokenizer.json
│   ├── tokenizer_config.json
│   ├── special_tokens_map.json
│   └── vocab.txt
├── yolo/
│   ├── yolov8n.onnx
│   └── test_bus.jpg
└── tinyllama/
    └── TinyLlama-1.1B-Chat-v1.0-Q2_K.gguf
```

Use model files compatible with the preprocessing, output format, and runtime expected by `models.py`. The YOLO test image is included as a sample asset; verify its availability in your checkout.

Do not commit model weights, credentials, or private configuration files.

## Build the v3.1 Docker image

From the repository root, run:

```powershell
docker build -t ai-inference-platform:dev3.1 .\development_v3
```

The model artifacts must be present before building because the Dockerfile copies the `models/` directory into the image.

## Deploy to Kubernetes

The supplied v3.1 manifest uses the local image tag `ai-inference-platform:dev3.1`.

First confirm the active Kubernetes context:

```powershell
kubectl config current-context
kubectl get nodes
```

Then apply the manifest:

```powershell
kubectl apply -f .\development_v3\kubernetes-v3.1.yaml
kubectl rollout status deployment/ai-inference-gateway-v3
kubectl rollout status deployment/ai-inference-worker-v3
kubectl get deployments,services,hpa,pods
```

The manifest was validated with Docker Desktop Kubernetes. Review its image settings, resource requests, and limits before using a different cluster.

## API endpoints

The validated local Kubernetes gateway uses NodePort `32089`.

Health check:

```powershell
Invoke-RestMethod http://localhost:32089/health
```

The inference endpoint is:

```text
POST http://localhost:32089/infer
Content-Type: application/json
```

Example BERT request:

```powershell
$body = @{
    model = "bert"
    priority = 5
    text = "This platform is working well."
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri http://localhost:32089/infer `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

Example TinyLlama request:

```powershell
$body = @{
    model = "llama"
    priority = 5
    text = "Explain Kubernetes in two simple sentences."
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri http://localhost:32089/infer `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

For YOLO, provide a base64-encoded image in the `image_base64` request field. Consult `models.py` and `worker_api.py` for the accepted input and response formats.

Interactive API documentation is available at `/docs` when the gateway is running.

## Benchmarks

Detailed results and methodology are documented in `development_v3/PHASE4_REPORT.md`.

### Sequential inference benchmark

| Model | Requests | Successes | Mean latency | Median latency | p95 latency |
|---|---:|---:|---:|---:|---:|
| DistilBERT | 10 | 10 | 74.77 ms | 73.21 ms | 102.89 ms |
| YOLOv8n | 10 | 10 | 178.75 ms | 162.95 ms | 272.01 ms |
| TinyLlama | 10 | 10 | 1930.22 ms | 1953.18 ms | 2781.89 ms |

These measurements describe the tested sequential requests on the development environment. They are not production performance guarantees.

### Scheduler evaluation

The scheduler comparison uses seeded synthetic scenarios and proxy costs, not measured production inference latency. Queue-only scheduling performed better than the adaptive policy on the evaluated proxy. See the report and CSV artifacts for details.

## Current validation status

- v3.1 gateway and worker deployed successfully to Docker Desktop Kubernetes.
- BERT, YOLOv8n, and TinyLlama inference validated through the Kubernetes gateway.
- Worker HPA configured with a minimum of one and maximum of two replicas, targeting 70% CPU utilization.
- Actual HPA scale-out under load has not been demonstrated.
- Multi-worker routing across independently running workers has not been validated.
- The current scheduler uses synthetic worker metrics rather than live queue and resource measurements.

These limitations are part of the current implementation status and should not be interpreted as completed production capabilities.

## Research and reproducibility

Use the benchmark scripts and saved CSV files to reproduce the documented experiments. Compare scheduling policies using identical scenarios, and distinguish synthetic proxy metrics from real end-to-end inference measurements.

Review `development_v3/PHASE4_REPORT.md` for results, measurement details, and limitations.

## License

No license has been selected yet. Unless a license is added, standard copyright restrictions apply; do not assume the repository is open source for unrestricted reuse.
