# Live Debate Mitigation Design

## Purpose

This note sketches the next step after the Phase 4 synthetic-prefix mitigation diagnostic: a live multi-round debate protocol study that tests whether protocol-level controls can attenuate numeric-anchor contamination when peer context is constructed dynamically during debate.

The goal is mitigation, not elimination. Some cross-agent dependence is structurally unavoidable in a shared-context protocol, so the question is how much different designs reduce answer loss, same-error convergence, and target-wrong collapse while still preserving useful interaction.

## Existing Runner Architecture

The current runner is centered in `src/smdebate/cli.py` with prompt construction in `src/smdebate/protocol.py`.

### Condition Representation

- Supported conditions are defined in `src/smdebate/config.py` as a small literal set:
  - `independent`
  - `debate_1r`
  - `debate_3r_full_context`
  - `role_independent`
  - `role_debate_3r_full_context`
- `load_config()` stores the chosen condition in the experiment config.
- `cli.py` uses `_rounds_for_condition()` and `_role_profile_enabled()` to map the condition to orchestration behavior.

### Round Orchestration

- `run_item()` in `src/smdebate/cli.py` runs the initial independent answers, then iterates debate rounds.
- Round 0 always collects each agent's private answer via `initial_prompt()`.
- Later rounds call `debate_prompt()` for each agent.
- The loop stores:
  - `initial_answers`
  - `final_answers`
  - `final_answer`
  - `initial_raw`
  - `final_raw`
  - `transcript_raw`

### Peer Context Insertion

- `_visible_responses_for_condition()` decides which prior responses are visible to each agent.
- For `debate_3r_full_context`, an agent can see all prior responses except its own current response, across the full accumulated history.
- For the other debate path, visibility is limited to the current round's peer responses.
- `debate_prompt()` concatenates visible peer responses into the `Other agents' responses:` section.

### Final Answer Extraction

- `extract_answer()` in `src/smdebate/protocol.py` extracts `<answer>...</answer>` content when present.
- If extraction fails, the raw text is preserved and the row is marked with `extraction_failed=True`.
- `summarize_rows()` in `src/smdebate/metrics.py` computes final accuracy, oracle-at-k, answer loss, same-error agreement, diversity drop, and extraction failure rate from the stored row fields.

### Raw History Storage

- `run_item()` stores full per-agent response objects in:
  - `initial_raw`
  - `final_raw`
  - `transcript_raw`
- Each response includes:
  - `agent_id`
  - `round_index`
  - `raw_text`
  - `answer`
  - `extraction_failed`
- The raw JSONL written by the CLI preserves these histories for later audit.

### Existing Tests

- `tests/test_contract.py` covers:
  - independent versus debate behavior
  - 1-round and multi-round orchestration
  - full-context transcript reuse
  - role-profile injection
  - extraction-failure handling
  - resume/output-dir behavior
- The Phase 4 synthetic mitigation tests cover peer-context masking utilities and synthetic dataset construction, but not the live runner itself.

## Proposed Live Mitigation Conditions

The live runner can likely support the following conditions with a small peer-context transformation layer:

1. `full_context_debate`
   - Current full-context debate behavior, or a thin alias for the existing full-context debate condition.
   - Peer outputs are visible with text, numbers, and final answers.

2. `answer_hidden_debate`
   - Later-round peer context hides explicit final answers.
   - Reasoning text remains visible.
   - Hidden-answer matching should cover forms such as `Answer: 96`, `Final answer: 96`, `<answer>96</answer>`, `- Peer A: Answer: 96`, and `The answer is 96.`

3. `numeric_masked_debate`
   - Later-round peer context masks numeric tokens in peer-visible text only.
   - The original problem text must remain unchanged.
   - The current agent's private reasoning or own answer should not be transformed unless it is already part of peer-visible context.

