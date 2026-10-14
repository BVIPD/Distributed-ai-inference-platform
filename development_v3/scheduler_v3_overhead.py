import random
import statistics
import time
from pathlib import Path
from scheduler_v3_evaluation import choose, generate_scenarios, WORKERS

REPEATS = 1000
POLICIES = ["round_robin", "queue_only", "resource_only", "adaptive"]
OUTPUT = Path(__file__).resolve().parent / "scheduler_v3_overhead.csv"

scenarios = generate_scenarios()
rows = []

for policy in POLICIES:
    durations = []
    for i in range(REPEATS):
        workers, priority = scenarios[i % len(scenarios)]
        start = time.perf_counter_ns()
        choose(policy, workers, priority, i)
        durations.append((time.perf_counter_ns() - start) / 1_000_000)

    rows.append({
        "policy": policy,
        "repeats": REPEATS,
        "mean_decision_ms": round(statistics.mean(durations), 6),
        "median_decision_ms": round(statistics.median(durations), 6),
        "max_decision_ms": round(max(durations), 6),
    })

with OUTPUT.open("w", newline="", encoding="utf-8") as f:
    import csv
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

print("Scheduler decision overhead (local Python microbenchmark)")
for row in rows:
    print(
        f"{row['policy']:<16} "
        f"mean={row['mean_decision_ms']:.6f} ms  "
        f"median={row['median_decision_ms']:.6f} ms  "
        f"max={row['max_decision_ms']:.6f} ms"
    )
print(f"\nSaved to: {OUTPUT}")
