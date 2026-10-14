
import csv
import json
import time
import urllib.error
import urllib.request
from statistics import mean, median

API_URL = "http://127.0.0.1:8001/infer"
MODELS = ["yolo", "llama", "bert"]
WARMUP_REQUESTS = 3
MEASURED_REQUESTS = 30

results = []

def send_request(model):
    url = f"{API_URL}?model={model}&priority=5"
    request = urllib.request.Request(url, method="POST")

    start = time.perf_counter()

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = json.loads(response.read().decode("utf-8"))
            elapsed_ms = (time.perf_counter() - start) * 1000

            return {
                "model": model,
                "latency_ms": round(elapsed_ms, 3),
                "status_code": response.status,
                "selected_worker": body.get("selected_worker", ""),
            }

    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(
            f"Request failed for {model}: {exc}"
        ) from exc


# Warm up the API before measuring.
for model in MODELS:
    for _ in range(WARMUP_REQUESTS):
        send_request(model)

# Measure each model.
for model in MODELS:
    print(f"Benchmarking {model.upper()}...")

    for iteration in range(1, MEASURED_REQUESTS + 1):
        result = send_request(model)
        result["iteration"] = iteration
        results.append(result)

# Save every measured request.
with open("benchmark_results.csv", "w", newline="") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=[
            "model",
            "iteration",
            "latency_ms",
            "status_code",
            "selected_worker",
        ],
    )
    writer.writeheader()
    writer.writerows(results)

# Print summary statistics.
print("\n=== BENCHMARK SUMMARY ===")

for model in MODELS:
    measurements = [
        row["latency_ms"]
        for row in results
        if row["model"] == model
    ]

    successes = sum(
        row["status_code"] == 200
        for row in results
        if row["model"] == model
    )

    print(f"\nModel: {model.upper()}")
    print(f"Successful requests: {successes}/{len(measurements)}")
    print(f"Mean latency: {mean(measurements):.3f} ms")
    print(f"Median latency: {median(measurements):.3f} ms")

print("\nSaved measurements to benchmark_results.csv")
