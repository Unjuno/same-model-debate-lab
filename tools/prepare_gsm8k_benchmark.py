from __future__ import annotations

import argparse
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ANSWER_RE = re.compile(r"####\s*(.+)$", re.MULTILINE)
NUMBER_RE = re.compile(r"^-?[\d,]+(?:\.\d+)?$")


def load_dataset_from_datasets(split: str) -> list[dict[str, Any]]:
    try:
        from datasets import load_dataset
    except ImportError as exc:  # pragma: no cover - exercised in environments without datasets
        raise RuntimeError(
            "datasets is required for this code path."
        ) from exc

    rows = load_dataset("gsm8k", "main", split=split)
    return [dict(row) for row in rows]


def normalize_answer(value: Any) -> str:
    text = str(value).strip()
    match = ANSWER_RE.search(text)
    if match:
        text = match.group(1).strip()
    text = text.replace(",", "")
    if NUMBER_RE.match(text):
        if "." in text:
            integer, fraction = text.split(".", 1)
            if set(fraction) <= {"0"} and integer not in {"", "-"}:
                return integer
        return text
    return text


def normalize_gsm8k_gold(value: Any) -> str:
    return normalize_answer(value)


def load_dataset_from_http(split: str, limit: int | None = None) -> list[dict[str, Any]]:
    base_url = "https://datasets-server.huggingface.co/rows"
    params = {
        "dataset": "openai/gsm8k",
        "config": "main",
        "split": split,
        "offset": 0,
        "length": limit or 2000,
    }
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=30) as response:  # nosec B310 - trusted HF endpoint
        payload = json.loads(response.read().decode("utf-8"))
    rows = payload.get("rows", [])
    return [row["row"] for row in rows]


def render_question(question: str) -> str:
    return (
        f"{question.strip()}\n\n"
        "Return only the final answer inside <answer>...</answer>."
    )


def convert_gsm8k_row(row: dict[str, Any], *, original_index: int, split: str) -> dict[str, Any]:
    answer = normalize_gsm8k_gold(row.get("answer", ""))
    return {
        "id": f"gsm8k_{split}_{original_index:06d}",
        "type": "gsm8k",
        "difficulty": "unknown",
        "question": render_question(row["question"]),
        "answer": answer,
        "metadata": {
            "source": "gsm8k/main",
            "split": split,
            "original_index": original_index,
        },
    }


def load_dataset(split: str, limit: int | None = None) -> list[dict[str, Any]]:
    try:
        return load_dataset_from_datasets(split)
    except Exception:
        return load_dataset_from_http(split, limit=limit)


def prepare_gsm8k_benchmark(*, split: str = "test", limit: int | None = None, rows: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    source_rows = list(rows if rows is not None else load_dataset(split))
    if limit is not None:
        source_rows = source_rows[:limit]
    return [
        convert_gsm8k_row(row, original_index=index, split=split)
        for index, row in enumerate(source_rows)
    ]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare GSM8K benchmark JSONL files.")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--limits", nargs="+", type=int, required=True)
    parser.add_argument("--split", default="test")
    args = parser.parse_args()

    rows = load_dataset(args.split)
    out_dir = Path(args.out_dir)
    for limit in args.limits:
        selected = prepare_gsm8k_benchmark(split=args.split, limit=limit, rows=rows)
        out_path = out_dir / f"gsm8k_{args.split}_{limit}.jsonl"
        write_jsonl(out_path, selected)
        print(f"wrote {len(selected)} rows to {out_path}")


if __name__ == "__main__":
    main()
