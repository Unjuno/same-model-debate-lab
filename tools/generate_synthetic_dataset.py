from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any


def make_arith(index: int, rng: random.Random) -> dict[str, Any]:
    red = rng.randint(8, 40)
    blue = rng.randint(8, 40)
    remove_blue = rng.randint(1, min(blue, 12))
    add_red = rng.randint(1, 12)
    answer = red + blue - remove_blue + add_red
    return {
        "id": f"arith_{index:03d}",
        "type": "arith",
        "difficulty": "easy",
        "question": (
            f"A box has {red} red balls and {blue} blue balls. "
            f"{remove_blue} blue balls are removed and {add_red} red balls are added. "
            "How many balls are in the box now? Return only the number."
        ),
        "answer": str(answer),
        "metadata": {
            "red": red,
            "blue": blue,
            "remove_blue": remove_blue,
            "add_red": add_red,
        },
    }


def make_code_output(index: int, rng: random.Random) -> dict[str, Any]:
    templates = [
        (
            "x = [{a}, {b}]\ny = x\nx.append({c})\nprint(len(y))",
            lambda a, b, c: str(3),
        ),
        (
            "total = 0\nfor n in range({a}, {b}):\n    total += n\nprint(total)",
            lambda a, b, c: str(sum(range(a, b))),
        ),
        (
            "x = {a}\ny = {b}\nprint((x < y) and (x + y == {s}))",
            lambda a, b, c: str((a < b) and (a + b == a + b)),
        ),
        (
            "d = {{'a': {a}}}\nd['b'] = d['a'] + {b}\nprint(d['b'])",
            lambda a, b, c: str(a + b),
        ),
    ]
    a = rng.randint(1, 8)
    b = rng.randint(a + 1, a + 8)
    c = rng.randint(1, 9)
    template, answer_fn = rng.choice(templates)
    code = template.format(a=a, b=b, c=c, s=a + b)
    return {
        "id": f"code_{index:03d}",
        "type": "code_output",
        "difficulty": "easy",
        "question": f"What does this Python code print?\n\n{code}\n\nReturn only the printed output.",
        "answer": answer_fn(a, b, c),
        "metadata": {"a": a, "b": b, "c": c, "template": code},
    }


def make_rule_logic(index: int, rng: random.Random) -> dict[str, Any]:
    base = rng.randint(2, 12)
    red_bonus = rng.randint(2, 6)
    multiplier = rng.choice([2, 3])
    small_penalty = rng.randint(1, 4)
    is_red = rng.choice([True, False])
    is_square = rng.choice([True, False])
    is_small = rng.choice([True, False])

    score = base
    if is_red:
        score += red_bonus
    if is_square:
        score *= multiplier
    if is_small:
        score -= small_penalty

    traits = []
    traits.append("red" if is_red else "blue")
    traits.append("square" if is_square else "circle")
    traits.append("small" if is_small else "large")
    trait_text = " ".join(traits)

    return {
        "id": f"logic_{index:03d}",
        "type": "rule_logic",
        "difficulty": "easy",
        "question": (
            f"Rules: Start with {base} points. If a card is red, add {red_bonus} points. "
            f"If it is square, multiply the current score by {multiplier}. "
            f"If it is small, subtract {small_penalty} points after all other operations. "
            f"A {trait_text} card is evaluated. What is the final score? Return only the number."
        ),
        "answer": str(score),
        "metadata": {
            "base": base,
            "red_bonus": red_bonus,
            "multiplier": multiplier,
            "small_penalty": small_penalty,
            "is_red": is_red,
            "is_square": is_square,
            "is_small": is_small,
        },
    }


def generate_dataset(seed: int = 0, n_per_type: int = 30) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    rows: list[dict[str, Any]] = []
    for index in range(1, n_per_type + 1):
        rows.append(make_arith(index, rng))
        rows.append(make_code_output(index, rng))
        rows.append(make_rule_logic(index, rng))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a deterministic synthetic dataset.")
    parser.add_argument("--out", default="data/generated/synthetic_minimal_90.jsonl")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--n-per-type", type=int, default=30)
    args = parser.parse_args()

    rows = generate_dataset(seed=args.seed, n_per_type=args.n_per_type)
    write_jsonl(Path(args.out), rows)
    print(f"wrote {len(rows)} rows to {args.out}")


if __name__ == "__main__":
    main()
