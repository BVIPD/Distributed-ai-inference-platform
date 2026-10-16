# Distributed Multi-Model AI Inference Platform
### A Cloud-Native Platform for Heterogeneous AI Inference, Worker Scheduling, and Kubernetes Autoscaling

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10-blue?logo=python" alt="Python 3.10" />
  <img src="https://img.shields.io/badge/FastAPI-API%20Gateway-009688?logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Docker-Containerized%20Inference-2496ED?logo=docker" alt="Docker" />
  <img src="https://img.shields.io/badge/Kubernetes-Orchestration-326CE5?logo=kubernetes" alt="Kubernetes" />
  <img src="https://img.shields.io/badge/ONNX%20Runtime-Model%20Inference-7B61FF" alt="ONNX Runtime" />
</p>

<p align="center">
  <b>Research focus:</b> heterogeneous model serving · worker selection · multi-model inference · resource-aware orchestration
</p>

<p align="center">
  <a href="#research-motivation">Research Motivation</a> ·
  <a href="#system-architecture">Architecture</a> ·
  <a href="#experimental-results">Results</a> ·
  <a href="#reproducibility">Reproducibility</a> ·
  <a href="#limitations-and-future-work">Future Work</a>
</p>

---

## Abstract

Serving heterogeneous artificial intelligence models through a shared inference platform introduces challenges in request routing, computational cost, resource allocation, and workload management. Different model families exhibit different execution characteristics, making a common serving interface and efficient worker selection important system-design considerations.

This project presents a cloud-native multi-model inference platform that integrates a FastAPI gateway, a scheduling layer, independent inference workers, containerized model runtimes, and Kubernetes-based orchestration. The platform supports three distinct workloads: DistilBERT sentiment classification, YOLOv8n object detection, and TinyLlama text generation.

The implementation provides a reproducible environment for evaluating inference latency, request completion, worker distribution, and horizontal scaling. Initial experiments demonstrate successful execution of all three model workloads and operation across multiple workers. Scheduler evaluation currently uses seeded synthetic scenarios and proxy costs; therefore, its results are preliminary and do not establish real-world scheduling superiority.

The platform serves as an experimental foundation for investigating scheduling strategies for heterogeneous AI inference under resource-constrained deployment conditions.

## Research Motivation

### The problem

A multi-model inference service must accommodate workloads with different execution requirements through a shared serving infrastructure.

Three practical challenges motivate this project:

- **Workload heterogeneity:** classification, object detection, and text generation differ in model execution, input representation, and computational cost.
- **Worker selection:** routing requests across multiple inference workers requires a policy for choosing where requests should execute.
- **Resource management:** inference workloads can cause changes in CPU utilization and replica requirements, motivating orchestration and autoscaling.

### Research question

**How do different worker-selection policies affect request distribution and estimated scheduling cost in a cloud-native platform serving heterogeneous AI workloads, and how can Kubernetes autoscaling support its deployment?**

The current implementation provides the infrastructure for investigating this question. Establishing an effective scheduling policy requires further experiments using representative workloads and measured runtime conditions.

## Research Objectives

1. Develop a unified API for serving multiple AI model families.
2. Integrate a scheduling and routing layer between the gateway and independent inference workers.
3. Deploy the platform using Docker and Kubernetes.
4. Evaluate inference latency and request completion for the supported workloads.
5. Examine worker distribution and observed horizontal scaling behavior.
6. Compare scheduling policies using reproducible scenarios while identifying the limitations of synthetic evaluation.

## System Architecture

The platform separates request handling, worker selection, model execution, and infrastructure orchestration.

```text
                     Client Applications
                             |
                             v
                    FastAPI API Gateway
                             |
                             v
                      Request Scheduler
                             |
                             v
                       Worker Router
                             |
                 +-----------+-----------+
                 |                       |
                 v                       v
          Inference Worker 1      Inference Worker 2
                 |                       |
          +------+------+         +------+------+
          |      |      |         |      |      |
        BERT    YOLO  TinyLlama  BERT    YOLO  TinyLlama
                 |                       |
                 +-----------+-----------+
                             |
                     Inference Response

                 Kubernetes Orchestration
                 Deployment / Services / HPA
```

