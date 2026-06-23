from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_synthetic_prefix_phase3_dataset import load_jsonl  # noqa: E402
from tools.select_partial_correct_items import normalize_answer  # noqa: E402

REQUIRED = {"item_id", "gold", "target_wrong", "weak_wrong_rationale", "medium_wrong_rationale", "strong_wrong_rationale"}


def _load_phase3_items(path: Path) -> dict[str, dict[str, str]]:
    rows = load_jsonl(path)
    items: dict[str, dict[str, str]] = {}
    for row in rows:
        metadata = row.get("metadata", {})
        if not isinstance(metadata, dict):
            continue
        item_id = str(metadata.get("base_item_id", ""))
        if not item_id:
            continue
        if item_id not in items:
            items[item_id] = {
                "gold": normalize_answer(metadata.get("gold", "")),
                "target_wrong": normalize_answer(metadata.get("target_wrong_answer", "")),
            }
    return items


def audit_phase3b_rationales(*, phase3_data: Path, rationales: Path) -> dict[str, Any]:
    phase3_items = _load_phase3_items(phase3_data)
    payload = json.loads(rationales.read_text(encoding="utf-8"))
    items = payload.get("items", [])
    errors: list[str] = []
    warnings: list[str] = []
    seen: set[str] = set()
    if len(items) != len(phase3_items):
        errors.append("item count mismatch")
    for item in items:
        if not isinstance(item, dict):
            errors.append("item is not a dict")
            continue
        missing = REQUIRED - set(item)
        if missing:
            errors.append(f"missing fields for {item.get('item_id', '')}: {', '.join(sorted(missing))}")
            continue
        item_id = str(item["item_id"])
        if item_id in seen:
            errors.append(f"duplicate item_id {item_id}")
            continue
        seen.add(item_id)
        if item_id not in phase3_items:
            errors.append(f"unknown item_id {item_id}")
            continue
        if normalize_answer(item["gold"]) != phase3_items[item_id]["gold"]:
            errors.append(f"gold mismatch for {item_id}")
        if normalize_answer(item["target_wrong"]) != phase3_items[item_id]["target_wrong"]:
            errors.append(f"target_wrong mismatch for {item_id}")
        texts = [str(item[k]).strip() for k in ("weak_wrong_rationale", "medium_wrong_rationale", "strong_wrong_rationale")]
        if any(not text for text in texts):
            errors.append(f"empty rationale for {item_id}")
        if len(set(texts)) != 3:
            errors.append(f"rationale strengths must differ for {item_id}")
        for text in texts:
            lowered = text.lower()
            if "<answer>" in lowered or "</answer>" in lowered or "####" in lowered:
                errors.append(f"forbidden tag in {item_id}")
                break
            if len(text.split()) > 80:
                errors.append(f"rationale too long for {item_id}")
                break
        target = normalize_answer(item["target_wrong"])
        for text in texts:
            lowered = text.lower()
            forbidden = [
                f"answer is {target}",
                f"final answer is {target}",
                f"therefore the answer is {target}",
                f"<answer>{target}</answer>",
                f"#### {target}",
            ]
            if any(phrase in lowered for phrase in forbidden):
                errors.append(f"final-answer leakage for {item_id}")
                break
            if target and target in text:
                warnings.append(f"target_wrong appears as bare number for {item_id}")
    missing_items = sorted(set(phase3_items) - seen)
    for item_id in missing_items:
        errors.append(f"missing item_id {item_id}")
    return {"ok": not errors, "items": len(phase3_items), "errors": errors, "warnings": warnings}


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit Phase 3b rationales.")
    parser.add_argument("--phase3-data", required=True)
    parser.add_argument("--rationales", required=True)
    args = parser.parse_args()
    report = audit_phase3b_rationales(phase3_data=Path(args.phase3_data), rationales=Path(args.rationales))
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
