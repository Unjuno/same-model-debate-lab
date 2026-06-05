# Difficulty Calibration

The goal of this workflow is not to build the hardest possible dataset.
The goal is to build a calibrated dataset where independent same-model agents are only partially correct.

Why this matters:

- All-correct items are too easy.
- All-wrong items cannot measure answer loss, because there is no correct candidate to lose.
- Partially correct items let us test whether debate causes a model to lose a correct answer that was already present in one or more independent samples.

Calibration workflow:

1. Generate parametric logical items with controlled difficulty.
2. Run the independent condition.
3. Keep only items with `extraction_failures == 0`.
4. Keep only items where `1 <= initial_correct_count <= agent_count - 1`.
5. Use the selected subset for debate comparisons.

For three agents, the target calibration band is exactly one or two correct initial answers.

This produces a benchmark for answer-loss analysis without relying on public benchmark contamination.
