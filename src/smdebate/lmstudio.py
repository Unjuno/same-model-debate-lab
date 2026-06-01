from __future__ import annotations

from typing import Any

from smdebate.config import ExperimentConfig


def create_local_chat_model(config: ExperimentConfig) -> Any:
    try:
        from langchain_openai import ChatOpenAI
    except ImportError as exc:
        raise RuntimeError(
            "Local LLM execution requires the optional local dependencies. "
            "Install them with: python -m pip install -e '.[local]'"
        ) from exc

    return ChatOpenAI(
        model=config.model_identifier,
        base_url=config.base_url,
        api_key=config.api_key,
        temperature=config.temperature,
        top_p=config.top_p,
    )


def invoke_text(model: Any, prompt: str) -> str:
    response = model.invoke(prompt)
    return str(response.content)
