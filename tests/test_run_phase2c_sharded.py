import json
from pathlib import Path

import pytest

from tools.run_phase2c_sharded import (
    analyze_run,
    merge_raw_outputs,
    plan_commands,
    split_dataset,
    write_jsonl,
)


def _row(index: int) -> dict:
    return {
        "id": f"row_{index}",
        "question": f"Question {index}",
        "answer": str(index),
        "metadata": {"base_item_id": f"item_{index}", "condition": "baseline_no_prefix"},
    }


def _raw_row(row_id: str) -> dict:
    return {
        "id": row_id,
        "final_raw": [
            {"agent_id": 1, "round_index": 0, "answer": "1", "extraction_failed": False},
            {"agent_id": 2, "round_index": 0, "answer": "1", "extraction_failed": False},
            {"agent_id": 3, "round_index": 0, "answer": "1", "extraction_failed": False},
        ],
    }


def test_split_round_robin_preserves_ids_and_balance(tmp_path: Path) -> None:
    data_path = tmp_path / "data.jsonl"
    write_jsonl(data_path, [_row(index) for index in range(10)])
    out_dir = tmp_path / "shards"

    summary = split_dataset(data_path=data_path, out_dir=out_dir, shards=2)

    assert summary["rows"] == 10
    assert summary["shard_counts"] == {"phase2c_shard_0.jsonl": 5, "phase2c_shard_1.jsonl": 5}
    shard0 = [json.loads(line)["id"] for line in (out_dir / "phase2c_shard_0.jsonl").read_text(encoding="utf-8").splitlines()]
    shard1 = [json.loads(line)["id"] for line in (out_dir / "phase2c_shard_1.jsonl").read_text(encoding="utf-8").splitlines()]
    assert shard0 == ["row_0", "row_2", "row_4", "row_6", "row_8"]
    assert shard1 == ["row_1", "row_3", "row_5", "row_7", "row_9"]
    assert set(shard0).isdisjoint(set(shard1))

    out_dir = tmp_path / "shards3"
    summary = split_dataset(data_path=data_path, out_dir=out_dir, shards=3)
    assert summary["shard_counts"] == {
        "phase2c_shard_0.jsonl": 4,
        "phase2c_shard_1.jsonl": 3,
        "phase2c_shard_2.jsonl": 3,
    }


def test_merge_detects_missing_and_duplicates_and_writes_output(tmp_path: Path) -> None:
    data_path = tmp_path / "data.jsonl"
    write_jsonl(data_path, [_row(index) for index in range(4)])
    shard_root = tmp_path / "shard_runs"
    shard0 = shard_root / "shard_0"
    shard1 = shard_root / "shard_1"
    shard0.mkdir(parents=True)
    shard1.mkdir(parents=True)
    write_jsonl(shard0 / "raw.jsonl", [_raw_row("row_0"), _raw_row("row_1")])
    write_jsonl(shard1 / "raw.jsonl", [_raw_row("row_2"), _raw_row("row_2")])

    out_run = tmp_path / "merged"
    with pytest.raises(ValueError, match="missing dataset ids"):
        merge_raw_outputs(data_path=data_path, shard_run_root=shard_root, out_run=out_run)

    summary = merge_raw_outputs(data_path=data_path, shard_run_root=shard_root, out_run=out_run, allow_missing=True)
    assert summary["out_raw"] == str(out_run / "raw.jsonl")
    assert (out_run / "raw.jsonl").exists()
    assert summary["duplicate_ids"] == ["row_2"]
    assert "row_3" in summary["missing_ids"]


def test_plan_includes_env_vars_wait_and_paths(tmp_path: Path) -> None:
    shard_dir = tmp_path / "phase2c_shards"
    run_root = tmp_path / "runs"
    command_text = plan_commands(shard_dir=shard_dir, run_root=run_root, condition="independent", jobs=2)
    assert "SMDEBATE_PROGRESS=1" in command_text
    assert "SMDEBATE_REQUEST_TIMEOUT_SECONDS=600" in command_text
    assert "SMDEBATE_MAX_TOKENS=64" in command_text
    assert "SMDEBATE_CONTINUE_ON_ERROR=1" in command_text
    assert str(shard_dir / "phase2c_shard_0.jsonl") in command_text
    assert str(shard_dir / "phase2c_shard_1.jsonl") in command_text
    assert str(run_root / "shard_0") in command_text
    assert str(run_root / "shard_1") in command_text
    assert "wait $PID0" in command_text
    assert "wait $PID1" in command_text


def test_analyze_wraps_existing_analyzer_without_running_expensive_jobs(monkeypatch, tmp_path: Path) -> None:
    called = {}

    def fake_analyzer(*, data_path: Path, raw_path: Path) -> dict:
        called["data_path"] = data_path
        called["raw_path"] = raw_path
        return {"summary": {"qualitative_labels": []}}

    monkeypatch.setattr("tools.run_phase2c_sharded.analyze_synthetic_prefix_phase2c", fake_analyzer)
    monkeypatch.setattr("tools.run_phase2c_sharded.write_json", lambda path, payload: path.write_text("{}", encoding="utf-8"))
    monkeypatch.setattr("tools.run_phase2c_sharded.write_markdown", lambda report, path: path.write_text("md", encoding="utf-8"))

    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "raw.jsonl").write_text("[]\n", encoding="utf-8")
    result = analyze_run(data_path=tmp_path / "data.jsonl", run_dir=run_dir)
    assert called["raw_path"] == run_dir / "raw.jsonl"
    assert result["mode"] == "analyze"
