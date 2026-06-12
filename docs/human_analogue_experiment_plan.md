# Human-Analogue Experiment Plan

## 1. Purpose

This document translates human social-influence paradigms into controlled LLM prompt experiments for the same-model debate project.

The goal is not to claim that LLMs and humans share the same psychological mechanism. The analogy is structural: human experiments often separate an initial private answer, exposure to other answers, majority pressure, dissent, repeated questioning, misinformation exposure, and changes in group diversity. Those same structural elements can be mapped into prompt conditions for a next-step LLM agent.

The central question is:

> When previous agents' answers are placed in the prompt, does a next LLM agent behave like an independent solver, or does it show context-induced effects analogous in structure to human conformity, suggestibility, or social influence?

The current project has already found diagnostic cases where same-model debate lost correct paths. This document defines the next experiments that should test the mechanism more directly.

Use this plan as an experiment-design document, not as a result report.

## 2. Human Reference Paradigms

### 2.1 Asch-style conformity

In Asch-style conformity experiments, a participant gives an answer after hearing answers from other people. A key observation is that people can conform to an incorrect majority even on simple perceptual tasks. Majority size matters: one opposing answer is weaker, while two or three opposing answers can substantially increase conformity. A dissenting partner can reduce conformity.

LLM mapping:

- Previous agents' answers act like confederate responses.
- A wrong-majority context corresponds to multiple previous agents giving the observed wrong answer.
- A correct dissent corresponds to preserving a minority correct path in the context.
- The next LLM output is used to test whether the model follows the contextual majority.

This is a structural analogy only. LLMs do not experience human social pressure. The experiment tests whether prompt-conditioned outputs show similar input-output patterns.

### 2.2 Repeated questioning and suggestibility

In human repeated-questioning settings, asking the same question repeatedly can signal that the previous answer was not accepted. In witness and child suggestibility contexts, repeated or suggestive questioning can lead to answer changes. The relevant analogy here is not human memory; it is the change in interpretation of the task context.

LLM mapping:

- Repeated problem and answer history may shift the prompt from ordinary Q&A into a verification, correction, or trick-question frame.
- Low repetition may act as an answer anchor.
- High repetition may create dispersion or instability if the context appears suspicious or corrective.

This motivates tracking not only correct and wrong-answer rates, but also unique answer count and answer entropy.

### 2.3 Misinformation and illusory truth

Human misinformation studies show that post-event information can alter later reports. Illusory truth effects show that repeated information can become more credible through familiarity or processing fluency. We do not assume the same internal mechanism for LLMs.

LLM mapping:

- Prior wrong answers or rationales in the prompt are post-event information.
- Repeated wrong answer strings may become more likely completions.
- Wrong rationales may contaminate later reasoning more strongly than answer-only anchors.

This motivates separating answer-only context from rationale-bearing context.

### 2.4 Wisdom of crowds under social influence

Independent crowd judgments can be useful because errors may cancel. Social influence can reduce diversity and undermine crowd wisdom. This maps closely to the concern that same-model debate is not independent aggregation once agents share context.

LLM mapping:

- Independent samples may contain diverse answers, including correct minority paths.
- Debate context may reduce diversity and collapse toward a wrong attractor.
- Diversity loss, answer entropy, and unique answer count should be tracked alongside final accuracy.

## 3. Human-to-LLM Mapping Table

| Human experiment element | LLM experiment analogue | Metric |
| --- | --- | --- |
| participant | next-step LLM agent | output answer |
| confederates | previous agent answers | anchor adoption |
| incorrect majority | wrong-majority context | target_wrong_rate |
| dissenting partner | minority correct answer | correct retention |
| repeated questioning | repeated previous answer blocks | entropy / answer change |
| post-event misinformation | wrong answer or rationale in prompt | wrong adoption |
| private written response | one-step independent answer after context | reduced public-pressure analogue |
| crowd diversity | answer distribution across samples | entropy / unique answers |

## 4. Primary Diagnostic Item

Primary item:

- item_id: `gsm8k_test_000234`
- gold: `21`
- observed wrong attractor: `14`

Observed debate trajectory:

| round | answers |
| ---: | --- |
| 0 | `21`, `21`, `21` |
| 1 | `21`, `21`, `14` |
| 2 | `14`, `14`, `21` |
| 3 | `14`, `14`, `14` |

