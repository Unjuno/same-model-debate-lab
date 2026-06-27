from __future__ import annotations

from pathlib import Path

import pytest

from tools.build_synthetic_prefix_phase3c_dataset import (
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
        _phase3_row("gsm8k_test_000089", "24", "18", item_group="rationale_corrective_reversal"),
    ]


def test_builder_creates_expected_rows_and_metadata(tmp_path: Path) -> None:
    rows = build_dataset(phase3_data=_phase3_data(), replicates=2)
    assert len(rows) == 2 * len(CONDITION_ORDER) * 2
    assert {row["metadata"]["condition"] for row in rows} == set(CONDITION_ORDER)
    assert len({row["id"] for row in rows}) == len(rows)
    assert all(row["question"].endswith(FINAL_INSTRUCTION) for row in rows)
    assert all("<answer>" not in row["question"] for row in rows)
    assert all("####" not in row["question"] for row in rows)
    metadata = rows[0]["metadata"]
    for key in [
        "phase",
        "base_item_id",
        "condition",
        "prompt_format",
        "anchor_format",
        "item_group",
        "gold",
        "target_wrong",
        "replicate",
        "prefix_contains_number",
        "prefix_number",
        "prefix_contains_answer_label",
        "prefix_contains_uncertainty",
        "prefix_contains_warning",
        "source_metadata",
    ]:
        assert key in metadata
    assert metadata["phase"] == "phase3c"
    assert metadata["prompt_format"] == "plain_final"


def test_builder_condition_metadata_booleans(tmp_path: Path) -> None:
    rows = build_dataset(phase3_data=_phase3_data(), replicates=1)
    by_condition = {row["metadata"]["condition"]: row for row in rows}
    assert by_condition["baseline_no_prefix"]["metadata"]["prefix_contains_number"] is False
    assert by_condition["wrong_answer_labeled"]["metadata"]["prefix_contains_answer_label"] is True
    assert by_condition["wrong_number_unlabeled"]["metadata"]["prefix_contains_answer_label"] is False
    assert by_condition["wrong_answer_with_uncertainty"]["metadata"]["prefix_contains_uncertainty"] is True
    assert by_condition["wrong_answer_marked_possibly_wrong"]["metadata"]["prefix_contains_warning"] is True


def test_builder_refuses_empty_selection() -> None:
    with pytest.raises(ValueError, match="no Phase 3 items selected"):
        build_dataset(phase3_data=[], replicates=1)


def test_builder_real_dataset_row_count() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    data_path = repo_root / "data/benchmarks/gsm8k_synthetic_prefix_phase3_rationale_9items.jsonl"
    assert data_path.exists()
    assert data_path.read_text(encoding="utf-8").strip()
