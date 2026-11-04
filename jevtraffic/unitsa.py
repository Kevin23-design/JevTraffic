"""UniTSA (Wang et al., IEEE TVT 2024) as the v3 teacher / baseline, on top of SingleTSCBaselines' implementation.

We reuse the benchmark's UniTSA pieces unchanged (movement-token Transformer, `next_or_not` action, cumulative
waiting reward, PPO settings) and add what a *universal* model across junctions needs:
  * `PadPhases`: the movement features end with a phase-binding block of `num_phases` columns (3 or 4 by
    junction), so observations are zero-padded to `PHASE_PAD` phases and one network fits every junction;
  * `train_env`: one worker per (junction, net) that samples a demand pattern on every reset;
  * `UniTSAAgent`: runs a trained policy inside our `SumoTSCEnv(action_type="next_or_not")`, rebuilding the
    benchmark state (and its max-green guard) from the env's raw TSCInfoWrapper output.
"""
from __future__ import annotations

import time

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from . import sumo_env  # noqa: F401  (puts SingleTSCBaselines on sys.path, sets SUMO_HOME)

PHASE_PAD = 4
HISTORY_LEN = 5
MAX_GREEN = 45  # s, the benchmark's train_random_scenarios default
NUM_MOVEMENTS = 12
POLICY_KWARGS = dict(features_dim=128, embedding_dim=128, num_heads=4, num_layers=2, dim_feedforward=256,
                     dropout=0.1)
PPO_PARAMS = dict(learning_rate=1e-4, n_steps=256, batch_size=256, n_epochs=10, gamma=0.99, gae_lambda=0.95,
                  clip_range=0.2, ent_coef=0.005, vf_coef=0.5, max_grad_norm=0.5)


def fit_shape(state: np.ndarray, shape) -> np.ndarray:
    """Zero-pad / truncate a (T, M, F) state to `shape`, as NextOrNotWrapper._build_state does."""
    if state.shape == tuple(shape):
        return state
    out = np.zeros(shape, dtype=np.float32)
    out[tuple(slice(0, min(a, b)) for a, b in zip(state.shape, shape))] = \
        state[tuple(slice(0, min(a, b)) for a, b in zip(state.shape, shape))]
    return out


class PadPhases(gym.ObservationWrapper):
    def __init__(self, env: gym.Env, phase_pad: int = PHASE_PAD):
        super().__init__(env)
        from tsc_algos.rl.unitsa.unitsa_env.state_funcs import MOVEMENT_BASE_DIM

        t, m, _ = env.observation_space.shape
        self.observation_space = spaces.Box(low=-1.0, high=1.0, shape=(t, m, MOVEMENT_BASE_DIM + phase_pad),
                                            dtype=np.float32)

    def observation(self, obs):
        return fit_shape(np.asarray(obs, dtype=np.float32), self.observation_space.shape)


def train_env(junction: str, net: str, patterns: list[str], seed: int, log_file: str | None = None,
              reward_scale: float = 0.1):
    """Factory for one training worker: `junction` on network `net`, a random pattern per episode."""

    def _init():
        from stable_baselines3.common.monitor import Monitor
        from tsc_algos.rl.unitsa.unitsa_env.random_scenario_env import make_random_scenario_env

        sumo_env._quiet_loguru()
        env = make_random_scenario_env(junction=junction, env_names=[f"{net}_{p}" for p in patterns],
                                       env_index=f"{junction}_{net}_{seed}", num_movements=NUM_MOVEMENTS,
                                       history_len=HISTORY_LEN, max_green=MAX_GREEN, reward_scale=reward_scale,
                                       seed=seed)()
        env = PadPhases(env)
        if log_file:
            env = Monitor(env, filename=log_file, info_keywords=("env_name",))
        return env

    return _init


class UniTSAAgent:
    """A trained UniTSA policy driving `SumoTSCEnv(action_type="next_or_not")` (1 keep, 0 switch)."""

    def __init__(self, env, model_path: str, max_green: int = MAX_GREEN, device: str = "cpu"):
        import torch
        from stable_baselines3 import PPO

        assert env.action_type == "next_or_not"
        torch.set_num_threads(1)  # one decision of a 0.3M-parameter net; threads only add overhead
        self.env, self.max_green = env, max_green
        self.model = PPO.load(model_path, device=device)
        self.shape = self.model.observation_space.shape
        self._phase = None
        self._green = 0
        self._last_t = 0
        self.forced = 0
        self.calls, self.seconds = 0, 0.0

    def _update_green(self, raw, info):  # NextOrNotWrapper._update_green_time
        frames = raw["tls_dynamic_features_seq"]
        phase = frames[-1][0].get("this_phase_index") if frames and frames[-1] else None
        t = int(info.get("step_time", self._last_t))
        if self._phase is None or phase != self._phase:
            self._green = 0
        else:
            self._green += max(t - self._last_t, 0)
        self._phase, self._last_t = phase, t

    def act(self, obs) -> int:
        from tsc_algos.rl.unitsa.unitsa_env.state_funcs import movement_sequence_state

        t0 = time.perf_counter()
        raw = self.env.raw
        if self.env.steps == 0 and self._phase is None:  # reset: as NextOrNotWrapper.reset
            frames = raw["tls_dynamic_features_seq"]
            self._phase = frames[-1][0].get("this_phase_index") if frames and frames[-1] else None
            self._green, self._last_t = 0, int(self.env.info.get("step_time", 0))
        else:
            self._update_green(raw, self.env.info)
        state = movement_sequence_state(raw["tls_dynamic_features_seq"], self.env.cfg["num_phases"],
                                        history_len=self.shape[0], current_green_time=self._green,
                                        max_green=self.max_green).astype(np.float32)
        import torch

        obs_t, _ = self.model.policy.obs_to_tensor(fit_shape(state, self.shape))
        with torch.no_grad():
            probs = self.model.policy.get_distribution(obs_t).distribution.probs[0].tolist()
        self.last_probs = probs  # by env action: [switch, keep]; deterministic predict() is the argmax
        action = int(np.argmax(probs))
        if self.max_green > 0 and action == 1 and self._green >= self.max_green:
            action, self.forced = 0, self.forced + 1
        self.calls += 1
        self.seconds += time.perf_counter() - t0
        return action

    def summary(self) -> dict:
        pol = self.model.policy
        return {"max_green_forced": self.forced, "calls": self.calls,
                "ms_per_call": round(1000 * self.seconds / max(self.calls, 1), 3),
                "params": sum(p.numel() for p in self.model.policy.parameters()),
                "actor_params": sum(p.numel() for m in (pol.pi_features_extractor, pol.mlp_extractor.policy_net,
                                                         pol.action_net) for p in m.parameters())}
        # (the critic has its own Transformer, share_features_extractor=False; only the actor runs at deployment)
