# Trajectory Mixing Hypothesis

## Core Idea

Same-model debate may not aggregate independent reasoning paths. It may instead mix highly correlated reasoning trajectories that were already produced by the same model under slightly different prompts.

## Empirical Pattern

On the 11-item role-separated AQuA follow-up:

- initial majority accuracy was `0.7272727272727273`
- final majority accuracy was `0.5454545454545454`
- oracle-any-history accuracy was `0.9090909090909091`
- correct-to-wrong majority transitions occurred
- wrong-to-correct majority transitions did not occur in this subset

The flip dynamics summary is consistent with this pattern:

- preserved_correct: 6
- correct_to_wrong: 2
- persistent_error: 3

## Interpretation

Later debate rounds may reinforce whichever reasoning path becomes contextually dominant. Under that interpretation, both correct and incorrect paths can become attractors.

Stability or consensus does not imply correctness.

## Relation to Chain-of-Thought

Chain-of-thought can be read as constructing a useful sequential reasoning path. Debate or persona context may perturb or mix such paths.

The present results are consistent with that interpretation, but they do not prove the mechanism.

## What This Does Not Show

- no statistical significance
- no general causal proof
- no claim that all debate is harmful
- no claim that role prompts are generally harmful
- no claim beyond this model, backend, and subset

## Next Falsification Checks

- Compute the same flip dynamics for non-role R3.
- Compare self-consistency without shared context.
- Test aggregation rules that preserve initially correct paths.
- Rerun on another small calibrated subset before scaling.

## Non-role Comparison

The non-role R3 run also shows a correct-to-wrong majority flip and no wrong-to-correct majority flips on this 11-item subset.
That makes the trajectory-mixing failure pattern look broader than the role-separated setup alone.

The role-separated run still appears more fragile: its final majority accuracy is lower and its correct-to-wrong majority rate is higher.
This is consistent with role prompts changing the failure mode, but it does not establish a general causal mechanism.
