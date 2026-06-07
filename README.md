# Same Model Debate Lab

Same Model Debate Lab is a local-first experimental framework for testing whether same-model multi-agent debate can reduce independence and cause answer loss, same-error agreement, or diversity collapse.

This project does **not** try to prove that all multi-agent LLM systems are bad. The narrower question is:

> When multiple agents are instances of the same local model, does sharing a debate transcript make them more likely to converge on the same incorrect answer compared with independent sampling?

## Scope

- Local LLM execution through OpenAI-compatible local APIs
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

## Recommended smoke model: Ollama qwen3:8b

Use Ollama for the first smoke test if `qwen3:8b` is already installed locally. The repository talks to Ollama through its OpenAI-compatible API.

- Base URL: `http://localhost:11434/v1`
- Model id: `qwen3:8b`
- API key placeholder: `ollama`
- Primary environment variables: `SMDEBATE_*`
- Legacy fallback variables: `LMSTUDIO_*`

The `LMSTUDIO_*` variables still work, but they are now legacy fallback values. If `SMDEBATE_BASE_URL`, `SMDEBATE_API_KEY`, or `SMDEBATE_MODEL` are set, they win.

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

## Calibrated parametric logic workflow

This workflow builds machine-checkable logical items with controlled difficulty, then filters them using the independent condition so the final dataset is partially solved rather than trivial.

```bash
python tools/generate_parametric_logic_dataset.py \
  --out data/generated/parametric_logic_600.jsonl \
  --seed 1 \
  --n-per-type 100 \
  --difficulty medium

smdebate \
  --data data/generated/parametric_logic_600.jsonl \
  --condition independent \
  --out runs/qwen3_8b_parametric_logic_600_independent

python tools/filter_by_independent_calibration.py \
  --raw runs/qwen3_8b_parametric_logic_600_independent/raw.jsonl \
  --data data/generated/parametric_logic_600.jsonl \
  --out data/generated/parametric_logic_calibrated.jsonl \
  --report runs/qwen3_8b_parametric_logic_600_independent/calibration_report.json

smdebate \
  --data data/generated/parametric_logic_calibrated.jsonl \
  --condition debate_1r \
  --out runs/qwen3_8b_parametric_logic_calibrated_debate_1r
```

Only proceed to the final debate step if the calibration report shows `selected > 0`.

## Minimal existing-problem screening

This is a small screening flow for existing candidate JSONL files in the standard Item schema.

1. Prepare or provide a candidate JSONL in existing Item schema.
2. Run independent only:

```bash
smdebate \
  --data data/benchmarks/candidates.jsonl \
  --condition independent \
  --out runs/qwen3_8b_candidates_independent
```

3. Filter partial-correct items:

```bash
python tools/filter_by_independent_calibration.py \
  --raw runs/qwen3_8b_candidates_independent/raw.jsonl \
  --data data/benchmarks/candidates.jsonl \
  --out data/benchmarks/calibrated_partial.jsonl \
  --report runs/qwen3_8b_candidates_independent/calibration_report.json
```

4. If `selected >= 10`, run `debate_1r`:

```bash
smdebate \
  --data data/benchmarks/calibrated_partial.jsonl \
  --condition debate_1r \
  --out runs/qwen3_8b_calibrated_debate_1r
```

## Quick AQuA-RAT screening

```bash
python tools/prepare_aqua_hf_subset.py \
  --out data/benchmarks/aqua_candidates_100.jsonl \
  --split test \
  --seed 0 \
  --limit 100

smdebate \
  --data data/benchmarks/aqua_candidates_100.jsonl \
  --condition independent \
  --out runs/qwen3_8b_aqua_candidates_100_independent

python tools/filter_by_independent_calibration.py \
  --raw runs/qwen3_8b_aqua_candidates_100_independent/raw.jsonl \
  --data data/benchmarks/aqua_candidates_100.jsonl \
  --out data/benchmarks/aqua_calibrated_partial.jsonl \
  --report runs/qwen3_8b_aqua_candidates_100_independent/calibration_report.json

cat runs/qwen3_8b_aqua_candidates_100_independent/calibration_report.json
wc -l data/benchmarks/aqua_calibrated_partial.jsonl
```

If `selected >= 10`:

```bash
smdebate \
  --data data/benchmarks/aqua_calibrated_partial.jsonl \
  --condition debate_1r \
  --out runs/qwen3_8b_aqua_calibrated_debate_1r
```

## Current minimal result

- Synthetic smoke passed but was too easy.
- AQuA-RAT screening found 11 partial_correct items from 354 screened candidates.
- debate_1r on those 11 items produced `answer_loss_rate = 0.3` with `extraction_failure_rate = 0.0`.
- This is exploratory, not statistically conclusive.
- See [docs/aqua_minimal_result.md](docs/aqua_minimal_result.md) and [docs/aqua_answer_loss_audit.md](docs/aqua_answer_loss_audit.md).
- For transcript-level trajectory analysis, see [docs/aqua_round_sweep.md](docs/aqua_round_sweep.md) if you have a completed round-sweep report.

## Clone to smoke

macOS / zsh:

```bash
cd ~/repos
git clone https://github.com/Unjuno/same-model-debate-lab.git
cd same-model-debate-lab

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,local]"

ollama list | grep "qwen3:8b"
curl http://localhost:11434/v1/models

export SMDEBATE_BASE_URL="http://localhost:11434/v1"
export SMDEBATE_API_KEY="ollama"
export SMDEBATE_MODEL="qwen3:8b"
export SMDEBATE_MODEL_REF="ollama:qwen3:8b"
export SMDEBATE_MODEL_FAMILY="qwen3"
export SMDEBATE_PARAMETER_SIZE="8B"
export SMDEBATE_QUANTIZATION="ollama-default"
export SMDEBATE_REASONING_MODE="no_think"
export SMDEBATE_CONTEXT_LENGTH="4096"
export SMDEBATE_TEMPERATURE="0.7"
export SMDEBATE_TOP_P="0.8"
export SMDEBATE_AGENT_COUNT="3"
export SMDEBATE_ROUNDS="2"

smdebate --data data/smoke.jsonl --condition independent --out runs/smoke_qwen3_8b_independent
smdebate --data data/smoke.jsonl --condition debate_1r --out runs/smoke_qwen3_8b_debate_1r
smdebate --data data/smoke.jsonl --condition debate_3r_full_context --out runs/smoke_qwen3_8b_debate_3r

cat runs/smoke_qwen3_8b_independent/summary.json
cat runs/smoke_qwen3_8b_debate_1r/summary.json
cat runs/smoke_qwen3_8b_debate_3r/summary.json
```

The same command set works with LM Studio if you export `LMSTUDIO_*` instead of `SMDEBATE_*`, but that is now the legacy fallback path. For LM Studio, query the actual model `id` from `/v1/models` and set it as `LMSTUDIO_MODEL`.

Outputs are written under `runs/<utc-run-id>/` unless `--out` is specified.

## Run with LM Studio

LM Studio remains supported as an alternative OpenAI-compatible local server.

1. Open LM Studio.
2. Download/load a compatible model.
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

Set `LMSTUDIO_MODEL` to the returned `id` if you prefer the legacy fallback path. The `SMDEBATE_*` variables still take priority if present.

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
