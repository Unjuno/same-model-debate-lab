from __future__ import annotations

import argparse
import json
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_synthetic_prefix_continuation_dataset import (  # noqa: E402
    _problem_without_final_instruction,
    write_jsonl,
)
from tools.build_synthetic_prefix_phase3_dataset import load_jsonl  # noqa: E402
from tools.select_partial_correct_items import normalize_answer  # noqa: E402

PHASE = "phase3c"
DEFAULT_REPLICATES = 20
CONDITION_ORDER = [
    "baseline_no_prefix",
    "wrong_answer_labeled",
    "wrong_number_unlabeled",
    "wrong_number_in_explanation",
    "wrong_number_as_intermediate",
    "wrong_answer_with_uncertainty",
    "wrong_answer_marked_possibly_wrong",
]

ANCHOR_FORMAT_BY_CONDITION = {
    "baseline_no_prefix": ("none", False, None, False, False),
    "wrong_answer_labeled": ("answer_labeled", True, "target_wrong", False, True),
    "wrong_number_unlabeled": ("number_unlabeled", True, "target_wrong", False, False),
    "wrong_number_in_explanation": ("number_in_explanation", True, "target_wrong", False, True),
    "wrong_number_as_intermediate": ("number_as_intermediate", True, "target_wrong", False, True),
    "wrong_answer_with_uncertainty": ("answer_with_uncertainty", True, "target_wrong", True, False),
    "wrong_answer_marked_possibly_wrong": ("answer_marked_possibly_wrong", True, "target_wrong", False, True),
}
FINAL_INSTRUCTION = "Return only the final numeric answer."


def _question_without_final_instruction(question: str) -> str:
    text = question.strip()
    if text.startswith("Problem:"):
        text = text[len("Problem:") :].lstrip()
    marker = "\n\nNow solve the original problem independently."
    if marker in text:
        text = text.split(marker, 1)[0].rstrip()
    instruction = "\nReturn only the final numeric answer."
    if text.endswith(instruction):
        text = text[: -len(instruction)].rstrip()
    return _problem_without_final_instruction(text)


def _select_phase3_items(phase3_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered: OrderedDict[str, dict[str, Any]] = OrderedDict()
    for row in phase3_rows:
        metadata = row.get("metadata", {})
        if not isinstance(metadata, dict):
            continue
        item_id = str(metadata.get("base_item_id", ""))
        if not item_id or item_id in ordered:
            continue
        gold = normalize_answer(metadata.get("gold", row.get("answer", "")))
        target_wrong = normalize_answer(metadata.get("target_wrong_answer", ""))
        if not gold or not target_wrong:
            raise ValueError(f"missing gold or target_wrong for {item_id}")
        ordered[item_id] = {
            "id": item_id,
            "question": _question_without_final_instruction(str(row.get("question", ""))),
            "gold": gold,
            "target_wrong": target_wrong,
            "metadata": metadata,
        }
    return list(ordered.values())


def build_question(original_question: str, condition: str, target_wrong: str) -> str:
    lines = ["Problem:", original_question, ""]
    if condition == "baseline_no_prefix":
        lines.extend(["Now solve the original problem independently.", FINAL_INSTRUCTION])
    elif condition == "wrong_answer_labeled":
        lines.extend([
            "Previous agent response:",
            f"Answer: {target_wrong}",
            "Now solve the original problem independently.",
            "The previous response may be right or wrong.",
            FINAL_INSTRUCTION,
        ])
    elif condition == "wrong_number_unlabeled":
        lines.extend([
            "Previous context:",
            target_wrong,
            "Now solve the original problem independently.",
            FINAL_INSTRUCTION,
        ])
    elif condition == "wrong_number_in_explanation":
        lines.extend([
            "Previous explanation note:",
            f"The earlier reasoning used {target_wrong} while working through the problem.",
            "Now solve the original problem independently.",
            "The previous explanation may be right or wrong.",
            FINAL_INSTRUCTION,
        ])
    elif condition == "wrong_number_as_intermediate":
        lines.extend([
            "Previous calculation note:",
            f"One intermediate value considered earlier was {target_wrong}.",
            "Now solve the original problem independently.",
            "The previous calculation note may be right or wrong.",
            FINAL_INSTRUCTION,
        ])
    elif condition == "wrong_answer_with_uncertainty":
        lines.extend([
            "Previous agent response:",
            f"The agent guessed {target_wrong}, but was uncertain.",
            "Now solve the original problem independently.",
            FINAL_INSTRUCTION,
        ])
    elif condition == "wrong_answer_marked_possibly_wrong":
        lines.extend([
            "Previous agent response:",
            f"Answer: {target_wrong}",
            "Note: This previous answer may be incorrect.",
            "Now solve the original problem independently.",
            FINAL_INSTRUCTION,
        ])
    else:
        raise ValueError(f"unknown condition: {condition}")
    return "\n".join(lines)


def build_dataset(*, phase3_data: list[dict[str, Any]], replicates: int = DEFAULT_REPLICATES) -> list[dict[str, Any]]:
    if replicates <= 0:
        raise ValueError("replicates must be positive")
    items = _select_phase3_items(phase3_data)
    if not items:
        raise ValueError("no Phase 3 items selected")
    rows: list[dict[str, Any]] = []
    for item in items:
        item_id = str(item["id"])
        for condition in CONDITION_ORDER:
            anchor_format, prefix_contains_number, prefix_number_mode, prefix_contains_uncertainty, prefix_contains_warning = ANCHOR_FORMAT_BY_CONDITION[condition]
            for replicate in range(replicates):
                prefix_number = None if prefix_number_mode is None else item["target_wrong"]
                rows.append(
                    {
                        "id": f"{item_id}__phase3c_{condition}_sample_{replicate:03d}",
                        "type": "gsm8k_synthetic_prefix_phase3c",
                        "question": build_question(item["question"], condition, item["target_wrong"]),
                        "answer": item["gold"],
                        "metadata": {
                            "phase": PHASE,
                            "base_item_id": item_id,
                            "condition": condition,
                            "prompt_format": "plain_final",
                            "anchor_format": anchor_format,
                            "item_group": item.get("metadata", {}).get("item_group", "unknown"),
                            "gold": item["gold"],
                            "target_wrong": item["target_wrong"],
                            "replicate": replicate,
                            "prefix_contains_number": prefix_contains_number,
                            "prefix_number": prefix_number,
                            "prefix_contains_answer_label": condition in {
                                "wrong_answer_labeled",
                                "wrong_answer_with_uncertainty",
                                "wrong_answer_marked_possibly_wrong",
                            },
                            "prefix_contains_uncertainty": prefix_contains_uncertainty,
                            "prefix_contains_warning": prefix_contains_warning,
                            "source_metadata": item.get("metadata", {}),
                        },
                    }
                )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a GSM8K synthetic-prefix phase 3c dataset.")
    parser.add_argument("--phase3-data", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--replicates", type=int, default=DEFAULT_REPLICATES)
    args = parser.parse_args()
    rows = build_dataset(phase3_data=load_jsonl(Path(args.phase3_data)), replicates=args.replicates)
    write_jsonl(Path(args.out), rows)
    print(json.dumps({"phase": PHASE, "items": 9, "conditions": CONDITION_ORDER, "replicates": args.replicates, "rows": len(rows)}, sort_keys=True))


if __name__ == "__main__":
    main()
