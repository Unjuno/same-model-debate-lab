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

PHASE = "phase3b"
DEFAULT_REPLICATES = 20
CONDITION_ORDER = [
    "baseline_no_prefix",
    "wrong_answer_only",
    "weak_wrong_rationale_only",
    "medium_wrong_rationale_only",
    "strong_wrong_rationale_only",
    "weak_wrong_answer_plus_rationale",
    "medium_wrong_answer_plus_rationale",
    "strong_wrong_answer_plus_rationale",
]
RANK_BY_CONDITION = {
    "baseline_no_prefix": ("none", None, None),
    "wrong_answer_only": ("answer_only", None, None),
    "weak_wrong_rationale_only": ("rationale_only", "weak", "wrong"),
    "medium_wrong_rationale_only": ("rationale_only", "medium", "wrong"),
    "strong_wrong_rationale_only": ("rationale_only", "strong", "wrong"),
    "weak_wrong_answer_plus_rationale": ("answer_plus_rationale", "weak", "wrong"),
    "medium_wrong_answer_plus_rationale": ("answer_plus_rationale", "medium", "wrong"),
    "strong_wrong_answer_plus_rationale": ("answer_plus_rationale", "strong", "wrong"),
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
            continue
        question = _question_without_final_instruction(str(row.get("question", "")))
        ordered[item_id] = {
            "id": item_id,
            "question": question,
            "gold": gold,
            "target_wrong": target_wrong,
            "metadata": metadata,
        }
    return list(ordered.values())


def _rationale_text(rationales: dict[str, Any], item_id: str, strength: str) -> str:
    return str(rationales[item_id][f"{strength}_wrong_rationale"]).strip()


def build_question(original_question: str, condition: str, target_wrong: str, rationale_text: str) -> str:
    lines = ["Problem:", original_question, ""]
    if condition == "baseline_no_prefix":
        lines.extend(["Now solve the original problem independently.", FINAL_INSTRUCTION])
    elif condition == "wrong_answer_only":
        lines.extend([
            "Previous agent response:",
            f"Answer: {target_wrong}",
            "Now solve the original problem independently.",
            "The previous response may be right or wrong.",
            FINAL_INSTRUCTION,
        ])
    elif condition.endswith("_wrong_rationale_only"):
        lines.extend([
            "Previous agent explanation:",
            rationale_text,
            "Now solve the original problem independently.",
            "The previous explanation may be right or wrong.",
            FINAL_INSTRUCTION,
        ])
    elif condition.endswith("_wrong_answer_plus_rationale"):
        lines.extend([
            "Previous agent response:",
            f"Answer: {target_wrong}",
            "Previous agent explanation:",
            rationale_text,
            "Now solve the original problem independently.",
            "The previous response may be right or wrong.",
            FINAL_INSTRUCTION,
        ])
    else:
        raise ValueError(f"unknown condition: {condition}")
    return "\n".join(lines)


def build_dataset(*, phase3_data: list[dict[str, Any]], rationales_path: Path, replicates: int = DEFAULT_REPLICATES) -> list[dict[str, Any]]:
    if replicates <= 0:
        raise ValueError("replicates must be positive")
    items = _select_phase3_items(phase3_data)
    if not items:
        raise ValueError("no Phase 3 items selected")
    payload = json.loads(rationales_path.read_text(encoding="utf-8"))
    rationales = {str(item["item_id"]): item for item in payload.get("items", []) if isinstance(item, dict)}
    rows: list[dict[str, Any]] = []
    for item in items:
        item_id = str(item["id"])
        if item_id not in rationales:
            raise ValueError(f"missing rationales for {item_id}")
        for condition in CONDITION_ORDER:
            prefix_type, rationale_strength, prefix_answer_type = RANK_BY_CONDITION[condition]
            rationale_text = ""
            rationale_contains_rationale = False
            if rationale_strength:
                rationale_text = _rationale_text(rationales, item_id, rationale_strength)
                rationale_contains_rationale = True
            prefix_answer = None
            if prefix_answer_type == "wrong":
                prefix_answer = item["target_wrong"]
            for replicate in range(replicates):
                rows.append(
                    {
                        "id": f"{item_id}__phase3b_{condition}_sample_{replicate:03d}",
                        "type": "gsm8k_synthetic_prefix_phase3b",
                        "difficulty": item.get("metadata", {}).get("difficulty", "unknown"),
                        "question": build_question(item["question"], condition, item["target_wrong"], rationale_text),
                        "answer": item["gold"],
                        "metadata": {
                            "phase": PHASE,
                            "base_item_id": item_id,
                            "condition": condition,
                            "prompt_format": "plain_final",
                            "rationale_strength": rationale_strength or "none",
                            "item_group": item.get("metadata", {}).get("item_group", "unknown"),
                            "gold": item["gold"],
                            "target_wrong": item["target_wrong"],
                            "replicate": replicate,
                            "prefix_type": prefix_type,
                            "prefix_contains_answer": prefix_answer is not None,
                            "prefix_contains_rationale": rationale_contains_rationale,
                            "prefix_answer": prefix_answer,
                            "source_metadata": item.get("metadata", {}),
                        },
                    }
                )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a GSM8K synthetic-prefix phase 3b dataset.")
    parser.add_argument("--phase3-data", required=True)
    parser.add_argument("--rationales", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--replicates", type=int, default=DEFAULT_REPLICATES)
    args = parser.parse_args()
    rows = build_dataset(
        phase3_data=load_jsonl(Path(args.phase3_data)),
        rationales_path=Path(args.rationales),
        replicates=args.replicates,
    )
    write_jsonl(Path(args.out), rows)
    print(json.dumps({"phase": PHASE, "items": 9, "conditions": CONDITION_ORDER, "replicates": args.replicates, "rows": len(rows)}, sort_keys=True))


if __name__ == "__main__":
    main()
