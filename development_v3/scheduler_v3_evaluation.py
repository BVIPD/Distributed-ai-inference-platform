import csv
import random
import statistics
from pathlib import Path

SEED = 42
SCENARIOS = 1000
WORKERS = ["worker-1", "worker-2", "worker-3"]
ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "scheduler_v3_comparison.csv"

def generate_scenarios():
    rng = random.Random(SEED)
    scenarios = []
    for _ in range(SCENARIOS):
        workers = {
            worker: {
                "queue_length": rng.randint(0, 10),
                "resource_usage": rng.randint(1, 100),
                "node_load": rng.randint(1, 100),
            }
            for worker in WORKERS
        }
        priority = rng.randint(1, 10)
        scenarios.append((workers, priority))
    return scenarios

def choose(policy, workers, priority, index):
    if policy == "round_robin":
        return WORKERS[index % len(WORKERS)]
    if policy == "queue_only":
        return min(WORKERS, key=lambda w: (workers[w]["queue_length"], WORKERS.index(w)))
    if policy == "resource_only":
        return min(WORKERS, key=lambda w: (workers[w]["resource_usage"], WORKERS.index(w)))
    if policy == "adaptive":
        def score(w):
            s = workers[w]
            return (
                0.45 * s["queue_length"]
                + 0.30 * (s["resource_usage"] / 10)
                + 0.25 * (s["node_load"] / 10)
                - 0.05 * priority * s["queue_length"]
            )
        return min(WORKERS, key=lambda w: (score(w), WORKERS.index(w)))
    raise ValueError(policy)

def proxy_cost(state):
    # Independent synthetic proxy, not measured inference latency.
    return (
        1.0
        + 0.20 * state["queue_length"]
        + 0.08 * (state["resource_usage"] / 10)
        + 0.05 * (state["node_load"] / 10)
    )

def main():
    policies = ["round_robin", "queue_only", "resource_only", "adaptive"]
    scenarios = generate_scenarios()
    rows = []

    for index, (workers, priority) in enumerate(scenarios):
        for policy in policies:
            selected = choose(policy, workers, priority, index)
            state = workers[selected]
            rows.append({
                "scenario": index + 1,
                "policy": policy,
                "priority": priority,
                "selected_worker": selected,
                "queue_length": state["queue_length"],
                "resource_usage": state["resource_usage"],
                "node_load": state["node_load"],
                "synthetic_proxy_cost": round(proxy_cost(state), 4),
            })

    with OUTPUT.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Fixed seed: {SEED}; scenarios: {SCENARIOS}")
    print("Results are synthetic proxy costs, NOT real inference latency.")
    print("\npolicy          mean_cost   median_cost")
    for policy in policies:
        values = [r["synthetic_proxy_cost"] for r in rows if r["policy"] == policy]
        print(f"{policy:<16} {statistics.mean(values):>9.4f}   "
              f"{statistics.median(values):>11.4f}")

    print(f"\nSaved {len(rows)} policy decisions to: {OUTPUT}")

if __name__ == "__main__":
    main()
