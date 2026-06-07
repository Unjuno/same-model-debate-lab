from __future__ import annotations

import json
from pathlib import Path

from tools.analyze_round_trajectory import analyze_round_trajectory, write_markdown


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row) + "\n")


def test_analyze_round_trajectory_reconstructs_rounds_from_transcript_raw(tmp_path: Path) -> None:
    data_path = tmp_path / "data.jsonl"
    _write_jsonl(data_path, [{"id": "x", "answer": "A"}, {"id": "y", "answer": "A"}, {"id": "z", "answer": "A"}, {"id": "w", "answer": "A"}, {"id": "v", "answer": "A"}])

    raw_path = tmp_path / "raw.jsonl"
    _write_jsonl(
        raw_path,
        [
            {
                "id": "x",
                "initial_answers": ["A", "A", "A"],
                "transcript_raw": [
                    {"round_index": 0, "answer": "A"},
                    {"round_index": 0, "answer": "A"},
                    {"round_index": 0, "answer": "A"},
                    {"round_index": 1, "answer": "A"},
                    {"round_index": 1, "answer": "A"},
                    {"round_index": 1, "answer": "A"},
                ],
            },
            {
                "id": "y",
                "initial_answers": ["B", "B", "B"],
                "transcript_raw": [
                    {"round_index": 0, "answer": "B"},
                    {"round_index": 0, "answer": "B"},
                    {"round_index": 0, "answer": "B"},
                    {"round_index": 1, "answer": "B"},
                    {"round_index": 1, "answer": "B"},
                    {"round_index": 1, "answer": "B"},
                ],
            },
            {
                "id": "z",
                "initial_answers": ["B", "B", "B"],
                "transcript_raw": [
                    {"round_index": 0, "answer": "B"},
                    {"round_index": 0, "answer": "B"},
                    {"round_index": 0, "answer": "B"},
                    {"round_index": 1, "answer": "A"},
                    {"round_index": 1, "answer": "A"},
                    {"round_index": 1, "answer": "A"},
                ],
            },
            {
                "id": "w",
                "initial_answers": ["A", "A", "A"],
                "transcript_raw": [
                    {"round_index": 0, "answer": "A"},
                    {"round_index": 0, "answer": "A"},
                    {"round_index": 0, "answer": "A"},
                    {"round_index": 1, "answer": "B"},
                    {"round_index": 1, "answer": "B"},
                    {"round_index": 1, "answer": "B"},
                ],
            },
            {
                "id": "v",
                "initial_answers": ["B", "B", "B"],
                "transcript_raw": [
                    {"round_index": 0, "answer": "B"},
                    {"round_index": 0, "answer": "B"},
                    {"round_index": 0, "answer": "B"},
                    {"round_index": 1, "answer": "A"},
                    {"round_index": 1, "answer": "A"},
                    {"round_index": 1, "answer": "A"},
                    {"round_index": 2, "answer": "B"},
                    {"round_index": 2, "answer": "B"},
                    {"round_index": 2, "answer": "B"},
                ],
            },
        ],
    )

    report = analyze_round_trajectory(data_path=data_path, raw_path=raw_path)
    trajectories = {row["item_id"]: row for row in report["trajectories"]}

    assert trajectories["x"]["category"] == "preserved_correct"
    assert trajectories["y"]["category"] == "persistent_error"
    assert trajectories["z"]["category"] == "recovery"
    assert trajectories["w"]["category"] == "deterioration"
    assert trajectories["v"]["category"] == "oscillation"
    assert trajectories["v"]["flip_count"] == 2
    assert trajectories["z"]["majority_answer_by_round"]["1"] == "A"


def test_analyze_round_trajectory_markdown_omits_raw_text(tmp_path: Path) -> None:
    report = {
        "category_counts": {"preserved_correct": 1, "persistent_error": 0, "recovery": 0, "deterioration": 0, "oscillation": 0},
        "trajectories": [
            {
                "item_id": "x",
                "gold": "A",
                "initial_answers": ["A"],
                "answers_by_round": {"0": ["A"]},
                "majority_answer_by_round": {"0": "A"},
                "correctness_by_round": {"0": True},
                "flip_count": 0,
                "category": "preserved_correct",
            }
        ],
    }
    out = tmp_path / "report.md"
    write_markdown(report, out)
    text = out.read_text(encoding="utf-8")
    assert "raw_text" not in text
    assert "transcript_raw" not in text
