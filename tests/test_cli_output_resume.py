from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest

import smdebate.cli as cli
from smdebate.protocol import Item


@dataclass
class _DummySummary:
    n: int
    accuracy: float = 1.0
    oracle_at_k: float = 1.0
    answer_loss_rate: float = 0.0
    same_error_agreement_rate: float = 0.0
    diversity_drop: float = 0.0
    extraction_failure_rate: float = 0.0


def _config(condition: str = "independent"):
    return SimpleNamespace(
        agent_count=3,
        rounds=3,
        condition=condition,
        model_family="qwen3",
        reasoning_mode="no_think",
    )


def _item(item_id: str) -> Item:
    return Item(id=item_id, type="arith", question="q", answer="1", difficulty="easy")


def test_completed_run_refuses_overwrite(tmp_path: Path) -> None:
    out_dir = tmp_path / "run"
    out_dir.mkdir()
    (out_dir / "summary.json").write_text("{}", encoding="utf-8")

    with pytest.raises(FileExistsError):
        cli._prepare_out_dir(out_dir, force=False, resume=False)


def test_incomplete_run_refuses_without_resume_or_force(tmp_path: Path) -> None:
    out_dir = tmp_path / "run"
    out_dir.mkdir()
    (out_dir / "raw.jsonl").write_text("{}", encoding="utf-8")

    with pytest.raises(FileExistsError):
        cli._prepare_out_dir(out_dir, force=False, resume=False)


def test_force_deletes_old_output_and_reruns(tmp_path: Path, monkeypatch) -> None:
    out_dir = tmp_path / "run"
    out_dir.mkdir()
    (out_dir / "summary.json").write_text("old", encoding="utf-8")
    (out_dir / "raw.jsonl").write_text("old", encoding="utf-8")

    cli._prepare_out_dir(out_dir, force=True, resume=False)
    assert not out_dir.exists()

    out_dir.mkdir()

    monkeypatch.setattr(cli, "run_item", lambda item, model, config: {"id": item.id})
    monkeypatch.setattr(cli, "summarize_rows", lambda rows: _DummySummary(n=len(rows)))
    rows, summary = cli._run_experiment(
        items=[_item("a"), _item("b")],
        model=object(),
        config=_config(),
        out_dir=out_dir,
        resume=False,
    )

    assert [row["id"] for row in rows] == ["a", "b"]
    assert summary.n == 2
    assert (out_dir / "raw.jsonl").exists()


def test_resume_skips_completed_item_ids(tmp_path: Path, monkeypatch) -> None:
    out_dir = tmp_path / "run"
    out_dir.mkdir()
    (out_dir / "raw.jsonl").write_text('{"id":"a"}\n', encoding="utf-8")

    calls: list[str] = []

    def fake_run_item(item, model, config):
        calls.append(item.id)
        return {"id": item.id}

    monkeypatch.setattr(cli, "run_item", fake_run_item)
    monkeypatch.setattr(cli, "summarize_rows", lambda rows: _DummySummary(n=len(rows)))

    rows, summary = cli._run_experiment(
        items=[_item("a"), _item("b")],
        model=object(),
        config=_config(),
        out_dir=out_dir,
        resume=True,
    )

    assert calls == ["b"]
    assert [row["id"] for row in rows] == ["a", "b"]
    assert summary.n == 2


def test_summary_is_written_atomically(tmp_path: Path) -> None:
    summary_path = tmp_path / "summary.json"
    cli._write_summary_atomic(summary_path, _DummySummary(n=1))

    assert summary_path.exists()
    assert not summary_path.with_suffix(".json.tmp").exists()
    assert "n" in summary_path.read_text(encoding="utf-8")
