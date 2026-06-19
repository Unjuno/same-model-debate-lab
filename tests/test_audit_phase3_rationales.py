from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.audit_phase3_rationales import audit_phase3_rationales
from tools.build_synthetic_prefix_phase2c_dataset import write_jsonl


def _phase2c_rows() -> list[dict]:
    rows = []
    pairs = [
        ("gsm8k_test_000012", "13", "12"),
        ("gsm8k_test_000089", "24", "18"),
    ]
    for item_id, gold, wrong in pairs:
        rows.append(
            {
                "id": item_id,
                "metadata": {
                    "base_item_id": item_id,
                    "gold": gold,
                    "target_wrong_answer": wrong,
                },
            }
        )
    return rows


def _rationales(items: list[dict]) -> dict:
    return {"phase": "phase3_rationale_contamination", "items": items}


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_audit_successful_clean_file(tmp_path: Path) -> None:
    phase2c = tmp_path / "phase2c.jsonl"
    write_jsonl(phase2c, _phase2c_rows())
    rationales = tmp_path / "rationales.json"
    _write(
        rationales,
        _rationales(
            [
                {
                    "base_item_id": "gsm8k_test_000012",
                    "gold": "13",
                    "target_wrong_answer": "12",
                    "correct_rationale": "After a small yearly gain, one more year puts him ahead of the cost.",
                    "wrong_rationale": "A rough yearly gain estimate keeps the result just above the lower estimate.",
                },
                {
                    "base_item_id": "gsm8k_test_000089",
                    "gold": "24",
                    "target_wrong_answer": "18",
                    "correct_rationale": "Twelve bags at two dollars each gives the gold total of 24.",
                    "wrong_rationale": "A smaller estimate undercounts the bags and lands below the correct total.",
                },
            ]
        ),
    )
    report = audit_phase3_rationales(phase2c_data=phase2c, rationales=rationales)
    assert report["ok"] is True
    assert report["errors"] == []
    assert report["items"] == 2


@pytest.mark.parametrize(
    "mutator, message",
    [
        (lambda items: items[:1], "item coverage"),
        (lambda items: items + [{"base_item_id": "extra", "gold": "1", "target_wrong_answer": "2", "correct_rationale": "ok", "wrong_rationale": "ok"}], "extra item"),
    ],
)
def test_audit_missing_and_extra_items(tmp_path: Path, mutator, message) -> None:
    phase2c = tmp_path / "phase2c.jsonl"
    write_jsonl(phase2c, _phase2c_rows())
    items = [
        {
            "base_item_id": "gsm8k_test_000012",
            "gold": "13",
            "target_wrong_answer": "12",
            "correct_rationale": "Twelve plus one.",
            "wrong_rationale": "Close to twelve.",
        },
        {
            "base_item_id": "gsm8k_test_000089",
            "gold": "24",
            "target_wrong_answer": "18",
            "correct_rationale": "Twelve times two.",
            "wrong_rationale": "Undercounted.",
        },
    ]
    rationales = tmp_path / "rationales.json"
    _write(rationales, _rationales(mutator(items)))
    report = audit_phase3_rationales(phase2c_data=phase2c, rationales=rationales)
    assert report["ok"] is False
    assert any(message in error for error in report["errors"])


def test_audit_detects_field_and_phrase_errors(tmp_path: Path) -> None:
    phase2c = tmp_path / "phase2c.jsonl"
    write_jsonl(phase2c, _phase2c_rows())
    rationales = tmp_path / "rationales.json"
    _write(
        rationales,
        _rationales(
            [
                {
                    "base_item_id": "gsm8k_test_000012",
                    "gold": "999",
                    "target_wrong_answer": "12",
                    "correct_rationale": "This answer is 12.",
                    "wrong_rationale": "Therefore 12.",
                },
                {
                    "base_item_id": "gsm8k_test_000089",
                    "gold": "24",
                    "target_wrong_answer": "18",
                    "correct_rationale": "word " * 81,
                    "wrong_rationale": "<answer>18</answer>",
                },
            ]
        ),
    )
    report = audit_phase3_rationales(phase2c_data=phase2c, rationales=rationales)
    assert report["ok"] is False
    assert any("gold mismatch" in error for error in report["errors"])
    assert any("target-wrong leakage" in error for error in report["errors"])
    assert any("forbidden final-answer phrase" in error for error in report["errors"])
    assert any("too long" in error for error in report["errors"])
    assert any("answer tag" in error for error in report["errors"])
