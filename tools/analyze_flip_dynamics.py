from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ruff: noqa: E402

from tools.filter_by_independent_calibration import load_jsonl, normalize_answer, write_json

ROLE_BY_AGENT_ID = {
    1: "solver",
    2: "skeptic/error-checker",
    3: "alternative-solver",
}

AGENT_TRANSITIONS = [
    "correct_to_correct",
    "correct_to_wrong",
    "wrong_to_correct",
    "wrong_to_wrong",
    "missing_initial",
    "missing_final",
]

MAJORITY_TRANSITIONS = [
    "preserved_correct",
    "correct_to_wrong",
    "wrong_to_correct",
    "persistent_error",
    "no_initial_majority",
    "no_final_majority",
]


def _majority(values: list[str]) -> str:
    counts: dict[str, int] = {}
    order: list[str] = []
    for value in values:
        normalized = normalize_answer(value)
        if not normalized:
            continue
        if normalized not in counts:
            order.append(normalized)
            counts[normalized] = 0
        counts[normalized] += 1
    if not counts:
        return ""
    best = max(counts, key=lambda value: (counts[value], -order.index(value)))
    return best


def _correct(answer: str, gold: str) -> bool:
    return normalize_answer(answer) == normalize_answer(gold)


def _answers_for_round(row: dict[str, Any], round_index: int) -> list[str]:
    return [
        normalize_answer(entry.get("answer", ""))
        for entry in row.get("transcript_raw", [])
        if int(entry["round_index"]) == round_index
    ]


def _max_round(row: dict[str, Any]) -> int:
    return max(int(entry["round_index"]) for entry in row.get("transcript_raw", []))


def _agent_transition(initial: str, final: str, gold: str) -> str:
    if not initial:
        return "missing_initial"
    if not final:
        return "missing_final"
    initial_correct = _correct(initial, gold)
    final_correct = _correct(final, gold)
    if initial_correct and final_correct:
        return "correct_to_correct"
    if initial_correct and not final_correct:
        return "correct_to_wrong"
    if not initial_correct and final_correct:
        return "wrong_to_correct"
    return "wrong_to_wrong"


def _majority_transition(initial_majority: str, final_majority: str, gold: str) -> str:
    if not initial_majority:
        return "no_initial_majority"
    if not final_majority:
        return "no_final_majority"
    initial_correct = _correct(initial_majority, gold)
    final_correct = _correct(final_majority, gold)
    if initial_correct and final_correct:
        return "preserved_correct"
    if initial_correct and not final_correct:
        return "correct_to_wrong"
    if not initial_correct and final_correct:
        return "wrong_to_correct"
    return "persistent_error"


