"""Which scheduler helps a simulated student most?

    python -m sim.compare_policies --seeds 500 --plot bench/results/bandit.png
"""

import argparse

import numpy as np

from sim.student import SimStudent


def p_random(state, w, student, rng, step):
    return int(rng.integers(len(w)))


def p_round_robin(state, w, student, rng, step):
    return step % len(w)


def p_greedy(state, w, student, rng, step):
    untried = np.flatnonzero(state["n"] == 0)
    if untried.size:
        return int(untried[0])
    acc = (state["alpha"] - 1) / np.maximum(state["alpha"] + state["beta"] - 2, 1e-9)
    return int(np.argmax(w * (1 - acc)))


def p_eps_greedy(state, w, student, rng, step, eps=0.1):
    if rng.random() < eps:
        return p_random(state, w, student, rng, step)
    return p_greedy(state, w, student, rng, step)


def p_thompson(state, w, student, rng, step):
    return int(np.argmax(w * rng.beta(state["beta"], state["alpha"])))


def p_oracle(state, w, student, rng, step):
    return int(np.argmax(w * (1 - student.mastery)))


POLICIES = {
    "random": (p_random, 0.98),
    "round_robin": (p_round_robin, 0.98),
    "greedy": (p_greedy, 0.98),
    "eps_greedy": (p_eps_greedy, 0.98),
    "thompson": (p_thompson, 1.0),
    "thompson_disc": (p_thompson, 0.98),
    "oracle": (p_oracle, 0.98),
}


def run(policy, gamma: float, seed: int, n_topics: int = 10, budget: int = 150,
        learn_rate: float = 0.06) -> float:
    rng = np.random.default_rng(seed)
    w = rng.uniform(0.8, 1.5, n_topics)
    student = SimStudent(mastery=rng.beta(2, 2, n_topics), learn_rate=learn_rate)
    state = {"alpha": np.ones(n_topics), "beta": np.ones(n_topics), "n": np.zeros(n_topics)}
    for step in range(budget):
        t = policy(state, w, student, rng, step)
        r = student.answer(t, rng)
        state["alpha"] = 1 + (state["alpha"] - 1) * gamma
        state["beta"] = 1 + (state["beta"] - 1) * gamma
        state["alpha"][t] += r
        state["beta"][t] += 1 - r
        state["n"][t] += 1
    return float(w @ student.mastery / w.sum())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=500)
    ap.add_argument("--topics", type=int, default=10)
    ap.add_argument("--budget", type=int, default=150)
    ap.add_argument("--learn-rate", type=float, default=0.06)
    ap.add_argument("--plot")
    args = ap.parse_args()

    results = {}
    for name, (policy, gamma) in POLICIES.items():
        scores = np.array([run(policy, gamma, s, args.topics, args.budget, args.learn_rate)
                           for s in range(args.seeds)])
        half = 1.96 * scores.std(ddof=1) / np.sqrt(len(scores))
        results[name] = (scores.mean(), half)

    oracle = results["oracle"][0]
    print(f"{'policy':<14} {'final mastery':>14} {'95% CI':>10} {'regret':>8}")
    for name, (m, h) in sorted(results.items(), key=lambda kv: -kv[1][0]):
        print(f"{name:<14} {m:>14.4f} {'±' + format(h, '.4f'):>10} {oracle - m:>8.4f}")

    if args.plot:
        import matplotlib.pyplot as plt

        names = list(results)
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.barh(names, [results[n][0] for n in names], xerr=[results[n][1] for n in names])
        ax.set_xlabel("weighted final mastery (higher is better)")
        ax.set_xlim(min(r[0] for r in results.values()) - 0.02, oracle + 0.01)
        fig.tight_layout()
        fig.savefig(args.plot, dpi=150)
        print(f"saved {args.plot}")


if __name__ == "__main__":
    main()
