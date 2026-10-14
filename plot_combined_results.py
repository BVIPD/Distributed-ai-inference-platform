
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def load_csv(filename):
    with open(filename, newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))

cost_rows = load_csv("scheduler_comparison.csv")
time_rows = load_csv("scheduler_independent_eval.csv")

labels = {
    "round_robin": "Round robin",
    "queue_only": "Queue only",
    "resource_only": "Resource only",
    "adaptive": "Adaptive",
}

algorithms = ["round_robin", "queue_only", "resource_only", "adaptive"]

costs = {
    row["algorithm"]: float(row["mean_estimated_cost"])
    for row in cost_rows
}
times = {
    row["algorithm"]: float(row["mean_estimated_completion_units"])
    for row in time_rows
}

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

axes[0].bar(
    [labels[a] for a in algorithms],
    [costs[a] for a in algorithms],
)
axes[0].set_title("Scheduling Cost Objective")
axes[0].set_ylabel("Mean estimated cost")
axes[0].tick_params(axis="x", rotation=20)

axes[1].bar(
    [labels[a] for a in algorithms],
    [times[a] for a in algorithms],
)
axes[1].set_title("Independent Completion-Time Proxy")
axes[1].set_ylabel("Mean estimated units")
axes[1].tick_params(axis="x", rotation=20)

fig.suptitle("Scheduling Algorithm Comparison — Simulated Workloads")
fig.tight_layout()
fig.savefig("combined_scheduler_comparison.png", dpi=200)
plt.close(fig)

print("Generated combined_scheduler_comparison.png")
