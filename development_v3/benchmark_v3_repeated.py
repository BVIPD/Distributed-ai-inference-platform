import base64
import csv
import json
import math
import statistics
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = "http://127.0.0.1:8002"
REPEATS = 10
ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "benchmark_v3_repeated_results.csv"
IMAGE_PATH = ROOT / "models" / "yolo" / "test_bus.jpg"

def post_json(payload, timeout=180):
    request = urllib.request.Request(
        f"{BASE_URL}/infer",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))

def percentile(values, p):
    ordered = sorted(values)
    index = max(0, math.ceil(p * len(ordered)) - 1)
    return ordered[index]

def main():
    image_base64 = base64.b64encode(IMAGE_PATH.read_bytes()).decode("ascii")
    cases = [
        ("bert", {"model": "bert", "priority": 1,
                  "text": "I absolutely love this platform. It works wonderfully!"}),
        ("yolo", {"model": "yolo", "priority": 1,
                  "image_base64": image_base64}),
        ("llama", {"model": "llama", "priority": 1,
                   "text": "Explain cloud computing in one short sentence."}),
    ]

    rows = []
    for model, payload in cases:
        print(f"\nTesting {model}: {REPEATS} sequential requests")
        for number in range(1, REPEATS + 1):
            start = time.perf_counter()
            try:
                result = post_json(payload)
                elapsed = (time.perf_counter() - start) * 1000
                success = result.get("execution_status") == "completed"
                error = "" if success else "Response not completed"
                worker = result.get("selected_worker", "")
            except Exception as exc:
                elapsed = (time.perf_counter() - start) * 1000
                success = False
                error = f"{type(exc).__name__}: {exc}"
                worker = ""

            rows.append({
                "model": model,
                "request": number,
                "latency_ms": round(elapsed, 2),
                "success": success,
                "worker": worker,
                "error": error,
            })
            print(f"  {number:02d}/{REPEATS}: {elapsed:.2f} ms - "
                  f"{'OK' if success else 'FAILED'}")
            if not success:
                print(f"      {error}")

    with OUTPUT.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["model", "request", "latency_ms", "success", "worker", "error"],
        )
        writer.writeheader()
        writer.writerows(rows)

    print("\nSUMMARY (end-to-end latency)")
    print("model   success   mean_ms   median_ms   p95_ms")
    for model, _ in cases:
        group = [r for r in rows if r["model"] == model]
        successful = [r["latency_ms"] for r in group if r["success"]]
        if successful:
            print(f"{model:<7} {len(successful):>2}/{len(group):<7} "
                  f"{statistics.mean(successful):>8.2f} "
                  f"{statistics.median(successful):>11.2f} "
                  f"{percentile(successful, 0.95):>8.2f}")
        else:
            print(f"{model:<7} 0/{len(group)}       no successful measurements")

    print(f"\nDetailed CSV: {OUTPUT}")

if __name__ == "__main__":
    main()
