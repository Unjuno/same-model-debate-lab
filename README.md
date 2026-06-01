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

### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### Verify installation

```bash
python -m ruff check .
python -m pytest -q
```

CI runs the same lint and test commands on Python 3.11 and 3.12.

## Contract tests

The repository includes no-LLM contract tests. They use fake model responses and verify that:

- `independent` calls the model boundary only for initial isolated answers;
- `debate_1r` shares prior responses in the debate prompt;
- `debate_3r_full_context` performs the expected number of agent calls;
- answer-loss and same-error-agreement metrics are computed from recorded rows.

These tests check experiment wiring. They do **not** prove that a real local model will follow `<answer>...</answer>`.

## Generate a synthetic dataset

```bash
python tools/generate_synthetic_dataset.py --out data/generated/synthetic_minimal_90.jsonl --seed 0 --n-per-type 30
```

The generated file contains 90 machine-checkable items:

- 30 arithmetic items;
- 30 Python output-prediction items;
- 30 rule-logic items.

## Run with LM Studio

1. Open LM Studio.
2. Download and load a local model, preferably Qwen3 4B GGUF Q4_K_M for the first baseline.
3. Start the local server.
4. Confirm the base URL, usually `http://localhost:1234/v1`.
5. Copy the exact model identifier from LM Studio.
6. Set environment variables.

Example:

```bash
export LMSTUDIO_BASE_URL=http://localhost:1234/v1
export LMSTUDIO_API_KEY=lm-studio
export LMSTUDIO_MODEL=Qwen3-4B-Q4_K_M
export SMDEBATE_MODEL_FAMILY=qwen3
export SMDEBATE_PARAMETER_SIZE=4B
export SMDEBATE_QUANTIZATION=Q4_K_M
export SMDEBATE_REASONING_MODE=no_think
export SMDEBATE_CONTEXT_LENGTH=8192
```

Windows PowerShell example:

```powershell
$env:LMSTUDIO_BASE_URL="http://localhost:1234/v1"
$env:LMSTUDIO_API_KEY="lm-studio"
$env:LMSTUDIO_MODEL="Qwen3-4B-Q4_K_M"
$env:SMDEBATE_MODEL_FAMILY="qwen3"
$env:SMDEBATE_PARAMETER_SIZE="4B"
$env:SMDEBATE_QUANTIZATION="Q4_K_M"
$env:SMDEBATE_REASONING_MODE="no_think"
$env:SMDEBATE_CONTEXT_LENGTH="8192"
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

## Dependencies and external boundary

See [`docs/dependencies.md`](docs/dependencies.md).

Short version:

- CI installs Python packages and runs tests.
- CI does not call LM Studio.
- Real experiments require the LM Studio desktop app, a locally loaded model, and the local server.
- Raw model transcripts are ignored by default through `.gitignore`.

## Safety and publication notes

- CI does not call LM Studio or any cloud LLM API.
- Raw transcripts are ignored by default through `.gitignore`.
- Review transcripts before publishing them.
- Prefer publishing aggregate summaries first.

## License

Apache License 2.0
