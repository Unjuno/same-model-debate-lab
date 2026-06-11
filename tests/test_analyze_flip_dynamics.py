from __future__ import annotations

import json
from pathlib import Path

from tools.analyze_flip_dynamics import analyze_flip_dynamics, write_markdown


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row) + "\n")


def test_analyze_flip_dynamics_tracks_majority_and_agent_transitions(tmp_path: Path) -> None:
    data_path = tmp_path / "data.jsonl"
    raw_path = tmp_path / "raw.jsonl"

    _write_jsonl(data_path, [{"id": "x", "answer": "A"}])
    _write_jsonl(
        raw_path,
        [
                {
                    "id": "x",
                    "transcript_raw": [
                        {"agent_id": 1, "round_index": 0, "answer": "A", "extraction_failed": False},
                        {"agent_id": 2, "round_index": 0, "answer": "B", "extraction_failed": False},
                        {"agent_id": 3, "round_index": 0, "answer": "", "extraction_failed": True},
                        {"agent_id": 1, "round_index": 1, "answer": "B", "extraction_failed": False},
                        {"agent_id": 2, "round_index": 1, "answer": "B", "extraction_failed": False},
                        {"agent_id": 3, "round_index": 1, "answer": "A", "extraction_failed": False},
                    ],
                }
            ],
        )

    report = analyze_flip_dynamics(data_path=data_path, raw_path=raw_path)

    assert report["n"] == 1
    assert report["majority_transition_counts"]["correct_to_wrong"] == 1
    assert report["agent_transition_counts"]["correct_to_wrong"] == 1
    assert report["agent_transition_counts"]["wrong_to_correct"] == 0
    assert report["agent_transition_counts"]["missing_initial"] == 1
    assert report["role_transition_counts"]["solver"]["correct_to_wrong"] == 1
    assert report["role_transition_counts"]["skeptic/error-checker"]["wrong_to_correct"] == 0
    assert report["role_transition_counts"]["alternative-solver"]["missing_initial"] == 1

    item = report["items"][0]
    assert item["initial_majority"] == "A"
    assert item["final_majority"] == "B"
    assert item["majority_transition_category"] == "correct_to_wrong"


def test_analyze_flip_dynamics_markdown_is_compact(tmp_path: Path) -> None:
    report = {
        "n": 1,
        "correct_to_wrong_majority_rate": 0.0,
        "wrong_to_correct_majority_rate": 0.0,
        "correct_path_retention_rate": 1.0,
        "extraction_failure_count": 0,
        "item_count_with_any_extraction_failure": 0,
        "majority_transition_counts": {"preserved_correct": 1, "correct_to_wrong": 0, "wrong_to_correct": 0, "persistent_error": 0, "no_initial_majority": 0, "no_final_majority": 0},
        "agent_transition_counts": {"correct_to_correct": 0, "correct_to_wrong": 0, "wrong_to_correct": 0, "wrong_to_wrong": 0, "missing_initial": 0, "missing_final": 0},
        "role_transition_counts": {
            "solver": {"correct_to_correct": 0, "correct_to_wrong": 0, "wrong_to_correct": 0, "wrong_to_wrong": 0, "missing_initial": 0, "missing_final": 0},
            "skeptic/error-checker": {"correct_to_correct": 0, "correct_to_wrong": 0, "wrong_to_correct": 0, "wrong_to_wrong": 0, "missing_initial": 0, "missing_final": 0},
            "alternative-solver": {"correct_to_correct": 0, "correct_to_wrong": 0, "wrong_to_correct": 0, "wrong_to_wrong": 0, "missing_initial": 0, "missing_final": 0},
        },
        "items": [{"item_id": "x", "gold": "A", "initial_majority": "A", "final_majority": "A", "majority_transition_category": "preserved_correct"}],
    }
    out = tmp_path / "report.md"
    write_markdown(report, out)
    text = out.read_text(encoding="utf-8")
    assert "raw_text" not in text
    assert "transcript" not in text
