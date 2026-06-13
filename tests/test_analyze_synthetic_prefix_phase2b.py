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


def _raw_row(item_id: str, answers: list[object]) -> dict:
    entries = []
    for agent_id, answer in enumerate(answers, start=1):
        if answer is None:
            entries.append({"agent_id": agent_id, "round_index": 0, "answer": "", "extraction_failed": True})
        else:
            entries.append({"agent_id": agent_id, "round_index": 0, "answer": answer, "extraction_failed": False})
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


def test_analyzer_aggregates_by_item_and_condition(tmp_path: Path) -> None:
    data_rows = [_source_row(0), _source_row(1)]
    data_path = tmp_path / "data.jsonl"
    built_rows = build_dataset(data_rows=data_rows, items=2, replicates=1, raw_lookup=_raw_lookup())
    write_jsonl(data_path, built_rows)

    raw_rows = []
    for item_index in range(2):
        base_row = next(
            row
            for row in built_rows
            if row["metadata"]["base_item_id"] == f"gsm8k_test_{item_index:06d}" and row["metadata"]["condition"] == "baseline_no_prefix"
        )
        base = base_row["id"].rsplit("_baseline_no_prefix_sample_000", 1)[0]
        raw_rows.extend(
            [
                _raw_row(
                    f"{base}_baseline_no_prefix_sample_000",
                    [str(item_index + 1), str(item_index + 10), "99"],
                ),
                _raw_row(f"{base}_single_round_correct_consensus_sample_000", [str(item_index + 1)] * 3),
                _raw_row(f"{base}_single_round_correct_majority_sample_000", [str(item_index + 1), str(item_index + 1), str(item_index + 10)]),
                _raw_row(f"{base}_single_round_wrong_majority_sample_000", [str(item_index + 10), str(item_index + 10), str(item_index + 1)]),
                _raw_row(f"{base}_single_round_wrong_consensus_sample_000", [str(item_index + 10)] * 3),
            ]
        )
    raw_path = tmp_path / "raw.jsonl"
    write_jsonl(raw_path, raw_rows)

    report = analyze_synthetic_prefix_phase2b(data_path=data_path, raw_path=raw_path)

    assert report["summary"]["n_items"] == 2
    assert report["summary"]["n_conditions"] == 5
    assert report["summary"]["n_outputs"] == 30
    baseline = report["aggregate_by_condition"]["baseline_no_prefix"]
    assert baseline["correct_count"] == 2
    assert baseline["target_wrong_count"] == 2
    assert baseline["other_count"] == 2
    assert baseline["correct_rate"] == 2 / 6
    assert baseline["target_wrong_rate"] == 2 / 6

    wrong_majority = report["aggregate_by_condition"]["single_round_wrong_majority"]
    assert wrong_majority["target_wrong_rate"] == 2 / 3
    assert report["indicator_counts"]["wrong_majority_anchor_positive"] == 2
    assert "majority_effect_weaker_than_consensus" in report["summary"]["qualitative_labels"]


def test_analyzer_handles_normalization_deltas_skips_and_markdown(tmp_path: Path) -> None:
    data_rows = [_source_row(0)]
    data_path = tmp_path / "data.jsonl"
    built_rows = build_dataset(data_rows=data_rows, items=1, replicates=1, raw_lookup=_raw_lookup())
    write_jsonl(data_path, built_rows)

    raw_rows = [
        _raw_row(built_rows[0]["id"], ["1.00", "1.0", "1"]),
        _raw_row(built_rows[1]["id"], ["1", "1.00", "1.0"]),
        _raw_row("missing", ["21", "14", "99"]),
    ]
    raw_path = tmp_path / "raw.jsonl"
    write_jsonl(raw_path, raw_rows)

    report = analyze_synthetic_prefix_phase2b(data_path=data_path, raw_path=raw_path)
    assert report["summary"]["skipped_raw_ids"] == ["missing"]
    assert math.isclose(report["aggregate_by_condition"]["baseline_no_prefix"]["correct_rate"], 1.0)
    assert report["summary"]["qualitative_labels"] == ["inconclusive"]

    out_md = tmp_path / "report.md"
    write_markdown(report, out_md)
    text = out_md.read_text(encoding="utf-8")
    assert "# GSM8K Synthetic Prefix Phase 2b Multi-Item Analysis" in text
    assert "Aggregate by Condition" in text
    assert "No raw model text" in text
