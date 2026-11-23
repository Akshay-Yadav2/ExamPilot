from sim.compare_policies import POLICIES, run


def test_oracle_beats_random_on_average():
    seeds = range(40)
    oracle = sum(run(POLICIES["oracle"][0], 0.98, s) for s in seeds)
    rand = sum(run(POLICIES["random"][0], 0.98, s) for s in seeds)
    assert oracle > rand
