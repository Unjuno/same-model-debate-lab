from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from smdebate.metrics import is_correct
from tools.filter_by_independent_calibration import load_jsonl, normalize_answer, write_json


def _load_summary(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _initial_answers(row: dict[str, Any]) -> list[str]:
    if "initial_raw" in row:
        return [normalize_answer(entry.get("answer", "")) for entry in row["initial_raw"]]
    return [normalize_answer(answer) for answer in row.get("initial_answers", [])]


def _final_answer(row: dict[str, Any]) -> str:
    if "final_answer" in row:
        return normalize_answer(row["final_answer"])
    final_answers = row.get("final_answers", [])
    return normalize_answer(final_answers[0]) if final_answers else ""


def _category(correctness: list[bool]) -> str:
    if not correctness:
        return "persistent_error"
    if all(correctness):
        return "preserved_correct"
    if not any(correctness):
        return "persistent_error"

    transitions = sum(int(a != b) for a, b in zip(correctness, correctness[1:], strict=False))
    if transitions > 1:
        return "oscillation"
    first_true = correctness.index(True)
    last_true = len(correctness) - 1 - correctness[::-1].index(True)
    if first_true > 0 and all(correctness[first_true:]):
        return "recovery"
    if last_true < len(correctness) - 1 and all(not value for value in correctness[last_true + 1 :]):
        return "deterioration"
    if correctness[0] and not correctness[-1]:
        return "deterioration"
    if not correctness[0] and correctness[-1]:
        return "recovery"
    return "oscillation" if transitions else "persistent_error"


def _flip_count(correctness: list[bool]) -> int:
    return sum(int(a != b) for a, b in zip(correctness, correctness[1:], strict=False))


def analyze_round_sweep(*, data_path: Path, run_specs: list[tuple[int, Path]]) -> dict[str, Any]:
    data_rows = {row["id"]: row for row in load_jsonl(data_path)}
    runs: dict[int, dict[str, Any]] = {}
    per_run_rows: dict[int, dict[str, dict[str, Any]]] = {}

    for r, run_dir in run_specs:
        raw_rows = {row["id"]: row for row in load_jsonl(run_dir / "raw.jsonl")}
        summary = _load_summary(run_dir / "summary.json")
        runs[r] = summary
        per_run_rows[r] = raw_rows

    item_id_sets = [set(rows) for rows in per_run_rows.values()]
    item_ids = sorted(set.intersection(*item_id_sets)) if item_id_sets else []
    trajectories: list[dict[str, Any]] = []
    categories: dict[str, int] = {
        "preserved_correct": 0,
        "persistent_error": 0,
        "recovery": 0,
        "deterioration": 0,
        "oscillation": 0,
    }

    for item_id in item_ids:
        data_row = data_rows.get(item_id, {})
        rows_by_r = [per_run_rows[r][item_id] for r, _ in run_specs]
        initial_answers = _initial_answers(rows_by_r[0])
        final_answer_by_r = {
            str(r): _final_answer(row) for (r, _), row in zip(run_specs, rows_by_r, strict=True)
        }
        correctness_by_r = {str(r): is_correct(final_answer_by_r[str(r)], data_row.get("answer", "")) for r, _ in run_specs}
        correctness_list = [correctness_by_r[str(r)] for r, _ in run_specs]
        category = _category(correctness_list)
        categories[category] += 1
        flip_count = _flip_count(correctness_list)
        round_numbers = [r for r, _ in run_specs]
        first_correct_r = next(
            (r for r, ok in zip(round_numbers, correctness_list, strict=True) if ok),
            None,
        )
        first_wrong_after_correct_r = None
        seen_correct = False
        for r, ok in zip(round_numbers, correctness_list, strict=True):
            if ok:
                seen_correct = True
            elif seen_correct:
                first_wrong_after_correct_r = r
                break

        trajectories.append(
            {
                "item_id": item_id,
                "gold": normalize_answer(data_row.get("answer", "")),
                "initial_answers": initial_answers,
                "final_answer_by_R": final_answer_by_r,
                "correctness_by_R": correctness_by_r,
                "flip_count": flip_count,
                "first_correct_R": first_correct_r,
                "first_wrong_after_correct_R": first_wrong_after_correct_r,
                "category": category,
            }
        )

    return {
        "data": str(data_path),
        "run_summaries": {str(r): runs[r] for r in sorted(runs)},
        "trajectories": trajectories,
        "category_counts": categories,
    }


def _markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(out)


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines: list[str] = []
    lines.append("# AQuA Round Sweep")
    lines.append("")
    lines.append("## Aggregate Metrics")
    rows = []
    for r, summary in sorted(report["run_summaries"].items(), key=lambda item: int(item[0])):
        rows.append(
            [
                r,
                summary["accuracy"],
                summary["answer_loss_rate"],
                summary["same_error_agreement_rate"],
                summary["diversity_drop"],
                summary["extraction_failure_rate"],
            ]
        )
    lines.append(
        _markdown_table(
            ["R", "accuracy", "answer_loss_rate", "same_error_agreement_rate", "diversity_drop", "extraction_failure_rate"],
            rows,
        )
    )
    lines.append("")
    lines.append("## Trajectory Categories")
    for category, count in report["category_counts"].items():
        lines.append(f"- {category}: {count}")
    lines.append("")
    lines.append("## Item Trajectories")
    lines.append(
        _markdown_table(
            [
                "item_id",
                "gold",
                "initial_answers",
                "final_answer_by_R",
                "correctness_by_R",
                "flip_count",
                "category",
            ],
            [
                [
                    row["item_id"],
                    row["gold"],
                    row["initial_answers"],
                    row["final_answer_by_R"],
                    row["correctness_by_R"],
                    row["flip_count"],
                    row["category"],
                ]
                for row in report["trajectories"]
            ],
        )
    )
    lines.append("")
    lines.append("No raw transcripts are included in this report.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a debate round sweep.")
    parser.add_argument("--data", required=True)
    parser.add_argument("--runs", nargs="+", required=True, help="Pairs like R:path/to/run_dir")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    run_specs: list[tuple[int, Path]] = []
    for spec in args.runs:
        rounds_text, run_dir = spec.split(":", 1)
        run_specs.append((int(rounds_text), Path(run_dir)))

    report = analyze_round_sweep(data_path=Path(args.data), run_specs=run_specs)
    write_json(Path(args.out_json), report)
    write_markdown(report, Path(args.out_md))
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
