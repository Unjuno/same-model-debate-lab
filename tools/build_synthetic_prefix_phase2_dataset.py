from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_synthetic_prefix_continuation_dataset import (  # noqa: E402
    _problem_without_final_instruction,
    load_jsonl,
    write_jsonl,
)

PHASE = "phase2_majority_recency"
DEFAULT_TARGET_WRONG_ANSWER = "14"

CONTEXT_BY_CONDITION: dict[str, dict[int, list[str]]] = {
    "baseline_no_prefix": {},
    "single_round_correct_consensus": {0: ["21", "21", "21"]},
    "single_round_correct_majority": {0: ["21", "21", "14"]},
    "single_round_wrong_majority": {0: ["14", "14", "21"]},
    "single_round_wrong_consensus": {0: ["14", "14", "14"]},
    "trajectory_forward": {
        0: ["21", "21", "21"],
        1: ["21", "21", "14"],
        2: ["14", "14", "21"],
    },
    "trajectory_reversed": {
        0: ["14", "14", "21"],
        1: ["21", "21", "14"],
        2: ["21", "21", "21"],
    },
}

CONDITION_ORDER = list(CONTEXT_BY_CONDITION)


def _find_item(data_rows: list[dict[str, Any]], item_id: str) -> dict[str, Any]:
    for row in data_rows:
        if str(row.get("id")) == item_id:
            return row
    raise ValueError(f"item_id not found: {item_id}")


def _format_previous_debate(context_answers_by_round: dict[int, list[str]]) -> str:
    lines = ["Previous debate answers:"]
    for round_index in sorted(context_answers_by_round):
        lines.append(f"Round {round_index}:")
        for agent_index, answer in enumerate(context_answers_by_round[round_index], start=1):
            lines.append(f"- Agent {agent_index}: {answer}")
        lines.append("")
    return "\n".join(lines).rstrip()


def build_question(original_question: str, context_answers_by_round: dict[int, list[str]]) -> str:
    problem = _problem_without_final_instruction(original_question)
    lines = ["Problem:", problem]

    if context_answers_by_round:
        lines.extend(["", _format_previous_debate(context_answers_by_round)])
        lines.extend(
            [
                "",
                "Now solve the original problem independently.",
                "The previous answers may be right or wrong.",
                "Return only the final answer inside <answer>...</answer>.",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "Now solve the original problem independently.",
                "Return only the final answer inside <answer>...</answer>.",
            ]
        )
    return "\n".join(lines)


def _prefix_answer_counts(context_answers_by_round: dict[int, list[str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for answers in context_answers_by_round.values():
        for answer in answers:
            counts[answer] = counts.get(answer, 0) + 1
    return dict(sorted(counts.items()))


def _latest_round_answers(context_answers_by_round: dict[int, list[str]]) -> list[str]:
    if not context_answers_by_round:
        return []
    return context_answers_by_round[max(context_answers_by_round)]


def _latest_round_majority(latest_round_answers: list[str]) -> str:
    if not latest_round_answers:
        return ""
    counts: dict[str, int] = {}
    for answer in latest_round_answers:
        counts[answer] = counts.get(answer, 0) + 1
    return max(sorted(counts), key=lambda answer: counts[answer])


def build_dataset(
    *,
    data_rows: list[dict[str, Any]],
    item_id: str,
    replicates: int,
    target_wrong_answer: str = DEFAULT_TARGET_WRONG_ANSWER,
) -> list[dict[str, Any]]:
    if replicates <= 0:
        raise ValueError("replicates must be positive")

    source = _find_item(data_rows, item_id)
    gold = str(source["answer"])
    original_metadata = source.get("metadata", {})

    rows: list[dict[str, Any]] = []
    for condition in CONDITION_ORDER:
        context = CONTEXT_BY_CONDITION[condition]
        latest_round_answers = _latest_round_answers(context)
        latest_majority = _latest_round_majority(latest_round_answers)
        condition_family = "baseline" if condition == "baseline_no_prefix" else (
            "single_round" if condition.startswith("single_round_") else "trajectory"
        )
        for replicate_index in range(replicates):
            rows.append(
                {
                    "id": f"{item_id}_{condition}_sample_{replicate_index:03d}",
                    "type": "gsm8k_synthetic_prefix_phase2",
                    "difficulty": source.get("difficulty", "unknown"),
                    "question": build_question(str(source["question"]), context),
                    "answer": gold,
                    "metadata": {
                        "base_item_id": item_id,
                        "condition": condition,
                        "replicate_index": replicate_index,
                        "gold": gold,
                        "target_wrong_answer": target_wrong_answer,
                        "synthetic_prefix": True,
                        "phase": PHASE,
                        "condition_family": condition_family,
                        "context_rounds_included": sorted(context),
                        "context_answers_by_round": {
                            str(key): value for key, value in sorted(context.items())
                        },
                        "prefix_answer_counts": _prefix_answer_counts(context),
                        "latest_round_answers": latest_round_answers,
                        "latest_round_majority": latest_majority,
                        "source_metadata": original_metadata,
                    },
                }
            )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a GSM8K synthetic-prefix phase 2 dataset.")
    parser.add_argument("--data", required=True, help="Input JSONL benchmark file containing the target item.")
    parser.add_argument("--out", required=True, help="Output JSONL dataset path.")
    parser.add_argument("--item-id", default="gsm8k_test_000234")
    parser.add_argument("--replicates", type=int, default=20)
    parser.add_argument("--target-wrong-answer", default=DEFAULT_TARGET_WRONG_ANSWER)
    args = parser.parse_args()

    rows = build_dataset(
        data_rows=load_jsonl(Path(args.data)),
        item_id=args.item_id,
        replicates=args.replicates,
        target_wrong_answer=args.target_wrong_answer,
    )
    write_jsonl(Path(args.out), rows)
    summary = {
        "conditions": CONDITION_ORDER,
        "item_id": args.item_id,
        "replicates": args.replicates,
        "rows": len(rows),
        "target_wrong_answer": args.target_wrong_answer,
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
