from tools.build_synthetic_prefix_phase2c_dataset import (
    CONDITION_ORDER,
    PROMPT_FORMAT_ORDER,
    build_dataset,
)


def _phase2b_row(item_id: str, gold: str, wrong: str, condition: str, question_suffix: str = "") -> dict:
    question = (
        f"Problem {item_id}{question_suffix}.\n\nReturn only the final answer inside <answer>...</answer>."
    )
    context = {
        "baseline_no_prefix": [],
        "single_round_correct_consensus": [gold, gold, gold],
        "single_round_wrong_consensus": [wrong, wrong, wrong],
    }[condition]
    return {
        "id": f"{item_id}__slot_00_{condition}_sample_000",
        "type": "gsm8k_synthetic_prefix_phase2b",
        "difficulty": "unknown",
        "question": question,
        "answer": gold,
        "metadata": {
            "base_item_id": item_id,
            "condition": condition,
            "replicate_index": 0,
            "gold": gold,
            "target_wrong_answer": wrong,
            "target_wrong_source": "raw_lookup",
            "synthetic_prefix": True,
            "phase": "phase2b_multi_item",
            "condition_family": "baseline" if condition == "baseline_no_prefix" else "single_round",
            "context_rounds_included": [] if not context else [0],
            "context_answers_by_round": {} if not context else {"0": context},
            "prefix_answer_counts": {} if not context else {gold if condition == "single_round_correct_consensus" else wrong: 3},
            "latest_round_answers": [] if not context else context,
            "latest_round_majority": "" if not context else (gold if condition == "single_round_correct_consensus" else wrong),
            "source_metadata": {"source": "gsm8k/main"},
        },
    }


def _phase2b_data() -> list[dict]:
    rows = []
    for index in range(3):
        item_id = f"gsm8k_test_{index:06d}"
        gold = str(index + 1)
        wrong = str(index + 10)
        rows.append(_phase2b_row(item_id, gold, wrong, "baseline_no_prefix"))
        rows.append(_phase2b_row(item_id, gold, wrong, "single_round_correct_consensus"))
        rows.append(_phase2b_row(item_id, gold, wrong, "single_round_wrong_consensus"))
    return rows


def test_build_dataset_uses_phase2b_items_and_prompt_formats() -> None:
    rows = build_dataset(phase2b_data=_phase2b_data(), replicates=2)
    assert len(rows) == 3 * 3 * 3 * 2
    assert [rows[index]["metadata"]["prompt_format"] for index in (0, 6, 12)] == [
        "answer_tag",
        "json",
        "plain_final",
    ]
    assert [rows[index]["metadata"]["condition"] for index in range(0, 6, 2)] == [
        "baseline_no_prefix",
        "single_round_correct_consensus",
        "single_round_wrong_consensus",
    ]
    assert rows[0]["metadata"]["base_item_id"] == "gsm8k_test_000000"
    assert rows[0]["metadata"]["prompt_format"] == "answer_tag"
    assert rows[0]["metadata"]["context_rounds_included"] == []
    assert rows[0]["metadata"]["latest_round_majority"] == ""
    assert rows[2]["metadata"]["context_rounds_included"] == [0]
    assert rows[2]["metadata"]["target_wrong_source"] == "raw_lookup"
    assert len({row["id"] for row in rows}) == len(rows)


def test_build_dataset_prompt_formats_and_text_rules() -> None:
    rows = build_dataset(phase2b_data=_phase2b_data(), replicates=1)
    baseline = next(row for row in rows if row["metadata"]["condition"] == "baseline_no_prefix" and row["metadata"]["prompt_format"] == "json")
    wrong = next(
        row
        for row in rows
        if row["metadata"]["condition"] == "single_round_wrong_consensus" and row["metadata"]["prompt_format"] == "plain_final"
    )

    assert "Previous debate answers:" not in baseline["question"]
    assert "The previous answers may be right or wrong." not in baseline["question"]
    assert 'Return JSON only, with this exact schema: {"answer": "..."}.' in baseline["question"]
    assert "Previous debate answers:" in wrong["question"]
    assert "The previous answers may be right or wrong." in wrong["question"]
    assert "Return only the final numeric answer. Do not include explanation." in wrong["question"]


def test_build_dataset_metadata_and_counts() -> None:
    rows = build_dataset(phase2b_data=_phase2b_data(), replicates=1)
    assert set(PROMPT_FORMAT_ORDER) == {"answer_tag", "json", "plain_final"}
    for row in rows:
        metadata = row["metadata"]
        assert metadata["phase"] == "phase2c_prompt_format"
        assert metadata["base_item_id"].startswith("gsm8k_test_")
        assert metadata["condition"] in CONDITION_ORDER
        assert metadata["prompt_format"] in PROMPT_FORMAT_ORDER
        assert metadata["prefix_answer_counts"] in ({}, {"1": 3}, {"2": 3}, {"3": 3}, {"10": 3}, {"11": 3}, {"12": 3})
        assert "source_metadata" in metadata
