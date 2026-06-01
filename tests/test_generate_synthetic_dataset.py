from tools.generate_synthetic_dataset import generate_dataset


def test_generated_dataset_has_expected_count() -> None:
    rows = generate_dataset(seed=0, n_per_type=2)
    assert len(rows) == 6


def test_generated_dataset_has_required_fields_and_unique_ids() -> None:
    rows = generate_dataset(seed=0, n_per_type=5)
    ids = [row["id"] for row in rows]

    assert len(ids) == len(set(ids))
    for row in rows:
        assert set(row) >= {"id", "type", "difficulty", "question", "answer", "metadata"}
        assert row["answer"] != ""


def test_generation_is_deterministic_for_same_seed() -> None:
    assert generate_dataset(seed=123, n_per_type=3) == generate_dataset(seed=123, n_per_type=3)
