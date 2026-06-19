from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_synthetic_prefix_phase2c_dataset import load_jsonl  # noqa: E402
from tools.select_partial_correct_items import normalize_answer  # noqa: E402

MAX_WORDS = 80
REQUIRED_FIELDS = {
    "base_item_id",
    "gold",
    "target_wrong_answer",
    "correct_rationale",
    "wrong_rationale",
}


def _word_count(text: str) -> int:
    return len(text.split())


def _phase2c_items(rows: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    items: dict[str, dict[str, str]] = {}
    for row in rows:
        metadata = row.get("metadata", {})
        if not isinstance(metadata, dict):
            continue
        item_id = str(metadata.get("base_item_id", ""))
        if not item_id or item_id in items:
            continue
        gold = normalize_answer(metadata.get("gold", ""))
        target_wrong = normalize_answer(metadata.get("target_wrong_answer", ""))
        if gold and target_wrong:
            items[item_id] = {"gold": gold, "target_wrong_answer": target_wrong}
    return items


def audit_phase3_rationales(*, phase2c_data: Path, rationales: Path, max_words: int = MAX_WORDS, fail_on_correct_leakage: bool = True) -> dict[str, Any]:
    phase2c_rows = load_jsonl(phase2c_data)
    phase2c_items = _phase2c_items(phase2c_rows)
    payload = json.loads(rationales.read_text(encoding="utf-8"))
    rationale_items = payload.get("items", [])
    if not isinstance(rationale_items, list):
        raise ValueError("rationale items must be a list")

    errors: list[str] = []
    warnings: list[str] = []
    seen: dict[str, dict[str, Any]] = {}
    if len(rationale_items) != len(phase2c_items):
        errors.append("item coverage count mismatch")

    for item in rationale_items:
        if not isinstance(item, dict):
            errors.append("each rationale item must be a dict")
            continue
        missing = REQUIRED_FIELDS - set(item)
        if missing:
            errors.append(f"missing fields for {item.get('base_item_id', '')}: {', '.join(sorted(missing))}")
            continue
        base_item_id = str(item["base_item_id"])
        if base_item_id in seen:
            errors.append(f"duplicate item {base_item_id}")
            continue
        seen[base_item_id] = item
        if base_item_id not in phase2c_items:
            errors.append(f"extra item {base_item_id}")
            continue

        gold = normalize_answer(item["gold"])
        target_wrong = normalize_answer(item["target_wrong_answer"])
        phase2c_gold = phase2c_items[base_item_id]["gold"]
        phase2c_wrong = phase2c_items[base_item_id]["target_wrong_answer"]
        if gold != phase2c_gold:
            errors.append(f"gold mismatch for {base_item_id}")
        if target_wrong != phase2c_wrong:
            errors.append(f"target wrong mismatch for {base_item_id}")

        correct = str(item["correct_rationale"]).strip()
        wrong = str(item["wrong_rationale"]).strip()
        if _word_count(correct) > max_words:
            errors.append(f"correct rationale too long for {base_item_id}")
        if _word_count(wrong) > max_words:
            errors.append(f"wrong rationale too long for {base_item_id}")
        if "<answer>" in correct.lower() or "</answer>" in correct.lower():
            errors.append(f"answer tag found in correct rationale for {base_item_id}")
        if "<answer>" in wrong.lower() or "</answer>" in wrong.lower():
            errors.append(f"answer tag found in wrong rationale for {base_item_id}")

        forbidden_phrases = [
            f"answer is {phase2c_wrong.lower()}",
            f"final answer is {phase2c_wrong.lower()}",
            f"therefore {phase2c_wrong.lower()}",
            f"so the answer is {phase2c_wrong.lower()}",
            f"gives {phase2c_wrong.lower()}",
        ]
        lowered_wrong = wrong.lower()
        for phrase in forbidden_phrases:
            if phrase in lowered_wrong:
                errors.append(f"forbidden final-answer phrase for {base_item_id}: {phrase}")
                break

        if phase2c_wrong and phase2c_wrong in correct:
            message = f"target-wrong leakage in correct rationale for {base_item_id}"
            if fail_on_correct_leakage:
                errors.append(message)
            else:
                warnings.append(message)

        if phase2c_gold and phase2c_gold not in correct:
            warnings.append(f"gold not referenced in correct rationale for {base_item_id}")

    missing_items = sorted(set(phase2c_items) - set(seen))
    for item_id in missing_items:
        errors.append(f"missing item {item_id}")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "items": len(phase2c_items),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit Phase 3 rationales against the Phase 2c source set.")
    parser.add_argument("--phase2c-data", required=True)
    parser.add_argument("--rationales", required=True)
    parser.add_argument("--max-words", type=int, default=MAX_WORDS)
    parser.add_argument("--warn-only-correct-leakage", action="store_true")
    args = parser.parse_args()
    report = audit_phase3_rationales(
        phase2c_data=Path(args.phase2c_data),
        rationales=Path(args.rationales),
        max_words=args.max_words,
        fail_on_correct_leakage=not args.warn_only_correct_leakage,
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    raise SystemExit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