4. `commit_then_numeric_masked_debate`
   - Round 0 is a private independent commitment step.
   - Later rounds expose only numeric-masked peer context.
   - The raw history must preserve round-0 answers so collapse metrics can be computed.
   - The prompt should make the commit step explicit before any peer exposure.

5. Optional later: `answer_hidden_numeric_masked_debate`
   - Hide explicit final answers and mask remaining numeric tokens.
   - This is a natural combination control if it fits cleanly into the same abstraction.

## Required Code Touch Points

If live mitigation is implemented, the smallest likely touch points are:

- `src/smdebate/config.py`
  - add mitigation condition literals
- `src/smdebate/cli.py`
  - branch on mitigation conditions
  - transform peer-visible text before prompt assembly
- `src/smdebate/protocol.py`
  - possibly add a helper to render peer context cleanly
- `src/smdebate/mitigation.py`
  - reuse `mask_numeric_tokens`, `hide_final_answer`, and `apply_peer_context_policy`
- tests
  - add prompt-construction tests for the new conditions

If the runner coupling turns out to be tighter than expected, a wrapper/adaptor around peer-context construction is the safer alternative to broad orchestration changes.

## Raw Output / History Requirements

Live mitigation metrics need raw histories that preserve:

- initial round answers for all agents
- later-round answers for all agents
- the exact peer context shown to each agent, or enough information to reconstruct it deterministically

That is important for collapse metrics such as:

- correct-to-wrong collapse
- correct-initial-lost rate
- target-wrong convergence

The raw outputs should remain unmodified. Any mitigation should apply only to the text shown to other agents, not to the stored raw transcript.

## Metrics Needed

A live mitigation run should support the following readouts where applicable:

- final accuracy
- oracle_at_k
- answer_loss_rate
- same_error_agreement_rate
- diversity_drop
- extraction_failure_rate
- target_wrong_rate
- correct_to_wrong_collapse_rate
- correct_initial_lost_rate
- target_wrong_convergence_rate

For protocols that do not preserve a multi-round history, the collapse metrics should be reported as not applicable rather than inferred.

## Test Plan

The first test layer should be small and deterministic:

- unit tests for `hide_final_answer()` on peer-prefixed lines
- unit tests for `mask_numeric_tokens()` on peer-visible text
- tests that verify the original problem text is not transformed
- prompt-construction tests that confirm the correct peer context is visible under each condition
- if live runner branching is added, a contract test that round-0 answers remain in raw history

## Risks and Limitations

- This is still a same-model, shared-context diagnostic, not a safety proof.
- Hiding explicit answers may be insufficient because Phase 3c showed that unlabeled and embedded numbers can also anchor.
- Numeric masking may reduce contamination while also removing useful reasoning detail.
- A commit-then-mask protocol may preserve some interaction, but its effect is empirical rather than guaranteed.
- Any result will remain family-specific to the present model/backend/config setup.

## Recommended Implementation Order

1. Add a minimal context-policy abstraction for peer-visible text.
2. Extend conditions in the runner only if the abstraction is straightforward.
3. Add contract tests for prompt construction and history preservation.
4. Run a small smoke test before any broader evaluation.
5. Only then decide whether a larger live protocol study is worth scaling.

## Implementation Route

The implementation route selected for the first live step is:

- Route B: a small peer-context policy abstraction inside the existing debate runner.

This keeps the orchestration path stable while adding the minimal condition-specific transformation needed for live mitigation tests.

## Implemented Conditions

The first live implementation supports:

- `full_context_debate`
- `answer_hidden_debate`
- `numeric_masked_debate`
- `commit_then_numeric_masked_debate`

All of these reuse the existing round orchestration and preserve raw stored outputs.

## Current Limitation

- `commit_then_numeric_masked_debate` currently uses the existing debate prompt wording with a private round-0 commitment followed by masked peer context. If a stronger commit-first prompt needs to be introduced later, that can be done as a small follow-up change.

That keeps the next step focused on protocol design rather than a risky orchestration refactor.
