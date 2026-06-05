from tools.generate_parametric_logic_dataset import PROBLEM_TYPES, generate_dataset


def test_generation_is_deterministic_for_same_seed() -> None:
    left = generate_dataset(seed=123, n_per_type=2, difficulty="medium")
    right = generate_dataset(seed=123, n_per_type=2, difficulty="medium")
    assert left == right


def test_generated_rows_have_required_fields_and_answer_suffix() -> None:
    rows = generate_dataset(seed=1, n_per_type=1, difficulty="easy")
    assert len(rows) == len(PROBLEM_TYPES)

    for row in rows:
        assert set(row) >= {"id", "type", "difficulty", "question", "answer", "metadata"}
        assert row["answer"] != ""
        assert row["question"].endswith("Return only the final answer inside <answer>...</answer>.")
        assert row["type"] in PROBLEM_TYPES


def test_each_problem_type_appears_and_all_difficulties_work() -> None:
    for difficulty in ["easy", "medium", "hard", "adversarial"]:
        rows = generate_dataset(seed=7, n_per_type=2, difficulty=difficulty)
        types = {row["type"] for row in rows}
        assert types == set(PROBLEM_TYPES)
        assert all(row["difficulty"] == difficulty for row in rows)


def test_generation_does_not_touch_network(monkeypatch) -> None:
    import socket

    def fail_connect(*args, **kwargs):  # pragma: no cover - defensive guard
        raise AssertionError("network access is not allowed")

    monkeypatch.setattr(socket.socket, "connect", fail_connect, raising=True)
    generate_dataset(seed=0, n_per_type=1, difficulty="easy")
