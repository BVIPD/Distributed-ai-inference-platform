
import csv
import random
import time
from statistics import mean

WORKERS = ["worker-1", "worker-2", "worker-3"]
NUM_SCENARIOS = 1000
SEED = 42


def generate_scenarios():
    """Generate one fixed workload shared by every algorithm."""
    rng = random.Random(SEED)
    scenarios = []

    for scenario_id in range(NUM_SCENARIOS):
        workers = {}

        for worker in WORKERS:
            workers[worker] = {
                "queue_length": rng.randint(1, 10),
                "resource_usage": rng.randint(1, 10),
                "node_load": rng.randint(1, 10),
            }

        scenarios.append({
            "scenario_id": scenario_id + 1,
            "priority": rng.randint(1, 10),
            "workers": workers,
        })

    return scenarios


def adaptive_score(state, priority):
    return (
        0.45 * state["queue_length"]
        + 0.30 * state["resource_usage"]
        + 0.25 * state["node_load"]
        - 0.05 * priority * state["queue_length"]
    )


def choose_worker(algorithm, scenario):
    workers = scenario["workers"]
    priority = scenario["priority"]

    if algorithm == "round_robin":
        index = (scenario["scenario_id"] - 1) % len(WORKERS)
        return WORKERS[index]

    if algorithm == "queue_only":
        return min(
            WORKERS,
            key=lambda w: workers[w]["queue_length"]
        )

    if algorithm == "resource_only":
        return min(
            WORKERS,
            key=lambda w: workers[w]["resource_usage"]
        )

    if algorithm == "adaptive":
        return min(
            WORKERS,
            key=lambda w: adaptive_score(workers[w], priority)
        )

    raise ValueError(f"Unknown algorithm: {algorithm}")


def estimated_cost(state, priority):
    """Common evaluation objective, not measured execution latency."""
    return (
        0.45 * state["queue_length"]
        + 0.30 * state["resource_usage"]
        + 0.25 * state["node_load"]
        - 0.05 * priority * state["queue_length"]
    )


def main():
    scenarios = generate_scenarios()
    algorithms = [
        "round_robin",
        "queue_only",
        "resource_only",
        "adaptive",
    ]

    results = []

    for algorithm in algorithms:
        costs = []
        decisions = {worker: 0 for worker in WORKERS}
        start = time.perf_counter()

        for scenario in scenarios:
            worker = choose_worker(algorithm, scenario)
            decisions[worker] += 1
            costs.append(
                estimated_cost(
                    scenario["workers"][worker],
                    scenario["priority"],
                )
            )

        elapsed_ms = (time.perf_counter() - start) * 1000

        results.append({
            "algorithm": algorithm,
            "scenarios": len(scenarios),
            "mean_estimated_cost": round(mean(costs), 4),
            "min_estimated_cost": round(min(costs), 4),
            "max_estimated_cost": round(max(costs), 4),
            "worker_1_selections": decisions["worker-1"],
            "worker_2_selections": decisions["worker-2"],
            "worker_3_selections": decisions["worker-3"],
            "decision_time_ms": round(elapsed_ms, 3),
        })

    with open(
        "scheduler_comparison.csv",
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=results[0].keys(),
        )
        writer.writeheader()
        writer.writerows(results)

    print(f"Fixed scenarios: {NUM_SCENARIOS}")
    print(f"Random seed: {SEED}")
    print("\nAlgorithm comparison:")
    for result in results:
        print(
            f"{result['algorithm']:15s} "
            f"mean_cost={result['mean_estimated_cost']:8.4f} "
            f"decision_time={result['decision_time_ms']:8.3f} ms"
        )

    print("\nSaved: scheduler_comparison.csv")
    print(
        "Note: costs are simulated objective values, "
        "not real inference latency."
    )


if __name__ == "__main__":
    main()
