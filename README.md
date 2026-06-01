# Same Model Debate Lab

Same Model Debate Lab is a local-first experimental framework for testing whether same-model multi-agent debate can reduce independence and cause answer loss, same-error agreement, or diversity collapse.

This project does **not** try to prove that all multi-agent LLM systems are bad. The narrower question is:

> When multiple agents are instances of the same local model, does sharing a debate transcript make them more likely to converge on the same incorrect answer compared with independent sampling?

## Scope

- Local LLM execution through LM Studio's OpenAI-compatible API
- Experiment orchestration through LangChain
- Local UI with Streamlit
- Machine-checkable synthetic tasks with known answers
- CI for code quality and unit tests only
- No cloud LLM calls in CI
- No API keys or secrets required for CI

## Initial experiment

The first experiment compares:

1. `independent`: same-model agents answer independently; no shared transcript.
2. `debate_1r`: agents share initial answers and revise once.
3. `debate_3r_full_context`: agents share the evolving transcript for three rounds.

Main metrics:

- `accuracy`
- `oracle_at_k`
- `answer_loss_rate`
- `same_error_agreement_rate`
- `diversity_drop`
- `extraction_failure_rate`

## Recommended first local model

Use a 3B-4B class model first. The recommended baseline is:

- Qwen3 4B GGUF
- Quantization: Q4_K_M
- Runtime: LM Studio
- Reasoning mode: `/no_think`

Do not start the main experiment with a 1B or smaller model. If the model is too weak, failures may mostly reflect base model weakness rather than shared-context debate effects.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Generate a synthetic dataset

```bash
python tools/generate_synthetic_dataset.py --out data/generated/synthetic_minimal_90.jsonl --seed 0 --n-per-type 30
```

## Run local tests

```bash
python -m ruff check .
python -m pytest -q
```

## Run with LM Studio

1. Open LM Studio.
2. Load a local model.
3. Start the local server.
4. Confirm the base URL, usually `http://localhost:1234/v1`.
5. Set the model identifier in your shell.

Example:

```bash
export LMSTUDIO_BASE_URL=http://localhost:1234/v1
export LMSTUDIO_API_KEY=lm-studio
export LMSTUDIO_MODEL=Qwen3-4B-Q4_K_M
export SMDEBATE_MODEL_FAMILY=qwen3
export SMDEBATE_QUANTIZATION=Q4_K_M
export SMDEBATE_REASONING_MODE=no_think
```

Run one condition:

```bash
smdebate --data data/generated/synthetic_minimal_90.jsonl --condition independent
smdebate --data data/generated/synthetic_minimal_90.jsonl --condition debate_1r
smdebate --data data/generated/synthetic_minimal_90.jsonl --condition debate_3r_full_context
```

Outputs are written under `runs/<utc-run-id>/` unless `--out` is specified.

## Streamlit UI

```bash
streamlit run app/streamlit_app.py
```

The Streamlit UI is for local inspection. The CLI is preferred for repeatable experiment runs.

## Safety and publication notes

- CI does not call LM Studio or any cloud LLM API.
- Raw transcripts are ignored by default through `.gitignore`.
- Review transcripts before publishing them.
- Prefer publishing aggregate summaries first.

## License

Apache License 2.0
