from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from typing import Literal

ReasoningMode = Literal["none", "think", "no_think"]
Condition = Literal["independent", "debate_1r", "debate_3r_full_context"]

DEFAULT_BASE_URL = "http://localhost:11434/v1"
DEFAULT_API_KEY = "ollama"
DEFAULT_MODEL_IDENTIFIER = "qwen3:8b"
DEFAULT_MODEL_REF = "ollama:qwen3:8b"
DEFAULT_MODEL_FAMILY = "qwen3"
DEFAULT_PARAMETER_SIZE = "8B"
DEFAULT_QUANTIZATION = "ollama-default"
DEFAULT_REASONING_MODE = "no_think"
DEFAULT_CONTEXT_LENGTH = 4096
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 0.8
DEFAULT_MAX_TOKENS = 128
DEFAULT_AGENT_COUNT = 3
DEFAULT_ROUNDS = 2


@dataclass(frozen=True)
class ExperimentConfig:
    runtime: str
    base_url: str
    api_key: str
    model_identifier: str
    model_ref: str
    model_family: str
    parameter_size: str
    quantization: str
    reasoning_mode: ReasoningMode
    context_length_requested: int
    temperature: float
    top_p: float
    max_tokens: int
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
    base_url = os.getenv("SMDEBATE_BASE_URL") or os.getenv("LMSTUDIO_BASE_URL") or DEFAULT_BASE_URL
    api_key = os.getenv("SMDEBATE_API_KEY") or os.getenv("LMSTUDIO_API_KEY") or DEFAULT_API_KEY
    model_identifier = (
        os.getenv("SMDEBATE_MODEL")
        or os.getenv("LMSTUDIO_MODEL")
        or DEFAULT_MODEL_IDENTIFIER
    )
    return ExperimentConfig(
        runtime="openai_compatible_local",
        base_url=base_url,
        api_key=api_key,
        model_identifier=model_identifier,
        model_ref=os.getenv("SMDEBATE_MODEL_REF", DEFAULT_MODEL_REF),
        model_family=os.getenv("SMDEBATE_MODEL_FAMILY", DEFAULT_MODEL_FAMILY),
        parameter_size=os.getenv("SMDEBATE_PARAMETER_SIZE", DEFAULT_PARAMETER_SIZE),
        quantization=os.getenv("SMDEBATE_QUANTIZATION", DEFAULT_QUANTIZATION),
        reasoning_mode=_reasoning_mode(os.getenv("SMDEBATE_REASONING_MODE", DEFAULT_REASONING_MODE)),
        context_length_requested=int(os.getenv("SMDEBATE_CONTEXT_LENGTH", str(DEFAULT_CONTEXT_LENGTH))),
        temperature=float(os.getenv("SMDEBATE_TEMPERATURE", str(DEFAULT_TEMPERATURE))),
        top_p=float(os.getenv("SMDEBATE_TOP_P", str(DEFAULT_TOP_P))),
        max_tokens=load_max_tokens(),
        agent_count=int(os.getenv("SMDEBATE_AGENT_COUNT", str(DEFAULT_AGENT_COUNT))),
        rounds=int(os.getenv("SMDEBATE_ROUNDS", str(DEFAULT_ROUNDS))),
        condition=condition,
    )


def load_request_timeout_seconds() -> float | None:
    raw = os.getenv("SMDEBATE_REQUEST_TIMEOUT_SECONDS")
    if raw is None or raw.strip() == "":
        return None
    return float(raw)


def load_max_tokens() -> int:
    return int(os.getenv("SMDEBATE_MAX_TOKENS", str(DEFAULT_MAX_TOKENS)))
