# Publication Readiness Checklist

This checklist describes the current public-facing state without publishing or pushing anything automatically.

## Evidence and analysis

- [x] Main GSM8K partial9 live run completed: 20 repeats × 5 conditions.
- [x] Raw run artifacts retained locally: 100 run directories.
- [x] Machine-readable aggregate report generated.
- [x] Condition-level confidence intervals generated.
- [x] Repeat-level accuracy plot generated.
- [x] Answer-loss and initial-correct-path plots generated.
- [x] Regeneration commands documented.
- [x] Exploratory limitations stated.

## Code and documentation

- [x] Analysis tools are dependency-free beyond the project runtime.
- [x] Analysis tests are included.
- [x] Full test suite passes.
- [x] Ruff passes across `tools/`.
- [x] README links to current conclusions, results, and preservation policy.
- [x] Run plans no longer instruct unconditional deletion of existing runs.

## Before external publication

- [ ] Decide whether to publish raw transcripts. The default is aggregate-only publication.
- [ ] Archive raw data and record its checksum outside Git.
- [ ] Review model/backend metadata and any local paths or secrets in artifacts.
- [ ] Commit the intended code and documentation changes.
- [ ] Push only after reviewing the final diff and repository visibility settings.

The final unchecked items are release actions, not experiment or analysis gaps. No data deletion is required for publication preparation.
