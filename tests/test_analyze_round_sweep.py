from __future__ import annotations

import json
from pathlib import Path

from tools.analyze_round_sweep import analyze_round_sweep, write_markdown


def _write_run(run_dir: Path, rows: list[dict], summary: dict) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    with (run_dir / "raw.jsonl").open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row) + "\n")
    (run_dir / "summary.json").write_text(json.dumps(summary), encoding="utf-8")


def _row(item_id: str, initial: list[str], final: str) -> dict:
    return {
        "id": item_id,
        "gold": "A",
        "initial_answers": initial,
        "final_answers": [final, final, final],
        "final_answer": final,
    }


def test_analyze_round_sweep_joins_runs_and_classifies_trajectories(tmp_path: Path) -> None:
    data_path = tmp_path / "data.jsonl"
    data_path.write_text('{"id":"x","answer":"A"}\n{"id":"y","answer":"A"}\n{"id":"z","answer":"A"}\n{"id":"w","answer":"A"}\n{"id":"v","answer":"A"}\n', encoding="utf-8")

    _write_run(tmp_path / "r1", [_row("x", ["A"], "A"), _row("y", ["B"], "B"), _row("z", ["B"], "B"), _row("w", ["A"], "A"), _row("v", ["B"], "B")], {"accuracy": 1.0, "answer_loss_rate": 0.0, "same_error_agreement_rate": 0.0, "diversity_drop": 0.0, "extraction_failure_rate": 0.0})
    _write_run(tmp_path / "r2", [_row("x", ["A"], "A"), _row("y", ["B"], "B"), _row("z", ["B"], "B"), _row("w", ["A"], "A"), _row("v", ["A"], "A")], {"accuracy": 1.0, "answer_loss_rate": 0.0, "same_error_agreement_rate": 0.0, "diversity_drop": 0.0, "extraction_failure_rate": 0.0})
    _write_run(tmp_path / "r3", [_row("x", ["A"], "A"), _row("y", ["B"], "B"), _row("z", ["A"], "A"), _row("w", ["B"], "B"), _row("v", ["B"], "B")], {"accuracy": 1.0, "answer_loss_rate": 0.0, "same_error_agreement_rate": 0.0, "diversity_drop": 0.0, "extraction_failure_rate": 0.0})

    report = analyze_round_sweep(
        data_path=data_path,
        run_specs=[(1, tmp_path / "r1"), (2, tmp_path / "r2"), (3, tmp_path / "r3")],
    )

    trajectories = {row["item_id"]: row for row in report["trajectories"]}
    assert trajectories["x"]["category"] == "preserved_correct"
    assert trajectories["y"]["category"] == "persistent_error"
    assert trajectories["z"]["category"] == "recovery"
    assert trajectories["w"]["category"] == "deterioration"
    assert trajectories["v"]["category"] == "oscillation"
    assert trajectories["v"]["flip_count"] == 2


def test_markdown_omits_raw_transcripts(tmp_path: Path) -> None:
    report = {
        "run_summaries": {"1": {"accuracy": 0.5, "answer_loss_rate": 0.1, "same_error_agreement_rate": 0.2, "diversity_drop": 0.3, "extraction_failure_rate": 0.0}},
        "trajectories": [{"item_id": "x", "gold": "A", "initial_answers": ["A"], "final_answer_by_R": {"1": "A"}, "correctness_by_R": {"1": True}, "flip_count": 0, "category": "preserved_correct"}],
        "category_counts": {"preserved_correct": 1, "persistent_error": 0, "recovery": 0, "deterioration": 0, "oscillation": 0},
    }
    out = tmp_path / "report.md"
    write_markdown(report, out)
    text = out.read_text(encoding="utf-8")
    assert "raw transcripts" in text.lower()
    assert "raw_text" not in text
    assert "transcript_raw" not in text
