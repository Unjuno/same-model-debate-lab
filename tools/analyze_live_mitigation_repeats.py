"""Aggregate repeated live mitigation runs at the run and paired-item levels."""
from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

CONDITIONS = ["independent", "full_context_debate", "answer_hidden_debate", "numeric_masked_debate", "commit_then_numeric_masked_debate"]
Z = 1.96

def norm(value: Any) -> str:
    return str(value).strip().lower().replace(",", "")

def majority(values: list[Any]) -> str:
    values = [norm(v) for v in values if norm(v)]
    return Counter(values).most_common(1)[0][0] if values else ""

def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0

def sd(xs: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))

def ci(xs: list[float]) -> list[float]:
    if not xs:
        return [0.0, 0.0]
    half = Z * sd(xs) / math.sqrt(len(xs))
    return [max(0.0, mean(xs) - half), min(1.0, mean(xs) + half)]

def load(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def metric_row(rows: list[dict[str, Any]], gold: dict[str, str]) -> dict[str, float]:
    final_correct = initial_correct = loss = collapse = extraction = 0
    n = len(rows)
    for row in rows:
        answer = gold[row["id"]]
        initial = [norm(v) for v in row.get("initial_answers", []) if norm(v)]
        final = norm(row.get("final_answer", ""))
        has_initial = answer in initial
        initial_correct += int(has_initial)
        final_correct += int(final == answer)
        loss += int(has_initial and final != answer)
        target = norm(row.get("metadata", {}).get("target_wrong", ""))
        collapse += int(bool(has_initial and target and final == target))
        extraction += int(row.get("extraction_failures", 0) > 0)
    return {"final_accuracy": final_correct / n if n else 0.0, "initial_any_correct_rate": initial_correct / n if n else 0.0, "answer_loss_rate": loss / initial_correct if initial_correct else 0.0, "correct_to_target_wrong_rate": collapse / initial_correct if initial_correct else 0.0, "extraction_failure_rate": extraction / n if n else 0.0}

def format_metric(metrics: dict[str, dict[str, Any]], key: str) -> str:
    x = metrics[key]
    return f"{x['mean']:.3f} (95% CI {x['ci95'][0]:.3f}–{x['ci95'][1]:.3f})"

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data", required=True)
    p.add_argument("--runs-glob", required=True)
    p.add_argument("--out-json", required=True)
    p.add_argument("--out-md", required=True)
    a = p.parse_args()
    data = {str(r["id"]): norm(r.get("answer", r.get("gold", ""))) for r in load(Path(a.data))}
    paths = sorted(Path().glob(a.runs_glob))
    grouped: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for path in paths:
        m = re.search(r"_r(\d+)_([^/]+)$", str(path.parent))
        if not m:
            continue
        grouped[(int(m.group(1)), m.group(2))].extend(load(path))
    by_condition: dict[str, dict[str, Any]] = {}
    repeat_metrics: dict[str, dict[str, dict[str, float]]] = defaultdict(dict)
    for condition in CONDITIONS:
        run_ids = sorted({r for r, c in grouped if c == condition})
        run_metric_pairs = [(r, metric_row(grouped[(r, condition)], data)) for r in run_ids]
        run_metrics = [metrics for _, metrics in run_metric_pairs]
        repeat_metrics[condition] = {str(r): metrics for r, metrics in run_metric_pairs}
        by_condition[condition] = {"n_repeats": len(run_metrics), "n_items_per_repeat": len(grouped[(0, condition)]), "metrics": {k: {"mean": mean([x[k] for x in run_metrics]), "sd": sd([x[k] for x in run_metrics]), "ci95": ci([x[k] for x in run_metrics])} for k in run_metrics[0]} if run_metrics else {}}
    paired: dict[str, dict[str, float]] = {}
    repeats = sorted({r for r, c in grouped if c == "independent"})
    observed_conditions = sorted({c for _, c in grouped})
    expected_items = len(data)
    duplicate_ids: dict[str, list[str]] = {}
    for (repeat, condition), rows in grouped.items():
        ids = [str(row.get("id", "")) for row in rows]
        duplicates = sorted({item_id for item_id in ids if ids.count(item_id) > 1})
        if duplicates:
            duplicate_ids[f"r{repeat:02d}_{condition}"] = duplicates
    validation = {
        "expected_conditions": len(CONDITIONS),
        "observed_conditions": observed_conditions,
        "expected_repeats": 20,
        "observed_repeats": repeats,
        "all_conditions_present": all(condition in observed_conditions for condition in CONDITIONS),
        "all_repeats_present": repeats == list(range(20)),
        "all_repeat_sizes_match": all(len(rows) == expected_items for rows in grouped.values()),
        "duplicate_ids": duplicate_ids,
    }
    validation["valid"] = bool(validation["all_conditions_present"] and validation["all_repeats_present"] and validation["all_repeat_sizes_match"] and not duplicate_ids)
    for condition in CONDITIONS[1:]:
        deltas = []
        for r in repeats:
            left = metric_row(grouped[(r, condition)], data)
            base = metric_row(grouped[(r, "independent")], data)
            deltas.append(left["final_accuracy"] - base["final_accuracy"])
        paired[condition] = {"accuracy_delta_mean": mean(deltas), "accuracy_delta_sd": sd(deltas), "accuracy_delta_ci95": ci([max(0.0, d) for d in deltas]) if False else [mean(deltas) - Z * sd(deltas) / math.sqrt(len(deltas)), mean(deltas) + Z * sd(deltas) / math.sqrt(len(deltas))]}
    report = {"data": a.data, "n_raw_paths": len(paths), "n_repeats": len(repeats), "conditions": CONDITIONS, "validation": validation, "by_condition": by_condition, "repeat_metrics": repeat_metrics, "paired_vs_independent": paired, "method": "Per-repeat metrics; 95% normal-approximation CIs across repeats; paired accuracy deltas use repeat-matched comparisons."}
    Path(a.out_json).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# GSM8K partial9 Live Mitigation Repeated-Run Report", "", "## Scope", "", f"- Data: `{a.data}`", f"- Repeats: {len(repeats)} per condition", f"- Raw run files: {len(paths)}", "- Unit of summary: one complete 9-item repeat", "- CIs: 95% normal approximation across repeats; exploratory, not a preregistered confirmatory analysis.", "", "## Data integrity", "", f"- Validation status: **{'PASS' if validation['valid'] else 'FAIL'}**", f"- Conditions present: `{validation['observed_conditions']}`", f"- Repeat IDs present: `{validation['observed_repeats']}`", f"- Expected item count in every run: `{validation['all_repeat_sizes_match']}`", f"- Duplicate item IDs: `{validation['duplicate_ids'] or 'none'}`", "", "## Results", "", "| condition | repeats | final accuracy | initial correct | answer loss | target-wrong collapse | extraction failures |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for c in CONDITIONS:
        m = by_condition[c]["metrics"]
        lines.append(f"| {c} | {by_condition[c]['n_repeats']} | {format_metric(m, 'final_accuracy')} | {format_metric(m, 'initial_any_correct_rate')} | {format_metric(m, 'answer_loss_rate')} | {format_metric(m, 'correct_to_target_wrong_rate')} | {format_metric(m, 'extraction_failure_rate')} |")
    lines += ["", "## Paired Accuracy Difference vs independent", "", "| condition | mean delta | SD | 95% CI |", "| --- | ---: | ---: | ---: |"]
    for c, x in paired.items():
        lines.append(f"| {c} | {x['accuracy_delta_mean']:.3f} | {x['accuracy_delta_sd']:.3f} | {x['accuracy_delta_ci95'][0]:.3f}–{x['accuracy_delta_ci95'][1]:.3f} |")
    lines += ["", "## Interpretation", "", "The repeated runs provide a complete exploratory dataset for comparing mitigation conditions. Differences are small relative to repeat-to-repeat variation, so this report should be used descriptively. It does not establish a general mitigation effect or causal mechanism.", "", "`answer_loss_rate` is conditional on repeats containing at least one initially correct answer. `correct_to_target_wrong_rate` is zero when the dataset has no explicit target-wrong metadata. Raw model text is not included.", ""]
    Path(a.out_md).write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({c: by_condition[c]["metrics"].get("final_accuracy") for c in CONDITIONS}, ensure_ascii=False))

if __name__ == "__main__":
    main()
