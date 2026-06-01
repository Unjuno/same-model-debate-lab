# Dependencies and external runtime boundary

This repository intentionally separates CI-tested code from local LLM execution.

## Python package dependencies

Declared in `pyproject.toml`:

| Package | Used for | Required for CI | Notes |
|---|---|---:|---|
| `langchain` | LangChain runtime interfaces | Yes, import/install check | Experiment orchestration dependency. |
| `langchain-openai` | `ChatOpenAI` client for OpenAI-compatible local server | Yes, import/install check | Used to call LM Studio through `base_url`. |
| `pandas` | Streamlit result table | Yes, import/install check | Not central to metrics. |
| `pydantic` | Transitive/runtime compatibility dependency | Yes, install check | Kept explicit because LangChain stack uses it heavily. |
| `streamlit` | Local UI | Yes, install check | CI does not run the UI server. |
| `pytest` | Test runner | Yes | Dev dependency. |
| `ruff` | Lint/import checks | Yes | Dev dependency. |

## External runtime dependencies

These are not provided by the repository and are not used in CI.

| External component | Required for real experiments | Required for CI | Boundary |
|---|---:|---:|---|
| LM Studio desktop app | Yes | No | Must run locally by the user. |
| Local model file, e.g. Qwen3 4B GGUF Q4_K_M | Yes | No | Downloaded/managed by LM Studio, not committed. |
| LM Studio local server | Yes | No | Default base URL: `http://localhost:1234/v1`. |
| GPU/CPU capable of running the local model | Yes | No | Hardware-dependent; repo cannot guarantee speed. |
| Internet access | Only for installing packages/model download | No after install | CI installs Python packages, but does not call LLM APIs. |

## API boundary

The code assumes an OpenAI-compatible chat API.

Default local endpoint:

```text
http://localhost:1234/v1
```

The repository does not require a cloud API key. `LMSTUDIO_API_KEY=lm-studio` is a local placeholder because OpenAI-compatible clients usually require an API key field.

## What CI guarantees

CI guarantees:

- package installation works for Python 3.11 and 3.12;
- imports are valid;
- formatting/lint baseline passes;
- JSONL storage works;
- synthetic dataset generation is deterministic;
- metrics compute expected values;
- protocol prompts include expected shared context;
- contract tests verify that `independent`, `debate_1r`, and `debate_3r_full_context` call the local model boundary in the expected pattern using a fake model call.

CI does not guarantee:

- LM Studio is installed;
- a specific model exists locally;
- model output follows `<answer>...</answer>`;
- local inference speed is acceptable;
- a given quantized model reproduces results across machines.

## Reproducibility notes

Each real run writes:

- `config.json`
- `summary.json`
- `raw.jsonl`

The `config.json` redacts the API key and records model/runtime parameters. Raw transcripts are ignored by default because they may contain noisy model output and should be reviewed before publication.
