# AQuA 11-Item Takeaways

## Purpose
Summarize the current 11-item calibrated AQuA same-model debate findings.

## What Was Tested
- `independent`
- `debate_1r`
- `non-role R3`
- `role_independent`
- `role-separated R3`

## Key Empirical Patterns
- Final-round majority did not consistently outperform initial majority.
- Oracle-any-history remained high.
- Correct-to-wrong majority flips occurred.
- Wrong-to-correct majority flips were absent in both non-role and role-separated R3.
- Role-separated R3 looked more fragile than non-role R3 on this subset.

## Interpretation
These observations are consistent with trajectory mixing failure:
same-model debate may mix correlated reasoning trajectories and reinforce contextually dominant paths, rather than reliably selecting the correct path.

## What This Does Not Show
- no statistical significance
- no general causal proof
- no claim that all debate is harmful
- no claim that role prompts are generally harmful
- no conclusion beyond this model/backend/subset

## Next Checks
- Repeat flip dynamics on another small calibrated subset.
- Compare self-consistency without shared debate context.
- Test aggregation rules that preserve initially correct paths.
- Only then consider scaling `n`.

## Reference Values

### Non-Role R3
- initial majority accuracy: `0.7272727272727273`
- final majority accuracy: `0.6363636363636364`
- oracle-any-history accuracy: `0.9090909090909091`
- correct_to_wrong: `1`
- wrong_to_correct: `0`
- correct_path_retention_rate: `0.875`

### Role-Separated R3
- initial majority accuracy: `0.7272727272727273`
- final majority accuracy: `0.5454545454545454`
- oracle-any-history accuracy: `0.9090909090909091`
- correct_to_wrong: `2`
- wrong_to_correct: `0`
- correct_path_retention_rate: `0.75`

## Short Takeaway
On this small calibrated subset, same-model debate did not reliably improve the final majority, and the role-separated variant was more fragile than the non-role variant.
That is consistent with trajectory mixing, but it remains an exploratory post-hoc observation rather than a general conclusion.
A two-item follow-up sanity check was completed but did not meaningfully test trajectory mixing because both items were solved unanimously from the initial round.