*Conceptual architecture. Model availability and execution depend on the deployed worker configuration.*

### Main components

| Component | Responsibility |
|---|---|
| API Gateway | Accepts inference requests and returns responses |
| Scheduler | Evaluates configured worker-selection information |
| Worker Router | Directs requests to the selected worker |
| Inference Workers | Execute supported models using their configured runtimes |
| Docker | Packages application services and model dependencies |
| Kubernetes | Manages deployments, services, and worker replicas |
| Horizontal Pod Autoscaler | Adjusts worker replica count according to configured CPU utilization targets |

## Supported AI Workloads

| Workload | Model | Task | Runtime |
|---|---|---|---|
| Text | DistilBERT | Sentiment classification | ONNX Runtime |
| Vision | YOLOv8n | Object detection | ONNX Runtime |
| Language generation | TinyLlama 1.1B | Text generation | llama.cpp |

The workloads provide a useful starting point for studying differences between model-serving tasks. The current evaluation does not, by itself, establish performance across all model sizes, hardware configurations, or production workloads.

## Technology Stack

- **Application:** Python 3.10, FastAPI, Uvicorn
- **Inference:** ONNX Runtime, NumPy, Hugging Face tokenizers, llama-cpp-python
- **Containerization:** Docker
- **Orchestration:** Kubernetes, Deployments, Services, Horizontal Pod Autoscaler
- **Evaluation:** Python benchmark scripts, CSV results, synthetic scheduler scenarios
- **Development environment:** Docker Desktop Kubernetes and PowerShell

## Experimental Results

### 1. Sequential inference benchmark

The following measurements are from the development environment and are documented in `development_v3/PHASE4_REPORT.md`.

| Model | Requests | Successful | Mean latency | Median latency | p95 latency |
|---|---:|---:|---:|---:|---:|
| DistilBERT | 10 | 10 | 74.77 ms | 73.21 ms | 102.89 ms |
| YOLOv8n | 10 | 10 | 178.75 ms | 162.95 ms | 272.01 ms |
| TinyLlama | 10 | 10 | 1,930.22 ms | 1,953.18 ms | 2,781.89 ms |

These results characterize the tested sequential requests, not production throughput or performance under concurrent load.

### 2. Multi-worker routing validation

A post-deployment regression test submitted 20 BERT requests through the Kubernetes gateway.

| Metric | Result |
|---|---:|
| Requests submitted | 20 |
| Successful responses | 20 |
| Failed responses | 0 |
| Requests routed to worker-1 | 10 |
| Requests routed to worker-2 | 10 |

The test confirms successful request completion and an even worker-selection distribution in that run. It does not establish that the scheduler will maintain an even distribution under every workload.

### 3. Kubernetes autoscaling validation

The worker Horizontal Pod Autoscaler is configured with:

| Setting | Value |
|---|---|
| Minimum replicas | 1 |
| Maximum replicas | 2 |
| CPU utilization target | 70% |

During a controlled test, the worker deployment scaled from one replica to two. HPA metrics and worker service endpoints were subsequently verified, and inference continued successfully after scale-out.

This demonstrates observed scale-out behavior in the tested Docker Desktop Kubernetes environment. It is not evidence of production-scale elasticity or a measured reduction in end-to-end latency due to autoscaling.

### 4. Scheduler evaluation

The repository includes scheduler evaluation scripts and saved experiment artifacts. The current comparison uses seeded synthetic scenarios and proxy costs rather than live worker queues, measured resource availability, and real-time inference-cost estimates.

The queue-only policy performed better than the adaptive policy under the evaluated proxy. This is an important preliminary finding: a more elaborate policy does not necessarily outperform a simpler baseline under a particular evaluation model.

The next research step is to validate both policies against measured workloads and actual worker conditions.

## Reproducibility

The repository contains the implementation, deployment manifests, benchmark scripts, and experiment artifacts needed to inspect and reproduce the documented tests.

### Repository structure

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

The original prototype is preserved separately from the v3 implementation.

### Prerequisites

