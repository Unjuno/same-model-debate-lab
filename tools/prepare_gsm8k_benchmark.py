from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

try:
    import pandas as pd
except ImportError:  # pragma: no cover - plain python bootstrap path
    pd = None

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
    api_url = "https://huggingface.co/api/datasets/openai/gsm8k/tree/main?recursive=1"
    with urllib.request.urlopen(api_url, timeout=30) as response:  # nosec B310 - trusted HF endpoint
        tree = json.loads(response.read().decode("utf-8"))
    parquet_paths = [
        entry["path"]
        for entry in tree
        if entry.get("path", "").endswith(f"{split}-00000-of-00001.parquet")
    ]
    if not parquet_paths:
        raise RuntimeError(f"Could not find GSM8K {split} parquet file on Hugging Face.")

    parquet_path = parquet_paths[0]
    download_url = f"https://huggingface.co/datasets/openai/gsm8k/resolve/main/{parquet_path}"
    local_dir = Path(".cache") / "gsm8k"
    local_dir.mkdir(parents=True, exist_ok=True)
    local_path = local_dir / parquet_path.replace("/", "_")
    if not local_path.exists():
        with urllib.request.urlopen(download_url, timeout=60) as response:  # nosec B310 - trusted HF endpoint
            local_path.write_bytes(response.read())

    if pd is None:
        raise RuntimeError("pandas is required to read GSM8K parquet files.")

    frame = pd.read_parquet(local_path)
    rows = frame.to_dict(orient="records")
    return rows[:limit] if limit is not None else rows


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


def ensure_virtualenv_runtime() -> None:
    if "datasets" in sys.modules:
        return
    try:
        import datasets  # noqa: F401
    except ImportError:
        venv_python = Path(".venv") / "bin" / "python"
        if venv_python.exists() and Path(sys.executable) != venv_python.resolve():
            os.execv(str(venv_python), [str(venv_python), *sys.argv])


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
    ensure_virtualenv_runtime()
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
