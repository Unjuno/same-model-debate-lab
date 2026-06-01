from pathlib import Path

from smdebate.storage import load_items, write_json, write_jsonl


def test_jsonl_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "items.jsonl"
    write_jsonl(
        path,
        [
            {
                "id": "q1",
                "type": "arith",
                "difficulty": "easy",
                "question": "What is 1+1?",
                "answer": "2",
                "metadata": {"x": 1},
            }
        ],
    )

    items = load_items(path)

    assert len(items) == 1
    assert items[0].id == "q1"
    assert items[0].answer == "2"


def test_write_json(tmp_path: Path) -> None:
    path = tmp_path / "summary.json"
    write_json(path, {"accuracy": 1.0})
    assert path.exists()
    assert "accuracy" in path.read_text(encoding="utf-8")