- Docker Desktop with Kubernetes enabled
- `kubectl` configured for the intended cluster
- Python 3.10 for local development
- Compatible model artifacts
- Sufficient RAM and disk space, particularly for TinyLlama

### Model artifacts

Model weights are not included in the repository. Obtain compatible artifacts from their official publishers and observe their licenses.

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

Verify that the artifacts match the expected paths, preprocessing, and output formats in the implementation.

### Build the Docker image

Run these commands from the repository root:

```powershell
docker build -t ai-inference-platform:dev3.1 .\development_v3
```

### Deploy to Kubernetes

Confirm the active context and cluster:

```powershell
kubectl config current-context
kubectl get nodes
```

Apply the v3.1 manifest:

```powershell
kubectl apply -f .\development_v3\kubernetes-v3.1.yaml
```

Wait for the deployments:

```powershell
kubectl rollout status deployment/ai-inference-gateway-v3 --timeout=120s
kubectl rollout status deployment/ai-inference-worker-v3 --timeout=120s
kubectl rollout status deployment/ai-inference-worker-v3-2 --timeout=120s
```

Inspect deployment and autoscaler status:

```powershell
kubectl get deployments,services,hpa,pods
```

The manifest preserves the original v2 deployment. Review image settings, resource requests, and limits before deploying to another cluster.

### Verify the gateway

```powershell
Invoke-RestMethod http://localhost:32089/health
```

The expected response is:

```json
{
  "status": "ok"
}
```

### Run an inference request

The validated local Kubernetes gateway exposes port `32089`.

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

For text generation, use the `llama` model alias and supply a `text` field. For object detection, use the `yolo` alias and supply a base64-encoded image through `image_base64`.

Interactive API documentation is available at:

`http://localhost:32089/docs`

## Limitations and Future Work

The current implementation is an experimental platform, not a production-ready inference service.

### Current limitations

- **Synthetic scheduling metrics:** the scheduler does not yet establish decisions using a fully validated live measurement pipeline.
- **Preliminary policy evaluation:** synthetic proxy results cannot establish general scheduling superiority.
- **Limited workload scale:** the demonstrated setup uses a small number of workers and a local development cluster.
- **Limited performance evidence:** sequential latency measurements do not characterize sustained throughput, tail latency under contention, or large-scale concurrency.
- **Autoscaling scope:** the observed HPA behavior validates a configured CPU-based scale-out path, not an optimized autoscaling policy.

### Research directions

1. Integrate live queue depth, worker CPU utilization, and measured inference latency into scheduling decisions.
2. Compare round-robin, queue-only, resource-aware, and adaptive scheduling baselines.
3. Evaluate repeated trials with controlled request mixes, concurrency levels, and model combinations.
4. Report throughput, p50/p95/p99 latency, error rate, scheduling overhead, and resource utilization.
5. Investigate the relationship between scheduling policy, autoscaling delay, and end-to-end inference performance.
6. Evaluate the trade-offs between scheduling complexity and measurable performance improvements.

These experiments would help determine whether the proposed scheduling approach provides benefits beyond simpler baselines.

## Project Artifacts

- **Deployment:** `development_v3/kubernetes-v3.1.yaml`
- **Benchmarking:** `development_v3/benchmark_v3.py`
- **Repeated benchmarks:** `development_v3/benchmark_v3_repeated.py`
- **Scheduler evaluation:** `development_v3/scheduler_v3_evaluation.py`
- **Scheduler overhead:** `development_v3/scheduler_v3_overhead.py`
- **Experimental report:** `development_v3/PHASE4_REPORT.md`

Use the scripts and report together when interpreting results. Confirm the experiment configuration and saved data before making comparisons.

## Conclusion

This project establishes a reproducible cloud-native environment for serving heterogeneous AI workloads through a common gateway and multiple inference workers. The implementation demonstrates successful multi-model inference, worker routing, and Kubernetes HPA scale-out in a local development environment.

Its principal research opportunity is the systematic evaluation of scheduling policies using measured runtime conditions. Establishing a robust adaptive scheduling contribution requires further controlled experiments against simpler baselines, with transparent reporting of performance, overhead, and limitations.

## License

No license has been selected yet. Until a license is added, standard copyright restrictions apply.
