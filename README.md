<div align="center">

# Distributed Multi-Model AI Inference Fabric

### A Cloud-Native Platform for Heterogeneous AI Inference, Prometheus-Backed Scheduling, and Kubernetes Autoscaling

<p>
  <img src="https://img.shields.io/badge/Python-3.10-3776AB?logo=python&logoColor=white" alt="Python 3.10">
  <img src="https://img.shields.io/badge/FastAPI-Gateway-009688?logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/Docker-Containers-2496ED?logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/Kubernetes-Orchestration-326CE5?logo=kubernetes&logoColor=white" alt="Kubernetes">
  <img src="https://img.shields.io/badge/Prometheus-Monitoring-E6522C?logo=prometheus" alt="Prometheus">
  <img src="https://img.shields.io/badge/Grafana-Dashboards-F46800?logo=grafana" alt="Grafana">
  <img src="https://img.shields.io/badge/ONNX_Runtime-Inference-7B61FF" alt="ONNX Runtime">
</p>

**Research focus:** Distributed AI Inference · Heterogeneous Model Serving · Adaptive Worker Scheduling · Resource Monitoring · Cloud-Native Orchestration

[Architecture](#system-architecture) · [Monitoring](#monitoring-and-observability) · [Scheduling](#prometheus-backed-adaptive-scheduling) · [Experiments](#experimental-validation) · [Deployment](#deployment-and-verification) · [Future Work](#limitations-and-future-work)

</div>

---

## Abstract

Serving heterogeneous artificial intelligence models through a shared inference platform introduces challenges in request routing, resource allocation, workload management, and horizontal scaling. Different model families exhibit different computational characteristics, making a unified serving interface and an explicit worker-selection policy important systems-design considerations.

This project implements a cloud-native multi-model AI inference platform integrating a FastAPI gateway, a request scheduler, a worker router, independent inference workers, containerized model runtimes, and Kubernetes orchestration. It supports DistilBERT sentiment classification, YOLOv8n object detection, and TinyLlama text generation.

The platform integrates Prometheus-backed metric retrieval into the scheduler and uses Kubernetes resource metrics to support Horizontal Pod Autoscaler (HPA) decisions. Grafana provides monitoring visualization, while Redis is included in the infrastructure for the application's configured state or caching functionality.

Validation in a local Docker Desktop Kubernetes environment demonstrated successful execution of all three model workloads, availability of the configured Prometheus scrape targets, scheduler access to Prometheus metrics, and observed HPA scaling behavior between one and two worker replicas.

These results demonstrate functional integration in the tested environment. They do not establish production-scale performance or prove that the adaptive scheduling policy outperforms simpler alternatives.

## Table of Contents

- [Research Motivation](#research-motivation)
- [Research Objectives](#research-objectives)
- [System Architecture](#system-architecture)
- [Architecture Components](#architecture-components)
- [Supported AI Workloads](#supported-ai-workloads)
- [Monitoring and Observability](#monitoring-and-observability)
- [Prometheus-Backed Adaptive Scheduling](#prometheus-backed-adaptive-scheduling)
- [Kubernetes Autoscaling](#kubernetes-autoscaling)
- [Technology Stack](#technology-stack)
- [Experimental Validation](#experimental-validation)
- [Repository Structure](#repository-structure)
- [Prerequisites](#prerequisites)
- [Deployment and Verification](#deployment-and-verification)
- [API Usage](#api-usage)
- [Limitations and Future Work](#limitations-and-future-work)
- [Conclusion](#conclusion)

---

## Research Motivation

### Problem Statement

A shared inference service must accommodate workloads with different input formats, execution characteristics, and resource requirements.

The main challenges are:

1. **Workload heterogeneity:** Serving text classification, object detection, and text generation through a common interface.
2. **Worker selection:** Selecting an appropriate inference worker for each incoming request.
3. **Resource monitoring:** Collecting metrics to understand worker utilization and operational behavior.
4. **Autoscaling:** Adjusting worker replicas according to Kubernetes resource metrics.
5. **Observability:** Monitoring application behavior and infrastructure health.
6. **Experimental evaluation:** Comparing scheduling strategies using reproducible experiments without confusing synthetic estimates with real measurements.

### Research Question

> How can runtime metrics, worker scheduling, and Kubernetes autoscaling be integrated into a cloud-native platform serving heterogeneous AI workloads, and how should the resulting scheduling behavior be evaluated against simpler baseline policies?

## Research Objectives

- Develop a unified API for heterogeneous AI inference.
- Integrate a scheduler and worker router between the gateway and inference workers.
- Use Prometheus-backed metrics in the worker-selection process.
- Deploy application services using Docker and Kubernetes.
- Integrate Prometheus and Grafana for monitoring.
- Configure Kubernetes HPA for CPU-based worker scaling.
- Validate model inference, metric collection, and autoscaling behavior.
- Evaluate scheduling strategies using reproducible scenarios and document their limitations.

---

## System Architecture

The platform separates request handling, scheduling, model execution, monitoring, and infrastructure orchestration.

<p align="center">
  <img src="development_v3/Architecture.png" alt="Distributed Multi-Model AI Inference Fabric architecture showing client applications, FastAPI gateway, Prometheus-backed request scheduler, worker router, two inference workers, Redis, Prometheus, Grafana, Metrics Server, Kubernetes Services and Deployments, and Horizontal Pod Autoscaler." width="100%">
</p>

<p align="center">
  <em>Figure 1. Architecture of the Distributed Multi-Model AI Inference Fabric, including inference services, monitoring infrastructure, and Kubernetes autoscaling.</em>
</p>

### Request Processing Flow

1. A client submits an inference request to the FastAPI gateway.
2. The gateway processes the request and passes it to the scheduling and routing layer.
3. The scheduler evaluates the configured worker-selection policy using available worker metrics.
4. The worker router forwards the request to the selected inference worker.
5. The worker executes the requested model using its configured inference runtime.
6. The result returns through the gateway to the client.

### Monitoring and Control Flow

The architecture has two distinct metric paths.

**Application monitoring and scheduling**

1. The gateway and workers expose configured application metrics.
2. Prometheus scrapes the configured metric endpoints.
3. The scheduler queries Prometheus for supported worker metrics.
4. Available metric information contributes to the configured worker-selection policy.
5. Grafana visualizes monitoring data provided by Prometheus.

**Kubernetes resource monitoring and autoscaling**

1. Metrics Server provides Kubernetes node and pod resource metrics.
2. Kubernetes HPA evaluates CPU utilization against the configured target.
3. HPA adjusts the replica count of the managed worker deployment within its configured limits.
4. Kubernetes Deployments and Services manage the worker pods and their networking.

Prometheus and Metrics Server are complementary components, not interchangeable ones. Prometheus supplies application metrics and scheduler queries, while Metrics Server supplies resource metrics used by Kubernetes HPA.

---

## Architecture Components

| Component | Responsibility |
|---|---|
| FastAPI Gateway | Receives inference requests and exposes API and health endpoints |
| Request Scheduler | Evaluates worker-selection decisions using available metrics and the configured policy |
| Worker Router | Routes requests to the selected inference worker |
| Inference Worker 1 | Executes configured AI workloads |
| Inference Worker 2 | Provides an additional inference worker for routing and scaling |
| Prometheus | Scrapes and stores configured application metrics and supports metric queries |
| Grafana | Provides dashboards and monitoring visualization |
| Redis | Supports configured application state or caching functionality |
| Metrics Server | Supplies Kubernetes node and pod resource metrics |
| Horizontal Pod Autoscaler | Adjusts worker replica counts according to the configured scaling policy |
| Kubernetes Services | Provide networking and service discovery |
| Kubernetes Deployments | Manage application pods and desired replica counts |
| Docker | Packages application services and model dependencies |

**Configuration note:** The diagram represents the overall deployment architecture. The precise use of Redis, the set of Grafana dashboards, and the metrics available to the scheduler depend on the deployed configuration.

## Supported AI Workloads

| Workload | Model | Task | Runtime |
|---|---|---|---|
| Natural Language Processing | DistilBERT | Sentiment classification | ONNX Runtime |
| Computer Vision | YOLOv8n | Object detection | ONNX Runtime |
| Language Generation | TinyLlama 1.1B | Text generation | llama.cpp |

The workloads provide a starting point for investigating heterogeneous model serving. Actual model availability depends on the model artifacts and worker configuration.

---

## Monitoring and Observability

Monitoring is essential for understanding inference behavior, diagnosing service issues, and providing the information used by the scheduler and autoscaling components.

### Prometheus

Prometheus collects application metrics from configured scrape targets and provides a query interface for the scheduler.

The validated development environment included scrape targets for:

- `ai-inference-gateway-v3`
- `ai-inference-worker-v3`
- `ai-inference-worker-v3-2`

All three targets were reported as available during validation.

The scheduler was also tested with a reachable Prometheus endpoint and returned:

```json
{
  "metrics_source": "prometheus"
}
```

This indicates that the scheduler used the Prometheus metric path during the reported test. It does not establish that every metric is always available or that the resulting worker-selection policy is optimal.

### Grafana

Grafana is included in the deployment stack for monitoring visualization.

It can display available Prometheus metrics through configured dashboards. Dashboard completeness, alert rules, and specific visualizations depend on the deployed configuration.

### Redis

Redis is included as an infrastructure service.

Its exact application role should be determined from the current source code and runtime configuration. It should not be assumed to provide scheduler metrics or caching for every request unless those behaviors are explicitly implemented.

### Metrics Server

Metrics Server supplies resource metrics for Kubernetes.

The development environment supported commands such as:

```powershell
kubectl top pods
kubectl top nodes
```

These commands depend on a functioning Kubernetes resource-metrics pipeline.

### Monitoring Component Summary

| Component | Primary purpose | Validation |
|---|---|---|
| Prometheus | Application metric collection and queries | Configured scrape targets verified |
| Scheduler metric integration | Retrieves supported metrics from Prometheus | Prometheus metric path exercised |
| Grafana | Monitoring visualization | Service reported healthy |
| Metrics Server | Kubernetes resource metrics | `kubectl top` worked |
| Kubernetes HPA | CPU-based replica scaling | Scale-up and scale-down behavior observed |
| Redis | Configured state or caching functionality | Service reported healthy; application behavior depends on configuration |

---

## Prometheus-Backed Adaptive Scheduling

The scheduler evaluates available information to select a worker for an incoming inference request.

The updated implementation supports Prometheus-backed retrieval of configured worker metrics, including:

- CPU usage.
- Memory consumption.
- Average inference latency.
- Request rate.

The precise behavior depends on the configured Prometheus queries, metric labels, worker identifiers, and metric availability.

### Scheduling Metric Sources

| Metric | Purpose |
|---|---|
| CPU usage | Provides information about worker computational utilization |
| Memory usage | Provides information about worker memory consumption |
| Average inference latency | Helps characterize observed inference execution time |
| Request rate | Provides information about workload activity |
| Round-robin fallback | Provides deterministic worker selection when the required CPU or memory data is unavailable |

The implementation distinguishes between Prometheus-backed metric retrieval and fallback selection. When the required CPU or memory data is unavailable, the scheduler can use a deterministic round-robin fallback.

A live metric source does not automatically make a scheduling policy optimal. Its effectiveness must be evaluated against suitable baselines under controlled workloads.

### Scheduler Evaluation

The repository also includes experimental scripts for comparing scheduling policies.

Synthetic scenarios and proxy costs are useful for reproducible preliminary experiments, but they cannot substitute for measurements of actual worker queues, resource contention, inference times, and request completion.

A rigorous evaluation should compare round-robin, queue-based, resource-aware, and adaptive scheduling under identical workload conditions.

---

## Kubernetes Autoscaling

The platform uses Kubernetes Horizontal Pod Autoscaler to adjust the replica count of the managed worker deployment according to CPU utilization.

### Validated HPA Configuration

| Setting | Value |
|---|---:|
| Minimum replicas | 1 |
| Maximum replicas | 2 |
| CPU utilization target | 70% |

During testing, the worker deployment was observed scaling from one replica to two. HPA information and worker service endpoints were subsequently inspected, and inference requests continued to complete.

This demonstrates the configured scaling path in the tested Docker Desktop Kubernetes environment. It does not establish production-scale elasticity, optimal replica selection, or reduced end-to-end inference latency.

### Relationship Between Scheduling and Autoscaling

- **Application scheduler:** Selects an available worker for an inference request.
- **Prometheus:** Supplies application metrics to configured monitoring and scheduling paths.
- **Metrics Server:** Supplies Kubernetes resource metrics.
- **HPA:** Adjusts worker replica counts according to the configured scaling policy.
- **Kubernetes Services and Deployments:** Manage networking, service discovery, and worker pods.

These mechanisms operate at different levels and should be evaluated separately as well as together.

---

## Technology Stack

| Category | Technologies |
|---|---|
| Application | Python 3.10, FastAPI, Uvicorn |
| NLP | DistilBERT, Hugging Face tokenizers |
| Computer Vision | YOLOv8n, ONNX Runtime |
| Language Generation | TinyLlama, llama.cpp |
| Monitoring | Prometheus, Grafana |
| Resource Metrics | Kubernetes Metrics Server |
| Shared Infrastructure | Redis |
| Containerization | Docker |
| Orchestration | Kubernetes |
| Autoscaling | Horizontal Pod Autoscaler |
| Evaluation | Python benchmark scripts, CSV artifacts |
| Development Environment | Docker Desktop Kubernetes, PowerShell |

---

## Experimental Validation

The following results summarize validation performed in the development environment. They are not production performance guarantees.

### 1. Model Inference Validation

All three supported model workloads were exercised through the deployed gateway.

| Model | Task | Result |
|---|---|---|
| DistilBERT | Sentiment classification | Successful inference |
| YOLOv8n | Object detection | Successful inference; five objects detected in the test image |
| TinyLlama | Text generation | Execution completed; output quality and completeness depend on the request and runtime |

The YOLO test image produced five detections: four people and one bus.

These tests establish functional execution of the tested inference paths, not a statistically controlled performance comparison.

### 2. Prometheus Integration

The following checks were reported successful:

- Prometheus service availability.
- Gateway metric scraping.
- Primary worker metric scraping.
- Secondary worker metric scraping.
- Scheduler access to Prometheus-backed metrics.

During testing, the scheduler returned `metrics_source: "prometheus"`.

### 3. Kubernetes Autoscaling

The HPA was configured with a CPU utilization target of 70%, a minimum of one replica, and a maximum of two replicas.

Scale-up and scale-down behavior was observed during testing. The final recorded deployment state had two ready replicas for the HPA-managed primary worker deployment.

This validates observed autoscaling behavior in the local test environment. It does not establish production-scale performance.

### 4. Performance Evaluation

The repository contains benchmark scripts and CSV artifacts for further analysis.

Performance results should be reported alongside the workload, request count, concurrency, measurement method, and test environment. Sequential inference measurements should not be interpreted as sustained throughput under concurrent load.

Synthetic scheduler experiments must be identified as such. They should not be presented as measurements of real-world scheduling performance.

---

## Repository Structure

```text
Distributed-ai-inference-platform/
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
│   ├── metrics-server-patch.yaml
│   ├── worker-deployment-final.yaml
│   ├── hpa-final-evidence.yaml
│   ├── openapi-live.json
│   ├── Architecture.png
│   └── models/
├── evidence/
│   └── final-20261027-232859/
│       ├── deployments.txt
│       ├── events.txt
│       ├── hpa-details.txt
│       ├── hpa.txt
│       ├── pods.txt
│       └── resource-usage.txt
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
└── README.md
```

This is a high-level overview. Consult the repository for the complete list of implementation modules and deployment artifacts.

The `development_v3` directory contains the newer implementation, while root-level files preserve the earlier prototype and related experimental artifacts.

---

## Prerequisites

- Docker Desktop with Kubernetes enabled.
- `kubectl` configured for the intended cluster.
- Python 3.10 for local development and applicable scripts.
- Required model artifacts and compatible runtime dependencies.
- Sufficient memory and disk space for the configured workloads.
- Metrics Server and other required services for the selected Kubernetes configuration.

Model weights may not be included in the repository. Verify required artifacts, expected paths, and model licensing before deployment.

## Deployment and Verification

**Important:** The commands below are intended for inspecting and accessing the validated development deployment. Review the current manifests and image tags before rebuilding or applying resources. Avoid applying an older manifest blindly over the working deployment.

### 1. Verify the Kubernetes Context

Run from PowerShell:

```powershell
kubectl config current-context
kubectl get nodes
```

Confirm that the intended cluster is active.

### 2. Inspect Deployments and Services

```powershell
kubectl get deployments
kubectl get pods
kubectl get services
kubectl get hpa
```

Check the application rollouts:

```powershell
kubectl rollout status deployment/ai-inference-gateway-v3 --timeout=120s
kubectl rollout status deployment/ai-inference-worker-v3 --timeout=120s
kubectl rollout status deployment/ai-inference-worker-v3-2 --timeout=120s
```

### 3. Inspect Resource Metrics

```powershell
kubectl top pods
kubectl top nodes
```

These commands require a working Kubernetes resource-metrics pipeline.

### 4. Inspect Autoscaling

```powershell
kubectl describe hpa ai-inference-worker-v3
kubectl get hpa ai-inference-worker-v3 -w
```

The second command watches HPA status. It does not generate workload or guarantee scaling.

### 5. Access the Gateway

The validated development workflow used port forwarding to access the gateway.

Run in a separate PowerShell terminal:

```powershell
kubectl port-forward deployment/ai-inference-gateway-v3 8001:8000
```

Keep the terminal open while accessing the API.

Base URL:

```text
http://127.0.0.1:8001
```

Check health:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8001/health"
```

Open interactive API documentation:

```text
http://127.0.0.1:8001/docs
```

### 6. Access Prometheus

Inspect the actual resource names first:

```powershell
kubectl get deployments,services
```

If the Prometheus deployment is named `prometheus`, port-forward it:

```powershell
kubectl port-forward deployment/prometheus 9090:9090
```

Then open:

```text
http://127.0.0.1:9090
```

The scheduler's Prometheus URL is environment-dependent. A scheduler running inside Kubernetes normally needs a reachable in-cluster Prometheus endpoint rather than the host-only port-forward address.

### 7. Access Grafana

Inspect the actual Grafana deployment and service names:

```powershell
kubectl get deployments,services
```

If the deployment is named `grafana` and exposes port 3000:

```powershell
kubectl port-forward deployment/grafana 3000:3000
```

Then open:

```text
http://127.0.0.1:3000
```

Authentication, service names, and dashboard configuration depend on the deployed setup.

### 8. Inspect Redis

```powershell
kubectl get pods,services
```

Use the Redis resource name and connection settings defined by the active configuration. Do not expose Redis publicly without suitable network restrictions and authentication.

---

## API Usage

The gateway exposes inference functionality through the deployed API. Request fields and supported model aliases should be checked against the implementation and live OpenAPI specification.

### Health Check

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8001/health"
```

The reported validation response indicated a healthy gateway, Redis connectivity, and three registered model artifacts.

### DistilBERT Sentiment Inference

```powershell
$body = @{
    model = "bert"
    priority = 5
    text = "This platform is working well."
} | ConvertTo-Json -Compress

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8001/infer" `
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
    -Uri "http://127.0.0.1:8001/infer" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

### YOLO Object Detection

The tested YOLO request used the `yolo` model alias and a base64-encoded image in the `image_base64` field.

Consult `development_v3/models.py`, the worker implementation, and the live OpenAPI specification for the accepted input and response formats.

---

## Limitations and Future Work

The platform is an experimental implementation validated in a local Kubernetes environment. It should not yet be considered a production-ready inference service.

### Current Limitations

- **Limited deployment scale:** Validation was performed with a small number of worker replicas in a local development cluster.
- **Scheduling evaluation:** Synthetic proxy results do not establish scheduling superiority under real workload conditions.
- **Performance characterization:** Functional inference tests do not establish sustained throughput under concurrent load.
- **Autoscaling scope:** Observed HPA behavior validates a configured CPU-based scaling path, not an optimized autoscaling strategy.
- **Monitoring coverage:** Dashboard completeness, alert rules, and metric coverage depend on the deployed configuration.
- **Hardware diversity:** Results from the tested environment cannot automatically be generalized to GPU clusters or larger production environments.

### Future Research Directions

1. Compare round-robin, queue-based, resource-aware, and adaptive worker-selection policies.
2. Measure real worker queues, resource utilization, and inference latency under controlled workloads.
3. Evaluate scheduling overhead and its effect on end-to-end response time.
4. Run repeated experiments at multiple concurrency levels and workload mixes.
5. Report throughput, p50/p95/p99 latency, error rate, and resource consumption.
6. Investigate the interaction between scheduling decisions and HPA reaction time.
7. Develop and validate monitoring dashboards and alerting rules.
8. Evaluate performance across different model combinations and hardware configurations.
9. Test failure handling, worker unavailability, and recovery behavior.
10. Compare measured results against simpler baselines before claiming adaptive-scheduling benefits.

---

## Conclusion

The Distributed Multi-Model AI Inference Fabric provides a cloud-native environment for serving heterogeneous AI workloads through a common gateway and multiple inference workers.

The implementation brings together FastAPI, a scheduler and worker router, ONNX Runtime, llama.cpp, Docker, Kubernetes, Prometheus, Grafana, Redis, Kubernetes resource metrics, and HPA-based autoscaling.

Validation demonstrated successful execution of the supported model workloads, Prometheus-backed scheduler operation, availability of configured monitoring targets, and observed worker autoscaling in the local development environment.

The central research opportunity is to determine, through controlled experiments, whether metric-informed worker selection improves inference performance compared with simpler scheduling policies. Establishing such a contribution requires measured runtime conditions, reproducible experiments, suitable baselines, and transparent reporting of limitations.

## License

No license has been selected for this repository. Unless a license is added, standard copyright restrictions apply.
