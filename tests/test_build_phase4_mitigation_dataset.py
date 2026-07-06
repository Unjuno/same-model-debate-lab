from tools.build_phase4_mitigation_dataset import CONDITION_ORDER, build_dataset


def _phase3c_row(item_id: str, gold: str, wrong: str, *, item_group: str = "numeric_anchor_dominant") -> dict:
    return {
        "id": f"{item_id}__phase3c_baseline_no_prefix_sample_000",
        "type": "gsm8k_synthetic_prefix_phase3c",
        "question": "Problem:\nExample.\n\nNow solve the original problem independently.\nReturn only the final numeric answer.",
        "answer": gold,
        "metadata": {
            "base_item_id": item_id,
            "gold": gold,
            "target_wrong": wrong,
            "item_group": item_group,
        },
    }


def _phase3c_data() -> list[dict]:
    return [
        _phase3c_row("gsm8k_test_000012", "13", "12"),
        _phase3c_row("gsm8k_test_000089", "24", "18", item_group="rationale_corrective_reversal"),
    ]


def test_builder_creates_expected_conditions_and_metadata() -> None:
    rows = build_dataset(phase3c_data=_phase3c_data(), replicates=2)
    assert len(rows) == 2 * len(CONDITION_ORDER) * 2
    assert {row["metadata"]["condition"] for row in rows} == set(CONDITION_ORDER)
    assert len({row["id"] for row in rows}) == len(rows)
    metadata = rows[0]["metadata"]
    for key in [
        "phase",
        "source_item_id",
        "condition",
        "mitigation_condition",
        "history_metrics_applicable",
        "peer_final_answer_visible",
        "peer_numeric_tokens_visible",
        "peer_full_text_visible",
        "requires_initial_commit",
        "gold",
        "target_wrong",
        "item_group",
        "source_metadata",
        "replicate",
    ]:
        assert key in metadata


def test_builder_marks_visibility_controls() -> None:
    rows = build_dataset(phase3c_data=_phase3c_data(), replicates=1)
    by_condition = {row["metadata"]["condition"]: row for row in rows}
    assert by_condition["independent"]["metadata"]["peer_full_text_visible"] is False
    assert by_condition["full_context_debate"]["metadata"]["peer_full_text_visible"] is True
    assert by_condition["answer_hidden_debate"]["metadata"]["peer_final_answer_visible"] is False
    assert by_condition["numeric_masked_debate"]["metadata"]["peer_numeric_tokens_visible"] is False
    assert by_condition["commit_then_numeric_masked_debate"]["metadata"]["requires_initial_commit"] is True


def test_builder_preserves_problem_text_and_only_masks_peer_context() -> None:
    rows = build_dataset(phase3c_data=_phase3c_data(), replicates=1)
    answer_hidden = next(row for row in rows if row["metadata"]["condition"] == "answer_hidden_debate")
    numeric_masked = next(row for row in rows if row["metadata"]["condition"] == "numeric_masked_debate")
    commit_masked = next(row for row in rows if row["metadata"]["condition"] == "commit_then_numeric_masked_debate")
    assert answer_hidden["question"].count("Problem:") == 1
    assert "Answer: [ANSWER_HIDDEN]" in answer_hidden["question"]
    assert "Answer: [NUM]" in numeric_masked["question"]
    assert "Answer: [NUM]" in commit_masked["question"] or "Answer: [ANSWER_HIDDEN]" in commit_masked["question"]
