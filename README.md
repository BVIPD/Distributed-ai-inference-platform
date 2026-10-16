 <div align="center">

# Distributed Multi-Model AI Inference Fabric

### A Cloud-Native Platform for Heterogeneous AI Inference, Worker Scheduling, and Kubernetes Autoscaling

<p>
  <img src="https://img.shields.io/badge/Python-3.10-3776AB?logo=python&logoColor=white" alt="Python 3.10">
  <img src="https://img.shields.io/badge/FastAPI-Gateway-009688?logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/Docker-Containers-2496ED?logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/Kubernetes-Orchestration-326CE5?logo=kubernetes&logoColor=white" alt="Kubernetes">
  <img src="https://img.shields.io/badge/ONNX_Runtime-Inference-7B61FF" alt="ONNX Runtime">
</p>

**Research focus:** Heterogeneous Model Serving · Worker Scheduling · Multi-Model Inference · Cloud-Native Orchestration

[Architecture](#system-architecture) · [Experiments](#experimental-results) · [Deployment](#deployment) · [Reproducibility](#reproducibility) · [Future Work](#limitations-and-future-work)

</div>

---

## Abstract

Serving heterogeneous artificial intelligence models through a shared inference platform introduces challenges in request routing, computational cost, resource allocation, and workload management. Different model families have different execution characteristics, making a common serving interface and an explicit worker-selection policy important systems-design considerations.

This project implements a cloud-native multi-model inference platform integrating a FastAPI gateway, a scheduling and routing layer, independent inference workers, containerized model runtimes, and Kubernetes orchestration. The platform supports three workloads: DistilBERT sentiment classification, YOLOv8n object detection, and TinyLlama text generation.

The implementation provides an experimental environment for evaluating inference latency, request completion, worker distribution, and horizontal scaling. Initial validation demonstrates successful execution of all three model workloads and routing across multiple workers. Scheduler-policy evaluation currently uses seeded synthetic scenarios and proxy costs; these results are preliminary and do not establish real-world scheduling superiority.

## Research Motivation

### Problem Statement

A shared inference service must accommodate workloads with different input formats, execution characteristics, and resource requirements. This creates several practical challenges:

- **Workload heterogeneity:** Serving text classification, object detection, and text generation through a common interface.
- **Worker selection:** Choosing an appropriate inference worker for incoming requests.
- **Resource management:** Coordinating inference workers and Kubernetes-based scaling.
- **Experimental evaluation:** Comparing scheduling policies reproducibly without confusing synthetic estimates with measured system behavior.

### Research Question

> How do different worker-selection policies affect request distribution and estimated scheduling cost in a cloud-native platform serving heterogeneous AI workloads, and how can Kubernetes autoscaling support its deployment?

The current implementation provides a platform for investigating this question. Establishing scheduling effectiveness requires controlled experiments using measured runtime conditions and comparable baselines.

## Research Objectives

1. Develop a unified API for serving heterogeneous AI models.
2. Integrate a scheduler and worker router between the gateway and inference workers.
3. Deploy the platform using Docker and Kubernetes.
4. Measure inference latency and request completion for supported workloads.
5. Examine worker distribution and observed horizontal scaling.
6. Compare scheduling policies using reproducible scenarios and document their limitations.

## System Architecture

The platform separates request handling, worker selection, model execution, and infrastructure orchestration.

<p align="center">
  <img src="development_v3/Architecture.png" alt="Conceptual system architecture showing client applications, FastAPI gateway, request scheduler, worker router, two inference workers, supported models, and Kubernetes autoscaling." width="100%">
</p>

<p align="center">
  <em>Figure 1. Conceptual architecture of the Distributed Multi-Model AI Inference Fabric. Model availability and execution depend on the deployed worker configuration.</em>
</p>

### Architecture Components

| Component | Responsibility |
|---|---|
| FastAPI Gateway | Accepts inference requests and returns model responses |
| Request Scheduler | Evaluates the configured worker-selection policy |
| Worker Router | Routes requests to the selected worker |
| Inference Workers | Execute supported models using configured runtimes |
| Docker | Packages application services and model dependencies |
| Kubernetes | Manages deployments, services, and replicas |
| Horizontal Pod Autoscaler | Adjusts worker replica count according to the configured CPU utilization target |

## Supported AI Workloads

| Workload | Model | Task | Runtime |
|---|---|---|---|
| Text | DistilBERT | Sentiment classification | ONNX Runtime |
| Vision | YOLOv8n | Object detection | ONNX Runtime |
| Language Generation | TinyLlama 1.1B | Text generation | llama.cpp |

These workloads provide a starting point for examining heterogeneous model serving. The current evaluation does not establish performance across all model sizes, hardware configurations, or production workloads.

## Technology Stack

- **Application:** Python 3.10, FastAPI, Uvicorn
- **Inference:** ONNX Runtime, NumPy, Hugging Face tokenizers, `llama-cpp-python`
- **Containerization:** Docker
- **Orchestration:** Kubernetes, Deployments, Services, Horizontal Pod Autoscaler
- **Evaluation:** Python benchmark scripts, CSV artifacts, synthetic scheduler scenarios
- **Development environment:** Docker Desktop Kubernetes and PowerShell

## Experimental Results

The following results summarize tests performed in the development environment. They are not production performance guarantees.

### 1. Sequential Inference Benchmark

| Model | Requests | Successful | Mean Latency | Median Latency | p95 Latency |
|---|---:|---:|---:|---:|---:|
| DistilBERT | 10 | 10 | 74.77 ms | 73.21 ms | 102.89 ms |
| YOLOv8n | 10 | 10 | 178.75 ms | 162.95 ms | 272.01 ms |
| TinyLlama | 10 | 10 | 1,930.22 ms | 1,953.18 ms | 2,781.89 ms |

Detailed methodology and results are documented in [`development_v3/PHASE4_REPORT.md`](development_v3/PHASE4_REPORT.md).

These sequential measurements do not characterize sustained throughput or latency under concurrent load.

### 2. Multi-Worker Routing Validation

A post-deployment regression test sent 20 BERT requests through the Kubernetes gateway.

| Metric | Result |
|---|---:|
| Requests submitted | 20 |
| Successful responses | 20 |
| Failed responses | 0 |
| Requests routed to worker-1 | 10 |
| Requests routed to worker-2 | 10 |

All requests completed successfully, with an even worker-selection distribution in this run. This does not guarantee equal distribution for every workload or scheduling condition.

### 3. Kubernetes Autoscaling Validation

The worker Horizontal Pod Autoscaler is configured as follows:

| Setting | Value |
|---|---:|
| Minimum replicas | 1 |
| Maximum replicas | 2 |
| CPU utilization target | 70% |

During a controlled test, the worker deployment scaled from one replica to two. HPA metrics and worker service endpoints were subsequently verified, and inference continued successfully after scale-out.

This demonstrates observed scale-out behavior in the tested Docker Desktop Kubernetes environment. It does not establish production-scale elasticity or prove that autoscaling reduced end-to-end latency.

### 4. Scheduler Evaluation

The current scheduler comparison uses seeded synthetic scenarios and proxy costs rather than live worker queues, measured resource availability, and real-time inference-cost estimates.

The queue-only policy performed better than the adaptive policy under the evaluated proxy. This preliminary result illustrates that a more complex policy does not necessarily outperform a simpler baseline under a particular evaluation model.

Further experiments should compare policies using measured workloads and actual worker conditions before drawing broader conclusions.

## Reproducibility

The repository contains application code, Kubernetes manifests, benchmark scripts, and experiment artifacts for inspecting and reproducing the documented tests.

### Repository Structure

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
│   ├── Architecture.png
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

The original prototype is preserved separately from the v3 implementation.

### Prerequisites

- Docker Desktop with Kubernetes enabled
- `kubectl` configured for the intended cluster
- Python 3.10 for local development
- Compatible model artifacts
- Sufficient RAM and disk space, particularly for TinyLlama

### Model Artifacts

Model weights are not included in this repository. Obtain compatible artifacts from their official publishers and comply with their licenses.

Expected directory layout:

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

Verify that the artifacts match the paths, preprocessing, and output formats expected by the implementation.

## Deployment

Run these commands from the repository root in PowerShell.

### 1. Build the Docker Image

Ensure the required model artifacts are present before building because the Dockerfile copies the `models/` directory into the image.

```powershell
docker build -t ai-inference-platform:dev3.1 .\development_v3
```

### 2. Verify the Kubernetes Context

```powershell
kubectl config current-context
kubectl get nodes
```

Confirm that the intended cluster is active before applying manifests.

### 3. Apply the v3.1 Manifest

```powershell
kubectl apply -f .\development_v3\kubernetes-v3.1.yaml
```

### 4. Wait for the Deployments

```powershell
kubectl rollout status deployment/ai-inference-gateway-v3 --timeout=120s
kubectl rollout status deployment/ai-inference-worker-v3 --timeout=120s
kubectl rollout status deployment/ai-inference-worker-v3-2 --timeout=120s
```

Inspect the deployed resources:

```powershell
kubectl get deployments,services,hpa,pods
```

The v3.1 manifest is designed to preserve the original v2 deployment. Review image settings, resource requests, and limits before deploying to another cluster.

## API Usage

The validated local Kubernetes gateway uses NodePort `32089`.

### Health Check

```powershell
Invoke-RestMethod -Uri "http://localhost:32089/health"
```

Expected response:

```json
{
  "status": "ok"
}
```

### BERT Sentiment Inference

```powershell
$body = @{
    model = "bert"
    priority = 5
    text = "This platform is working well."
} | ConvertTo-Json -Compress

Invoke-RestMethod `
    -Uri "http://localhost:32089/infer" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

### TinyLlama Text Generation

```powershell
$body = @{
    model = "llama"
    priority = 5
    text = "Explain Kubernetes in two simple sentences."
} | ConvertTo-Json -Compress

Invoke-RestMethod `
    -Uri "http://localhost:32089/infer" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

### YOLO Object Detection

Use the `yolo` model alias and supply a base64-encoded image in the `image_base64` request field. Refer to `development_v3/models.py` and `development_v3/worker_api.py` for the accepted input and response formats.

Interactive API documentation is available at [`http://localhost:32089/docs`](http://localhost:32089/docs) while the gateway is running.

## Limitations and Future Work

The current implementation is an experimental platform, not a production-ready inference service.

### Current Limitations

- **Synthetic scheduling metrics:** The scheduler does not yet rely on a fully validated live measurement pipeline for worker selection.
- **Preliminary policy evaluation:** Synthetic proxy results cannot establish general scheduling superiority.
- **Limited workload scale:** The demonstrated setup uses a small number of workers in a local development cluster.
- **Limited performance evidence:** Sequential latency measurements do not characterize sustained throughput, tail latency under contention, or large-scale concurrency.
- **Autoscaling scope:** The observed HPA behavior validates a configured CPU-based scale-out path, not an optimized autoscaling policy.

### Research Directions

1. Integrate live queue depth, worker CPU utilization, and measured inference latency into scheduling decisions.
2. Compare round-robin, queue-only, resource-aware, and adaptive scheduling baselines.
3. Run repeated trials with controlled request mixes, concurrency levels, and model combinations.
4. Report throughput, p50/p95/p99 latency, error rate, scheduling overhead, and resource utilization.
5. Investigate interactions between scheduling decisions, autoscaling delay, and end-to-end inference performance.
6. Evaluate whether added scheduling complexity produces measurable benefits over simpler policies.

These experiments would help determine whether the scheduling approach provides benefits beyond simpler baselines.

## Project Artifacts

| Artifact | Purpose |
|---|---|
| `development_v3/kubernetes-v3.1.yaml` | Multi-worker Kubernetes deployment |
| `development_v3/benchmark_v3.py` | Sequential benchmark |
| `development_v3/benchmark_v3_repeated.py` | Repeated benchmark |
| `development_v3/scheduler_v3_evaluation.py` | Scheduler evaluation |
| `development_v3/scheduler_v3_overhead.py` | Scheduler overhead evaluation |
| `development_v3/PHASE4_REPORT.md` | Experimental report and validation details |

Use the scripts and report together when interpreting results. Confirm experiment settings and saved data before making comparisons.

## Conclusion

This project establishes a reproducible cloud-native environment for serving heterogeneous AI workloads through a common gateway and multiple inference workers. The implementation demonstrates successful multi-model inference, worker routing, and Kubernetes HPA scale-out in a local development environment.

The main research opportunity is the systematic evaluation of scheduling policies using measured runtime conditions. Establishing a robust adaptive-scheduling contribution requires controlled comparisons against simpler baselines and transparent reporting of performance, overhead, and limitations.

## License

No license has been selected yet. Until a license is added, standard copyright restrictions apply.
