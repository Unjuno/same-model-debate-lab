import sys
from types import ModuleType, SimpleNamespace

import smdebate.config as config
import smdebate.lmstudio as lmstudio


def test_create_local_chat_model_passes_max_tokens(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class _FakeChatOpenAI:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    fake_module = ModuleType("langchain_openai")
    fake_module.ChatOpenAI = _FakeChatOpenAI
    monkeypatch.setitem(sys.modules, "langchain_openai", fake_module)
    monkeypatch.setenv("SMDEBATE_MAX_TOKENS", "64")

    loaded = config.load_config()
    model = lmstudio.create_local_chat_model(loaded)

    assert isinstance(model, _FakeChatOpenAI)
    assert captured["max_tokens"] == 64
    assert captured["model"] == loaded.model_identifier
    assert captured["base_url"] == loaded.base_url


def test_create_local_chat_model_falls_back_to_max_completion_tokens(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class _FakeChatOpenAI:
        def __init__(self, **kwargs):
            if "max_tokens" in kwargs:
                raise TypeError("unexpected keyword argument 'max_tokens'")
            captured.update(kwargs)

    fake_module = ModuleType("langchain_openai")
    fake_module.ChatOpenAI = _FakeChatOpenAI
    monkeypatch.setitem(sys.modules, "langchain_openai", fake_module)

    loaded = SimpleNamespace(
        model_identifier="qwen3:8b",
        base_url="http://localhost:11434/v1",
        api_key="ollama",
        temperature=0.7,
        top_p=0.8,
        max_tokens=128,
    )

    model = lmstudio.create_local_chat_model(loaded)

    assert isinstance(model, _FakeChatOpenAI)
    assert captured["max_completion_tokens"] == 128
    assert "max_tokens" not in captured