def analyze_flip_dynamics(*, data_path: Path, raw_path: Path) -> dict[str, Any]:
    data_rows = {row["id"]: row for row in load_jsonl(data_path)}
    raw_rows = load_jsonl(raw_path)

    items: list[dict[str, Any]] = []
    majority_transition_counts = {key: 0 for key in MAJORITY_TRANSITIONS}
    agent_transition_counts = {key: 0 for key in AGENT_TRANSITIONS}
    agent_transition_counts_by_agent_id: dict[str, dict[str, int]] = {
        str(agent_id): {key: 0 for key in AGENT_TRANSITIONS} for agent_id in ROLE_BY_AGENT_ID
    }
    role_transition_counts: dict[str, dict[str, int]] = {
        role: {key: 0 for key in AGENT_TRANSITIONS} for role in ROLE_BY_AGENT_ID.values()
    }
    extraction_failure_count = 0
    item_count_with_any_extraction_failure = 0
    correct_to_wrong_majority = 0
    wrong_to_correct_majority = 0
    preserved_correct = 0

    for row in raw_rows:
        item_id = row["id"]
        gold = normalize_answer(data_rows.get(item_id, {}).get("answer", ""))
        max_round = _max_round(row)

        initial_answers_by_agent: dict[str, str] = {}
        final_answers_by_agent: dict[str, str] = {}
        any_failure = False
        for agent_id in sorted(ROLE_BY_AGENT_ID):
            initial_entry = next((entry for entry in row.get("transcript_raw", []) if int(entry["agent_id"]) == agent_id and int(entry["round_index"]) == 0), None)
            final_entry = next((entry for entry in row.get("transcript_raw", []) if int(entry["agent_id"]) == agent_id and int(entry["round_index"]) == max_round), None)
            initial_answer = normalize_answer(initial_entry.get("answer", "")) if initial_entry else ""
            final_answer = normalize_answer(final_entry.get("answer", "")) if final_entry else ""
            initial_answers_by_agent[str(agent_id)] = initial_answer
            final_answers_by_agent[str(agent_id)] = final_answer
            transition = _agent_transition(initial_answer, final_answer, gold)
            agent_transition_counts[transition] += 1
            agent_transition_counts_by_agent_id[str(agent_id)][transition] += 1
            role_transition_counts[ROLE_BY_AGENT_ID[agent_id]][transition] += 1

            if initial_entry and initial_entry.get("extraction_failed", False):
                extraction_failure_count += 1
                any_failure = True
            if final_entry and final_entry.get("extraction_failed", False):
                extraction_failure_count += 1
                any_failure = True

        if any_failure:
            item_count_with_any_extraction_failure += 1

        initial_majority = _majority(_answers_for_round(row, 0))
        final_majority = _majority(_answers_for_round(row, max_round))
        initial_majority_correct = _correct(initial_majority, gold) if initial_majority else False
        final_majority_correct = _correct(final_majority, gold) if final_majority else False
        majority_transition = _majority_transition(initial_majority, final_majority, gold)
        majority_transition_counts[majority_transition] += 1
        preserved_correct += int(majority_transition == "preserved_correct")
        correct_to_wrong_majority += int(majority_transition == "correct_to_wrong")
        wrong_to_correct_majority += int(majority_transition == "wrong_to_correct")

        items.append(
            {
                "item_id": item_id,
                "gold": gold,
                "initial_majority": initial_majority,
                "final_majority": final_majority,
                "initial_majority_correct": initial_majority_correct,
                "final_majority_correct": final_majority_correct,
                "majority_transition_category": majority_transition,
                "agent_initial_answers": initial_answers_by_agent,
                "agent_final_answers": final_answers_by_agent,
                "per_agent_transition": {
                    str(agent_id): _agent_transition(
                        initial_answers_by_agent[str(agent_id)],
                        final_answers_by_agent[str(agent_id)],
                        gold,
                    )
                    for agent_id in sorted(ROLE_BY_AGENT_ID)
                },
            }
        )

    correct_path_retention_rate = (
        preserved_correct / (preserved_correct + correct_to_wrong_majority)
        if (preserved_correct + correct_to_wrong_majority)
        else 0.0
    )

    return {
        "data": str(data_path),
        "raw": str(raw_path),
        "n": len(items),
        "majority_transition_counts": majority_transition_counts,
        "correct_to_wrong_majority_rate": correct_to_wrong_majority / len(items) if items else 0.0,
        "wrong_to_correct_majority_rate": wrong_to_correct_majority / len(items) if items else 0.0,
        "correct_path_retention_rate": correct_path_retention_rate,
        "agent_transition_counts": agent_transition_counts,
        "agent_transition_counts_by_agent_id": agent_transition_counts_by_agent_id,
        "role_transition_counts": role_transition_counts,
        "extraction_failure_count": extraction_failure_count,
        "item_count_with_any_extraction_failure": item_count_with_any_extraction_failure,
        "items": items,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines: list[str] = []
    lines.append("# AQuA Role Debate Flip Dynamics")
    lines.append("")
    lines.append("## Purpose")
    lines.append("Post-hoc flip analysis for the role-separated same-model debate trajectories.")
    lines.append("")
    lines.append("## Summary")
    lines.append("| metric | value |")
    lines.append("| --- | ---: |")
    lines.append(f"| n | {report['n']} |")
    lines.append(f"| correct_to_wrong_majority_rate | {report['correct_to_wrong_majority_rate']} |")
    lines.append(f"| wrong_to_correct_majority_rate | {report['wrong_to_correct_majority_rate']} |")
    lines.append(f"| correct_path_retention_rate | {report['correct_path_retention_rate']} |")
    lines.append(f"| extraction_failure_count | {report['extraction_failure_count']} |")
    lines.append(f"| item_count_with_any_extraction_failure | {report['item_count_with_any_extraction_failure']} |")
    lines.append("")
    lines.append("## Majority Transition Counts")
    for key, value in report["majority_transition_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("## Agent-Level Transition Counts")
    for key, value in report["agent_transition_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("## Role-Level Transition Counts")
    for role, counts in report["role_transition_counts"].items():
        lines.append(f"- {role}: {counts}")
    lines.append("")
    lines.append("## Item-Level Compact Table")
    lines.append("| item_id | gold | initial_majority | final_majority | majority_transition_category |")
    lines.append("| --- | --- | --- | --- | --- |")
    for item in report["items"]:
        lines.append(
            f"| {item['item_id']} | {item['gold']} | {item['initial_majority']} | {item['final_majority']} | {item['majority_transition_category']} |"
        )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("On this 11-item exploratory subset, the majority path often held steady, but the final majority still lost some correct cases.")
    lines.append("This is consistent with trajectory-mixing failure: same-model debate may reinforce contextually dominant reasoning paths rather than reliably selecting the correct path.")
    lines.append("This does not establish a general causal mechanism.")
    lines.append("")
    lines.append("## Limitations")
    lines.append("- n=11 only")
    lines.append("- post-hoc analysis")
    lines.append("- one model/backend")
    lines.append("- no statistical significance")
    lines.append("- role prompts are simple")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze flip dynamics in role-separated debate trajectories.")
    parser.add_argument("--data", required=True)
    parser.add_argument("--raw", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    report = analyze_flip_dynamics(data_path=Path(args.data), raw_path=Path(args.raw))
    write_json(Path(args.out_json), report)
    write_markdown(report, Path(args.out_md))
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
