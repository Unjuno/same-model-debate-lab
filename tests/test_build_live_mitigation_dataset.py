from pathlib import Path

from tools.build_live_mitigation_dataset import build_dataset
from tools.build_synthetic_prefix_phase3c_dataset import write_jsonl


def test_build_live_mitigation_dataset_limits_rows(tmp_path: Path) -> None:
    data_rows = [
        {"id": "a", "question": "Q1", "answer": "1", "metadata": {"k": 1}},
        {"id": "b", "question": "Q2", "answer": "2", "metadata": {"k": 2}},
    ]
    out = tmp_path / "subset.jsonl"
    rows = build_dataset(data_rows=data_rows, limit=1)
    write_jsonl(out, rows)
    assert out.exists()
    assert len(rows) == 1
    assert rows[0]["id"] == "a"
    assert rows[0]["question"] == "Q1"
    assert rows[0]["answer"] == "1"
