from __future__ import annotations

from dataclasses import dataclass


def normalize_answer(value: str) -> str:
    return str(value).strip().lower().replace(",", "")


def is_correct(predicted: str, gold: str) -> bool:
    return normalize_answer(predicted) == normalize_answer(gold)


def unique_count(values: list[str]) -> int:
    return len({normalize_answer(value) for value in values})


@dataclass(frozen=True)
class MetricSummary:
    n: int
    accuracy: float
    oracle_at_k: float
    answer_loss_rate: float
    same_error_agreement_rate: float
    diversity_drop: float
    extraction_failure_rate: float


def summarize_rows(rows: list[dict]) -> MetricSummary:
    if not rows:
        raise ValueError("rows must not be empty")

    n = len(rows)
    correct_final = 0
    oracle_hits = 0
    loss_num = 0
    loss_den = 0
    same_error_agreement = 0
    diversity_drop_total = 0
    extraction_failures = 0
    extraction_total = 0

    for row in rows:
        gold = row["gold"]
        initial_answers = row["initial_answers"]
        final_answers = row["final_answers"]
        final_answer = row["final_answer"]

        final_ok = is_correct(final_answer, gold)
        initial_has_correct = any(is_correct(answer, gold) for answer in initial_answers)

        correct_final += int(final_ok)
        oracle_hits += int(initial_has_correct)

        if initial_has_correct:
            loss_den += 1
            loss_num += int(not final_ok)

        initial_unique = unique_count(initial_answers)
        final_unique = unique_count(final_answers)

        same_error_agreement += int((not final_ok) and final_unique == 1)
        diversity_drop_total += initial_unique - final_unique

        extraction_failures += int(row.get("extraction_failures", 0))
        extraction_total += int(row.get("extraction_total", len(initial_answers) + len(final_answers)))

    return MetricSummary(
        n=n,
        accuracy=correct_final / n,
        oracle_at_k=oracle_hits / n,
        answer_loss_rate=loss_num / loss_den if loss_den else 0.0,
        same_error_agreement_rate=same_error_agreement / n,
        diversity_drop=diversity_drop_total / n,
        extraction_failure_rate=extraction_failures / extraction_total if extraction_total else 0.0,
    )
