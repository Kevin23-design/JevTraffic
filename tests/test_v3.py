"""CPU tests for v3: keep/switch question, compact state, the controller's next_or_not path, soft targets."""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_v2 import make_obs  # noqa: E402

from jevtraffic.decider import Decision  # noqa: E402
from jevtraffic.sumo_agents import MAX_GREEN_SECONDS, Controller  # noqa: E402
from jevtraffic.sumo_prompts import (KEEP, SWITCH, action_to_option, option_to_action,  # noqa: E402
                                     render_compact, render_state, switch_question)


def switch_obs(green_seconds=10.0, **kw):
    obs = make_obs(**kw)
    obs.green_seconds = green_seconds
    return obs


class StubEnv:
    action_type = "next_or_not"
    junction = "J"

    def situation_label(self):
        return "normal"

    def pressures(self, waiting, exclude=frozenset()):
        return [4, 2]


class FakeDecider:
    def __init__(self, probs):
        self.probs, self.calls = probs, 0
        self.temperatures = {}

    def decide(self, state, q):
        self.calls += 1
        return Decision(q, list(self.probs))


def test_switch_question_and_action_mapping():
    obs = switch_obs()
    q = switch_question(obs)
    assert q.name == "switch" and q.options == ("keep: south through", "switch to: west left")
    assert option_to_action(KEEP) == 1 and option_to_action(SWITCH) == 0  # tshub: 1 keep, 0 switch
    assert action_to_option(1) == KEEP and action_to_option(0) == SWITCH


def test_state_uses_green_seconds_and_compact_is_shorter():
    obs = switch_obs(green_seconds=23)
    assert "(for 23 s)" in render_state(obs)
    c = render_compact(obs)
    assert c.startswith("t=100s green=P0 for 23s, next=P1") and "west right free: 0 1 0 0" in c
    assert len(c) < 0.7 * len(render_state(obs))
    assert "west left P1: BLOCKED" in render_compact(obs, blocked={"w_0"})


def test_controller_switch_mode():
    dec = FakeDecider([0.2, 0.8])  # prefers option 1 = switch
    ctl = Controller(StubEnv(), base="jev", decider=dec, state_format="compact")
    assert ctl.act(switch_obs()) == 0 and dec.calls == 1
    assert ctl.steps[-1]["mp"] == 1  # MaxPressure picks phase 0 = the current green -> keep
    assert ctl.act(switch_obs(green_seconds=MAX_GREEN_SECONDS)) == 0 and dec.calls == 1  # guard: no model call
    assert ctl.summary()["timing"]["skipped"] == 1
    mp = Controller(StubEnv(), base="mp")
    assert mp.act(switch_obs(phase=0)) == 1 and mp.act(switch_obs(phase=1)) == 0


def test_soft_targets_follow_shuffled_options():
    import pytest

    torch = pytest.importorskip("torch")
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
    from train_lora import make_batch

    class Tok:
        chat_template = ""

        def apply_chat_template(self, messages, tokenize, add_generation_prompt):
            return messages[-1]["content"]

    rec = {"kind": "switch", "state": "s", "question": "q?", "options": ["keep: a", "switch to: b"], "label": 0,
           "probs": [0.9, 0.1]}
    for seed in range(4):
        prompts, targets, _ = make_batch(Tok(), [rec], random.Random(seed), "soft", 0.25)
        first = prompts[0].split("A. ")[1].splitlines()[0]
        assert torch.isclose(targets[0][0], torch.tensor(0.9 if first == "keep: a" else 0.1))
        assert float(targets[0].sum()) == 1.0
