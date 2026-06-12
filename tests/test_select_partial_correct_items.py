from pathlib import Path

from tools.select_partial_correct_items import (
    normalize_answer,
    select_partial_correct_items,
    write_jsonl,
)


def _benchmark_row(item_id: str, answer: str) -> dict:
    return {"id": item_id, "type": "benchmark", "question": "q", "answer": answer, "metadata": {}}


def test_normalize_answer_handles_numeric_and_letter_answers() -> None:
    assert normalize_answer("29") == "29"
    assert normalize_answer("29.00") == "29"
    assert normalize_answer("1,000") == "1000"
    assert normalize_answer("<answer> b </answer>") == "B"


def test_select_partial_correct_items_handles_numeric_and_multiple_choice_answers(tmp_path: Path) -> None:
    data_rows = [
        _benchmark_row("gsm8k_keep", "1234"),
        _benchmark_row("gsm8k_skip", "1234"),
        _benchmark_row("mc_keep", "C"),
        _benchmark_row("mc_skip", "C"),
    ]
    raw_rows = [
        {
            "id": "gsm8k_keep",
            "gold": "#### 1,234.00",
            "initial_raw": [
                {"answer": "1,234", "extraction_failed": False},
                {"answer": "1234.00", "extraction_failed": False},
                {"answer": "1", "extraction_failed": False},
            ],
        },
        {
            "id": "gsm8k_skip",
            "gold": "#### 1,234",
            "initial_answers": ["1,234", "1,234.00", "1234"],
            "initial_extraction_failures": 0,
        },
        {
            "id": "mc_keep",
            "gold": "c",
            "initial_raw": [
                {"answer": "C", "extraction_failed": False},
                {"answer": "A", "extraction_failed": False},
                {"answer": "B", "extraction_failed": False},
            ],
        },
        {
            "id": "mc_skip",
            "gold": "C",
            "initial_raw": [
                {"answer": "C", "extraction_failed": False},
                {"answer": "C", "extraction_failed": False},
                {"answer": "C", "extraction_failed": False},
            ],
        },
    ]

    selected = select_partial_correct_items(raw_rows=raw_rows, data_rows=data_rows, limit=2)

    assert [row["id"] for row in selected] == ["gsm8k_keep", "mc_keep"]
    out = tmp_path / "out.jsonl"
    write_jsonl(out, selected)
    assert out.exists()


def test_select_partial_correct_items_excludes_failures_and_respects_exclusions() -> None:
    data_rows = [_benchmark_row("failed", "5"), _benchmark_row("excluded", "5"), _benchmark_row("wrong", "5")]
    raw_rows = [
        {
            "id": "failed",
            "gold": "#### 5",
            "initial_raw": [
                {"answer": "5", "extraction_failed": True},
                {"answer": "5", "extraction_failed": False},
                {"answer": "1", "extraction_failed": False},
            ],
        },
        {
            "id": "excluded",
            "gold": "#### 5",
            "initial_raw": [
                {"answer": "5", "extraction_failed": False},
                {"answer": "1", "extraction_failed": False},
                {"answer": "2", "extraction_failed": False},
            ],
        },
        {
            "id": "wrong",
            "gold": "#### 5",
            "initial_answers": ["1", "2", "3"],
            "initial_extraction_failures": 0,
        },
    ]

    selected = select_partial_correct_items(raw_rows=raw_rows, data_rows=data_rows, excluded_ids={"excluded"})

    assert selected == []
