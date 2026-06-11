# AQuA Role-Separated Round Trajectory: 11-Item R3 Follow-Up

This is a compact post-hoc round-trajectory summary over the existing `raw.jsonl` traces for the role-separated 11-item follow-up.

## Category Counts

- preserved_correct: 6
- persistent_error: 3
- recovery: 0
- deterioration: 2
- oscillation: 0

## Item-Level Summary

| item_id | gold | flip_count | category |
| --- | --- | ---: | --- |
| aqua_test_0_000016 | A | 0 | preserved_correct |
| aqua_test_0_000184 | D | 0 | preserved_correct |
| aqua_test_1_000016 | A | 0 | preserved_correct |
| aqua_test_1_000059 | C | 1 | deterioration |
| aqua_test_1_000067 | B | 0 | preserved_correct |
| aqua_test_1_000069 | C | 1 | deterioration |
| aqua_test_1_000117 | C | 0 | preserved_correct |
| aqua_test_1_000172 | E | 0 | persistent_error |
| aqua_test_1_000188 | D | 0 | persistent_error |
| aqua_test_1_000210 | E | 0 | persistent_error |
| aqua_test_1_000237 | B | 0 | preserved_correct |

## Notes

- `preserved_correct` means the round-majority stayed correct from the first to the last observed round.
- `deterioration` means the round-majority started correct and ended wrong.
- `persistent_error` means the round-majority stayed wrong across observed rounds.
- Categories are based on the observed round-majority trajectory, not on whether one isolated agent ever produced the gold answer.
- No raw transcripts, prompts, or model text are included.
- This summary is intended for coarse trajectory inspection only.
