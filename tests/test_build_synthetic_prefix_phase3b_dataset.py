from __future__ import annotations

import json
from pathlib import Path

from tools.build_synthetic_prefix_phase3_dataset import write_jsonl
from tools.build_synthetic_prefix_phase3b_dataset import CONDITION_ORDER, build_dataset


def _phase3_row(item_id: str, gold: str, wrong: str) -> dict:
    return {
        "id": f"{item_id}__phase3_baseline_no_prefix_sample_000",
        "type": "gsm8k_synthetic_prefix_phase3",
        "question": "Problem:\nExample.\n\nNow solve the original problem independently.\nReturn only the final numeric answer.",
        "answer": gold,
        "metadata": {
            "base_item_id": item_id,
            "gold": gold,
            "target_wrong_answer": wrong,
            "item_group": "numeric_anchor_dominant",
        },
    }


def _phase3_data() -> list[dict]:
    return [
        _phase3_row("gsm8k_test_000012", "13", "12"),
        _phase3_row("gsm8k_test_000089", "24", "18"),
    ]


def _rationales(tmp_path: Path) -> Path:
    payload = {
        "items": [
            {
                "item_id": "gsm8k_test_000012",
                "gold": "13",
                "target_wrong": "12",
                "weak_wrong_rationale": "A lower estimate slips under the final count.",
                "medium_wrong_rationale": "The yearly gain is handled as if the lower estimate were enough, so the count stays below the correct value.",
                "strong_wrong_rationale": "The count follows the lower estimate and stops before the extra step that would reach the correct value.",
            },
            {
                "item_id": "gsm8k_test_000089",
                "gold": "24",
                "target_wrong": "18",
                "weak_wrong_rationale": "A smaller bag count is implied by underweighting part of the setup.",
                "medium_wrong_rationale": "The bag count is derived from the invited guests, but the missing quarter is not fully included.",
                "strong_wrong_rationale": "The invited guests are counted without fully restoring the missing quarter, so the total stays below the correct value.",
            },
        ]
    }
    path = tmp_path / "rationales.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def test_builder_creates_expected_rows_and_ids(tmp_path: Path) -> None:
    data_path = tmp_path / "phase3.jsonl"
    write_jsonl(data_path, _phase3_data())
    rationales = _rationales(tmp_path)
    rows = build_dataset(phase3_data=_phase3_data(), rationales_path=rationales, replicates=2)
    assert len(rows) == 2 * len(CONDITION_ORDER) * 2
    assert {row["metadata"]["condition"] for row in rows} == set(CONDITION_ORDER)
    assert len({row["id"] for row in rows}) == len(rows)
    assert rows[0]["question"].count("Return only the final numeric answer.") == 1
    assert rows[0]["metadata"]["phase"] == "phase3b"
