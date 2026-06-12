from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CONTEXT_BY_CONDITION: dict[str, dict[int, list[str]]] = {
    "baseline_no_prefix": {},
    "prefix_correct_consensus_r0": {
        0: ["21", "21", "21"],
    },
    "prefix_mixed_correct_majority_r1": {
        0: ["21", "21", "21"],
        1: ["21", "21", "14"],
    },
    "prefix_wrong_majority_r2": {
        0: ["21", "21", "21"],
        1: ["21", "21", "14"],
        2: ["14", "14", "21"],
    },
    "prefix_wrong_consensus_r3": {
        0: ["21", "21", "21"],
        1: ["21", "21", "14"],
        2: ["14", "14", "21"],
        3: ["14", "14", "14"],
    },
}

CONDITION_ORDER = list(CONTEXT_BY_CONDITION)

DEFAULT_TARGET_WRONG_ANSWER = "14"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def _problem_without_final_instruction(question: str) -> str:
    instruction = "Return only the final answer inside <answer>...</answer>."
    text = question.strip()
    if text.endswith(instruction):
        text = text[: -len(instruction)].rstrip()
    return text


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
    return "\n".join(lines)


def _find_item(data_rows: list[dict[str, Any]], item_id: str) -> dict[str, Any]:
    for row in data_rows:
        if str(row.get("id")) == item_id:
            return row
    raise ValueError(f"item_id not found: {item_id}")


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
        for replicate_index in range(replicates):
            rows.append(
                {
                    "id": f"{item_id}_{condition}_sample_{replicate_index:03d}",
                    "type": "gsm8k_synthetic_prefix_continuation",
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
                        "context_rounds_included": sorted(context),
                        "context_answers_by_round": {
                            str(key): value for key, value in sorted(context.items())
                        },
                        "source_metadata": original_metadata,
                    },
                }
            )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a GSM8K synthetic-prefix continuation dataset.")
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
