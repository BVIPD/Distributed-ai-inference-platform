<div align="center">

# Distributed Multi-Model AI Inference Fabric

**A cloud-native platform that serves text, vision, and language models through one API, with Redis-backed queuing, Prometheus-informed scheduling, and Kubernetes autoscaling.**

<p>
  <img src="https://img.shields.io/badge/Python-3.10-3776AB?logo=python&logoColor=white" alt="Python 3.10">
  <img src="https://img.shields.io/badge/FastAPI-Gateway-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Docker-Containers-2496ED?logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/Kubernetes-HPA-326CE5?logo=kubernetes&logoColor=white" alt="Kubernetes">
  <img src="https://img.shields.io/badge/Redis-Queue-DC382D?logo=redis&logoColor=white" alt="Redis">
  <img src="https://img.shields.io/badge/Prometheus-Metrics-E6522C?logo=prometheus&logoColor=white" alt="Prometheus">
  <img src="https://img.shields.io/badge/Grafana-Dashboards-F46800?logo=grafana&logoColor=white" alt="Grafana">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/Status-Prototype-orange" alt="Status: prototype">
</p>

[Overview](#overview) · [Architecture](#architecture) · [Quick Start](#quick-start) · [API](#api-usage) · [Scheduling](#scheduling-and-worker-selection) · [Results](#validation-results) · [Limitations](#limitations)

</div>

---

## Overview

Serving different model families behind one platform raises practical systems questions: how to route requests, choose a worker, monitor load, and scale replicas. This project implements a working answer on Kubernetes.

A FastAPI gateway accepts requests and queues them in Redis. A consumer asks a scheduler to pick a worker using Prometheus metrics (with a round-robin fallback), and independent inference workers run the models. Prometheus and Grafana provide observability, and a Horizontal Pod Autoscaler scales the workers on CPU.

| Model | Task | Runtime |
|---|---|---|
| DistilBERT | Sentiment classification | ONNX Runtime |
| YOLOv8n | Object detection | ONNX Runtime |
| TinyLlama 1.1B | Text generation | llama.cpp |

> **Scope:** This is a prototype validated on a local Docker Desktop Kubernetes cluster. The results show functional integration and measured CPU latency. They do not establish production-scale performance, and they do not prove that adaptive scheduling beats simpler policies (see [Limitations](#limitations)).

### At a glance

| | |
|---|---|
| **Workloads** | 3 models behind one `POST /infer` endpoint |
| **Workers** | 2 inference workers, routed by a metrics-aware scheduler |
| **Autoscaling** | HPA, 1 to 2 replicas, 70% CPU target |
| **Observability** | Prometheus (3 scrape targets) and a 4-panel Grafana dashboard |
| **Measured latency** | 75 ms (DistilBERT), 179 ms (YOLOv8n), 1.93 s (TinyLlama), mean of 10 CPU requests each |
| **Evidence** | Raw `kubectl` outputs, benchmark CSVs, and screenshots committed to the repo |

## Key Features

- **One API, three workloads:** all models are served through `POST /infer`.
- **Redis-backed queue:** requests are queued and results are stored by request ID.
- **Metrics-informed scheduling:** CPU, memory, latency, and request rate from Prometheus, with a deterministic round-robin fallback.
- **Two workers behind a router:** requests are distributed across both workers.
- **Kubernetes autoscaling:** HPA scales the primary worker on CPU.
- **Observability:** Prometheus scrape targets for the gateway and both workers, plus a Grafana dashboard.
- **Honest evaluation:** measured latency, synthetic scheduler results, and their limits are reported separately.

## Architecture

![Architecture diagram](development_v3/Architecture.png)

### Request flow

```mermaid
flowchart LR
    C([Client]) -->|POST /infer| G["FastAPI Gateway<br/>validates model"]
    G -->|"1 · LPUSH job + request ID"| Q[("Redis<br/>inference:queue")]
    Q -->|"2 · BRPOP"| K["Queue Consumer<br/>+ Worker Router"]
    K -->|"3 · choose worker"| S{"Scheduler"}
    S -->|selected worker| K
    P[("Prometheus")] -.->|"CPU, memory,<br/>latency, request rate"| S
    K -->|"4 · forward"| W1["Worker 1"]
    K -->|"4 · forward"| W2["Worker 2"]
    W1 -->|response| K
    W2 -->|response| K
    K -->|"5 · SET result, TTL 180 s"| RS[("Redis<br/>inference:result:id")]
    G -.->|"6 · polls by request ID"| RS
    G -->|response| C

    classDef store fill:#fde8e8,stroke:#dc382d,color:#000
    classDef compute fill:#e0ecff,stroke:#326ce5,color:#000
    classDef sched fill:#fff3d6,stroke:#e6a100,color:#000
    class Q,RS,P store
    class G,K,W1,W2 compute
    class S sched
```

1. The gateway rejects unknown models, assigns a request ID, and pushes the job onto the Redis queue.
2. A background consumer pops the job.
3. The scheduler scores the workers using Prometheus metrics, or falls back to round robin.
4. The router forwards the job to the selected worker, which runs the model.
5. The consumer stores the result in Redis under the request ID with a 180-second TTL.
6. The gateway, which has been polling that key, returns the result to the client.

### Two separate metric paths

```mermaid
flowchart LR
    subgraph App["Application metrics"]
        G["Gateway"] --> P[("Prometheus")]
        W["Workers 1 and 2"] --> P
        P --> GR["Grafana"]
        P -.-> S{"Scheduler"}
    end

    subgraph K8s["Resource metrics"]
        MS[("Metrics Server")] --> H["HPA"]
        H -->|"scales 1 to 2 replicas<br/>70% CPU target"| WD["Worker deployment"]
    end

    classDef store fill:#fde8e8,stroke:#dc382d,color:#000
    classDef compute fill:#e0ecff,stroke:#326ce5,color:#000
    classDef sched fill:#fff3d6,stroke:#e6a100,color:#000
    class P,MS store
    class G,W,GR,H,WD compute
    class S sched
```

| Path | Source | Consumer | Purpose |
|---|---|---|---|
| Application metrics | Gateway and workers, scraped by Prometheus | Scheduler, Grafana | Worker selection and dashboards |
| Resource metrics | Kubernetes Metrics Server | HPA | CPU-based replica scaling |

Prometheus and Metrics Server are complementary, not interchangeable.

## Technology Stack

| Layer | Technologies |
|---|---|
| Application | Python 3.10, FastAPI, Uvicorn |
| Models | DistilBERT, YOLOv8n (ONNX Runtime), TinyLlama 1.1B (llama.cpp) |
| Queue and results | Redis |
| Packaging and orchestration | Docker, Kubernetes, Horizontal Pod Autoscaler |
| Monitoring | Prometheus, Grafana, Kubernetes Metrics Server |
| Evaluation | Python benchmark scripts, CSV results, Matplotlib |
| Local environment | Docker Desktop Kubernetes, PowerShell |

## Repository Structure
```text
Distributed-ai-inference-platform/
├── development_v3/                     # Current implementation
│   ├── main.py                         # FastAPI inference gateway
│   ├── router.py
│   ├── scheduler.py                    # Prometheus-based worker scheduling
│   ├── models.py
│   ├── worker_api.py
│   ├── redis.yaml
│   ├── prometheus.yaml
│   ├── grafana.yaml
│   ├── kubernetes-v3.yaml
│   ├── kubernetes-v3.1.yaml
│   ├── worker-deployment-final.yaml
│   ├── hpa-final-evidence.yaml
│   ├── metrics-server-patch.yaml
│   ├── openapi-live.json
│   ├── Architecture.png                # System architecture diagram
│   ├── benchmark_v3_repeated_results.csv
│   ├── benchmark_v3_results.csv
│   └── models/                          # Model artifacts
├── docs/                               # Screenshots and charts
├── evidence/                           # Deployment validation evidence
├── benchmark.py                        # Inference performance benchmarking
├── benchmark_results.csv
├── scheduler_experiment.py             # Scheduler performance experiments
├── scheduler_independent_eval.py
├── scheduler_comparison.csv
├── scheduler_independent_eval.csv
├── deployment.yaml
├── Dockerfile                          # Container build configuration
├── requirements.txt
├── LICENSE
└── README.md                           # Project documentation
```


## Prerequisites

- Docker Desktop with Kubernetes enabled
- `kubectl`
- Python 3.10 (for scripts and local development)
- Kubernetes Metrics Server (required for HPA)
- Enough CPU and memory for the three models

### Model files

Weights are not committed. Place compatible exports at the paths expected by `development_v3/models.py`:

```text
development_v3/models/
├── distilbert/
│   ├── model_quantized.onnx
│   ├── tokenizer.json
│   └── config.json
├── yolo/
│   └── yolov8n.onnx
└── tinyllama/
    └── TinyLlama-1.1B-Chat-v1.0-Q2_K.gguf
```

You need a quantized DistilBERT sentiment model in ONNX format, YOLOv8n exported to ONNX, and a TinyLlama 1.1B Chat Q2_K GGUF. Check each model's license before use or redistribution.

## Quick Start

These commands inspect and access the deployment. Review manifests and image tags before applying anything, and don't apply an older manifest over a working deployment.

**1. Verify the cluster and deployments**

```powershell
kubectl config current-context          # docker-desktop in the tested setup
kubectl get deployments,pods,services,hpa
kubectl rollout status deployment/ai-inference-gateway-v3 --timeout=120s
kubectl rollout status deployment/ai-inference-worker-v3 --timeout=120s
kubectl rollout status deployment/ai-inference-worker-v3-2 --timeout=120s
```

**2. Open the gateway** (keep this terminal open)

```powershell
kubectl port-forward deployment/ai-inference-gateway-v3 8001:8000
```

In a second terminal:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8001/health"
```

Interactive docs: <http://127.0.0.1:8001/docs>

**3. Monitoring** (each in its own terminal)

```powershell
kubectl port-forward deployment/prometheus 9090:9090   # http://localhost:9090/targets
kubectl port-forward deployment/grafana 3000:3000      # http://localhost:3000
```

Run `kubectl get deployments` first if your resource names differ. In Prometheus, the query `up` should return `1` for the gateway, worker-1, and worker-2.

**4. Resource usage and autoscaling**

```powershell
kubectl top pods
kubectl top nodes
kubectl describe hpa ai-inference-worker-v3
kubectl get hpa ai-inference-worker-v3 -w   # watch only; does not generate load
```

The HPA targets 70% CPU with 1 to 2 replicas. Actual scaling depends on load and resource requests.

## API Usage

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Platform information |
| GET | `/health` | Gateway, Redis, and model-artifact status |
| GET | `/models` | List registered models |
| GET | `/models/{model_id}` | Model details |
| POST | `/infer` | Submit an inference request |

**Sentiment (DistilBERT)**

```powershell
$body = @{ model = "bert"; priority = 5; text = "This platform is working well." } | ConvertTo-Json -Compress
Invoke-RestMethod -Uri "http://127.0.0.1:8001/infer" -Method Post -ContentType "application/json" -Body $body
```

**Text generation (TinyLlama)**

```powershell
$body = @{ model = "llama"; priority = 5; text = "Explain Kubernetes in two simple sentences." } | ConvertTo-Json -Compress
Invoke-RestMethod -Uri "http://127.0.0.1:8001/infer" -Method Post -ContentType "application/json" -Body $body
```

**Object detection (YOLOv8n)** uses `model = "yolo"` and a base64-encoded image in `image_base64`. Check the `InferenceRequest` schema in `/docs` or `openapi-live.json` for exact fields.

## Scheduling and Worker Selection

For each queued request the scheduler queries Prometheus for per-worker **CPU usage, memory usage, average inference latency, and request rate**, scores the workers, and selects one. Every scheduling decision reports where its data came from:

| `metrics_source` | Meaning |
|---|---|
| `prometheus` | Live Prometheus metrics were used |
| `round_robin_fallback` | Required CPU or memory data was unavailable, so the scheduler used round robin |

This field describes the data source. It does not show that one policy outperforms another.

## Redis: Request Queue and Result Store

- Each request gets a unique ID and is pushed onto the Redis list `inference:queue`.
- A background consumer pops jobs and dispatches them through the scheduler and router.
- The consumer stores each result under `inference:result:<request_id>` with a **180-second TTL**, and the gateway polls that key until the result appears or the request times out.
- The deployment runs with a **64 MB** memory cap, the `allkeys-lru` eviction policy, and persistence disabled.

Redis is therefore an **ephemeral queue and result store, not durable job storage**. A restart loses queued work, and memory pressure can evict keys.

## Validation Results

All results come from a local Docker Desktop Kubernetes cluster. They are not production guarantees.

### Measured inference latency

![Measured inference latency across models](docs/inference_latency.png)

*10 sequential requests per model (30/30 succeeded), CPU inference, one worker.*

| Model | Mean (ms) | Median (ms) | Max (ms) |
|---|---:|---:|---:|
| DistilBERT | 74.77 | 73.21 | 102.89 |
| YOLOv8n | 178.75 | 162.95 | 272.01 |
| TinyLlama 1.1B | 1930.22 | 1953.18 | 2781.89 |

TinyLlama is roughly 25 times slower than DistilBERT in this CPU test. The maximum is reported instead of p95 because ten samples are too few for a meaningful percentile. These numbers are not concurrent-load throughput and not a GPU comparison. Raw data: [`development_v3/benchmark_v3_repeated_results.csv`](development_v3/benchmark_v3_repeated_results.csv).

### Functional validation

| Area | Result |
|---|---|
| Gateway | `/health` reported a healthy gateway, Redis connected, and 3 registered model artifacts |
| DistilBERT, TinyLlama | Inference completed successfully |
| YOLOv8n | 5 detections on the 810×1080 test image |
| Prometheus targets | Gateway, worker-1, and worker-2 all `UP` |
| Scheduler | Responses reported `metrics_source: prometheus` |
| Multi-worker routing | Requests were served by both workers |
| Autoscaling | A second worker replica became Ready during a high-CPU test |
| Stability | Zero pod restarts at the final inspection |

### Monitoring evidence

| | |
|---|---|
| **Swagger UI**<br>![Swagger](docs/swagger_api.jpeg) | **Grafana dashboard**<br>![Grafana](docs/grafana_dashboard.jpeg) |
| **Prometheus targets**<br>![Targets](docs/prometheus_targets.jpeg) | **`up` query**<br>![up query](docs/prometheus_up_query.jpeg) |
| **Gateway request counters**<br>![Gateway counters](docs/gateway_inference_requests.jpeg) | **Worker request counters**<br>![Worker counters](docs/worker_inference_requests.jpeg) |

The captured counters are consistent end to end. The gateway recorded 32 BERT, 2 llama, and 2 YOLO successes. The worker counters sum to the same totals: BERT 18 on worker-1 and 14 on worker-2, llama 1 on each, and YOLO 2 on worker-1.

### Synthetic scheduler experiment

Seed 42, 1,000 synthetic scenarios, proxy costs. These are **not** measured inference latencies.

| Policy | Mean proxy cost |
|---|---:|
| Round robin | 2.678 |
| Queue-only | **2.131** |
| Resource-only | 2.457 |
| Adaptive | 2.259 |

Queue-only scored best, ahead of the adaptive policy. This supports the project's position that adaptive scheduling is unproven and needs real-load evaluation. Local decision overhead was about 0.0005 to 0.0027 ms per decision, excluding HTTP and inference. See `scheduler_experiment.py`, `scheduler_independent_eval.py`, `scheduler_comparison.csv`, and `scheduler_independent_eval.csv` in the repository root.

## Design Notes

- **Redis between gateway and workers.** Queuing decouples request intake from model execution and gives each request a stable ID. The cost is that Redis becomes a durability weak point (see below).
- **Two metric paths.** Application metrics feed the scheduler, while resource metrics feed the HPA. Keeping them separate lets each be tested on its own.
- **Round-robin fallback.** If Prometheus data is missing, the scheduler degrades to a predictable policy instead of failing requests.
- **`priority` field.** The API accepts it, but the queue is a plain Redis list, so treat it as request metadata rather than a guaranteed priority queue.

## Troubleshooting

| Symptom | Check |
|---|---|
| `kubectl top` returns an error | Metrics Server is missing or needs the patch in `metrics-server-patch.yaml` |
| `/health` reports a model artifact missing | Model files are not at the paths listed under [Model files](#model-files) |
| Scheduler reports `round_robin_fallback` | Prometheus is unreachable from inside the cluster, or the worker metrics are not scraped yet |
| `/infer` times out | Redis is down, the consumer is not running, or the model is still loading (TinyLlama is the slowest) |
| Port-forward drops | Re-run the command and keep its terminal open |

## Limitations

- **Local and small:** one Docker Desktop cluster, with HPA capped at 2 replicas.
- **CPU only:** no GPU or multi-node results.
- **Small benchmark:** 10 sequential requests per model, with no concurrent-load or sustained-throughput data.
- **Synthetic scheduler results:** proxy costs do not prove adaptive scheduling wins on real workloads.
- **Redis durability:** in-memory, evictable, non-persistent.
- **Not production-hardened:** no authentication, TLS, or durable job recovery.

## Future Work

1. Compare round-robin, queue-only, resource-only, and adaptive scheduling under identical **real** concurrent workloads.
2. Report throughput, p50/p95/p99 latency, error rate, queue wait, and resource use, with enough repetitions for stable percentiles.
3. Study how scheduling decisions interact with HPA reaction time.
4. Handle missing or stale metrics more gracefully.
5. Test worker failure and recovery, and add durable job handling to Redis.
6. Add authentication and deployment hardening, then evaluate on a multi-node cluster.

## Reproducibility

For any new experiment, record the code revision, manifests, model files and versions, resource limits, request payloads, warm-up and repetition counts, and the scheduling policy. Keep raw measurements, and label synthetic simulations separately from measured results.

## Author

**Bhuvanagiri Indira Priyadarshini** · [@BVIPD](https://github.com/BVIPD)

## License

Released under the [MIT License](LICENSE). Third-party dependencies and model weights keep their own licenses.