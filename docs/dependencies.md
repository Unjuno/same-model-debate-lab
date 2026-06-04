# Dependencies and external runtime boundary

This repository intentionally separates CI-tested experiment wiring from local LLM execution.
The code talks to OpenAI-compatible local APIs, so both Ollama and LM Studio are supported.

## Dependency groups

Declared in `pyproject.toml`:

| Group | Install command | Used for | Required for CI |
|---|---|---|---:|
| base package | `python -m pip install -e .` | Core package and CLI entry point | Yes, via `.[dev]` |
| `dev` | `python -m pip install -e ".[dev]"` | ruff, pytest, contract tests | Yes |
| `local` | `python -m pip install -e ".[local]"` | OpenAI-compatible local model execution and Streamlit UI | No |
| `dev,local` | `python -m pip install -e ".[dev,local]"` | Full local development and real experiments | No |

## Python package dependencies

| Package | Group | Used for | Required for CI | Notes |
|---|---|---|---:|---|
| `pytest` | `dev` | Test runner | Yes | Runs unit and contract tests. |
| `ruff` | `dev` | Lint/import checks | Yes | Keeps repository syntax and imports stable. |
| `langchain-openai` | `local` | `ChatOpenAI` client for OpenAI-compatible local server | No | Used only when running real local model experiments. |
| `pandas` | `local` | Streamlit result table | No | UI-only dependency. |
| `streamlit` | `local` | Local UI | No | CI does not run the UI server. |

The core CI path intentionally avoids importing `langchain_openai`, `pandas`, and `streamlit` at test import time. Real model execution raises a clear error if local dependencies are missing.

## External runtime dependencies

These are not provided by the repository and are not used in CI.

| External component | Required for real experiments | Required for CI | Boundary |
|---|---:|---:|---|
| Ollama desktop/app or LM Studio desktop app | Yes | No | Must run locally by the user. |
| Local model file, e.g. Qwen3 8B or Qwen3 4B GGUF Q4_K_M | Yes | No | Downloaded/managed by Ollama or LM Studio, not committed. |
| OpenAI-compatible local server | Yes | No | Default smoke base URL: `http://localhost:11434/v1`; LM Studio fallback: `http://localhost:1234/v1`. |
| GPU/CPU/RAM capable of running the local model | Yes | No | Hardware-dependent; repo cannot guarantee speed. |
| Internet access | Only for installing packages/model download | No after install | CI installs Python packages, but does not call LLM APIs. |

## API boundary

The real experiment path assumes an OpenAI-compatible chat API.

Default local endpoint:

```text
http://localhost:1234/v1
```

The repository does not require a cloud API key. `SMDEBATE_API_KEY=ollama` is the primary local placeholder. `LMSTUDIO_API_KEY` remains a backward-compatible fallback placeholder for existing setups.

## What CI guarantees

CI guarantees:

- package installation works for Python 3.11 and 3.12 using `.[dev]`;
- core imports are valid without local UI/LLM dependencies;
- ruff baseline passes;
- JSONL storage works;
- synthetic dataset generation is deterministic and runnable;
- metrics compute expected values;
- protocol prompts include expected shared context;
- contract tests verify that `independent`, `debate_1r`, and `debate_3r_full_context` call the local model boundary in the expected pattern using fake model calls;
- `debate_3r_full_context` passes earlier transcript entries into later prompts.
- `SMDEBATE_*` variables are the primary runtime inputs, with `LMSTUDIO_*` preserved as fallback compatibility.

CI does not guarantee:

- Ollama or LM Studio is installed;
- a specific model exists locally;
- model output follows `<answer>...</answer>`;
- local inference speed is acceptable;
- a given quantized model reproduces results across machines;
- Streamlit can display in your local browser.

## Reproducibility notes

Each real run writes:

- `config.json`
- `summary.json`
- `raw.jsonl`

The `config.json` redacts the API key and records model/runtime parameters. Raw transcripts are ignored by default because they may contain noisy model output and should be reviewed before publication.
