"""CPU-only tests: no CityFlow, no GPU. Run with `pytest tests/`."""
import math

from jevtraffic.agents import MaxPressureAgent, MaxQueueAgent, phase_pressure
from jevtraffic.decider import Choice, Score, TypedDecider, option_orders, render_turn, softmax
from jevtraffic.env import LANES, PHASES, Observation
from jevtraffic.prompts import PHASE_QUESTION, typed_state


def make_obs(queues: dict, downstream=None, phase=0):
    lanes = {l: {"queue_num": queues.get(l, 0), "moving_num": 0, "occupancy": 0.1 if queues.get(l) else 0.0,
                 "avg_wait_time": 30.0} for l in LANES}
    neighbour = {l: {"queue_num": 0, "moving_num": 0, "occupancy": 0.0, "avg_wait_time": 0.0} for l in LANES}
    for l, q in (downstream or {}).items():
        neighbour[l]["queue_num"] = q
    ds = {l: [] for l in LANES}
    ds["ET"] = [(1, "ET")]
    ds["WT"] = [(1, "WT")]
    return Observation(texts=["", ""], lanes=[lanes, neighbour], downstream=[ds, {l: [] for l in LANES}],
                       current_phase=[phase, phase])


def test_softmax():
    p = softmax([1.0, 1.0, 1.0])
    assert all(math.isclose(x, 1 / 3) for x in p)
    assert softmax([10.0, 0.0])[0] > 0.99


def test_question_matches_phase_order():
    assert len(PHASE_QUESTION.options) == len(PHASES)
    for opt, ph in zip(PHASE_QUESTION.options, PHASES):
        assert opt.startswith(ph)
    text = render_turn("STATE", PHASE_QUESTION)
    assert "A. ETWT" in text and "D. NLSL" in text and "STATE" in text


def test_maxqueue_and_pressure():
    obs = make_obs({"NL": 5, "SL": 4, "ET": 6})
    assert MaxQueueAgent().act(obs)[0] == PHASES.index("NLSL")
    # ET has queue 6 but its downstream is jammed -> pressure prefers NLSL
    obs = make_obs({"NL": 5, "SL": 4, "ET": 6}, downstream={"ET": 10})
    assert phase_pressure(obs, 0, "ETWT") < phase_pressure(obs, 0, "NLSL")
    assert MaxPressureAgent().act(obs)[0] == PHASES.index("NLSL")


def test_tie_keeps_current_phase():
    obs = make_obs({}, phase=2)
    assert MaxQueueAgent().act(obs)[0] == 2


def test_typed_state_contents():
    s = typed_state(make_obs({"NT": 3, "ST": 2}), 0)
    assert "NTST (NT + ST): queue=5" in s
    assert "Current signal: ETWT" in s


class _FakeDecider(TypedDecider):
    """Scores letters by a fixed preference for the option *text*, plus a bias towards position A.
    Score questions get logits peaked at the digit encoded in the state."""

    def __init__(self, permutations):
        self.temperature, self.temperatures, self.permutations = 1.0, {}, permutations
        self.stats = {"calls": 0, "sequences": 0, "prompt_tokens": 0, "seconds": 0.0}
        self.label_ids, self.digit_ids = list(range(26)), list(range(100, 110))

    def _prompt(self, state, q):
        return (state, tuple(q.options), isinstance(q, Score))

    def _score(self, prompts, label_ids):
        pref = {"x": 0.0, "y": 1.0, "z": 0.5}
        out = []
        for state, options, is_score in prompts:
            if is_score:
                out.append([5.0 if int(o) == int(state) else 0.0 for o in options])
            else:
                out.append([pref[o] + (2.0 if k == 0 else 0.0) for k, o in enumerate(options)])
        return out


def test_permutations_cancel_position_bias():
    q = Choice("q", ["x", "y"])
    biased = _FakeDecider(1).decide("s", q)
    assert biased.choice == "x"  # position bias wins
    debiased = _FakeDecider(2).decide("s", q)
    assert debiased.choice == "y"  # true preference wins after averaging both orders
    assert math.isclose(sum(debiased.probabilities), 1.0)


def test_option_orders_cover_every_position():
    orders = option_orders(4, 4)
    assert len(orders) == 4
    for pos in range(4):
        assert {o[pos] for o in orders} == set(range(4))


def test_full_permutation_debias_three_options():
    d = _FakeDecider(3).decide("s", Choice("q", ["x", "y", "z"]))
    assert d.choice == "y"


def test_score_expected_value_and_batching():
    dec = _FakeDecider(1)
    q = Score("urgency?", 0, 9)
    out = dec.decide_items([("7", q), ("2", q), ("s", Choice("q", ["x", "y"]))])
    assert out[0].index == 7 and 6.5 < out[0].expected < 7.5
    assert out[1].index == 2
    assert out[2].choice == "x"
    assert "Answer with one integer from 0 to 9." in render_turn("S", q)
