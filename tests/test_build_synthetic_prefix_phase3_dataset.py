from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.build_synthetic_prefix_phase2c_dataset import write_jsonl
from tools.build_synthetic_prefix_phase3_dataset import CONDITION_ORDER, build_dataset


def _phase2c_row(item_id: str, gold: str, wrong: str, condition: str) -> dict:
    return {
        "id": f"{item_id}__phase2c_answer_tag_{condition}_sample_000",
        "type": "gsm8k_synthetic_prefix_phase2c",
        "difficulty": "unknown",
        "question": "Problem:\nExample.\n\nNow solve the original problem independently.\nReturn only the final numeric answer. Do not include explanation.",
        "answer": gold,
        "metadata": {
            "base_item_id": item_id,
            "condition": condition,
            "prompt_format": "plain_final",
            "replicate_index": 0,
            "gold": gold,
            "target_wrong_answer": wrong,
            "target_wrong_source": "raw_lookup",
            "synthetic_prefix": True,
            "phase": "phase2c_prompt_format",
            "condition_family": "baseline",
            "source_metadata": {"source": "gsm8k/main"},
        },
    }


def _phase2c_data() -> list[dict]:
    rows = []
    for index, item_id in enumerate(["gsm8k_test_000001", "gsm8k_test_000002"]):
        gold = str(index + 10)
        wrong = str(index + 20)
        for condition in [
            "baseline_no_prefix",
            "single_round_correct_consensus",
            "single_round_wrong_consensus",
        ]:
            rows.append(_phase2c_row(item_id, gold, wrong, condition))
    return rows


def _make_rationales_path(tmp_path: Path) -> Path:
    path = tmp_path / "rationales.json"
    _write_rationales(path, _rationales())
    return path


def _rationales() -> dict:
    return {
        "phase": "phase3_rationale_contamination",
        "items": [
            {
                "base_item_id": "gsm8k_test_000001",
                "gold": "10",
                "target_wrong_answer": "20",
                "correct_rationale": "Add the two parts to get 10.",
                "wrong_rationale": "A smaller intermediate total suggests a value near twenty without stating it directly.",
            },
            {
                "base_item_id": "gsm8k_test_000002",
                "gold": "11",
                "target_wrong_answer": "21",
                "correct_rationale": "The arithmetic combines to 11.",
                "wrong_rationale": "The same setup pushes the total toward the low twenties in a rough estimate.",
            },
        ],
    }


def _write_rationales(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_builder_creates_expected_rows_and_metadata(tmp_path: Path) -> None:
    data_path = tmp_path / "phase2c.jsonl"
    write_jsonl(data_path, _phase2c_data())
    rationales_path = _make_rationales_path(tmp_path)
    rows = build_dataset(phase2c_data=_phase2c_data(), rationales_path=rationales_path, replicates=2)
    assert len(rows) == 2 * len(CONDITION_ORDER) * 2
    assert {row["metadata"]["condition"] for row in rows} == set(CONDITION_ORDER)
    assert len({row["id"] for row in rows}) == len(rows)
    baseline = next(row for row in rows if row["metadata"]["condition"] == "baseline_no_prefix")
    assert baseline["question"].count("Return only the final numeric answer. Do not include explanation.") == 1
    wrong_answer = next(row for row in rows if row["metadata"]["condition"] == "wrong_answer_only")
    assert "Previous agent response:" in wrong_answer["question"]
    assert "Explanation:" not in wrong_answer["question"]
    wrong_rationale = next(row for row in rows if row["metadata"]["condition"] == "wrong_rationale_only")
    assert "Previous agent explanation:" in wrong_rationale["question"]
    assert "Answer:" not in wrong_rationale["question"]
    combined = next(row for row in rows if row["metadata"]["condition"] == "wrong_answer_plus_rationale")
    assert "Answer:" in combined["question"]
    assert "Previous agent explanation:" in combined["question"]
    assert all(row["metadata"]["prompt_format"] == "plain_final" for row in rows)
    assert all(row["metadata"]["synthetic_prefix"] is True for row in rows)


def test_builder_rejects_mismatched_rationales_and_forbidden_phrases(tmp_path: Path) -> None:
    phase2c = _phase2c_data()
    bad = _rationales()
    bad["items"][0]["gold"] = "999"
    rationales_path = tmp_path / "bad.json"
    _write_rationales(rationales_path, bad)
    with pytest.raises(ValueError, match="mismatch"):
        build_dataset(phase2c_data=phase2c, rationales_path=rationales_path, replicates=1)

    bad = _rationales()
    bad["items"][0]["wrong_rationale"] = "The final answer is 20."
    _write_rationales(rationales_path, bad)
    with pytest.raises(ValueError, match="forbidden phrase"):
        build_dataset(phase2c_data=phase2c, rationales_path=rationales_path, replicates=1)

    bad = _rationales()
    bad["items"][0]["wrong_rationale"] = "word " * 81
    _write_rationales(rationales_path, bad)
    with pytest.raises(ValueError, match="too long"):
        build_dataset(phase2c_data=phase2c, rationales_path=rationales_path, replicates=1)
