from __future__ import annotations

import argparse
import json
import random
from collections.abc import Iterable
from pathlib import Path
from typing import Any


def _load_dataset(split: str):
    from datasets import load_dataset

    return load_dataset("deepmind/aqua_rat", split=split)


def _options_from_row(row: dict[str, Any]) -> list[str]:
    options = row.get("options")
    if options is None:
        options = [row.get(key) for key in ["option_a", "option_b", "option_c", "option_d", "option_e"]]
        options = [option for option in options if option is not None]
    return [str(option).strip() for option in options]


def _normalize_gold(row: dict[str, Any]) -> str:
    gold = row.get("correct", row.get("answer", row.get("label", "")))
    gold_text = str(gold).strip()
    if gold_text.isdigit():
        index = int(gold_text)
        if 0 <= index < 26:
            return chr(ord("A") + index)
    if len(gold_text) == 1 and gold_text.upper() in {"A", "B", "C", "D", "E"}:
        return gold_text.upper()
    return gold_text.upper()


def _render_question(question: str, options: Iterable[str]) -> str:
    lines = [str(question).strip(), ""]
    for index, option in enumerate(options):
        label = chr(ord("A") + index)
        lines.append(f"{label}. {option}")
    lines.append("")
    lines.append("Return only the option letter inside <answer>...</answer>.")
    return "\n".join(lines)


def convert_aqua_row(row: dict[str, Any], *, original_index: int, seed: int, split: str) -> dict[str, Any]:
    options = _options_from_row(row)
    answer = _normalize_gold(row)
    return {
        "id": f"aqua_{split}_{seed}_{original_index:06d}",
        "type": "aqua_rat",
        "difficulty": "unknown",
        "question": _render_question(row["question"], options),
        "answer": answer,
        "metadata": {
            "source": "deepmind/aqua_rat",
            "split": split,
            "original_index": original_index,
            "seed": seed,
        },
    }


def prepare_aqua_subset(*, split: str, seed: int, limit: int, dataset: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    rows = list(dataset if dataset is not None else _load_dataset(split))
    rng = random.Random(seed)
    indices = sorted(rng.sample(range(len(rows)), k=min(limit, len(rows))))
    return [
        convert_aqua_row(rows[index], original_index=index, seed=seed, split=split)
        for index in indices
    ]


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare a deterministic AQuA-RAT subset.")
    parser.add_argument("--out", required=True)
    parser.add_argument("--split", default="test")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()

    rows = prepare_aqua_subset(split=args.split, seed=args.seed, limit=args.limit)
    _write_jsonl(Path(args.out), rows)
    print(f"wrote {len(rows)} rows to {args.out}")


if __name__ == "__main__":
    main()
