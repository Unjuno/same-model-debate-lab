from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.build_synthetic_prefix_phase3_dataset import write_jsonl
from tools.build_synthetic_prefix_phase3b_dataset import (
    CONDITION_ORDER,
    FINAL_INSTRUCTION,
    build_dataset,
)


def _phase3_row(item_id: str, gold: str, wrong: str, *, item_group: str = "numeric_anchor_dominant") -> dict:
    return {
        "id": f"{item_id}__phase3_baseline_no_prefix_sample_000",
        "type": "gsm8k_synthetic_prefix_phase3",
        "question": "Problem:\nExample.\n\nNow solve the original problem independently.\nReturn only the final numeric answer.",
        "answer": gold,
        "metadata": {
            "base_item_id": item_id,
            "gold": gold,
            "target_wrong_answer": wrong,
            "item_group": item_group,
        },
    }


def _phase3_data() -> list[dict]:
    return [
        _phase3_row("gsm8k_test_000012", "13", "12", item_group="numeric_anchor_dominant"),
        _phase3_row("gsm8k_test_000089", "24", "18", item_group="numeric_anchor_dominant"),
    ]


def _rationales(tmp_path: Path) -> Path:
    payload = {
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
    path = tmp_path / "rationales.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def test_builder_creates_expected_rows_and_metadata(tmp_path: Path) -> None:
    data_path = tmp_path / "phase3.jsonl"
    write_jsonl(data_path, _phase3_data())
    rows = build_dataset(phase3_data=_phase3_data(), rationales_path=_rationales(tmp_path), replicates=2)
    assert len(rows) == 2 * len(CONDITION_ORDER) * 2
    assert {row["metadata"]["condition"] for row in rows} == set(CONDITION_ORDER)
    assert len({row["id"] for row in rows}) == len(rows)
    assert rows[0]["question"].count(FINAL_INSTRUCTION) == 1
    assert rows[0]["question"].endswith(FINAL_INSTRUCTION)
    metadata = rows[0]["metadata"]
    for key in [
        "phase",
        "base_item_id",
        "condition",
        "prompt_format",
        "rationale_strength",
        "item_group",
        "gold",
        "target_wrong",
        "replicate",
        "prefix_type",
        "prefix_contains_answer",
        "prefix_contains_rationale",
        "prefix_answer",
    ]:
        assert key in metadata
    assert all("<answer>" not in row["question"] for row in rows)


def test_builder_refuses_empty_selection(tmp_path: Path) -> None:
    rationales = _rationales(tmp_path)
    with pytest.raises(ValueError, match="no Phase 3 items selected"):
        build_dataset(phase3_data=[], rationales_path=rationales, replicates=1)


def test_real_dataset_is_non_empty() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    data_path = repo_root / "data/benchmarks/gsm8k_synthetic_prefix_phase3_rationale_9items.jsonl"
    assert data_path.exists()
    assert data_path.read_text(encoding="utf-8").strip()
