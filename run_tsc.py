"""Run one traffic-signal-control episode (USTBench TSC, CityFlow) with a chosen controller.

Examples:
    python run_tsc.py --agent maxpressure --dataset hangzhou --traffic_file anon_4_4_hangzhou_real.json
    python run_tsc.py --agent jev --state_format typed --model ~/zzy/hf_models/Qwen2.5-7B-Instruct
    python run_tsc.py --agent jev --gate_tau 0.6 --model ...
    python run_tsc.py --agent jev --state_format typed --permutations 4 --model ...
    python run_tsc.py --agent jev-score --state_format typed --model ...
    python run_tsc.py --agent llm-gen --model ...
"""
from __future__ import annotations

import argparse
import json
import os
import time

from jevtraffic.agents import (FixedTimeAgent, GenerativeLLMAgent, JevAgent, JevScoreAgent, MaxPressureAgent,
                               MaxQueueAgent, RandomAgent, RolloutGreedyAgent)
from jevtraffic.env import ROOT, TSCEnv
from jevtraffic.prompts import SYSTEM_PROMPT, load_task_info


def agent_label(args) -> str:
    """Agent name as used in run names (matches Agent.name), known before the model is loaded."""
    if args.agent == "jev-score":
        return f"jev-score-{args.state_format}"
    if args.agent == "jev":
        return f"jev-{args.state_format}" + (f"-gate{args.gate_tau:g}" if args.gate_tau > 0 else "")
    return args.agent


def build_agent(args, task_info):
    if args.agent == "fixedtime":
        return FixedTimeAgent()
    if args.agent == "random":
        return RandomAgent(args.seed)
    if args.agent == "maxqueue":
        return MaxQueueAgent()
    if args.agent == "maxpressure":
        return MaxPressureAgent()
    if args.agent == "rollout-greedy":
        return RolloutGreedyAgent(env=None)  # bound to the env once it exists
    if args.agent in ("jev", "jev-score"):
        from jevtraffic.decider import TypedDecider
        decider = TypedDecider(args.model, device=args.device, batch_size=args.batch_size,
                               permutations=args.permutations, system_prompt=SYSTEM_PROMPT,
                               adapters=args.adapters, temperature=args.temperature)
        if args.agent == "jev-score":
            return JevScoreAgent(decider, task_info, state_format=args.state_format)
        return JevAgent(decider, task_info, state_format=args.state_format, gate_tau=args.gate_tau)
    if args.agent == "llm-gen":
        return GenerativeLLMAgent(args.model, task_info, max_tokens=args.max_tokens,
                                  gpu_memory_utilization=args.gpu_memory_utilization)
    raise ValueError(args.agent)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--agent", required=True, choices=["fixedtime", "random", "maxqueue", "maxpressure", "rollout-greedy",
                                                    "jev", "jev-score", "llm-gen"])
    p.add_argument("--dataset", default="hangzhou")
    p.add_argument("--traffic_file", default="anon_4_4_hangzhou_real.json")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--run_counts", type=int, default=3600, help="simulated seconds (3600 = 120 decisions)")
    p.add_argument("--model", default=None, help="HF model path for jev / llm-gen")
    p.add_argument("--state_format", default="raw", choices=["raw", "typed"])
    p.add_argument("--adapters", nargs="*", default=[], help="LoRA adapters merged into --model, in order")
    p.add_argument("--temperature", type=float, default=None,
                   help="softmax temperature; default: <last adapter>/calib.json if present, else 1")
    p.add_argument("--gate_tau", type=float, default=0.0)
    p.add_argument("--permutations", type=int, default=1)
    p.add_argument("--batch_size", type=int, default=16)
    p.add_argument("--device", default="cuda")
    p.add_argument("--max_tokens", type=int, default=1024)
    p.add_argument("--gpu_memory_utilization", type=float, default=0.7,
                   help="fraction of the WHOLE GPU; vLLM counts memory held by other processes against it")
    p.add_argument("--data_root", default=os.path.join(ROOT, "data", "tsc"))
    p.add_argument("--out_dir", default=os.path.join(ROOT, "results", "runs"))
    p.add_argument("--tag", default="")
    p.add_argument("--save_steps", action="store_true", help="store per-step actions / probabilities")
    p.add_argument("--skip_existing", action="store_true", help="exit if this run's result file already exists")
    args = p.parse_args()

    if args.temperature is None:
        calib = os.path.join(args.adapters[-1], "calib.json") if args.adapters else ""
        args.temperature = json.load(open(calib))["temperature"] if os.path.exists(calib) else 1.0
    model_name = os.path.basename(os.path.normpath(args.model)) if args.model else None
    if model_name and args.adapters:
        model_name += "+" + "+".join(os.path.basename(os.path.normpath(a)) for a in args.adapters)
    run_name = "__".join(x for x in [args.dataset, args.traffic_file.removesuffix(".json"), agent_label(args),
                                      model_name, f"s{args.seed}", args.tag] if x)
    out = os.path.join(args.out_dir, f"{run_name}.json")
    if args.skip_existing and os.path.exists(out):
        print("exists, skipping", out)
        return

    task_info = load_task_info(args.data_root)
    agent = build_agent(args, task_info)
    assert agent.name == agent_label(args), (agent.name, agent_label(args))
    stamp = time.strftime("%m%d_%H%M%S") + f"_{os.getpid()}"
    work_dir = os.path.join(ROOT, "records", f"{run_name}__{stamp}")
    env = TSCEnv(args.dataset, args.traffic_file, work_dir, seed=args.seed, data_root=args.data_root,
                 run_counts=args.run_counts)
    if isinstance(agent, RolloutGreedyAgent):
        agent.env = env

    steps = []
    t_start = time.time()
    agent_seconds = 0.0
    while not env.done:
        obs = env.observe()
        t0 = time.time()
        actions = agent.act(obs)
        agent_seconds += time.time() - t0
        env.step(actions)
        if args.save_steps:
            steps.append({"t": obs.time, "actions": actions, **agent.step_log()})
        if env.step_count % 20 == 0:
            m = env.metrics()
            print(f"[{run_name}] step {env.step_count}/{env.end_step} ATT={m['ATT']:.1f} AWT={m['AWT']:.1f} "
                  f"AQL={m['AQL']:.1f} agent={agent_seconds:.0f}s sim={env.sim_seconds:.0f}s", flush=True)

    result = {
        "run": run_name, "agent": agent.name, "dataset": args.dataset, "traffic_file": args.traffic_file,
        "seed": args.seed, "model": model_name, "state_format": args.state_format if args.agent.startswith("jev") else None,
        "gate_tau": args.gate_tau, "permutations": args.permutations, "adapters": args.adapters,
        "temperature": args.temperature, "decisions": env.step_count,
        **env.metrics(),
        "agent_seconds": agent_seconds, "sim_seconds": env.sim_seconds, "wall_seconds": time.time() - t_start,
        "agent_summary": agent.summary(),
    }
    if steps:
        result["steps"] = steps
    os.makedirs(args.out_dir, exist_ok=True)
    with open(out, "w") as f:
        json.dump(result, f, indent=1)
    print(json.dumps({k: v for k, v in result.items() if k != "steps"}, indent=1))
    print("saved", out)


if __name__ == "__main__":
    main()
