from tools.prepare_gsm8k_benchmark import (
    convert_gsm8k_row,
    normalize_answer,
    prepare_gsm8k_benchmark,
)


def test_normalize_answer_extracts_final_number_and_strips_commas_and_zero_decimal() -> None:
    assert normalize_answer("#### 1,234") == "1234"
    assert normalize_answer("#### 12.0") == "12"
    assert normalize_answer("#### -7") == "-7"


def test_convert_row_renders_prompt_without_answer_leak() -> None:
    row = {
        "question": "If you have 2 apples and get 3 more, how many apples do you have?",
        "answer": "We compute it. #### 5",
    }

    item = convert_gsm8k_row(row, original_index=7, split="test")

    assert item["id"] == "gsm8k_test_000007"
    assert item["type"] == "gsm8k"
    assert item["answer"] == "5"
    assert "#### 5" not in item["question"]
    assert "Return only the final answer" in item["question"]
    assert item["metadata"]["source"] == "gsm8k/main"
    assert item["metadata"]["original_index"] == 7


def test_prepare_gsm8k_benchmark_is_deterministic_with_provided_rows() -> None:
    rows = [
        {"question": "Q0", "answer": "#### 0"},
        {"question": "Q1", "answer": "#### 1"},
        {"question": "Q2", "answer": "#### 2"},
    ]

    left = prepare_gsm8k_benchmark(split="test", limit=2, rows=rows)
    right = prepare_gsm8k_benchmark(split="test", limit=2, rows=rows)

    assert left == right
    assert len(left) == 2
