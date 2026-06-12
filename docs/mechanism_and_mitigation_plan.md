# Mechanism and Mitigation Plan

## 1. Purpose

Current answer-only analyses can detect answer loss and trajectory failures, but they do not identify the mechanism that causes those failures.
The purpose of this document is to define mechanism hypotheses and mitigation directions before adding more tooling or running more inference.

This is a planning document, not a result report.

## 2. Original Project Motivation

The original project idea was that same-model multi-agent debate may not be equivalent to aggregating independent reasoning paths.
Because the agents are instances of the same model and later rounds condition on shared context, debate may mix correlated reasoning trajectories.
That can potentially lose initially correct paths or produce misleading stable agreement.

One key observation from the current work is that stable final agreement is not necessarily evidence of correctness.

## 3. What Current Answer-Only Diagnostics Show

| Experiment | n | Key observation | Limitation |
| --- | ---: | --- | --- |
| AQuA 11 non-role R3 | 11 | accuracy `0.6364`, oracle_at_k `0.9091`, answer_loss_rate `0.3`, correct-to-wrong majority flips were observed | exploratory, post-hoc, small `n` |
| AQuA 11 role-separated R3 | 11 | accuracy `0.5455`, oracle_at_k `0.7273`, answer_loss_rate `0.25`, appeared more fragile than the non-role variant | exploratory only |
| AQuA screened3 | 3 | `aqua_test_1_000086` showed intermediate unanimous correct consensus that was later lost before final aggregation | diagnostic example, not replication |
| GSM8K 300 independent screening | 300 | accuracy `0.9533333333333334`, oracle_at_k `0.97`, answer_loss_rate `0.01718213058419244`, same_error_agreement_rate `0.02`, diversity_drop `0.0`, extraction_failure_rate `0.0`, selector found 9 partial-correct items | screening result, not mechanism evidence |
| GSM8K partial9 debate R3 | 9 | accuracy `0.5555555555555556`, oracle_at_k `0.8888888888888888`, answer_loss_rate `0.5`, same_error_agreement_rate `0.2222222222222222`, diversity_drop `0.3333333333333333`, extraction_failure_rate `0.0` | post-hoc selected subset |

These observations are consistent with a failure mode where shared debate context can cause loss of earlier correct paths, but they do not prove a mechanism.

## 4. Why Answer-Only Analysis Is Insufficient

Final answers show that a path was lost, but not why it was lost.
A correct answer may disappear because of answer anchoring, rationale contamination, majority following, shared-prior error, or weak verification.
Without rationales or controlled anchor conditions, these mechanisms cannot be distinguished.

At the same time, visible rationales can themselves become a contamination source.
That means rationale capture and mitigation design should be separated rather than conflated.

## 5. Mechanism Hypotheses

### 5.1 Shared-prior error

Definition:
The same model may independently rediscover the same wrong answer because the task activates the same flawed heuristic or learned pattern.

Expected signature in data:
The same wrong answer appears frequently even without any anchor or debate context.

How to test it:
Run baseline independent samples without previous answers or rationales.

Possible mitigation if supported:
Use heterogeneous models, external verifiers, calculators, or symbolic checks.

### 5.2 Answer anchoring

Definition:
A previously shown answer string, such as `14`, makes the model more likely to output the same answer later.

Expected signature in data:
Wrong-answer adoption increases when the wrong answer is shown in the prompt, even without a rationale.

How to test it:
Compare baseline, one wrong answer, two wrong answers, three wrong answers, and wrong majority answer-only conditions.

Possible mitigation if supported:
Delay disclosure of other agents' answers until after each agent commits to its own answer.

### 5.3 Majority following

Definition:
The model may follow the answer that appears most often in the context, independently of correctness.

Expected signature in data:
The model follows `14,14,21` toward `14`, and `21,21,14` toward `21`.

How to test it:
Use symmetric correct-majority and wrong-majority anchor prompts.

Possible mitigation if supported:
Hide majority counts, randomize presentation, or force independent verification before seeing group answers.

### 5.4 Rationale contamination

Definition:
The model may adopt not only another agent's answer but also the flawed explanation that makes the answer seem plausible.

Expected signature in data:
Wrong adoption is higher when a wrong rationale is shown than when only the wrong answer is shown.

How to test it:
Compare answer-only wrong anchors, rationale-only wrong anchors, and answer-plus-rationale wrong anchors.

Possible mitigation if supported:
Do not share free-form rationales directly across agents; share only structured checks, constraints, equations, or verifier outputs.

### 5.5 Unverified repetition

Definition:
A repeated answer that appears multiple times without explicit correction may become contextually credible.

Expected signature in data:
A small number of repeated wrong answers increases wrong adoption compared with baseline.

How to test it:
Repetition sweep over wrong answer counts such as `0`, `1`, `2`, `3`, `5`, `10`, `20`.

Possible mitigation if supported:
Limit repeated exposure to unverified answers and preserve dissenting alternatives.

### 5.6 Over-repetition suspicion

Definition:
Excessive repetition may make the context look suspicious, trick-like, or corrective, leading to answer dispersion rather than simple adoption.

Expected signature in data:
Wrong adoption rises at low repetition counts but plateaus or drops at high counts; unique answer count or answer entropy may increase at high counts.

How to test it:
Use repetition counts `0`, `1`, `2`, `3`, `5`, `10`, `20` and measure wrong adoption, correct rate, other rate, unique answer count, and answer entropy.

