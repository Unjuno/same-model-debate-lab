from tools.select_partial_correct_items import select_partial_correct_items


def _row(item_id: str, answer: str) -> dict:
    return {"id": item_id, "type": "gsm8k", "question": "q", "answer": answer, "metadata": {}}


def test_select_partial_correct_items_handles_numeric_answers() -> None:
    data_rows = [_row("keep", "1234"), _row("skip", "1234")]
    raw_rows = [
        {
            "id": "keep",
            "gold": "#### 1,234",
            "initial_answers": ["1,234", "1,234", "1"],
            "initial_extraction_failures": 0,
        },
        {
            "id": "skip",
            "gold": "#### 1,234",
            "initial_answers": ["1,234", "1,234", "1,234"],
            "initial_extraction_failures": 0,
        },
    ]

    selected = select_partial_correct_items(raw_rows=raw_rows, data_rows=data_rows)

    assert [row["id"] for row in selected] == ["keep"]


def test_select_partial_correct_items_excludes_failures_and_all_wrong() -> None:
    data_rows = [_row("failed", "5"), _row("wrong", "5")]
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
            "id": "wrong",
            "gold": "#### 5",
            "initial_answers": ["1", "2", "3"],
            "initial_extraction_failures": 0,
        },
    ]

    selected = select_partial_correct_items(raw_rows=raw_rows, data_rows=data_rows)

    assert selected == []
