# GSM8K Synthetic Prefix Phase 2c Prompt-Format Takeaways

## Status

Exploratory diagnostic result; same model/backend/config family; repeated stochastic prompt samples; not benchmark-level evidence.

## Setup

- 9 diagnostic GSM8K items
- 3 conditions:
  - `baseline_no_prefix`
  - `single_round_correct_consensus`
  - `single_round_wrong_consensus`
- 3 prompt formats:
  - `answer_tag`
  - `json`
  - `plain_final`
- 20 replicates
- 3 agents per row
- 4860 outputs total

## Main Result

Consensus effects were observed across all three prompt formats. Wrong-consensus prefixes increased target-wrong outputs by roughly 45-51 percentage points over baseline, while correct-consensus prefixes increased correct outputs by roughly 29-38 percentage points over baseline.

## Format-Level Results

| format | condition | correct_rate | target_wrong_rate | raw_failure | effective_failure | recovered_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| answer_tag | baseline_no_prefix | 0.622 | 0.363 | 0.000 | 0.000 | - |
| answer_tag | single_round_correct_consensus | 0.915 | 0.085 | 0.000 | 0.000 | - |
| answer_tag | single_round_wrong_consensus | 0.126 | 0.874 | 0.000 | 0.000 | - |
| json | baseline_no_prefix | 0.578 | 0.393 | 1.000 | 0.000 | 1.000 |
| json | single_round_correct_consensus | 0.891 | 0.109 | 1.000 | 0.000 | 1.000 |
| json | single_round_wrong_consensus | 0.156 | 0.844 | 1.000 | 0.000 | 1.000 |
| plain_final | baseline_no_prefix | 0.550 | 0.426 | 0.000 | 0.000 | - |
| plain_final | single_round_correct_consensus | 0.931 | 0.069 | 0.000 | 0.000 | - |
| plain_final | single_round_wrong_consensus | 0.115 | 0.885 | 0.015 | 0.015 | - |

## Consensus Effect by Format

| format | correct_consensus_delta_correct | wrong_consensus_delta_target_wrong |
| --- | ---: | ---: |
| answer_tag | +0.293 | +0.511 |
| json | +0.313 | +0.452 |
| plain_final | +0.381 | +0.459 |

## Extraction and Recovery Notes

- `answer_tag` had no extraction failures.
- `json` had raw failure 1.0 but effective failure 0.0 after format-aware recovery.
- `plain_final` had only small effective failure in the wrong-consensus condition: 0.015.
- Observed `APITimeoutError` during 4-shard execution means small failure rates should not be overinterpreted as prompt-only failure.

## Interpretation

The result is consistent with consensus anchoring being robust to output-format changes in this diagnostic setup.

## Limitations

- small item count
- selected diagnostic items
- single model/backend/config family
- same stochastic samples are not independent benchmark items
- possible timeout effects under 4-shard execution
- target_wrong derivation issue such as 106.12
- format-aware recovery makes JSON metrics not directly comparable to legacy raw extraction failure

## Next Step

The next diagnostic should separate answer anchoring from rationale contamination: whether the model follows the prior numeric answer itself, an accompanying incorrect rationale, or their combination.