Possible mitigation if supported:
Avoid long unconstrained debate loops; use explicit verification checkpoints instead of repeated discussion.

### 5.7 Verification failure

Definition:
The model may generate a plausible continuation or rationalization instead of explicitly checking arithmetic or logical constraints.

Expected signature in data:
Wrong answers persist even when the correct answer appeared earlier, unless a structured verification step is introduced.

How to test it:
Compare normal answer generation with a structured verification prompt that requires equation checks, arithmetic audit, or counterexample search.

Possible mitigation if supported:
Add external calculators, symbolic checkers, structured verifier prompts, or final consistency checks.

## 6. Rationale Capture Plan

Future observation runs should optionally collect:

```xml
<reasoning>
...
</reasoning>
<answer>
...
</answer>
```

Free-form rationale is not guaranteed to be faithful, and exposing rationales to later agents can itself create contamination.
Rationale capture should therefore be used in two separate modes:

1. Observation mode:
   Collect rationales to analyze why answers change.
2. Mitigation mode:
   Do not freely share rationales. Instead, share restricted structured artifacts such as equations, variable assignments, arithmetic checks, constraints, counterarguments, or verifier verdicts.

The proposed output schema is:

```xml
<reasoning>
...
</reasoning>
<answer>
...
</answer>
```

Do not treat rationale as guaranteed internal reasoning.

## 7. Controlled Experiments To Run Next

### 7.1 Repetition-anchor sweep

Primary item:
- `gsm8k_test_000234`
- gold = `21`
- wrong attractor = `14`

Repetition levels:
- `0`
- `1`
- `2`
- `3`
- `5`
- `10`
- `20`

Suggested samples:
- 20 replicates per level
- if independent condition uses 3 agents, this yields 60 outputs per level

Metrics:
- `correct_rate`
- `wrong_adoption_rate`
- `other_rate`
- `extraction_failure_rate`
- `unique_answer_count`
- `answer_entropy`
- `low_repetition_delta`: `wrong_adoption_rate` at 3 minus at 0
- `high_repetition_drop`: `wrong_adoption_rate` at 20 minus max `wrong_adoption_rate` at 2/3/5

Decision criteria:
- Non-monotonic repetition effect is supported if wrong adoption rises from 0 to 2/3/5 and then drops or answer entropy increases at 10/20.
- Simple answer anchoring is supported if wrong adoption increases monotonically or near-monotonically.
- Repetition-only explanation is weakened if wrong adoption is flat.

### 7.2 Answer-only vs rationale contamination

Primary items:
- `gsm8k_test_000234`: gold 21, wrong 14
- `gsm8k_test_000089`: gold 24, wrong 18
- `gsm8k_test_000147`: gold 75, wrong 15
- `gsm8k_test_000093`: gold 36, wrong 36.36

Conditions:
- `baseline_no_anchor`
- `wrong_answer_only`
- `wrong_rationale_only`
- `wrong_answer_plus_rationale`
- `correct_answer_only`
- `correct_answer_plus_rationale`

Metrics:
- `correct_rate`
- `target_wrong_adoption_rate`
- `rationale_contamination_delta`: `wrong_answer_plus_rationale` minus `wrong_answer_only`

Decision criteria:
- If `wrong_answer_plus_rationale` produces higher wrong adoption than `wrong_answer_only`, rationale contamination is plausible.
- If `wrong_answer_only` is already enough, answer anchoring is plausible.
- If neither changes behavior, shared-prior error or prompt/task-specific effects may dominate.

### 7.3 Mitigation pilot

Compare these conditions on the same diagnostic items:
- normal debate
- `private_first_then_compare`
- `delayed_disclosure`
- `answer_only_sharing`
- `structured_verifier`
- `minority_preserved_aggregation`

Metrics:
- `final accuracy`
- `initial_majority accuracy`
- `all_round_majority accuracy`
- `correct_to_wrong count`
- `transient_correct_majority_lost count`
- `transient_correct_consensus_lost count`
- `answer_loss_rate`

Decision criteria:
- A mitigation is promising if it reduces `correct_to_wrong` and transient-correctness loss without sharply reducing `recovered_to_correct` cases.
- A mitigation is not promising if it only suppresses debate dynamics while also reducing recovery of initially wrong items.

## 8. Mitigation Design Principles

1. Preserve independent first-pass answers.
2. Delay exposure to other agents' answers.
3. Avoid exposing free-form rationales by default.
4. Preserve dissenting answers rather than collapsing to majority too early.
5. Prefer structured verification over open-ended persuasion.
6. Separate generation from verification.
7. Do not treat final consensus as correctness evidence by itself.
8. Track trajectory-level metrics, not only final accuracy.

## 9. What This Plan Does Not Claim

- It does not prove same-model debate is generally harmful.
- It does not establish statistical significance.
- It does not prove a causal internal mechanism.
- It does not show that LLMs cannot reason.
- It does not claim rationales are faithful internal reasoning.
- It does not generalize across models or benchmarks yet.

## 10. Next Implementation Steps

1. Build repetition-anchor dataset builder.
2. Build repetition-anchor analyzer.
3. Add answer entropy and unique answer count metrics.
4. Run `gsm8k_test_000234` repetition sweep.
5. Document results.
6. Expand to the other GSM8K diagnostic items.
7. Add rationale-contamination prompts.
8. Only then evaluate mitigation variants.
