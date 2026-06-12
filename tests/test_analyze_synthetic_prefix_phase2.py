import math
from pathlib import Path

from tools.analyze_synthetic_prefix_phase2 import analyze_synthetic_prefix_phase2, write_markdown
from tools.build_synthetic_prefix_phase2_dataset import build_dataset, write_jsonl


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


def _raw_row(item_id: str, answers: list[object]) -> dict:
    entries = []
    for agent_id, answer in enumerate(answers, start=1):
        if answer is None:
            entries.append({"agent_id": agent_id, "round_index": 0, "answer": "", "extraction_failed": True})
        else:
            entries.append(
                {
                    "agent_id": agent_id,
                    "round_index": 0,
                    "raw_text": f"<answer>{answer}</answer>",
                    "answer": answer,
                    "extraction_failed": False,
                }
            )
    return {"id": item_id, "condition": "independent", "initial_raw": entries, "final_raw": entries}


def test_analyzer_aggregates_by_condition_and_computes_comparisons(tmp_path: Path) -> None:
    data_rows = build_dataset(data_rows=[_source_row()], item_id="gsm8k_test_000234", replicates=1)
    data_path = tmp_path / "data.jsonl"
    write_jsonl(data_path, data_rows)

    raw_rows = [
        _raw_row("gsm8k_test_000234_baseline_no_prefix_sample_000", ["21", "14", "99"]),
        _raw_row("gsm8k_test_000234_single_round_correct_consensus_sample_000", ["21", "21", "21"]),
        _raw_row("gsm8k_test_000234_single_round_correct_majority_sample_000", ["21", "14", "14"]),
        _raw_row("gsm8k_test_000234_single_round_wrong_majority_sample_000", ["14", "14", "21"]),
        _raw_row("gsm8k_test_000234_single_round_wrong_consensus_sample_000", ["14", "14", "14"]),
        _raw_row("gsm8k_test_000234_trajectory_forward_sample_000", ["14", "14", "21"]),
        _raw_row("gsm8k_test_000234_trajectory_reversed_sample_000", ["21", "21", "21"]),
    ]
    raw_path = tmp_path / "raw.jsonl"
    write_jsonl(raw_path, raw_rows)

    report = analyze_synthetic_prefix_phase2(data_path=data_path, raw_path=raw_path)

    baseline = report["by_condition"]["baseline_no_prefix"]
    assert baseline["n_outputs"] == 3
    assert baseline["correct_count"] == 1
    assert baseline["target_wrong_count"] == 1
    assert baseline["other_count"] == 1
    assert baseline["correct_rate"] == 1 / 3
    assert baseline["target_wrong_rate"] == 1 / 3
    assert math.isclose(baseline["answer_entropy"], math.log2(3))

    wrong_majority = report["by_condition"]["single_round_wrong_majority"]
    assert wrong_majority["target_wrong_count"] == 2
    assert wrong_majority["target_wrong_rate"] == 2 / 3
    assert report["planned_comparisons"]["single_round_wrong_majority_vs_baseline"]["delta_target_wrong_rate"] == 1 / 3
    assert math.isclose(
        report["planned_comparisons"]["single_round_wrong_consensus_vs_wrong_majority"]["delta_target_wrong_rate"],
        1 / 3,
    )

    assert "shared_prior_possible" in report["summary"]["qualitative_labels"]
    assert "correct_consensus_anchor_consistent" in report["summary"]["qualitative_labels"]
    assert "wrong_majority_anchor_consistent" in report["summary"]["qualitative_labels"]
    assert "wrong_consensus_stronger_than_wrong_majority" in report["summary"]["qualitative_labels"]
    assert "recency_order_consistent" in report["summary"]["qualitative_labels"]
    assert "frequency_without_recency_insufficient" in report["summary"]["qualitative_labels"]


def test_analyzer_handles_decimal_normalization_and_markdown(tmp_path: Path) -> None:
    data_rows = build_dataset(data_rows=[_source_row()], item_id="gsm8k_test_000234", replicates=1)
    data_path = tmp_path / "data.jsonl"
    write_jsonl(data_path, data_rows)

    raw_rows = [
        _raw_row("gsm8k_test_000234_baseline_no_prefix_sample_000", ["21.00", "21.0", "21"]),
        _raw_row("gsm8k_test_000234_single_round_correct_consensus_sample_000", ["21", "21.00", "21.0"]),
    ]
    raw_path = tmp_path / "raw.jsonl"
    write_jsonl(raw_path, raw_rows)

    report = analyze_synthetic_prefix_phase2(data_path=data_path, raw_path=raw_path)

    assert report["by_condition"]["baseline_no_prefix"]["correct_rate"] == 1.0
    assert report["by_condition"]["single_round_correct_consensus"]["correct_count"] == 3
    assert report["by_condition"]["single_round_correct_consensus"]["target_wrong_count"] == 0

    out_md = tmp_path / "report.md"
    write_markdown(report, out_md)
    text = out_md.read_text(encoding="utf-8")
    assert "# GSM8K 000234 Synthetic Prefix Phase 2 Analysis" in text
    assert "single-item diagnostic" in text
    assert "No raw model text" in text


def test_analyzer_skips_raw_rows_missing_from_data(tmp_path: Path) -> None:
    data_rows = build_dataset(data_rows=[_source_row()], item_id="gsm8k_test_000234", replicates=1)
    data_path = tmp_path / "data.jsonl"
    write_jsonl(data_path, data_rows)

    raw_path = tmp_path / "raw.jsonl"
    write_jsonl(raw_path, [_raw_row("unknown_id", ["21", "14", "99"])])

    report = analyze_synthetic_prefix_phase2(data_path=data_path, raw_path=raw_path)

    assert report["summary"]["skipped_raw_ids"] == ["unknown_id"]
    assert report["by_condition"]["baseline_no_prefix"]["n_outputs"] == 0
    assert report["summary"]["qualitative_labels"] == ["inconclusive"]
