"""Open-source Jev-style "System One" decider.

Jev (TypeSafe) takes program state plus typed questions and returns typed answers with probabilities,
without generating text. We do not call the TypeSafe API. Instead we follow the open-source recipe of
`open-alternative-jev` (github.com/ikermoel/open-alternative-jev, Apache-2.0, "separate" mode):

  1. render state + one typed question (lettered options) as a normal chat turn,
  2. run ONE forward pass of an open-weights chat LLM,
  3. read the next-token logits at the assistant position, restricted to the option letters,
  4. softmax over those letters (optionally / temperature) -> a distribution over the options.

The answer can never be outside the schema, and every decision carries a probability, which the
controllers use for confidence gating. `permutations=k` scores k option orders (identity, reversed,
then cyclic shifts) and averages the distributions to cancel the model's position bias; with k >= n we
use the n cyclic shifts, so every option appears at every letter exactly once.

Besides `Choice` (lettered options) there is `Score`, Jev's rubric/score type: the answer is a single
digit low..high read directly from the digit-token logits, so there is no option list to be biased by.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Sequence

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DEFAULT_INSTRUCTION = "Choose the correct option. Reply with only its letter."


@dataclass(frozen=True)
class Choice:
    """A typed question whose answer is exactly one of `options`."""
    question: str
    options: Sequence[str]
    name: str | None = None

    def __post_init__(self):
        options = tuple(str(o) for o in self.options)
        if not 2 <= len(options) <= len(LETTERS):
            raise ValueError(f"a Choice needs 2..{len(LETTERS)} options, got {len(options)}")
        object.__setattr__(self, "options", options)

    @property
    def n(self) -> int:
        return len(self.options)


@dataclass(frozen=True)
class Score:
    """A typed rubric question answered with one integer in [low, high] (single digits, read from digit logits)."""
    question: str
    low: int = 0
    high: int = 9
    name: str | None = None

    def __post_init__(self):
        if not 0 <= self.low < self.high <= 9:
            raise ValueError("Score supports single-digit ranges within 0..9")

    @property
    def options(self) -> tuple[str, ...]:
        return tuple(str(v) for v in range(self.low, self.high + 1))

    @property
    def n(self) -> int:
        return self.high - self.low + 1


@dataclass
class Decision:
    question: Choice
    probabilities: list[float]
    raw_scores: list[float] = field(default_factory=list, repr=False)

    @property
    def index(self) -> int:
        return max(range(len(self.probabilities)), key=self.probabilities.__getitem__)

    @property
    def choice(self) -> str:
        return self.question.options[self.index]

    @property
    def confidence(self) -> float:
        return self.probabilities[self.index]

    @property
    def expected(self) -> float:
        """Expected value of a Score answer (probability-weighted mean over low..high)."""
        return sum(p * (self.question.low + k) for k, p in enumerate(self.probabilities))


def softmax(xs: Sequence[float], temperature: float = 1.0) -> list[float]:
    m = max(xs)
    es = [math.exp((x - m) / temperature) for x in xs]
    s = sum(es)
    return [e / s for e in es]


SCORE_INSTRUCTION = "Answer with a single digit only."


def render_turn(state: str, question: Choice | Score, instruction: str = DEFAULT_INSTRUCTION) -> str:
    if isinstance(question, Score):
        return "\n".join([SCORE_INSTRUCTION, "", "Context:", state, "", f"Question: {question.question}",
                          f"Answer with one integer from {question.low} to {question.high}."])
    lines = [instruction, "", "Context:", state, "", f"Question: {question.question}"]
    lines += [f"{LETTERS[i]}. {opt}" for i, opt in enumerate(question.options)]
    return "\n".join(lines)


def option_orders(n: int, permutations: int) -> list[list[int]]:
    """Identity, then reversed, then cyclic shifts, until `permutations` distinct orders (as in so1).

    With permutations >= n we return the n cyclic shifts instead: a Latin square, so every option appears
    exactly once at every letter (so1's identity+reversed+shifts mix does not guarantee that for n >= 4).
    """
    if permutations >= n:
        return [[(i + shift) % n for i in range(n)] for shift in range(n)]
    orders = [list(range(n))]
    if permutations >= 2 and n >= 2:
        orders.append(list(reversed(range(n))))
    shift = 1
    while len(orders) < permutations and shift < n:
        order = [(i + shift) % n for i in range(n)]
        if order not in orders:
            orders.append(order)
        shift += 1
    return orders


def build_prompt(tokenizer, state: str, question: Choice | Score, system_prompt: str | None = None,
                 instruction: str = DEFAULT_INSTRUCTION) -> str:
    """Chat-formatted prompt ending at the assistant position whose next token is the answer.
    Shared by inference (TypedDecider) and fine-tuning (scripts/train_lora.py) so both read the same position."""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": render_turn(state, question, instruction)})
    kwargs = {}
    if "enable_thinking" in (tokenizer.chat_template or ""):
        kwargs["enable_thinking"] = False
    return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, **kwargs)


def single_token_ids(tokenizer, labels: str) -> list[int]:
    ids = []
    for letter in labels:
        toks = tokenizer.encode(letter, add_special_tokens=False)
        if len(toks) != 1:
            raise ValueError(f"label {letter!r} is not a single token: {toks}")
        ids.append(toks[0])
    return ids


def load_model(model_path: str, adapters: Sequence[str] = (), device: str = "cuda", dtype: str = "bfloat16"):
    """Base model with LoRA adapters merged in order (adapter k was trained on top of base + adapters < k)."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    tokenizer.padding_side = "left"
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=getattr(torch, dtype), device_map=device)
    for path in adapters:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, path).merge_and_unload()
    return tokenizer, model


