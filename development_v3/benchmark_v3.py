import base64
import csv
import json
import statistics
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = "http://127.0.0.1:8002"
OUTPUT = Path(__file__).resolve().parent / "benchmark_v3_results.csv"
IMAGE_PATH = Path(__file__).resolve().parent / "models" / "yolo" / "test_bus.jpg"

def post_json(path, payload, timeout=180):
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))

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
        print(f"\nTesting {model}...")
        start = time.perf_counter()
        try:
            result = post_json("/infer", payload)
            elapsed_ms = (time.perf_counter() - start) * 1000
            rows.append({
                "model": model,
                "request": 1,
                "latency_ms": round(elapsed_ms, 2),
                "success": result.get("execution_status") == "completed",
                "worker": result.get("selected_worker", ""),
                "error": "",
            })
            print(f"  Status: {result.get('execution_status')}")
            print(f"  Latency: {elapsed_ms:.2f} ms")
            print(f"  Worker: {result.get('selected_worker')}")
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            rows.append({
                "model": model,
                "request": 1,
                "latency_ms": round(elapsed_ms, 2),
                "success": False,
                "worker": "",
                "error": str(exc),
            })
            print(f"  FAILED after {elapsed_ms:.2f} ms: {exc}")

    with OUTPUT.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["model", "request", "latency_ms", "success", "worker", "error"],
        )
        writer.writeheader()
        writer.writerows(rows)

    print("\nSummary:")
    for model, _ in cases:
        values = [r["latency_ms"] for r in rows if r["model"] == model and r["success"]]
        if values:
            print(f"  {model}: {len(values)} successful request(s), "
                  f"mean={statistics.mean(values):.2f} ms")
        else:
            print(f"  {model}: no successful requests")
    print(f"\nCSV saved to: {OUTPUT}")

if __name__ == "__main__":
    main()
