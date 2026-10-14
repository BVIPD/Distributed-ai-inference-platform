
import csv
from collections import defaultdict
from statistics import mean

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Read actual benchmark measurements.
data = defaultdict(list)

with open("benchmark_results.csv", newline="") as file:
    for row in csv.DictReader(file):
        data[row["model"]].append(float(row["latency_ms"]))

models = ["yolo", "llama", "bert"]

# Graph 1: Mean API response latency.
averages = [mean(data[model]) for model in models]

plt.figure(figsize=(8, 5))
bars = plt.bar(
    [model.upper() for model in models],
    averages
)
plt.title("Mean API Response Latency by Model")
plt.xlabel("Model")
plt.ylabel("Mean latency (ms)")
plt.bar_label(bars, fmt="%.1f ms", padding=3)
plt.tight_layout()
plt.savefig("mean_latency.png", dpi=200)
plt.close()

# Graph 2: Individual request latency measurements.
plt.figure(figsize=(9, 5))
for model in models:
    iterations = range(1, len(data[model]) + 1)
    plt.plot(iterations, data[model], marker=".", label=model.upper())

plt.title("API Response Latency Across 30 Requests")
plt.xlabel("Request number")
plt.ylabel("Response latency (ms)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("request_latency.png", dpi=200)
plt.close()

print("Graphs generated successfully:")
print("1. mean_latency.png")
print("2. request_latency.png")
print("\nMean latency from CSV:")
for model in models:
    print(f"{model.upper()}: {mean(data[model]):.3f} ms")
