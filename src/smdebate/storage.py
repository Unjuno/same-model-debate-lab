from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from smdebate.protocol import Item


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_items(path: Path) -> list[Item]:
    items: list[Item] = []
    for row in load_jsonl(path):
        items.append(
            Item(
                id=row["id"],
                type=row["type"],
                difficulty=row.get("difficulty", "unknown"),
                question=row["question"],
                answer=str(row["answer"]),
                metadata=row.get("metadata"),
            )
        )
    return items


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
