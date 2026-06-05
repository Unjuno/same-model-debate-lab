from __future__ import annotations

import argparse
import json
import random
from collections.abc import Callable
from pathlib import Path
from typing import Any

PROBLEM_TYPES = (
    "symbolic_rule_chain",
    "table_lookup_arithmetic",
    "state_transition",
    "modular_schedule",
    "program_trace",
    "constraint_grid",
)

DIFFICULTY_STEPS = {
    "easy": (2, 3),
    "medium": (4, 6),
    "hard": (7, 10),
    "adversarial": (7, 10),
}


def _answer_suffix() -> str:
    return " Return only the final answer inside <answer>...</answer>."


def _step_count(rng: random.Random, difficulty: str) -> int:
    low, high = DIFFICULTY_STEPS[difficulty]
    return rng.randint(low, high)


def _make_id(prefix: str, index: int) -> str:
    return f"{prefix}_{index:03d}"


def make_symbolic_rule_chain(index: int, difficulty: str, rng: random.Random) -> dict[str, Any]:
    start = rng.randint(2, 9)
    add1 = rng.randint(1, 5)
    branch_value = rng.randint(2, 4)
    subtract = rng.randint(1, 5)
    branch_trigger = rng.choice([True, False])
    extra_add = rng.randint(1, 4)
    exception_value = rng.randint(1, 3)

    value = start
    steps = [f"Start with {start}."]
    value += add1
    steps.append(f"Add {add1}.")
    if branch_trigger:
        value *= branch_value
        steps.append(f"If the flag is true, multiply by {branch_value}.")
    else:
        value += extra_add
        steps.append(f"If the flag is false, add {extra_add}.")
    if difficulty in {"hard", "adversarial"}:
        value -= subtract
        steps.append(f"Then subtract {subtract}.")
    if difficulty == "adversarial":
        value += exception_value
        steps.append(f"An exception rule adds {exception_value} at the end.")

    metadata = {
        "start": start,
        "add1": add1,
        "branch_value": branch_value,
        "subtract": subtract,
        "extra_add": extra_add,
        "exception_value": exception_value,
        "branch_trigger": branch_trigger,
    }
    if difficulty == "adversarial":
        metadata["distractor_number"] = rng.randint(50, 120)

    question = _join(
        steps
        + (
            [f"Ignore the irrelevant reference number {metadata['distractor_number']}."]
            if difficulty == "adversarial"
            else []
        )
        + ["What is the final value?"]
    )
    return {
        "id": _make_id("symbolic_rule_chain", index),
        "type": "symbolic_rule_chain",
        "difficulty": difficulty,
        "question": question + _answer_suffix(),
        "answer": str(value),
        "metadata": metadata,
    }


def make_table_lookup_arithmetic(index: int, difficulty: str, rng: random.Random) -> dict[str, Any]:
    rows = [
        {"name": "alpha", "base": rng.randint(3, 9), "bonus": rng.randint(1, 4)},
        {"name": "beta", "base": rng.randint(4, 10), "bonus": rng.randint(1, 5)},
        {"name": "gamma", "base": rng.randint(5, 11), "bonus": rng.randint(1, 6)},
        {"name": "delta", "base": rng.randint(2, 8), "bonus": rng.randint(1, 4)},
    ]
    key = rng.choice([row["name"] for row in rows])
    modifier = 1 if difficulty == "easy" else rng.choice([2, 3])
    subtract_smallest_bonus = difficulty in {"hard", "adversarial"}
    lookup = next(row for row in rows if row["name"] == key)
    value = lookup["base"] + lookup["bonus"] * modifier
    if subtract_smallest_bonus:
        value -= min(row["bonus"] for row in rows)

    metadata = {
        "rows": rows,
        "key": key,
        "modifier": modifier,
        "subtract_smallest_bonus": subtract_smallest_bonus,
    }
    if difficulty == "adversarial":
        metadata["irrelevant_number"] = rng.randint(100, 999)

    question = (
        "A table lists names with a base value and a bonus value. "
        + _join(
            [f"{row['name']} has base {row['base']} and bonus {row['bonus']}." for row in rows]
        )
        + f" Use the row for {key}. Compute base plus bonus times {modifier}"
        + (
            " and then subtract the smallest bonus in the table."
            if subtract_smallest_bonus
            else "."
        )
        + (
            f" Ignore the irrelevant number {metadata['irrelevant_number']}."
            if difficulty == "adversarial"
            else ""
        )
        + " What is the final value?"
    )
    return {
        "id": _make_id("table_lookup_arithmetic", index),
        "type": "table_lookup_arithmetic",
        "difficulty": difficulty,
        "question": question + _answer_suffix(),
        "answer": str(value),
        "metadata": metadata,
    }


