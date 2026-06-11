import json

from tools.prepare_gsm8k_benchmark import (
    convert_gsm8k_row,
    load_dataset_from_http,
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


def test_http_loader_parses_rows(monkeypatch) -> None:
    tree = [{"path": "test-00000-of-00001.parquet"}]

    class FakeResponse:
        def __init__(self, payload: dict) -> None:
            self._payload = payload

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            if isinstance(self._payload, bytes):
                return self._payload
            return json.dumps(self._payload).encode("utf-8")

    def fake_urlopen(url, timeout=30):
        if "api/datasets/openai/gsm8k/tree/main" in url:
            return FakeResponse(tree)
        if "resolve/main/test-00000-of-00001.parquet" in url:
            return FakeResponse(b"parquet")
        raise AssertionError(f"unexpected url: {url}")

    class FakeFrame:
        def to_dict(self, orient="records"):
            return [
                {"question": "Q0", "answer": "#### 0"},
                {"question": "Q1", "answer": "#### 1"},
            ]

    monkeypatch.setattr("tools.prepare_gsm8k_benchmark.urllib.request.urlopen", fake_urlopen)
    monkeypatch.setattr("tools.prepare_gsm8k_benchmark.Path.exists", lambda self: False)
    monkeypatch.setattr("tools.prepare_gsm8k_benchmark.Path.write_bytes", lambda self, data: len(data))
    monkeypatch.setattr("tools.prepare_gsm8k_benchmark.Path.mkdir", lambda self, parents=True, exist_ok=True: None)
    monkeypatch.setattr("tools.prepare_gsm8k_benchmark.pd.read_parquet", lambda path: FakeFrame())

    rows = load_dataset_from_http("test", limit=2)

    assert len(rows) == 2
    assert rows[0]["question"] == "Q0"
