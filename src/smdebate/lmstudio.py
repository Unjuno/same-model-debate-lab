from __future__ import annotations

from langchain_openai import ChatOpenAI

from smdebate.config import ExperimentConfig


def create_local_chat_model(config: ExperimentConfig) -> ChatOpenAI:
    return ChatOpenAI(
        model=config.model_identifier,
        base_url=config.base_url,
        api_key=config.api_key,
        temperature=config.temperature,
        top_p=config.top_p,
    )


def invoke_text(model: ChatOpenAI, prompt: str) -> str:
    response = model.invoke(prompt)
    return str(response.content)
