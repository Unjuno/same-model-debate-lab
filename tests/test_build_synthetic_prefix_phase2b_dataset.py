from pathlib import Path

from tools.build_synthetic_prefix_phase2b_dataset import CONDITION_ORDER, build_dataset, write_jsonl


def _source_row(index: int) -> dict:
    return {
        "id": f"gsm8k_test_{index:06d}",
        "type": "gsm8k",
        "difficulty": "unknown",
        "question": (
            f"Problem {index}.\n\n"
            "Return only the final answer inside <answer>...</answer>."
        ),
        "answer": str(index + 1),
        "metadata": {"source": "gsm8k/main", "split": "test", "original_index": index},
    }


def _raw_lookup() -> dict[str, list[dict]]:
    lookup: dict[str, list[dict]] = {}
    for index in range(20):
        item_id = f"gsm8k_test_{index:06d}"
        gold = str(index + 1)
        target = str(index + 10)
        lookup[item_id] = [
            {
                "id": item_id,
                "initial_answers": [gold, target, gold],
                "final_answers": [gold, target, gold],
                "initial_raw": [
                    {"answer": gold, "extraction_failed": False},
                    {"answer": target, "extraction_failed": False},
                    {"answer": gold, "extraction_failed": False},
                ],
                "final_raw": [
                    {"answer": gold, "extraction_failed": False},
                    {"answer": target, "extraction_failed": False},
                    {"answer": gold, "extraction_failed": False},
                ],
                "transcript_raw": [
                    {"answer": gold, "extraction_failed": False},
                    {"answer": target, "extraction_failed": False},
                    {"answer": gold, "extraction_failed": False},
                ],
            }
        ]
    return lookup


def test_build_dataset_creates_expected_rows_and_deterministic_ids(tmp_path: Path) -> None:
    rows = build_dataset(
        data_rows=[_source_row(index) for index in range(20)],
        items=20,
        replicates=2,
        raw_lookup=_raw_lookup(),
    )

    assert len(rows) == 20 * 5 * 2
    assert [row["metadata"]["condition"] for row in rows[:10:2]] == CONDITION_ORDER[:5]
    assert rows[0]["id"] == "gsm8k_test_000000__slot_00_baseline_no_prefix_sample_000"
    assert rows[-1]["id"].startswith("gsm8k_test_000019__slot_19_single_round_wrong_consensus_sample_001")

    out = tmp_path / "synthetic.jsonl"
    write_jsonl(out, rows)
    assert out.read_text(encoding="utf-8").count("\n") == len(rows)


def test_baseline_and_single_round_metadata_are_correct() -> None:
    rows = build_dataset(
        data_rows=[_source_row(index) for index in range(20)],
        items=20,
        replicates=1,
        raw_lookup=_raw_lookup(),
    )
    baseline = next(row for row in rows if row["metadata"]["condition"] == "baseline_no_prefix")
    wrong_consensus = next(row for row in rows if row["metadata"]["condition"] == "single_round_wrong_consensus")
    correct_majority = next(row for row in rows if row["metadata"]["condition"] == "single_round_correct_majority")

    assert baseline["metadata"]["phase"] == "phase2b_multi_item"
    assert baseline["metadata"]["condition_family"] == "baseline"
    assert baseline["metadata"]["selection_slot"] == 0
    assert baseline["metadata"]["context_rounds_included"] == []
    assert baseline["metadata"]["context_answers_by_round"] == {}
    assert baseline["metadata"]["prefix_answer_counts"] == {}
    assert baseline["metadata"]["latest_round_answers"] == []
    assert baseline["metadata"]["latest_round_majority"] == ""
    assert "Previous debate answers:" not in baseline["question"]
    assert "The previous answers may be right or wrong." not in baseline["question"]

    assert wrong_consensus["metadata"]["condition_family"] == "single_round"
    assert wrong_consensus["metadata"]["selection_slot"] == 0
    assert wrong_consensus["metadata"]["latest_round_majority"] == "10"
    assert wrong_consensus["metadata"]["prefix_answer_counts"] == {"10": 3}
    assert "Previous debate answers:" in wrong_consensus["question"]
    assert "The previous answers may be right or wrong." in wrong_consensus["question"]

    assert correct_majority["metadata"]["prefix_answer_counts"] == {"1": 2, "10": 1}
    assert correct_majority["metadata"]["latest_round_majority"] == "1"


def test_builder_uses_fallback_when_fewer_than_requested_eligible_items_exist() -> None:
    data_rows = [_source_row(index) for index in range(19)]
    raw_lookup = _raw_lookup()
    raw_lookup.pop("gsm8k_test_000019")

    rows = build_dataset(data_rows=data_rows, items=20, replicates=1, raw_lookup=raw_lookup)

    assert len(rows) == 20 * 5
    assert rows[-1]["metadata"]["selection_slot"] == 19
    assert rows[-1]["metadata"]["base_item_id"] in {f"gsm8k_test_{index:06d}" for index in range(19)}
