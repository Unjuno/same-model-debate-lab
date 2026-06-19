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

from tools.build_synthetic_prefix_phase2c_dataset import (  # noqa: E402
    _problem_without_final_instruction,
    load_jsonl,
    write_jsonl,
)
from tools.select_partial_correct_items import normalize_answer  # noqa: E402

PHASE = "phase3_rationale_contamination"
DEFAULT_REPLICATES = 20
CONDITION_ORDER = [
    "baseline_no_prefix",
    "wrong_answer_only",
    "wrong_rationale_only",
    "wrong_answer_plus_rationale",
    "correct_answer_only",
    "correct_answer_plus_rationale",
]
MAX_RATIONALE_WORDS = 80
FINAL_INSTRUCTION = "Return only the final numeric answer. Do not include explanation."


def _word_count(text: str) -> int:
    return len(text.split())


def _validate_rationale_text(text: str, *, target_wrong_answer: str) -> None:
    lowered = text.lower()
    if "<answer>" in lowered or "</answer>" in lowered:
        raise ValueError("rationale must not contain <answer> tags")
    forbidden_phrases = [
        f"answer is {target_wrong_answer.lower()}",
        f"final answer is {target_wrong_answer.lower()}",
    ]
    for phrase in forbidden_phrases:
        if phrase in lowered:
            raise ValueError(f"rationale contains forbidden phrase: {phrase}")
    if _word_count(text) > MAX_RATIONALE_WORDS:
        raise ValueError("rationale is too long")


