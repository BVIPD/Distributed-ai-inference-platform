# Phase 4 — Scheduling Evaluation and Benchmarks

## Real-model inference benchmark

30/30 sequential requests succeeded across BERT, YOLOv8n, and TinyLlama.

| Model | Success | Mean (ms) | Median (ms) | p95 (ms) |
|---|---:|---:|---:|---:|
| DistilBERT | 10/10 | 74.77 | 73.21 | 102.89 |
| YOLOv8n | 10/10 | 178.75 | 162.95 | 272.01 |
| TinyLlama | 10/10 | 1930.22 | 1953.18 | 2781.89 |

Detailed results: `benchmark_v3_repeated_results.csv`

## Synthetic scheduler comparison

Seed: 42. Scenarios: 1000. Decisions: 4000. These are synthetic proxy costs, not measured inference latencies.

| Policy | Mean cost | Median cost |
|---|---:|---:|
| Round robin | 2.6781 | 2.6635 |
| Queue-only | 2.1308 | 2.0885 |
| Resource-only | 2.4574 | 2.4655 |
| Adaptive | 2.2594 | 2.1800 |

Detailed results: `scheduler_v3_comparison.csv`

## Scheduler decision overhead

| Policy | Mean (ms) | Median (ms) | Max observed (ms) |
|---|---:|---:|---:|
| Round robin | 0.000483 | 0.000400 | 0.007500 |
| Queue-only | 0.001652 | 0.001600 | 0.022800 |
| Resource-only | 0.001636 | 0.001500 | 0.024300 |
| Adaptive | 0.002696 | 0.002500 | 0.032000 |

Detailed results: `scheduler_v3_overhead.csv`

## Phase 4 limitations

- Inference measurements were sequential and used one worker.
- Scheduler scenarios and proxy costs were synthetic.
- Local scheduler timing excludes HTTP, networking, and inference.
- Multi-worker routing validation was completed in Phase 5; see the results below.
- Kubernetes deployment and inference validation are documented in Phase 5.

## Phase 5 — Kubernetes Deployment and Validation

### Deployment

- Preserved the original `ai-inference-api` deployment using `ai-inference-platform:v2`.
- Built the updated image `ai-inference-platform:dev3.1`.
- Deployed the v3 gateway and worker using `ai-inference-platform:dev3.1`.
- Exposed the v3 gateway through NodePort 32089.
- Exposed the v3 worker internally through a ClusterIP service.
- Preserved the original v2 API on NodePort 32088.
- Both v3 deployments successfully rolled out and reported 1/1 ready.
- Saved the final cluster snapshot in `kubernetes-v3-status.txt`.

### End-to-end inference validation

- BERT: DistilBERT sentiment analysis succeeded through the v3.1 Kubernetes gateway.
- YOLO: YOLOv8n ONNX object detection succeeded through the v3.1 Kubernetes gateway, producing five detections on the 810 x 1080 test image.
- TinyLlama: CPU text generation succeeded through the v3.1 Kubernetes gateway.
- The v3 gateway health endpoint returned status `ok`.
- Final cluster inspection showed the v2 API, v3.1 gateway, and v3.1 worker running with zero pod restarts.
- These tests validate end-to-end inference for the tested requests; they do not establish production reliability or load capacity.

### Horizontal Pod Autoscaling

- Configured an HPA for `ai-inference-worker-v3`.
- Minimum replicas: 1; maximum replicas: 2.
- Target CPU utilization: 70%.
- The HPA reported valid CPU metrics and a desired replica count.
- The final snapshot showed CPU utilization of 1% of the requested CPU.
- A controlled test sent 60 BERT requests through the v3 gateway; all 60 succeeded.
- HPA CPU reached 371% against the 70% target, and Kubernetes created a second worker replica; both replicas became Ready.
- After the load subsided, CPU returned to 1%; the HPA retained two replicas at the final check.

### Phase 5 limitations

- The gateway was configured with independently identified worker-1 and worker-2 endpoints.
- A 20-request BERT routing test completed successfully: worker-1 was selected 11 times and worker-2 9 times.
- HPA scale-out from one to two ready replicas was observed under controlled load.
- Scheduler metrics remain synthetic; live-metric scheduling and production-scale behavior are not validated.

## Overall status

- Phase 4 benchmark and synthetic scheduling experiments are documented.
- Phase 5 v3.1 deployment and BERT, YOLO, and TinyLlama inference validation are complete.
- HPA scale-out and multi-worker routing have been validated in the local Docker Desktop Kubernetes environment. Live-metric scheduling and production-scale behavior remain future work.
