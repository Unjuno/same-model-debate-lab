from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.audit_phase3b_rationales import audit_phase3b_rationales
from tools.build_synthetic_prefix_phase3_dataset import write_jsonl


def _phase3_rows() -> list[dict]:
    return [
        {"id": "gsm8k_test_000012__phase3_baseline_no_prefix_sample_000", "metadata": {"base_item_id": "gsm8k_test_000012", "gold": "13", "target_wrong_answer": "12"}},
        {"id": "gsm8k_test_000089__phase3_baseline_no_prefix_sample_000", "metadata": {"base_item_id": "gsm8k_test_000089", "gold": "24", "target_wrong_answer": "18"}},
    ]


def _payload() -> dict:
    return {
        "items": [
            {
                "item_id": "gsm8k_test_000012",
                "gold": "13",
                "target_wrong": "12",
                "weak_wrong_rationale": "A smaller count is implied.",
                "medium_wrong_rationale": "Only the smaller count is carried through, so the total stays low.",
                "strong_wrong_rationale": "The smaller count is kept and the extra step is skipped, leaving the total low.",
            },
            {
                "item_id": "gsm8k_test_000089",
                "gold": "24",
                "target_wrong": "18",
                "weak_wrong_rationale": "A smaller bag count is implied.",
                "medium_wrong_rationale": "The missing portion is not fully restored, so the total stays low.",
                "strong_wrong_rationale": "The missing portion is treated as still absent, which keeps the total low.",
            },
        ]
    }


def test_audit_passes_clean_fixture(tmp_path: Path) -> None:
    phase3 = tmp_path / "phase3.jsonl"
    write_jsonl(phase3, _phase3_rows())
    rationales = tmp_path / "rationales.json"
    rationales.write_text(json.dumps(_payload(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = audit_phase3b_rationales(phase3_data=phase3, rationales=rationales)
    assert report["ok"] is True
    assert report["items"] == 2
    assert report["errors"] == []


@pytest.mark.parametrize(
    "mutator, pattern",
    [
        (lambda payload: payload["items"].pop(), "missing item_id"),
        (lambda payload: payload["items"].append({"item_id": "gsm8k_test_999999", "gold": "1", "target_wrong": "2", "weak_wrong_rationale": "x", "medium_wrong_rationale": "y", "strong_wrong_rationale": "z"}), "unknown item_id"),
        (lambda payload: payload["items"].append(payload["items"][0].copy()), "duplicate item_id"),
        (lambda payload: payload["items"][0].__setitem__("strong_wrong_rationale", "final answer is 12"), "final-answer leakage"),
        (lambda payload: payload["items"][0].__setitem__("weak_wrong_rationale", "<answer>12</answer>"), "forbidden tag"),
        (lambda payload: payload["items"][0].__setitem__("weak_wrong_rationale", "#### 12"), "forbidden tag"),
    ],
)
def test_audit_detects_invalid_conditions(tmp_path: Path, mutator, pattern: str) -> None:
    phase3 = tmp_path / "phase3.jsonl"
    write_jsonl(phase3, _phase3_rows())
    payload = _payload()
    mutator(payload)
    rationales = tmp_path / "rationales.json"
    rationales.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = audit_phase3b_rationales(phase3_data=phase3, rationales=rationales)
    assert report["ok"] is False
    assert any(pattern in error for error in report["errors"])


def test_audit_warns_on_bare_target_wrong_number(tmp_path: Path) -> None:
    phase3 = tmp_path / "phase3.jsonl"
    write_jsonl(phase3, _phase3_rows())
    payload = _payload()
    payload["items"][0]["weak_wrong_rationale"] = "The count briefly uses 12 before the last adjustment."
    rationales = tmp_path / "rationales.json"
    rationales.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = audit_phase3b_rationales(phase3_data=phase3, rationales=rationales)
    assert report["ok"] is True
    assert any("bare number" in warning for warning in report["warnings"])


def test_audit_rejects_identical_strengths(tmp_path: Path) -> None:
    phase3 = tmp_path / "phase3.jsonl"
    write_jsonl(phase3, _phase3_rows())
    payload = _payload()
    payload["items"][0]["medium_wrong_rationale"] = payload["items"][0]["weak_wrong_rationale"]
    rationales = tmp_path / "rationales.json"
    rationales.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = audit_phase3b_rationales(phase3_data=phase3, rationales=rationales)
    assert report["ok"] is False
    assert any("rationale strengths must differ" in error for error in report["errors"])