def make_state_transition(index: int, difficulty: str, rng: random.Random) -> dict[str, Any]:
    start = rng.choice(["A", "B", "C"])
    steps = _step_count(rng, difficulty)
    ops: list[str] = []
    state = start
    for step_index in range(steps):
        if difficulty in {"hard", "adversarial"} and step_index % 3 == 2:
            op = "hold"
        else:
            op = rng.choice(["swap", "advance", "hold"])
        ops.append(op)
        if op == "swap":
            state = {"A": "B", "B": "C", "C": "A"}[state]
        elif op == "advance":
            state = {"A": "C", "B": "A", "C": "B"}[state]
    metadata = {"start": start, "ops": ops}
    if difficulty == "adversarial":
        metadata["noise"] = [rng.randint(20, 99) for _ in range(3)]

    question = (
        f"Start in state {start}. Apply these operations in order: "
        + ", ".join(ops)
        + (
            f". Ignore the unrelated counters {metadata['noise'][0]}, {metadata['noise'][1]}, and {metadata['noise'][2]}."
            if difficulty == "adversarial"
            else "."
        )
        + " What is the final state?"
    )
    return {
        "id": _make_id("state_transition", index),
        "type": "state_transition",
        "difficulty": difficulty,
        "question": question + _answer_suffix(),
        "answer": state,
        "metadata": metadata,
    }


def make_modular_schedule(index: int, difficulty: str, rng: random.Random) -> dict[str, Any]:
    start_day = rng.randint(1, 7)
    steps = _step_count(rng, difficulty)
    offset = rng.randint(2, 6)
    exception_offset = rng.randint(2, 5)
    day = start_day
    operations: list[str] = []
    for step_index in range(steps):
        if step_index == 1 and difficulty in {"medium", "hard", "adversarial"}:
            day = ((day + offset - 2) % 7) + 1
            operations.append(f"jump {offset}")
        else:
            day = ((day + 1 - 1) % 7) + 1
            operations.append("advance 1")
    if difficulty in {"hard", "adversarial"}:
        day = ((day + exception_offset - 2) % 7) + 1
        operations.append(f"exception jump {exception_offset}")

    metadata = {
        "start_day": start_day,
        "operations": operations,
        "offset": offset,
        "exception_offset": exception_offset,
    }
    if difficulty == "adversarial":
        metadata["irrelevant_numbers"] = [rng.randint(10, 99) for _ in range(2)]

    question = (
        f"The schedule starts on day {start_day} of a 7-day cycle. Apply these moves in order: "
        + "; ".join(operations)
        + (
            f". Ignore the irrelevant numbers {metadata['irrelevant_numbers'][0]} and {metadata['irrelevant_numbers'][1]}."
            if difficulty == "adversarial"
            else "."
        )
        + " What day number is the final result?"
    )
    return {
        "id": _make_id("modular_schedule", index),
        "type": "modular_schedule",
        "difficulty": difficulty,
        "question": question + _answer_suffix(),
        "answer": str(day),
        "metadata": metadata,
    }


