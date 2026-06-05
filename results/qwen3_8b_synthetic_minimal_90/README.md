# qwen3:8b synthetic_minimal_90 result

## Runtime
- Provider: Ollama OpenAI-compatible API
- Model: qwen3:8b
- Dataset: synthetic_minimal_90
- Items: 90
- Agent count: 3
- Conditions:
  - independent
  - debate_1r
  - debate_3r_full_context

## Result
All three conditions completed successfully.

| condition | n | accuracy | oracle_at_k | answer_loss_rate | same_error_agreement_rate | diversity_drop | extraction_failure_rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| independent | 90 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| debate_1r | 90 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| debate_3r_full_context | 90 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 |

## Interpretation
This run validates the local experiment harness.
It does not support the answer-loss hypothesis on this dataset. The synthetic_minimal_90 dataset is likely too easy for qwen3:8b, because all three conditions reached perfect accuracy.
Next step: evaluate a harder external benchmark such as GSM8K subset.

## Publication note
Raw transcripts are not committed in this result set.
