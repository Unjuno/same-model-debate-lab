# Same Model Debate Lab

Same Model Debate Lab is a local-first experimental framework for testing whether same-model multi-agent debate can reduce independence and cause answer loss, same-error agreement, or diversity collapse.

This project does **not** try to prove that all multi-agent LLM systems are bad. The narrower question is:

> When multiple agents are instances of the same local model, does sharing a debate transcript make them more likely to converge on the same incorrect answer compared with independent sampling?

## Scope

- Local LLM execution through LM Studio's OpenAI-compatible API
- Experiment orchestration through LangChain-compatible local chat calls
- Local UI with Streamlit
- Machine-checkable synthetic tasks with known answers
- CI for code quality and unit/contract tests only
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

## Fixed first local model

Use this model for the first baseline:

```text
Qwen/Qwen3-4B-GGUF:Q4_K_M
```

Fixed experiment metadata:

- Source/ref: `Qwen/Qwen3-4B-GGUF:Q4_K_M`
- Runtime: LM Studio
- Family: `qwen3`
- Parameter size: `4B`
- Quantization: `Q4_K_M`
- Reasoning mode: `/no_think`
- Initial context length: `4096`
- Temperature: `0.7`
- Top-p: `0.8`

Important distinction:

- `SMDEBATE_MODEL_REF` records the fixed experiment target: `Qwen/Qwen3-4B-GGUF:Q4_K_M`.
- `LMSTUDIO_MODEL` must be the actual model `id` returned by your running LM Studio server.

Do not guess `LMSTUDIO_MODEL`. Query it from LM Studio after loading the model.

## Setup

### CI / contract-test setup

Use this when you only want to run tests and verify the repository wiring. This does not install Streamlit or LangChain.

#### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

#### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### Local LM Studio setup

Use this when you want to run real local model experiments or the Streamlit UI.

```bash
python -m pip install -e ".[dev,local]"
```

Windows PowerShell:

```powershell
python -m pip install -e ".[dev,local]"
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
2. Download/load `Qwen/Qwen3-4B-GGUF` with `Q4_K_M` quantization.
3. Start the local server.
4. Confirm the base URL, usually `http://localhost:1234/v1`.
5. Query the actual model id from the running server.

PowerShell:

```powershell
Invoke-RestMethod http://localhost:1234/v1/models | ConvertTo-Json -Depth 10
```

macOS / Linux:

```bash
curl http://localhost:1234/v1/models
```

Use the returned `id` as `LMSTUDIO_MODEL`. If LM Studio returns `qwen/qwen3-4b-gguf`, use that. If it returns a longer local id, use the longer id exactly.

6. Install local dependencies with `python -m pip install -e ".[dev,local]"`.
7. Set environment variables.

Example PowerShell values for the fixed baseline:

```powershell
$env:LMSTUDIO_BASE_URL="http://localhost:1234/v1"
$env:LMSTUDIO_API_KEY="lm-studio"
$env:LMSTUDIO_MODEL="qwen/qwen3-4b-gguf"
$env:SMDEBATE_MODEL_REF="Qwen/Qwen3-4B-GGUF:Q4_K_M"
$env:SMDEBATE_MODEL_FAMILY="qwen3"
$env:SMDEBATE_PARAMETER_SIZE="4B"
$env:SMDEBATE_QUANTIZATION="Q4_K_M"
$env:SMDEBATE_REASONING_MODE="no_think"
$env:SMDEBATE_CONTEXT_LENGTH="4096"
$env:SMDEBATE_TEMPERATURE="0.7"
$env:SMDEBATE_TOP_P="0.8"
```

Run one condition:

```bash
smdebate --data data/generated/synthetic_minimal_90.jsonl --condition independent
smdebate --data data/generated/synthetic_minimal_90.jsonl --condition debate_1r
smdebate --data data/generated/synthetic_minimal_90.jsonl --condition debate_3r_full_context
```

Outputs are written under `runs/<utc-run-id>/` unless `--out` is specified.

## Streamlit UI

Install local dependencies first:

```bash
python -m pip install -e ".[dev,local]"
streamlit run app/streamlit_app.py
```

The Streamlit UI is for local inspection. The CLI is preferred for repeatable experiment runs.

## Dependencies and external boundary

See [`docs/dependencies.md`](docs/dependencies.md).

Short version:

- CI installs only the package and `dev` dependencies.
- CI does not install local UI/LLM dependencies.
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