def make_program_trace(index: int, difficulty: str, rng: random.Random) -> dict[str, Any]:
    initial_x = rng.randint(1, 6)
    initial_y = rng.randint(1, 6)
    x = initial_x
    y = initial_y
    steps = _step_count(rng, difficulty)
    ops: list[dict[str, Any]] = []
    for step_index in range(steps):
        if step_index % 3 == 0:
            inc = rng.randint(1, 3)
            x += inc
            ops.append({"op": "add_x", "value": inc})
        elif step_index % 3 == 1:
            factor = 2 if difficulty != "easy" else 1
            y *= factor
            ops.append({"op": "mul_y", "value": factor})
        else:
            x, y = y, x
            ops.append({"op": "swap"})

    metadata = {"initial": {"x": initial_x, "y": initial_y}, "ops": ops}
    x2 = initial_x
    y2 = initial_y
    for entry in ops:
        if entry["op"] == "add_x":
            x2 += int(entry["value"])
        elif entry["op"] == "mul_y":
            y2 *= int(entry["value"])
        else:
            x2, y2 = y2, x2
    if difficulty == "adversarial":
        metadata["noise"] = [rng.randint(10, 90) for _ in range(2)]

    question = (
        "Consider a tiny program that tracks x and y. Apply the following operations in order: "
        + ", ".join(entry["op"] + (f" {entry['value']}" if "value" in entry else "") for entry in ops)
        + (
            f". Ignore the unrelated constants {metadata['noise'][0]} and {metadata['noise'][1]}."
            if difficulty == "adversarial"
            else "."
        )
        + " What are the final values of x and y, in that order, separated by a comma?"
    )
    return {
        "id": _make_id("program_trace", index),
        "type": "program_trace",
        "difficulty": difficulty,
        "question": question + _answer_suffix(),
        "answer": f"{x2},{y2}",
        "metadata": metadata,
    }


def make_constraint_grid(index: int, difficulty: str, rng: random.Random) -> dict[str, Any]:
    positions = ["A", "B", "C", "D"]
    colors = ["red", "blue", "green", "yellow"]
    permuted = rng.sample(colors, k=4)
    mapping = dict(zip(positions, permuted, strict=True))
    target = rng.choice(positions)
    answer = mapping[target]
    clues = [f"{pos} is {color}." for pos, color in mapping.items()]
    if difficulty in {"medium", "hard", "adversarial"}:
        clues.append(f"{target} is not the last label in the alphabet.")
    if difficulty in {"hard", "adversarial"}:
        clues.append("The clue order is not important.")
    if difficulty == "adversarial":
        clues.append(f"Ignore the irrelevant count {rng.randint(10, 99)}.")

    metadata = {"mapping": mapping, "target": target, "clues": clues}
    question = (
        "A four-cell constraint grid has labels A, B, C, and D. "
        + " ".join(clues)
        + f" Which color is assigned to {target}?"
    )
    return {
        "id": _make_id("constraint_grid", index),
        "type": "constraint_grid",
        "difficulty": difficulty,
        "question": question + _answer_suffix(),
        "answer": answer,
        "metadata": metadata,
    }


def _join(parts: list[str]) -> str:
    return " ".join(part.strip() for part in parts if part.strip())


GENERATOR_BY_TYPE: dict[str, Callable[[int, str, random.Random], dict[str, Any]]] = {
    "symbolic_rule_chain": make_symbolic_rule_chain,
    "table_lookup_arithmetic": make_table_lookup_arithmetic,
    "state_transition": make_state_transition,
    "modular_schedule": make_modular_schedule,
    "program_trace": make_program_trace,
    "constraint_grid": make_constraint_grid,
}


def generate_dataset(*, seed: int, n_per_type: int, difficulty: str) -> list[dict[str, Any]]:
    if difficulty not in DIFFICULTY_STEPS:
        raise ValueError(f"unsupported difficulty: {difficulty}")
    rng = random.Random(seed)
    rows: list[dict[str, Any]] = []
    for type_name in PROBLEM_TYPES:
        maker = GENERATOR_BY_TYPE[type_name]
        for index in range(1, n_per_type + 1):
            rows.append(maker(index, difficulty, rng))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a parametric logical dataset.")
    parser.add_argument("--out", required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--n-per-type", type=int, default=100)
    parser.add_argument(
        "--difficulty",
        choices=["easy", "medium", "hard", "adversarial"],
        required=True,
    )
    args = parser.parse_args()

    rows = generate_dataset(seed=args.seed, n_per_type=args.n_per_type, difficulty=args.difficulty)
    write_jsonl(Path(args.out), rows)
    print(f"wrote {len(rows)} rows to {args.out}")


if __name__ == "__main__":
    main()
