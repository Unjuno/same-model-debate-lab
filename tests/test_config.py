import smdebate.config as config


def test_smdebate_env_vars_override_legacy_fallback(monkeypatch) -> None:
    monkeypatch.setenv("SMDEBATE_BASE_URL", "http://example.test/v1")
    monkeypatch.setenv("SMDEBATE_API_KEY", "primary")
    monkeypatch.setenv("SMDEBATE_MODEL", "primary-model")
    monkeypatch.setenv("LMSTUDIO_BASE_URL", "http://legacy.test/v1")
    monkeypatch.setenv("LMSTUDIO_API_KEY", "legacy")
    monkeypatch.setenv("LMSTUDIO_MODEL", "legacy-model")

    loaded = config.load_config()

    assert loaded.base_url == "http://example.test/v1"
    assert loaded.api_key == "primary"
    assert loaded.model_identifier == "primary-model"


def test_legacy_lmstudio_env_vars_are_used_when_primary_missing(monkeypatch) -> None:
    monkeypatch.delenv("SMDEBATE_BASE_URL", raising=False)
    monkeypatch.delenv("SMDEBATE_API_KEY", raising=False)
    monkeypatch.delenv("SMDEBATE_MODEL", raising=False)
    monkeypatch.setenv("LMSTUDIO_BASE_URL", "http://legacy.test/v1")
    monkeypatch.setenv("LMSTUDIO_API_KEY", "legacy")
    monkeypatch.setenv("LMSTUDIO_MODEL", "legacy-model")

    loaded = config.load_config()

    assert loaded.base_url == "http://legacy.test/v1"
    assert loaded.api_key == "legacy"
    assert loaded.model_identifier == "legacy-model"


def test_config_defaults_to_ollama_smoke_values_when_env_missing(monkeypatch) -> None:
    for key in [
        "SMDEBATE_BASE_URL",
        "SMDEBATE_API_KEY",
        "SMDEBATE_MODEL",
        "LMSTUDIO_BASE_URL",
        "LMSTUDIO_API_KEY",
        "LMSTUDIO_MODEL",
        "SMDEBATE_MODEL_REF",
        "SMDEBATE_MODEL_FAMILY",
        "SMDEBATE_PARAMETER_SIZE",
        "SMDEBATE_QUANTIZATION",
        "SMDEBATE_REASONING_MODE",
        "SMDEBATE_CONTEXT_LENGTH",
        "SMDEBATE_TEMPERATURE",
        "SMDEBATE_TOP_P",
        "SMDEBATE_MAX_TOKENS",
        "SMDEBATE_AGENT_COUNT",
        "SMDEBATE_ROUNDS",
    ]:
        monkeypatch.delenv(key, raising=False)

    loaded = config.load_config()

    assert loaded.base_url == "http://localhost:11434/v1"
    assert loaded.api_key == "ollama"
    assert loaded.model_identifier == "qwen3:8b"
    assert loaded.model_ref == "ollama:qwen3:8b"
    assert loaded.model_family == "qwen3"
    assert loaded.parameter_size == "8B"
    assert loaded.quantization == "ollama-default"
    assert loaded.reasoning_mode == "no_think"
    assert loaded.context_length_requested == 4096
    assert loaded.temperature == 0.7
    assert loaded.top_p == 0.8
    assert loaded.max_tokens == 128
    assert loaded.agent_count == 3
    assert loaded.rounds == 2


def test_config_reads_max_tokens_override(monkeypatch) -> None:
    monkeypatch.setenv("SMDEBATE_MAX_TOKENS", "256")

    loaded = config.load_config()

    assert loaded.max_tokens == 256