class TypedDecider:
    """Typed decisions from a Hugging Face causal LM via a single forward pass per (state, question)."""

    def __init__(self, model_path: str, device: str = "cuda", dtype: str = "bfloat16", batch_size: int = 16,
                 temperature: float = 1.0, permutations: int = 1, system_prompt: str | None = None,
                 instruction: str = DEFAULT_INSTRUCTION, adapters: Sequence[str] = ()):
        import torch

        self.torch = torch
        self.tokenizer, model = load_model(model_path, adapters, device, dtype)
        self.model = model.eval()
        self.device = self.model.device
        self.batch_size = batch_size
        self.temperature = temperature
        self.permutations = permutations
        self.system_prompt = system_prompt
        self.instruction = instruction
        self.label_ids = self._label_ids(LETTERS)
        self.digit_ids = self._label_ids("0123456789")
        self.stats = {"calls": 0, "sequences": 0, "prompt_tokens": 0, "seconds": 0.0}

    def _label_ids(self, labels: str) -> list[int]:
        return single_token_ids(self.tokenizer, labels)

    def _prompt(self, state: str, choice: Choice | Score) -> str:
        return build_prompt(self.tokenizer, state, choice, self.system_prompt, self.instruction)

    def _score(self, prompts: list[str], label_ids: list[int]) -> list[list[float]]:
        """Next-token logits restricted to `label_ids`, one row per prompt."""
        torch = self.torch
        out = []
        for i in range(0, len(prompts), self.batch_size):
            chunk = prompts[i:i + self.batch_size]
            enc = self.tokenizer(chunk, return_tensors="pt", padding=True, add_special_tokens=False).to(self.device)
            with torch.inference_mode():
                # only the last position is read out; skip the full-sequence vocab projection
                logits = self.model(**enc, logits_to_keep=1).logits[:, -1, :]
            scores = logits[:, label_ids].float().cpu().tolist()
            out.extend(scores)
            self.stats["sequences"] += len(chunk)
            self.stats["prompt_tokens"] += int(enc["attention_mask"].sum())
        return out

    def decide_items(self, items: Sequence[tuple[str, Choice | Score]]) -> list[Decision]:
        """Answer a batch of (state, question) pairs; all forward passes of the batch are scored together."""
        t0 = time.time()
        jobs = []  # (item index, order or None, prompt, label ids)
        for i, (state, q) in enumerate(items):
            if isinstance(q, Score):
                jobs.append((i, None, self._prompt(state, q), self.digit_ids[q.low:q.high + 1]))
                continue
            for order in option_orders(q.n, self.permutations):
                permuted = Choice(q.question, [q.options[j] for j in order], q.name)
                jobs.append((i, order, self._prompt(state, permuted), self.label_ids[:q.n]))
        rows: list[list[float]] = [None] * len(jobs)  # type: ignore[list-item]
        by_labels: dict[tuple, list[int]] = {}
        for k, (_, _, _, ids) in enumerate(jobs):
            by_labels.setdefault(tuple(ids), []).append(k)
        for ids, ks in by_labels.items():
            for k, row in zip(ks, self._score([jobs[k][2] for k in ks], list(ids))):
                rows[k] = row

        acc = [[0.0] * q.n for _, q in items]
        count = [0] * len(items)
        first_raw: list[list[float]] = [[] for _ in items]
        for (i, order, _, _), raw in zip(jobs, rows):
            probs = softmax(raw, self.temperature)
            for pos, orig in enumerate(order if order is not None else range(len(probs))):
                acc[i][orig] += probs[pos]
            count[i] += 1
            if not first_raw[i]:
                first_raw[i] = raw
        self.stats["calls"] += 1
        self.stats["seconds"] += time.time() - t0
        return [Decision(q, [p / count[i] for p in acc[i]], first_raw[i]) for i, (_, q) in enumerate(items)]

    def decide_many(self, states: Sequence[str], question: Choice | Score) -> list[Decision]:
        """One typed decision per state for the same question (e.g. one per intersection)."""
        return self.decide_items([(s, question) for s in states])

    def decide(self, state: str, question: Choice | Score) -> Decision:
        return self.decide_many([state], question)[0]
