"""Signal controllers. Every controller maps an Observation to one phase index (0..3) per intersection."""
from __future__ import annotations

import random
import re
import time

from .env import PHASES, PHASE_MOVEMENTS, Observation
from .prompts import PHASE_QUESTION, SYSTEM_PROMPT, phase_urgency_question, raw_state, render_state


class Agent:
    name = "agent"

    def act(self, obs: Observation) -> list[int]:
        raise NotImplementedError

    def step_log(self) -> dict:
        """Extra per-step information stored in the run log (confidences, fallbacks, ...)."""
        return {}

    def summary(self) -> dict:
        return {}


class FixedTimeAgent(Agent):
    """Cycle ETWT -> NTST -> ELWL -> NLSL, one 30 s action interval each (USTBench's FIXED_TIME=[30]*4)."""
    name = "fixedtime"

    def __init__(self):
        self.t = 0

    def act(self, obs):
        a = [self.t % len(PHASES)] * obs.n
        self.t += 1
        return a


class RandomAgent(Agent):
    name = "random"

    def __init__(self, seed: int = 0):
        self.rng = random.Random(seed)

    def act(self, obs):
        return [self.rng.randrange(len(PHASES)) for _ in range(obs.n)]


def phase_queue(obs: Observation, i: int, p: str) -> float:
    return sum(obs.lanes[i].get(l, {}).get("queue_num", 0) for l in PHASE_MOVEMENTS[p])


def phase_pressure(obs: Observation, i: int, p: str) -> float:
    """Queue-based movement pressure: upstream queue minus mean queue of the downstream lanes."""
    total = 0.0
    for lane in PHASE_MOVEMENTS[p]:
        up = obs.lanes[i].get(lane, {}).get("queue_num", 0)
        targets = obs.downstream[i].get(lane, [])
        down = sum(obs.lanes[j].get(l, {}).get("queue_num", 0) for j, l in targets) / len(targets) if targets else 0.0
        total += up - down
    return total


def argmax_keep(scores: list[float], current: int) -> int:
    """Argmax with ties broken in favour of the current phase (avoids needless yellow time)."""
    best = max(scores)
    if 0 <= current < len(scores) and scores[current] == best:
        return current
    return scores.index(best)


class MaxQueueAgent(Agent):
    name = "maxqueue"

    def act(self, obs):
        return [argmax_keep([phase_queue(obs, i, p) for p in PHASES], obs.current_phase[i]) for i in range(obs.n)]


class MaxPressureAgent(Agent):
    name = "maxpressure"

    def act(self, obs):
        return [argmax_keep([phase_pressure(obs, i, p) for p in PHASES], obs.current_phase[i]) for i in range(obs.n)]


class RolloutGreedyAgent(Agent):
    """Simulator-lookahead reference: pick the phase with the lowest 30 s rollout cost (TSCEnv.rollout_costs).
    Uses the simulator as a model, so it is an oracle-style upper reference, not a deployable controller.
    It is also the target that the sim-reward fine-tuning stage learns towards."""
    name = "rollout-greedy"

    def __init__(self, env):
        self.env = env

    def act(self, obs):
        costs = self.env.rollout_costs()
        return [argmax_keep([-c for c in cs], obs.current_phase[i]) for i, cs in enumerate(costs)]


class JevAgent(Agent):
    """Jev-style System One controller: one typed Choice per intersection, answered in one forward pass.

    gate_tau > 0 turns on confidence gating: when the decider's probability for its choice is below tau,
    the intersection falls back to MaxPressure ("act automatically when confident, escalate otherwise").
    """

    def __init__(self, decider, task_info: dict, state_format: str = "raw", gate_tau: float = 0.0):
        self.decider = decider
        self.task_info = task_info
        self.state_format = state_format
        self.gate_tau = gate_tau
        self.fallback = MaxPressureAgent()
        self.name = f"jev-{state_format}" + (f"-gate{gate_tau:g}" if gate_tau > 0 else "")
        self._log: dict = {}
        self.n_decisions = 0
        self.n_fallback = 0
        self.agree_mp = 0
        self.confidences: list[float] = []

    def act(self, obs):
        states = [render_state(obs, i, self.state_format, self.task_info) for i in range(obs.n)]
        decisions = self.decider.decide_many(states, PHASE_QUESTION)
        mp = self.fallback.act(obs)
        actions, used_fallback = [], []
        for i, d in enumerate(decisions):
            fb = self.gate_tau > 0 and d.confidence < self.gate_tau
            actions.append(mp[i] if fb else d.index)
            used_fallback.append(fb)
            self.confidences.append(d.confidence)
            self.agree_mp += int(d.index == mp[i])
        self.n_decisions += len(decisions)
        self.n_fallback += sum(used_fallback)
        self._log = {"probs": [[round(p, 4) for p in d.probabilities] for d in decisions],
                     "fallback": used_fallback, "maxpressure": mp}
        return actions

    def step_log(self):
        return self._log

    def summary(self):
        n = max(self.n_decisions, 1)
        return {"decider": dict(self.decider.stats),
                "mean_confidence": sum(self.confidences) / max(len(self.confidences), 1),
                "fallback_rate": self.n_fallback / n,
                "agreement_with_maxpressure": self.agree_mp / n,
                "latency_per_decision_ms": 1000 * self.decider.stats["seconds"] / n}


