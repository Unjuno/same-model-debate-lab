from __future__ import annotations

from dataclasses import asdict, dataclass
import os
from typing import Literal

ReasoningMode = Literal["none", "think", "no_think"]
Condition = Literal["independent", "debate_1r", "debate_3r_full_context"]


@dataclass(frozen=True)
class ExperimentConfig:
    runtime: str
    base_url: str
    api_key: str
    model_identifier: str
    model_family: str
    parameter_size: str
    quantization: str
    reasoning_mode: ReasoningMode
    context_length_requested: int
    temperature: float
    top_p: float
    agent_count: int
    rounds: int
    condition: str

    def to_public_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["api_key"] = "<redacted>"
        return data


def _reasoning_mode(value: str) -> ReasoningMode:
    normalized = value.strip().lower()
    if normalized in {"none", "think", "no_think"}:
        return normalized  # type: ignore[return-value]
    raise ValueError("SMDEBATE_REASONING_MODE must be one of: none, think, no_think")


def load_config(condition: str = "debate_1r") -> ExperimentConfig:
    return ExperimentConfig(
        runtime="lm_studio",
        base_url=os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1"),
        api_key=os.getenv("LMSTUDIO_API_KEY", "lm-studio"),
        model_identifier=os.getenv("LMSTUDIO_MODEL", "local-model"),
        model_family=os.getenv("SMDEBATE_MODEL_FAMILY", "qwen3"),
        parameter_size=os.getenv("SMDEBATE_PARAMETER_SIZE", "4B"),
        quantization=os.getenv("SMDEBATE_QUANTIZATION", "Q4_K_M"),
        reasoning_mode=_reasoning_mode(os.getenv("SMDEBATE_REASONING_MODE", "no_think")),
        context_length_requested=int(os.getenv("SMDEBATE_CONTEXT_LENGTH", "8192")),
        temperature=float(os.getenv("SMDEBATE_TEMPERATURE", "0.7")),
        top_p=float(os.getenv("SMDEBATE_TOP_P", "0.95")),
        agent_count=int(os.getenv("SMDEBATE_AGENT_COUNT", "3")),
        rounds=int(os.getenv("SMDEBATE_ROUNDS", "2")),
        condition=condition,
    )
