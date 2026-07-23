# GSM8K partial9 Live Mitigation Repeated-Run Report

## Scope

- Data: `data/benchmarks/gsm8k_test_300_partial_correct.jsonl`
- Repeats: 20 per condition
- Raw run files: 100
- Unit of summary: one complete 9-item repeat
- CIs: 95% normal approximation across repeats; exploratory, not a preregistered confirmatory analysis.

## Data integrity

- Validation status: **PASS**
- Conditions present: `['answer_hidden_debate', 'commit_then_numeric_masked_debate', 'full_context_debate', 'independent', 'numeric_masked_debate']`
- Repeat IDs present: `[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]`
- Expected item count in every run: `True`
- Duplicate item IDs: `none`

## Results

| condition | repeats | final accuracy | initial correct | answer loss | target-wrong collapse | extraction failures |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| independent | 20 | 0.678 (95% CI 0.621–0.735) | 0.883 (95% CI 0.828–0.939) | 0.230 (95% CI 0.181–0.279) | 0.000 (95% CI 0.000–0.000) | 0.000 (95% CI 0.000–0.000) |
| full_context_debate | 20 | 0.672 (95% CI 0.624–0.721) | 0.894 (95% CI 0.857–0.931) | 0.249 (95% CI 0.187–0.310) | 0.000 (95% CI 0.000–0.000) | 0.000 (95% CI 0.000–0.000) |
| answer_hidden_debate | 20 | 0.672 (95% CI 0.626–0.718) | 0.828 (95% CI 0.779–0.876) | 0.214 (95% CI 0.159–0.269) | 0.000 (95% CI 0.000–0.000) | 0.000 (95% CI 0.000–0.000) |
| numeric_masked_debate | 20 | 0.650 (95% CI 0.592–0.708) | 0.872 (95% CI 0.833–0.912) | 0.289 (95% CI 0.221–0.357) | 0.000 (95% CI 0.000–0.000) | 0.000 (95% CI 0.000–0.000) |
| commit_then_numeric_masked_debate | 20 | 0.633 (95% CI 0.581–0.686) | 0.867 (95% CI 0.826–0.907) | 0.285 (95% CI 0.218–0.353) | 0.000 (95% CI 0.000–0.000) | 0.000 (95% CI 0.000–0.000) |

## Paired Accuracy Difference vs independent

| condition | mean delta | SD | 95% CI |
| --- | ---: | ---: | ---: |
| full_context_debate | -0.006 | 0.175 | -0.082–0.071 |
| answer_hidden_debate | -0.006 | 0.167 | -0.079–0.068 |
| numeric_masked_debate | -0.028 | 0.183 | -0.108–0.053 |
| commit_then_numeric_masked_debate | -0.044 | 0.167 | -0.118–0.029 |

## Interpretation

The repeated runs provide a complete exploratory dataset for comparing mitigation conditions. Differences are small relative to repeat-to-repeat variation, so this report should be used descriptively. It does not establish a general mitigation effect or causal mechanism.

`answer_loss_rate` is conditional on repeats containing at least one initially correct answer. `correct_to_target_wrong_rate` is zero when the dataset has no explicit target-wrong metadata. Raw model text is not included.
