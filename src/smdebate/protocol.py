from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

ReasoningMode = Literal["none", "think", "no_think"]

ANSWER_RE = re.compile(r"<answer>(.*?)</answer>", re.DOTALL | re.IGNORECASE)


@dataclass(frozen=True)
class Item:
    id: str
    type: str
    question: str
    answer: str
    difficulty: str = "unknown"
    metadata: dict[str, object] | None = None


@dataclass(frozen=True)
class AgentResponse:
    agent_id: int
    round_index: int
    raw_text: str
    answer: str
    extraction_failed: bool


@dataclass(frozen=True)
class ExperimentResult:
    item: Item
    condition: str
    initial_responses: list[AgentResponse]
    final_responses: list[AgentResponse]
    final_answer: str


ROLE_LABELS = {
    1: "solver",
    2: "skeptic/error-checker",
    3: "alternative-solver",
}


def role_instruction(agent_id: int) -> str:
    role = ROLE_LABELS.get(agent_id, "solver")
    if role == "solver":
        return "Role: solver. Focus on solving directly and clearly."
    if role == "skeptic/error-checker":
        return "Role: skeptic/error-checker. Check assumptions, arithmetic, option consistency, and hidden traps."
    if role == "alternative-solver":
        return "Role: alternative-solver. Try a different route when possible."
    return "Role: solver. Focus on solving directly and clearly."


def extract_answer(text: str) -> tuple[str, bool]:
    match = ANSWER_RE.search(text)
    if match:
        return match.group(1).strip(), False
    return text.strip(), True


def reasoning_prefix(model_family: str, reasoning_mode: ReasoningMode) -> str:
    if model_family.strip().lower() != "qwen3":
        return ""
    if reasoning_mode == "no_think":
        return "/no_think\n\n"
    if reasoning_mode == "think":
        return "/think\n\n"
    return ""


def initial_prompt(
    item: Item,
    agent_id: int,
    *,
    model_family: str = "qwen3",
    reasoning_mode: ReasoningMode = "no_think",
    role_profile: bool = False,
) -> str:
    prefix = reasoning_prefix(model_family, reasoning_mode)
    role_text = f"\n{role_instruction(agent_id)}\n" if role_profile else ""
    return f"""{prefix}You are Agent {agent_id}.
{role_text}

Answer the question independently.
Do not assume other agents exist.
Return the final answer inside <answer>...</answer>.
Keep the answer short and machine-checkable.

Question:
{item.question}
"""


def debate_prompt(
    item: Item,
    agent_id: int,
    own_previous: AgentResponse,
    visible_responses: list[AgentResponse],
    round_index: int,
    *,
    model_family: str = "qwen3",
    reasoning_mode: ReasoningMode = "no_think",
    role_profile: bool = False,
) -> str:
    prefix = reasoning_prefix(model_family, reasoning_mode)
    role_text = f"\n{role_instruction(agent_id)}\n" if role_profile else ""
    others = "\n\n".join(
        f"Agent {response.agent_id}, round {response.round_index}:\n{response.raw_text}"
        for response in visible_responses
    )

    return f"""{prefix}You are Agent {agent_id}.
{role_text}
This is debate round {round_index}.

Question:
{item.question}

Your previous response:
{own_previous.raw_text}

Other agents' responses:
{others}

Task:
Review the shared context carefully.
You may keep your answer or revise it.
Return the final answer inside <answer>...</answer>.
Keep the answer short and machine-checkable.
"""
