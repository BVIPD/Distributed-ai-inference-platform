
import csv
import random
from statistics import mean

WORKERS = ["worker-1", "worker-2", "worker-3"]
NUM_SCENARIOS = 1000
SEED = 42


def generate_scenarios():
    rng = random.Random(SEED)
    scenarios = []

    for scenario_id in range(1, NUM_SCENARIOS + 1):
        worker_states = {}

        for worker in WORKERS:
            worker_states[worker] = {
                "queue_length": rng.randint(1, 10),
                "resource_usage": rng.randint(1, 10),
                "node_load": rng.randint(1, 10),
            }

        scenarios.append({
            "scenario_id": scenario_id,
            "priority": rng.randint(1, 10),
            "workers": worker_states,
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
    states = scenario["workers"]
    priority = scenario["priority"]

    if algorithm == "round_robin":
        return WORKERS[(scenario["scenario_id"] - 1) % len(WORKERS)]

    if algorithm == "queue_only":
        return min(WORKERS, key=lambda w: states[w]["queue_length"])

    if algorithm == "resource_only":
        return min(WORKERS, key=lambda w: states[w]["resource_usage"])

    if algorithm == "adaptive":
        return min(
            WORKERS,
            key=lambda w: adaptive_score(states[w], priority),
        )

    raise ValueError(f"Unknown algorithm: {algorithm}")


def estimated_completion_time(state):
    """Synthetic proxy in arbitrary time units; not measured latency."""
    queue = state["queue_length"]
    resource = state["resource_usage"]
    load = state["node_load"]

    return 1.0 + 0.20 * queue + 0.08 * resource + 0.05 * load


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
        completion_estimates = []
        worker_counts = {worker: 0 for worker in WORKERS}

        for scenario in scenarios:
            selected = choose_worker(algorithm, scenario)
            worker_counts[selected] += 1

            completion_estimates.append(
                estimated_completion_time(
                    scenario["workers"][selected]
                )
            )

        results.append({
            "algorithm": algorithm,
            "scenarios": len(scenarios),
            "mean_estimated_completion_units": round(
                mean(completion_estimates), 4
            ),
            "worker_1_selections": worker_counts["worker-1"],
            "worker_2_selections": worker_counts["worker-2"],
            "worker_3_selections": worker_counts["worker-3"],
        })

    with open(
        "scheduler_independent_eval.csv",
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(file, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print(f"Scenarios: {NUM_SCENARIOS}; seed: {SEED}")
    print("\nIndependent synthetic completion-time proxy:")
    for result in results:
        print(
            f"{result['algorithm']:15s} "
            f"mean={result['mean_estimated_completion_units']:.4f}"
        )

    print("\nSaved: scheduler_independent_eval.csv")
    print(
        "These are synthetic estimates, not real completion times "
        "or measured inference latency."
    )


if __name__ == "__main__":
    main()