Why this item is useful:

- It shows correct unanimous consensus becoming wrong unanimous consensus.
- It contains a correct-consensus state, a mixed-correct-majority state, a wrong-majority state, and a wrong-consensus state.
- It allows a one-step next-agent continuation test without rerunning full debate.

The item is diagnostic only. It should not be treated as a benchmark-level result.

## 5. Experiment A: Asch-Style Majority Influence Test

### Goal

Test whether the next LLM output follows the contextual majority answer.

### Conditions

| condition | answer-only context | purpose |
| --- | --- | --- |
| `baseline_no_context` | none | base distribution |
| `one_wrong_answer` | `14` | one wrong answer anchor |
| `wrong_majority_2v1` | `14`, `14`, `21` | wrong majority with correct dissent |
| `wrong_consensus_3v0` | `14`, `14`, `14` | wrong consensus |
| `one_correct_answer` | `21` | one correct answer anchor |
| `correct_majority_2v1` | `21`, `21`, `14` | correct majority with wrong dissent |
| `correct_consensus_3v0` | `21`, `21`, `21` | correct consensus |
| `balanced_split_order_A` | `14`, `21` | order-control split |
| `balanced_split_order_B` | `21`, `14` | order-control split |

### Prompt principle

- Include only answer strings, not rationales.
- Tell the model that previous answers may be right or wrong.
- Ask it to solve independently.
- Require the final answer inside `<answer>...</answer>`.

Example prompt fragment:

```text
Previous answers from other agents:
- Agent 1: 14
- Agent 2: 14
- Agent 3: 21

Now solve the original problem independently. The previous answers may be right or wrong.
Return only the final answer inside <answer>...</answer>.
```

### Suggested samples

- 20 rows per condition.
- If the independent runner creates 3 agent outputs per row, this yields 60 outputs per condition.

### Metrics

- `n_outputs`
- `correct_rate`
- `target_wrong_rate`
- `other_rate`
- `extraction_failure_rate`
- `unique_answer_count`
- `answer_entropy`

### Decision criteria

- Majority-following is consistent if `wrong_majority_2v1` increases `14` relative to baseline and `correct_majority_2v1` increases `21` relative to baseline.
- Wrong-consensus anchoring is consistent if `wrong_consensus_3v0` increases `14` further.
- Dissent preservation is suggested if the presence of `21` in `wrong_majority_2v1` reduces `14` relative to `wrong_consensus_3v0`.
- If all conditions are similar, answer-only social influence is weak for this item.

## 6. Experiment B: Trajectory Continuation Test

### Goal

Use the observed debate trajectory itself as context and test how the next one-step answer distribution changes.

This is the first coding target because it is closest to the observed failure trace and requires the least artificial manipulation.

### Conditions

| condition | context |
| --- | --- |
| `baseline_no_context` | original problem only |
| `after_round0_correct_consensus` | round 0 only: `21`, `21`, `21` |
| `after_round1_mixed_correct_majority` | rounds 0 and 1 |
| `after_round2_wrong_majority` | rounds 0, 1, and 2 |
| `after_round3_wrong_consensus` | rounds 0 through 3 |

### Prompt principle

- Include answer-only debate history.
- Do not include rationales.
- Tell the model previous answers may be right or wrong.
- Ask it to answer independently.
- Require the final answer inside `<answer>...</answer>`.

Example prompt fragment:

```text
Previous debate answers:
Round 0:
- Agent 1: 21
- Agent 2: 21
- Agent 3: 21
Round 1:
- Agent 1: 21
- Agent 2: 21
- Agent 3: 14

Now solve the original problem independently. The previous answers may be right or wrong.
Return only the final answer inside <answer>...</answer>.
```

### Metrics

- `correct_rate`
- `target_wrong_rate`
- `other_rate`
- `unique_answer_count`
- `answer_entropy`
- `delta_target_wrong_vs_baseline`
- `delta_entropy_vs_baseline`

### Decision criteria

- Context-attractor effect is consistent if `after_round2_wrong_majority` or `after_round3_wrong_consensus` increases `14` relative to baseline.
- Correct-anchor effect is consistent if `after_round0_correct_consensus` preserves or increases `21`.
- Dispersion or suspicion-like effects are consistent if `after_round3_wrong_consensus` increases entropy or `other_rate`.
- Shared-prior error is suspected if baseline already frequently outputs `14`.