class JevScoreAgent(Agent):
    """Jev-style controller using Score questions: one 0-9 urgency score per phase, pick the highest expectation.

    Each phase is judged on its own, so there is no lettered option list for the model to be position-biased
    on; the four scores of all intersections are answered in one batched forward pass.
    """

    def __init__(self, decider, task_info: dict, state_format: str = "typed"):
        self.decider = decider
        self.task_info = task_info
        self.state_format = state_format
        self.name = f"jev-score-{state_format}"
        self.questions = [phase_urgency_question(p) for p in PHASES]
        self.n_decisions = 0
        self.agree_mp = 0
        self._log: dict = {}

    def act(self, obs):
        states = [render_state(obs, i, self.state_format, self.task_info) for i in range(obs.n)]
        decisions = self.decider.decide_items([(s, q) for s in states for q in self.questions])
        k = len(self.questions)
        urgency = [[d.expected for d in decisions[i * k:(i + 1) * k]] for i in range(obs.n)]
        actions = [argmax_keep(u, obs.current_phase[i]) for i, u in enumerate(urgency)]
        mp = MaxPressureAgent().act(obs)
        self.agree_mp += sum(a == m for a, m in zip(actions, mp))
        self.n_decisions += obs.n
        self._log = {"urgency": [[round(x, 3) for x in u] for u in urgency], "maxpressure": mp}
        return actions

    def step_log(self):
        return self._log

    def summary(self):
        n = max(self.n_decisions, 1)
        return {"decider": dict(self.decider.stats), "agreement_with_maxpressure": self.agree_mp / n,
                "latency_per_decision_ms": 1000 * self.decider.stats["seconds"] / n}


GEN_INSTRUCTION = (
    "\n\nTask: {target}\n"
    "Think step by step about the traffic data, then finish with a final line of the form "
    "'Answer: <signal>' where <signal> is one of ETWT, NTST, ELWL, NLSL."
)
_ANSWER = re.compile(r"Answer\s*:\s*\**\s*(ETWT|NTST|ELWL|NLSL)", re.IGNORECASE)
_ANY = re.compile(r"\b(ETWT|NTST|ELWL|NLSL)\b", re.IGNORECASE)


class GenerativeLLMAgent(Agent):
    """System Two baseline: the same open-weights LLM generates free-text reasoning + an answer (vLLM).

    Mirrors the USTBench setting (chain-of-thought, answer parsed from text) without its reflection loop.
    Unparseable answers fall back to ETWT (USTBench's behaviour) and are counted.
    """
    name = "llm-gen"

    def __init__(self, model_path: str, task_info: dict, max_tokens: int = 1024, gpu_memory_utilization: float = 0.7,
                 max_model_len: int = 8192):
        from vllm import LLM, SamplingParams

        self.llm = LLM(model=model_path, gpu_memory_utilization=gpu_memory_utilization, max_model_len=max_model_len,
                       enable_prefix_caching=True)
        self.params = SamplingParams(temperature=0.0, max_tokens=max_tokens)
        self.task_info = task_info
        self.n_decisions = 0
        self.n_invalid = 0
        self.seconds = 0.0
        self.gen_tokens = 0
        self._log: dict = {}

    def act(self, obs):
        target = self.task_info["task_target"]
        msgs = [[{"role": "system", "content": SYSTEM_PROMPT},
                 {"role": "user", "content": raw_state(obs, i, self.task_info) + GEN_INSTRUCTION.format(target=target)}]
                for i in range(obs.n)]
        t0 = time.time()
        outs = self.llm.chat(msgs, self.params, use_tqdm=False)
        self.seconds += time.time() - t0
        actions, answers = [], []
        for o in outs:
            text = o.outputs[0].text
            self.gen_tokens += len(o.outputs[0].token_ids)
            m = _ANSWER.findall(text) or _ANY.findall(text)
            if m:
                actions.append(PHASES.index(m[-1].upper()))
                answers.append(m[-1].upper())
            else:
                actions.append(0)
                answers.append(None)
                self.n_invalid += 1
        self.n_decisions += len(outs)
        self._log = {"answers": answers}
        return actions

    def step_log(self):
        return self._log

    def summary(self):
        n = max(self.n_decisions, 1)
        return {"invalid_rate": self.n_invalid / n, "latency_per_decision_ms": 1000 * self.seconds / n,
                "gen_tokens_per_decision": self.gen_tokens / n, "seconds": self.seconds}
