"""CPU tests for the v2 (SUMO) context agent, event plans, prompts and day generator (no SUMO needed)."""
import json
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jevtraffic.events import EventManager, Notifier, rule_situation  # noqa: E402
from jevtraffic.memory import ContextAgent, TriggerConfig  # noqa: E402
from jevtraffic.sumo_env import Movement, SumoObs, compass_from  # noqa: E402
from jevtraffic.sumo_prompts import (SITUATION_QUESTION, history_table, phase_question,  # noqa: E402
                                     render_state)


def make_obs(t=100.0, phase=0, green=3, halting=None, discharged=None, special=(), allowed=(0, 1)):
    mv = [Movement("m0", "south", "through", [0], 4, 1, 10, 0, ["s_0", "s_1"], "s", "n"),
          Movement("m1", "west", "left", [1], 2, 0, 20, 0, ["w_0"], "w", "s"),
          Movement("m2", "west", "right", [], 0, 1, 0, 0, ["w_1"], "w", "n")]
    halting = halting if halting is not None else {"s_0": 3, "s_1": 1, "w_0": 2, "w_1": 0}
    discharged = discharged if discharged is not None else {"s_0": 1, "s_1": 1, "w_0": 0, "w_1": 0}
    return SumoObs(time=t, movements=mv, phase_movements=[[0], [1]], current_phase=phase, green_steps=green,
                   allowed=list(allowed), pressures=[4, 2], special=list(special), discharged=[2, 0, 0],
                   lane_halting=halting, lane_discharged=discharged, lane_wait={"s_0": 3, "s_1": 1, "w_0": 2},
                   lane_phases={"s_0": [0], "s_1": [0], "w_0": [1], "w_1": []})


def test_compass():
    assert compass_from([0, 1]) == "south"   # heading north -> comes from the south
    assert compass_from([1, 0]) == "west"
    assert compass_from([0, -1]) == "north"


def test_phase_question_and_state():
    obs = make_obs()
    q, phases = phase_question(obs)
    assert q.options == ("south through", "west left") and phases == [0, 1]
    s = render_state(obs)
    assert "Current green: south through (for 15 s)" in s and "west right [always allowed]" in s
    s = render_state(obs, blocked={"s_0"})
    assert "south through: stopped 1 (1 lane blocked, excluded)" in s
    s = render_state(obs, blocked={"w_0"})
    assert "west left: BLOCKED" in s


def test_stall_trigger_and_cooldown():
    agent = ContextAgent("triggered", config=TriggerConfig(cooldown=30))
    stalled = {"s_0": 4, "s_1": 1, "w_0": 2, "w_1": 0}
    none = {"s_0": 0, "s_1": 1, "w_0": 0, "w_1": 0}
    agent.observe(make_obs(t=100, halting=stalled, discharged=none))
    assert agent.triggers(make_obs(t=100)) == []          # one step is not enough
    obs = make_obs(t=105, halting=stalled, discharged=none)
    agent.observe(obs)
    trig = agent.triggers(obs)
    assert [t.kind for t in trig] == ["stall"] and trig[0].lanes == ["s_0"]
    obs = make_obs(t=110, halting=stalled, discharged=none)
    agent.observe(obs)
    assert agent.triggers(obs) == []                      # cooldown
    assert agent.summary()["extra_calls"] == 1


def test_v2x_trigger_once_per_vehicle_and_always_mode():
    sp = [{"id": "amb", "kind": "ambulance", "movement": 1, "phase": 1, "dist": 80.0, "speed": 8.0}]
    agent = ContextAgent("triggered")
    for t in (100, 105):
        obs = make_obs(t=t, special=sp)
        agent.observe(obs)
        fired = agent.triggers(obs)
        assert [x.kind for x in fired] == (["v2x"] if t == 100 else [])
    always = ContextAgent("always")
    obs = make_obs()
    always.observe(obs)
    assert [x.kind for x in always.triggers(obs)] == ["always"]
    assert ContextAgent("none").triggers(obs) == []


def test_preemption_plan(tmp_path):
    sp = [{"id": "amb", "kind": "ambulance", "movement": 1, "phase": 1, "dist": 80.0, "speed": 8.0},
          {"id": "pol", "kind": "police", "movement": 0, "phase": 0, "dist": 20.0, "speed": 8.0}]
    path = tmp_path / "ev.jsonl"
    em = EventManager(Notifier(str(path), "J"), tau=0.5, max_hold=2)
    obs = make_obs(special=sp)
    from jevtraffic.memory import Trigger
    assert rule_situation(obs, [])[0] == "normal"   # the rule detector only acts on triggers
    assert rule_situation(obs, [Trigger("v2x", vehicles=["amb", "pol"])]) == ("ambulance", 1.0)
    em.on_situation(obs, [Trigger("v2x", vehicles=["amb", "pol"])], "ambulance", 0.9, "jev")
    assert em.override(obs) == 1              # ambulance outranks police, despite being farther
    em.override(obs)
    em.update(obs)                            # held max_hold times -> released
    assert "amb" not in em.preempt
    em.update(make_obs(special=[]))           # police left
    actions = [json.loads(l)["action"] for l in open(path)]
    assert actions.count("preemption_start") == 2 and actions.count("preemption_end") == 2


def test_low_confidence_situation_is_ignored():
    em = EventManager(Notifier(None), tau=0.6)
    from jevtraffic.memory import Trigger
    em.on_situation(make_obs(), [Trigger("stall", lanes=["s_0"])], "blockage", 0.55, "jev")
    assert em.blocked_lanes() == set() and em.stats["dismissed"] == 1
    em.on_situation(make_obs(), [Trigger("stall", lanes=["s_0"])], "blockage", 0.9, "jev")
    assert em.blocked_lanes() == {"s_0"}
    em.update(make_obs(discharged={"s_0": 2, "s_1": 1, "w_0": 0, "w_1": 0}))  # green and discharging again
    assert em.blocked_lanes() == set()


def test_history_table():
    agent = ContextAgent("triggered")
    for t in (100, 105, 110):
        agent.observe(make_obs(t=t))
    table = history_table(make_obs(t=110), agent.memory.items())
    assert table.count("\nt=") == 3 and "Sou-T 4/2" in table
    assert len(SITUATION_QUESTION.options) == 5


def test_day_generator_deterministic(tmp_path):
    from jevtraffic.days import make_day
    from jevtraffic.sumo_env import SINGLETSC_DIR
    if not os.path.isdir(os.path.join(SINGLETSC_DIR, "junction_scenarios")):
        return  # third_party not fetched
    a = make_day("France_Massy", "normal", 2, str(tmp_path / "a"))
    b = make_day("France_Massy", "normal", 2, str(tmp_path / "b"))
    c = make_day("France_Massy", "normal", 3, str(tmp_path / "c"))
    assert a["pattern"] == "high_density" and a["vehicles"] == b["vehicles"]
    assert open(a["route_file"]).read() == open(b["route_file"]).read()
    assert open(a["route_file"]).read() != open(c["route_file"]).read()
    deps = [float(v.get("depart")) for v in ET.parse(a["route_file"]).getroot().iter("vehicle")]
    assert deps == sorted(deps)