def _load_rationales(path: Path) -> dict[str, dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("phase") != PHASE:
        raise ValueError("unexpected rationale file phase")
    items = payload.get("items", [])
    if not isinstance(items, list):
        raise ValueError("rationale file items must be a list")
    rationales: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("each rationale item must be a dict")
        base_item_id = str(item.get("base_item_id", ""))
        if not base_item_id:
            raise ValueError("missing base_item_id")
        if base_item_id in rationales:
            raise ValueError(f"duplicate rationale for {base_item_id}")
        correct = item.get("correct_rationale")
        wrong = item.get("wrong_rationale")
        gold = normalize_answer(item.get("gold", ""))
        target_wrong = normalize_answer(item.get("target_wrong_answer", ""))
        if not isinstance(correct, str) or not correct.strip():
            raise ValueError(f"missing correct_rationale for {base_item_id}")
        if not isinstance(wrong, str) or not wrong.strip():
            raise ValueError(f"missing wrong_rationale for {base_item_id}")
        _validate_rationale_text(correct, target_wrong_answer=target_wrong or "x")
        _validate_rationale_text(wrong, target_wrong_answer=target_wrong or "x")
        rationales[base_item_id] = {
            "base_item_id": base_item_id,
            "gold": gold,
            "target_wrong_answer": target_wrong,
            "correct_rationale": correct.strip(),
            "wrong_rationale": wrong.strip(),
        }
    return rationales


def _select_phase2c_items(phase2c_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered: OrderedDict[str, dict[str, Any]] = OrderedDict()
    for row in phase2c_rows:
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
        ordered[item_id] = {
            "id": item_id,
            "question": str(row.get("question", "")),
            "answer": gold,
            "metadata": metadata,
            "target_wrong_answer": target_wrong,
            "target_wrong_source": str(metadata.get("target_wrong_source", "raw_lookup")),
        }
    return list(ordered.values())


def _strip_final_instruction(question: str) -> str:
    text = question.strip()
    if text.endswith(FINAL_INSTRUCTION):
        text = text[: -len(FINAL_INSTRUCTION)].rstrip()
    return _problem_without_final_instruction(text)


def build_question(original_question: str, condition: str, *, gold: str, target_wrong_answer: str, correct_rationale: str, wrong_rationale: str) -> str:
    problem = _strip_final_instruction(original_question)
    lines = ["Problem:", problem, ""]
    if condition == "baseline_no_prefix":
        lines.extend(["Now solve the original problem independently.", FINAL_INSTRUCTION])
    elif condition == "wrong_answer_only":
        lines.extend([
            "Previous agent response:",
            f"Answer: {target_wrong_answer}",
            "Now solve the original problem independently.",
            "The previous response may be right or wrong.",
            FINAL_INSTRUCTION,
        ])
    elif condition == "wrong_rationale_only":
        lines.extend([
            "Previous agent explanation:",
            wrong_rationale,
            "Now solve the original problem independently.",
            "The previous explanation may be right or wrong.",
            FINAL_INSTRUCTION,
        ])
    elif condition == "wrong_answer_plus_rationale":
        lines.extend([
            "Previous agent response:",
            f"Answer: {target_wrong_answer}",
            "Previous agent explanation:",
            wrong_rationale,
            "Now solve the original problem independently.",
            "The previous response may be right or wrong.",
            FINAL_INSTRUCTION,
        ])
    elif condition == "correct_answer_only":
        lines.extend([
            "Previous agent response:",
            f"Answer: {gold}",
            "Now solve the original problem independently.",
            "The previous response may be right or wrong.",
            FINAL_INSTRUCTION,
        ])
    elif condition == "correct_answer_plus_rationale":
        lines.extend([
            "Previous agent response:",
            f"Answer: {gold}",
            "Previous agent explanation:",
            correct_rationale,
            "Now solve the original problem independently.",
            "The previous response may be right or wrong.",
            FINAL_INSTRUCTION,
        ])
    else:
        raise ValueError(f"unknown condition: {condition}")
    return "\n".join(lines)


def build_dataset(*, phase2c_data: list[dict[str, Any]], rationales_path: Path, replicates: int = DEFAULT_REPLICATES) -> list[dict[str, Any]]:
    if replicates <= 0:
        raise ValueError("replicates must be positive")
    items = _select_phase2c_items(phase2c_data)
    rationales = _load_rationales(rationales_path)
    selected_ids = [str(item["id"]) for item in items]
    missing = [item_id for item_id in selected_ids if item_id not in rationales]
    if missing:
        raise ValueError(f"missing rationales for: {', '.join(missing)}")

    rows: list[dict[str, Any]] = []
    for item in items:
        item_id = str(item["id"])
        gold = normalize_answer(item["answer"])
        target_wrong = normalize_answer(item["target_wrong_answer"])
        rationale = rationales[item_id]
        if normalize_answer(rationale["gold"]) != gold or normalize_answer(rationale["target_wrong_answer"]) != target_wrong:
            raise ValueError(f"rationale metadata mismatch for {item_id}")
        for condition in CONDITION_ORDER:
            if condition == "baseline_no_prefix":
                condition_family = "baseline"
                prefix_answer = None
                rationale_type = "none"
                rationale_contains_answer = False
            elif "wrong" in condition:
                condition_family = "answer_only" if condition.endswith("_only") else "answer_plus_rationale"
                prefix_answer = target_wrong if "answer" in condition else None
                rationale_type = "wrong" if "rationale" in condition else "none"
                rationale_contains_answer = bool("rationale" in condition)
            else:
                condition_family = "answer_only" if condition.endswith("_only") else "answer_plus_rationale"
                prefix_answer = gold if "answer" in condition else None
                rationale_type = "correct" if "rationale" in condition else "none"
                rationale_contains_answer = bool("rationale" in condition)

            for replicate_index in range(replicates):
                question = build_question(
                    str(item["question"]),
                    condition,
                    gold=gold,
                    target_wrong_answer=target_wrong,
                    correct_rationale=rationale["correct_rationale"],
                    wrong_rationale=rationale["wrong_rationale"],
                )
                rows.append(
                    {
                        "id": f"{item_id}__phase3_{condition}_sample_{replicate_index:03d}",
                        "type": "gsm8k_synthetic_prefix_phase3",
                        "difficulty": item.get("difficulty", "unknown"),
                        "question": question,
                        "answer": gold,
                        "metadata": {
                            "base_item_id": item_id,
                            "condition": condition,
                            "replicate_index": replicate_index,
                            "gold": gold,
                            "target_wrong_answer": target_wrong,
                            "target_wrong_source": item["target_wrong_source"],
                            "synthetic_prefix": True,
                            "phase": PHASE,
                            "condition_family": condition_family,
                            "prompt_format": "plain_final",
                            "rationale_id": item_id,
                            "rationale_contains_answer": rationale_contains_answer,
                            "rationale_type": rationale_type,
                            "prefix_answer": prefix_answer,
                            "source_metadata": item["metadata"],
                        },
                    }
                )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a GSM8K synthetic-prefix phase 3 dataset.")
    parser.add_argument("--phase2c-data", required=True)
    parser.add_argument("--rationales", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--replicates", type=int, default=DEFAULT_REPLICATES)
    args = parser.parse_args()

    rows = build_dataset(
        phase2c_data=load_jsonl(Path(args.phase2c_data)),
        rationales_path=Path(args.rationales),
        replicates=args.replicates,
    )
    write_jsonl(Path(args.out), rows)
    selected_item_ids = sorted({str(row["metadata"]["base_item_id"]) for row in rows})
    summary = {
        "phase": PHASE,
        "items": len(selected_item_ids),
        "conditions": CONDITION_ORDER,
        "replicates": args.replicates,
        "rows": len(rows),
        "selected_item_ids": selected_item_ids,
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
