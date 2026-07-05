from pathlib import Path

from tools.run_phase3c_sharded import plan_commands


def test_plan_adds_resume_when_raw_exists(tmp_path: Path) -> None:
    shard_dir = tmp_path / "phase3c_shards"
    shard_dir.mkdir()
    shard0 = shard_dir / "phase3c_shard_0.jsonl"
    shard1 = shard_dir / "phase3c_shard_1.jsonl"
    shard0.write_text("{}", encoding="utf-8")
    shard1.write_text("{}", encoding="utf-8")
    run_root = tmp_path / "runs"
    (run_root / "shard_0").mkdir(parents=True)
    (run_root / "shard_0" / "raw.jsonl").write_text("{}", encoding="utf-8")
    command_text = plan_commands(shard_dir=shard_dir, run_root=run_root, condition="independent", jobs=2, resume=True)
    assert "--resume" in command_text
    assert str(shard0) in command_text
    assert str(shard1) in command_text
