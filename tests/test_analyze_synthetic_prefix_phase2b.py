import math
from pathlib import Path

from tools.analyze_synthetic_prefix_phase2b import analyze_synthetic_prefix_phase2b, write_markdown
from tools.build_synthetic_prefix_phase2b_dataset import build_dataset, write_jsonl


def _source_row(index: int) -> dict:
    return {
        "id": f"gsm8k_test_{index:06d}",
        "type": "gsm8k",
        "difficulty": "unknown",
        "question": f"Problem {index}.\n\nReturn only the final answer inside <answer>...</answer>.",
        "answer": str(index + 1),
        "metadata": {"source": "gsm8k/main", "split": "test", "original_index": index},
    }


def _raw_row(item_id: str, answers: list[object], *, final_only: bool = False) -> dict:
    entries = []
    for agent_id, answer in enumerate(answers, start=1):
        if answer is None:
            entries.append({"agent_id": agent_id, "round_index": 0, "answer": "", "extraction_failed": True})
        else:
            entries.append({"agent_id": agent_id, "round_index": 0, "answer": answer, "extraction_failed": False})
    if final_only:
        return {"id": item_id, "final_raw": entries}
    return {"id": item_id, "initial_raw": entries, "final_raw": entries}


def _raw_lookup() -> dict[str, list[dict]]:
    lookup: dict[str, list[dict]] = {}
    for index in range(2):
        item_id = f"gsm8k_test_{index:06d}"
        gold = str(index + 1)
        wrong = str(index + 10)
        lookup[item_id] = [
            {
                "id": item_id,
                "initial_answers": [gold, wrong, gold],
                "final_answers": [gold, wrong, gold],
                "initial_raw": [
                    {"answer": gold, "extraction_failed": False},
                    {"answer": wrong, "extraction_failed": False},
                    {"answer": gold, "extraction_failed": False},
                ],
                "final_raw": [
                    {"answer": gold, "extraction_failed": False},
                    {"answer": wrong, "extraction_failed": False},
                    {"answer": gold, "extraction_failed": False},
                ],
                "transcript_raw": [
                    {"answer": gold, "extraction_failed": False},
                    {"answer": wrong, "extraction_failed": False},
                    {"answer": gold, "extraction_failed": False},
                ],
            }
        ]
    return lookup


def test_analyzer_accumulates_item_condition_across_replicates(tmp_path: Path) -> None:
    data_rows = [_source_row(0), _source_row(1)]
    built_rows = build_dataset(data_rows=data_rows, items="all", replicates=2, raw_lookup=_raw_lookup())
    data_path = tmp_path / "data.jsonl"
    write_jsonl(data_path, built_rows)

    raw_rows = []
    for row in built_rows:
        item_index = int(row["metadata"]["base_item_id"].rsplit("_", 1)[-1])
        condition = row["metadata"]["condition"]
        item_id = row["id"]
        gold = str(item_index + 1)
        wrong = str(item_index + 10)
        if condition == "baseline_no_prefix":
            answers = [gold, wrong, "99"]
        elif condition == "single_round_correct_consensus":
            answers = [gold, gold, gold]
        elif condition == "single_round_correct_majority":
            answers = [gold, gold, wrong]
        elif condition == "single_round_wrong_majority":
            answers = [wrong, wrong, gold]
        else:
            answers = [wrong, wrong, None]
        raw_rows.append(_raw_row(item_id, answers, final_only=False))

    raw_path = tmp_path / "raw.jsonl"
    write_jsonl(raw_path, raw_rows)

    report = analyze_synthetic_prefix_phase2b(data_path=data_path, raw_path=raw_path)

    assert report["summary"]["n_items"] == 2
    assert report["summary"]["n_conditions"] == 5
    assert report["summary"]["n_outputs"] == 60
    baseline = report["aggregate_by_condition"]["baseline_no_prefix"]
    assert baseline["n_outputs"] == 12
    assert baseline["non_failed_outputs"] == 12
    assert baseline["correct_count"] == 4
    assert baseline["target_wrong_count"] == 4
    assert baseline["other_count"] == 4
    assert baseline["correct_rate"] == 4 / 12
    assert baseline["target_wrong_rate"] == 4 / 12

    item_baseline = report["by_item_condition"]["gsm8k_test_000000"]["baseline_no_prefix"]
    assert item_baseline["n_outputs"] == 6
    assert item_baseline["non_failed_outputs"] == 6
    assert item_baseline["correct_count"] == 2
    assert item_baseline["target_wrong_count"] == 2

    wrong_majority = report["aggregate_by_condition"]["single_round_wrong_majority"]
    assert wrong_majority["n_outputs"] == 12
    assert wrong_majority["target_wrong_rate"] == 8 / 12
    assert report["indicator_counts"]["wrong_majority_anchor_positive"] == 2
    assert "majority_effect_weaker_than_consensus" in report["summary"]["qualitative_labels"]


def test_analyzer_failure_deltas_and_markdown(tmp_path: Path) -> None:
    data_rows = [_source_row(0)]
    built_rows = build_dataset(data_rows=data_rows, items="all", replicates=1, raw_lookup=_raw_lookup())
    data_path = tmp_path / "data.jsonl"
    write_jsonl(data_path, built_rows)

    raw_rows = [
        _raw_row(built_rows[0]["id"], ["1.00", "1.0", "1"], final_only=False),
        _raw_row(built_rows[1]["id"], ["1", "1.00", None], final_only=False),
        _raw_row(built_rows[2]["id"], ["1", "1.0", "1.00"], final_only=False),
        _raw_row(built_rows[3]["id"], ["10", "10", "10"], final_only=False),
        _raw_row(built_rows[4]["id"], ["10", "10", None], final_only=False),
        _raw_row("missing", ["21", "14", "99"], final_only=False),
    ]
    raw_path = tmp_path / "raw.jsonl"
    write_jsonl(raw_path, raw_rows)

    report = analyze_synthetic_prefix_phase2b(data_path=data_path, raw_path=raw_path)
    assert report["summary"]["skipped_raw_ids"] == ["missing"]
    assert math.isclose(report["aggregate_by_condition"]["baseline_no_prefix"]["correct_rate"], 1.0)
    assert report["by_item_condition"]["gsm8k_test_000000"]["baseline_no_prefix"]["extraction_failure_rate"] == 0.0
    assert "wrong_prefix_failure_increase_common" in report["indicator_counts"]

    failure_summary = report["effect_summaries"]["wrong_consensus_delta_failure"]
    assert failure_summary["mean"] >= 0.0
    assert "wrong_consensus_minus_wrong_majority_delta_failure" in report["effect_summaries"]

    out_md = tmp_path / "report.md"
    write_markdown(report, out_md)
    text = out_md.read_text(encoding="utf-8")
    assert "# GSM8K Synthetic Prefix Phase 2b Multi-Item Analysis" in text
    assert "## Failure Effects" in text
    assert "wrong_consensus_delta_failure" in text
    assert "No raw model text" in text
