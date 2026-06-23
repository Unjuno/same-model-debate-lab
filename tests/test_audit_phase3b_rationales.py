from __future__ import annotations

import json
from pathlib import Path

from tools.audit_phase3b_rationales import audit_phase3b_rationales
from tools.build_synthetic_prefix_phase3_dataset import write_jsonl


def _phase3_rows() -> list[dict]:
    return [
        {
            "id": "gsm8k_test_000012__phase3_baseline_no_prefix_sample_000",
            "metadata": {"base_item_id": "gsm8k_test_000012", "gold": "13", "target_wrong_answer": "12"},
        },
        {
            "id": "gsm8k_test_000089__phase3_baseline_no_prefix_sample_000",
            "metadata": {"base_item_id": "gsm8k_test_000089", "gold": "24", "target_wrong_answer": "18"},
        },
    ]


def _rationales_payload() -> dict:
    return {
        "items": [
            {
                "item_id": "gsm8k_test_000012",
                "gold": "13",
                "target_wrong": "12",
                "weak_wrong_rationale": "A lower estimate slips under the final count.",
                "medium_wrong_rationale": "The count stays below the correct value.",
                "strong_wrong_rationale": "The lower estimate keeps the count below the correct value.",
            },
            {
                "item_id": "gsm8k_test_000089",
                "gold": "24",
                "target_wrong": "18",
                "weak_wrong_rationale": "A smaller bag count is implied.",
                "medium_wrong_rationale": "The missing quarter is not fully included.",
                "strong_wrong_rationale": "The missing quarter is not fully restored.",
            },
        ]
    }


def test_audit_passes_and_detects_leakage(tmp_path: Path) -> None:
    phase3 = tmp_path / "phase3.jsonl"
    write_jsonl(phase3, _phase3_rows())
    rationales = tmp_path / "rationales.json"
    rationales.write_text(json.dumps(_rationales_payload(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = audit_phase3b_rationales(phase3_data=phase3, rationales=rationales)
    assert report["ok"] is True
    assert report["items"] == 2

    bad = _rationales_payload()
    bad["items"][0]["strong_wrong_rationale"] = "final answer is 12"
    rationales.write_text(json.dumps(bad, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = audit_phase3b_rationales(phase3_data=phase3, rationales=rationales)
    assert report["ok"] is False
    assert any("final-answer leakage" in error for error in report["errors"])
