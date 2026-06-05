from tools.prepare_aqua_hf_subset import convert_aqua_row, prepare_aqua_subset


def test_prepare_subset_is_deterministic(monkeypatch) -> None:
    dataset = [
        {"question": f"Q{i}", "options": [f"o{i}a", f"o{i}b", f"o{i}c", f"o{i}d"], "correct": "A"}
        for i in range(10)
    ]

    def fake_load_dataset(split: str):
        return dataset

    monkeypatch.setattr("tools.prepare_aqua_hf_subset._load_dataset", fake_load_dataset)

    left = prepare_aqua_subset(split="test", seed=0, limit=5)
    right = prepare_aqua_subset(split="test", seed=0, limit=5)
    assert left == right


def test_convert_row_renders_options_and_normalizes_answer() -> None:
    row = {
        "question": "What is 2+2?",
        "options": ["1", "2", "4", "5"],
        "correct": "b",
    }

    item = convert_aqua_row(row, original_index=7, seed=3, split="test")

    assert item["id"] == "aqua_test_3_000007"
    assert item["type"] == "aqua_rat"
    assert item["answer"] == "B"
    assert "A. 1" in item["question"]
    assert "B. 2" in item["question"]
    assert item["question"].endswith("Return only the option letter inside <answer>...</answer>.")
    assert item["metadata"]["source"] == "deepmind/aqua_rat"
    assert item["metadata"]["split"] == "test"
    assert item["metadata"]["original_index"] == 7
    assert item["metadata"]["seed"] == 3


def test_prepare_subset_uses_limit_and_sampling(monkeypatch) -> None:
    dataset = [
        {"question": f"Q{i}", "options": [f"a{i}", f"b{i}", f"c{i}", f"d{i}"], "correct": "A"}
        for i in range(20)
    ]

    monkeypatch.setattr("tools.prepare_aqua_hf_subset._load_dataset", lambda split: dataset)

    rows = prepare_aqua_subset(split="test", seed=1, limit=4)

    assert len(rows) == 4
    assert len({row["id"] for row in rows}) == 4


def test_prepare_subset_does_not_require_network(monkeypatch) -> None:
    import socket

    def fail_connect(*args, **kwargs):  # pragma: no cover - defensive guard
        raise AssertionError("network access is not allowed")

    monkeypatch.setattr(socket.socket, "connect", fail_connect, raising=True)
    monkeypatch.setattr("tools.prepare_aqua_hf_subset._load_dataset", lambda split: [])

    assert prepare_aqua_subset(split="test", seed=0, limit=1) == []