## 7. Experiment C: Repeated-Question / Over-Repetition Test

### Goal

Test whether repetition has a non-monotonic effect.

### Conditions

Wrong-answer conditions:

- `wrong_repetition_0`
- `wrong_repetition_1`
- `wrong_repetition_2`
- `wrong_repetition_3`
- `wrong_repetition_5`
- `wrong_repetition_10`
- `wrong_repetition_20`

Optional parallel correct-answer conditions:

- `correct_repetition_0`
- `correct_repetition_1`
- `correct_repetition_2`
- `correct_repetition_3`
- `correct_repetition_5`
- `correct_repetition_10`
- `correct_repetition_20`

### Metrics

- `correct_rate`
- `target_wrong_rate`
- `other_rate`
- `unique_answer_count`
- `answer_entropy`
- `low_repetition_delta`: `wrong_repetition_3` minus `wrong_repetition_0`
- `high_repetition_drop`: `wrong_repetition_20` minus max of `wrong_repetition_2`, `wrong_repetition_3`, and `wrong_repetition_5`

### Decision criteria

- Non-monotonic repetition is consistent if `14` rises at low repetition counts and drops or disperses at high counts.
- Simple repetition anchoring is consistent if `14` increases monotonically or near-monotonically.
- Repetition-only explanation is weakened if rates are flat.
- Suspicion-like dispersion is consistent if high repetition increases entropy or other answers.

## 8. Experiment D: Answer-Only vs Rationale Contamination

### Goal

Separate answer anchoring from rationale contamination.

### Primary items

- `gsm8k_test_000234`: gold `21`, wrong `14`
- `gsm8k_test_000089`: gold `24`, wrong `18`
- `gsm8k_test_000147`: gold `75`, wrong `15`
- `gsm8k_test_000093`: gold `36`, wrong `36.36`

### Conditions

- `baseline_no_anchor`
- `wrong_answer_only`
- `wrong_rationale_only`
- `wrong_answer_plus_rationale`
- `correct_answer_only`
- `correct_answer_plus_rationale`

### Decision criteria

- If `wrong_answer_plus_rationale` produces higher wrong adoption than `wrong_answer_only`, rationale contamination is plausible.
- If `wrong_answer_only` is sufficient, answer anchoring is plausible.
- If neither changes behavior but baseline already makes the same wrong answer, shared-prior error may dominate.

## 9. Implementation Order

Implement in this order:

1. Build dataset and analyzer for Experiment B: trajectory continuation.
2. Run only `gsm8k_test_000234` trajectory continuation.
3. Document results.
4. Build Experiment A if needed.
5. Build Experiment C if repetition-specific testing is still needed.
6. Build Experiment D only after answer-only context effects are measured.
7. Delay mitigation experiments until mechanism evidence is clearer.

Rationale:

Experiment B is closest to the actual observed failure trace and requires the least artificial manipulation.

## 10. Metrics Definitions

- `correct_rate`: fraction of non-failed outputs equal to the gold answer after normalization.
- `target_wrong_rate`: fraction of non-failed outputs equal to the observed wrong attractor after normalization.
- `other_rate`: fraction of non-failed outputs neither gold nor target wrong.
- `extraction_failure_rate`: failed outputs divided by total outputs.
- `unique_answer_count`: number of distinct normalized answers among non-failed outputs.
- `answer_entropy`: entropy over the normalized answer distribution among non-failed outputs.

Numeric answer comparison should use exact normalization. Treat `21` and `21.0` as equal. Treat comma-formatted numbers as equal to their unformatted equivalents. Do not use broad numerical tolerance.

## 11. Limitations

- The human analogy is structural, not mechanistic.
- LLMs do not have human social pressure or memory in the same sense.
- Prompt wording may strongly affect results.
- Single-item experiments are diagnostic only.
- Multiple samples are needed; one output is not a distribution.
- Rationale text is not guaranteed to be faithful.
- No statistical significance claim should be made at this stage.

## 12. Next Step

The next coding task should be:

- trajectory-continuation dataset builder
- trajectory-continuation analyzer
- tests
- small generated dataset for `gsm8k_test_000234`

Do not implement those in this documentation-only commit.
