
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

with open("scheduler_comparison.csv", newline="", encoding="utf-8") as file:
    rows = list(csv.DictReader(file))

algorithms = [row["algorithm"] for row in rows]
workers = ["worker-1", "worker-2", "worker-3"]

counts = {
    worker: [
        int(row[f"{worker.replace('-', '_')}_selections"])
        for row in rows
    ]
    for worker in workers
}

plt.figure(figsize=(9, 5))
x = list(range(len(algorithms)))
width = 0.25

for index, worker in enumerate(workers):
    positions = [value + (index - 1) * width for value in x]
    plt.bar(positions, counts[worker], width=width, label=worker)

plt.xticks(x, algorithms, rotation=15)
plt.ylabel("Number of worker selections")
plt.title("Worker Selection Distribution by Scheduling Algorithm")
plt.legend()
plt.tight_layout()
plt.savefig("worker_distribution.png", dpi=200)
plt.close()

print("Generated worker_distribution.png")
