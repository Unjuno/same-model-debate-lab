# Current Conclusions

## 1. Original Motivation

The project started from a simple exploratory question: same-model multi-agent debate may not be equivalent to aggregating independent reasoning paths.
If all agents are instantiated from the same model, they may share correlated errors.
Once agents exchange debate context, the transcript may mix trajectories and create either loss of an initially correct path or misleading stable agreement around the wrong answer.

## 2. What The Project Is Testing

The current experiments test whether shared debate context changes the behavior of same-model agents relative to independent sampling.
The focus is on trajectory-level diagnostics, not just final-answer accuracy.

The main checks used so far are:

- independent screening to find exploratory partial-correct subsets
- post-hoc aggregation rules
- flip dynamics across rounds
- transient correctness analysis

## 3. Current Evidence

### GSM8K partial9

The GSM8K partial9 subset is a post-hoc selected subset from the 300-item independent screening run.

- final_round_majority accuracy: `5/9`
- initial_majority accuracy: `7/9`
- all_round_majority accuracy: `7/9`
- oracle_any_history_correct: `9/9` full-history upper bound
- transient_correct_majority_lost: `2`
- transient_correct_consensus_lost: `1`
- correct_to_wrong: `3`
- wrong_to_correct: `1`
- extraction_failure_count: `0`
- key example: `gsm8k_test_000234`, where a correct unanimous consensus became a wrong unanimous consensus

### AQuA screened3

The AQuA screened3 subset provides an additional diagnostic example.

- key example: `aqua_test_1_000086`
- an intermediate unanimous correct consensus appeared and was later lost by final aggregation
- this is an additional diagnostic example, not replication

### AQuA 11

The AQuA 11-item results give a second exploratory comparison.

- non-role R3: accuracy `0.6364`, oracle_at_k `0.9091`, answer_loss_rate `0.3`
- role R3: accuracy `0.5455`, oracle_at_k `0.7273`, answer_loss_rate `0.25`
- n=`11` and the subset is post-hoc selected
- the role-separated variant appeared more fragile in this small subset

## 4. What We Can Currently Say

- Final consensus or final majority can miss correct paths that were present earlier in the trace.
- Stable agreement is not necessarily evidence of correctness.
- Final accuracy alone is insufficient for diagnosing this failure mode.
- Trajectory-level analyses are useful, especially aggregation rules, flip dynamics, and transient correctness.
- The current results are consistent with the idea that shared debate context may steer same-model agents toward correlated failures or post-hoc consensus collapse.

## 5. What We Cannot Currently Say

- We cannot make a general harmfulness claim.
- We cannot make a statistical significance claim from these exploratory subsets.
- We cannot claim causal proof of correlated reasoning trajectories.
- We cannot generalize across models, backends, prompts, or benchmarks.
- `oracle_any_history_correct` is not a deployable selector.

## 6. Key Diagnostic Examples

- `gsm8k_test_000234`: correct unanimous consensus became wrong unanimous consensus.
- `gsm8k_test_000089`: initially correct majority later flipped wrong.
- `gsm8k_test_000147`: initially correct majority later flipped wrong.
- `aqua_test_1_000086`: intermediate unanimous correct consensus was lost before final aggregation.

## 7. Limitations

- The current evidence is exploratory and post-hoc.
- The selected subsets are intentionally small and not random samples of the benchmarks.
- The conclusions come from a single model/backend/config family.
- Some comparisons are based on selected subsets rather than full benchmark sweeps.
- No result here establishes a general mechanism.

## 8. Next Decision Criteria

The next step should depend on whether the same failure mode continues to appear under new diagnostic checks.

Useful decision criteria:

- Does a new exploratory subset again show final-majority loss of earlier correct paths?
- Do alternative aggregation rules preserve more initially correct paths?
- Does the behavior persist when transcript structure or prompt style changes?
- Do results remain consistent across another benchmark or another model/backend/config?

If the answer is yes across several post-hoc diagnostics, the project may justify a broader study.
If not, the current result should remain a focused exploratory finding rather than a broader conclusion.

## 9. Live Mitigation Smoke

The live mitigation support is implemented and has been smoke-tested on a small sample.
The smoke confirmed that the live runner, raw-history preservation, and analyzer plumbing work together.
The partial9 live run is intentionally postponed until a longer backend window is available.

What the smoke suggests:

- the mitigation condition routing is usable
- raw histories remain intact
- the analyzer can aggregate multiple condition outputs

What it does not establish:

- a benchmark-level mitigation claim
- a statistically stable effect size
- a final decision on whether the mitigation conditions help on the full partial9 live run
