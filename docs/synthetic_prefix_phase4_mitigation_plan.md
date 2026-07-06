# Synthetic Prefix Phase 4 Mitigation Plan

## Purpose

Phase 4 tests whether protocol-level controls can reduce same-model debate contamination driven by shared numeric anchors.
This is a mitigation diagnostic, not a proof of safety.

## Background From Phase 3c

Phase 3c suggests that numeric anchoring is not solely an artifact of explicit final-answer labels.
Unlabeled numbers, explanation-internal numbers, and intermediate-value numbers also increased target-wrong outputs over baseline.
Uncertainty and explicit error warnings attenuated, but did not eliminate, the effect.

## Main Research Question

Given that some cross-agent contamination is structurally unavoidable in multi-agent protocols, which protocol designs attenuate answer loss, same-error convergence, and target-wrong collapse while still preserving some multi-agent interaction?

## Why Mitigation Rather Than Elimination

Contamination is not expected to be eliminated.
The goal is to measure how much different protocol designs attenuate it.

## Candidate Protocol Conditions

- `independent`
  - No cross-agent context
  - Baseline for preserving independent sampling
- `full_context_debate`
  - Standard debate or full-context interaction
  - Other agents' text, final answers, and numbers are visible
  - Expected contamination upper bound
- `answer_hidden_debate`
  - Explicit final answers are hidden
  - Reasoning text remains visible
  - Tests whether hiding answer labels alone is sufficient
- `numeric_masked_debate`
  - Numeric values in peer text are replaced with `[NUM]`
  - Tests whether removing numeric anchor tokens reduces convergence
- `commit_then_numeric_masked_debate`
  - Agents first commit to an independent initial answer
  - Later interaction is only through numeric-masked peer context
  - Tests whether initial independence plus masked critique preserves some multi-agent value while reducing contamination

An optional later `warning_debate` condition can be added if it fits cleanly.

## Primary Metrics

- final accuracy
- oracle_at_k
- answer_loss_rate
- same_error_agreement_rate
- diversity_drop
- extraction_failure_rate
- target_wrong_rate, when target_wrong is available
- correct_to_wrong_collapse_rate
- correct_initial_lost_rate
- target_wrong_convergence_rate
- numeric_anchor_exposure_level, recorded as condition metadata

If a condition is synthetic and does not include real debate history, history-based metrics should be marked not applicable rather than fabricated.

## Expected Qualitative Outcomes

- `full_context_debate` should be the strongest contamination condition
- `answer_hidden_debate` may still show substantial contamination if reasoning text or embedded numbers remain visible
- `numeric_masked_debate` should attenuate numeric-anchor carryover more than answer hiding alone
- `commit_then_numeric_masked_debate` may preserve some useful interaction while reducing collapse relative to full-context debate
- `warning_debate`, if added later, is expected to attenuate but not eliminate anchors

These are hypotheses for diagnostic comparison, not claims about general safety.

## Cautions and Limitations

- Exploratory, diagnostic, repeated-stochastic-sample setting
- Limited to the present model/backend/config family
- Human conformity and repeated-question experiments are only structural analogies
- Do not infer social pressure, persuasion, memory distortion, or belief change
- Do not claim statistical significance
- Do not generalize beyond this repository's current setup

## Implementation Approach

Phase 4 is implemented as a synthetic-prefix mitigation diagnostic rather than a new runner mode.
The code path is intentionally minimal:

- pure protocol transformation utilities for masking and answer hiding
- a dataset builder that emits transformed peer-context prompts
- an analyzer that groups results by mitigation condition and reports mitigation-oriented metrics

## Artifact Policy

Do not commit `runs/*`, raw JSONL, logs, summary JSON, or shard artifacts.
Only the curated plan, analysis code, tests, and promoted documentation should be committed.
