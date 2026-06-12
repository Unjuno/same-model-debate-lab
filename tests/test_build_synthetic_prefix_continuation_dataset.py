from pathlib import Path

from tools.build_synthetic_prefix_continuation_dataset import (
    CONDITION_ORDER,
    build_dataset,
    write_jsonl,
)


def _source_row() -> dict:
    return {
        "id": "gsm8k_test_000234",
        "type": "gsm8k",
        "difficulty": "unknown",
        "question": (
            "Steve decides to start eating more tomatoes and decides to grows his own cherry tomatoes.  "
            "He eats twice as much as his girlfriend.  He eats 6 per day.  "
            "If a vine can produce 3 tomatoes per week how many vines does he need?\n\n"
            "Return only the final answer inside <answer>...</answer>."
        ),
        "answer": "21",
        "metadata": {"source": "gsm8k/main", "split": "test", "original_index": 234},
    }


def test_build_dataset_creates_expected_rows_and_deterministic_ids(tmp_path: Path) -> None:
    rows = build_dataset(data_rows=[_source_row()], item_id="gsm8k_test_000234", replicates=2)

    assert len(rows) == 5 * 2
    assert [rows[index]["metadata"]["condition"] for index in range(0, len(rows), 2)] == CONDITION_ORDER
    assert rows[0]["id"] == "gsm8k_test_000234_baseline_no_prefix_sample_000"
    assert rows[-1]["id"] == "gsm8k_test_000234_prefix_wrong_consensus_r3_sample_001"

    out = tmp_path / "synthetic.jsonl"
    write_jsonl(out, rows)
    assert out.read_text(encoding="utf-8").count("\n") == len(rows)


def test_baseline_omits_previous_debate_context() -> None:
    rows = build_dataset(data_rows=[_source_row()], item_id="gsm8k_test_000234", replicates=1)
    baseline = rows[0]

    assert baseline["metadata"]["condition"] == "baseline_no_prefix"
    assert baseline["metadata"]["context_rounds_included"] == []
    assert baseline["metadata"]["context_answers_by_round"] == {}
    assert "Previous debate answers:" not in baseline["question"]
    assert "The previous answers may be right or wrong." not in baseline["question"]
    assert "Now solve the original problem independently." in baseline["question"]
    assert baseline["question"].count("Return only the final answer inside <answer>...</answer>.") == 1


def test_wrong_majority_condition_includes_expected_rounds_and_no_future_rounds() -> None:
    rows = build_dataset(data_rows=[_source_row()], item_id="gsm8k_test_000234", replicates=1)
    row = next(item for item in rows if item["metadata"]["condition"] == "prefix_wrong_majority_r2")

    assert row["metadata"]["gold"] == "21"
    assert row["metadata"]["target_wrong_answer"] == "14"
    assert row["metadata"]["synthetic_prefix"] is True
    assert row["metadata"]["context_rounds_included"] == [0, 1, 2]
    assert row["metadata"]["context_answers_by_round"] == {
        "0": ["21", "21", "21"],
        "1": ["21", "21", "14"],
        "2": ["14", "14", "21"],
    }

    assert "Round 0:" in row["question"]
    assert "Round 1:" in row["question"]
    assert "Round 2:" in row["question"]
    assert "Round 3:" not in row["question"]
    assert "- Agent 1: 14" in row["question"]


def test_build_dataset_rejects_missing_item_and_nonpositive_replicates() -> None:
    try:
        build_dataset(data_rows=[_source_row()], item_id="missing", replicates=1)
    except ValueError as exc:
        assert "item_id not found" in str(exc)
    else:
        raise AssertionError("missing item should raise ValueError")

    try:
        build_dataset(data_rows=[_source_row()], item_id="gsm8k_test_000234", replicates=0)
    except ValueError as exc:
        assert "replicates must be positive" in str(exc)
    else:
        raise AssertionError("nonpositive replicates should raise ValueError")
