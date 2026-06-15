from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_synthetic_prefix_continuation_dataset import (  # noqa: E402
    _problem_without_final_instruction,
    load_jsonl,
    write_jsonl,
)
from tools.select_partial_correct_items import normalize_answer  # noqa: E402

PHASE = "phase2c_prompt_format"
DEFAULT_REPLICATES = 20
CONDITION_ORDER = [
    "baseline_no_prefix",
    "single_round_correct_consensus",
    "single_round_wrong_consensus",
]
PROMPT_FORMAT_ORDER = ["answer_tag", "json", "plain_final"]


def _first_nonempty(row: dict[str, Any], keys: list[str]) -> str:
    for key in keys:
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def _extract_answers_from_row(row: dict[str, Any]) -> list[str]:
    answers: list[str] = []
    for key in ("initial_answers", "final_answers"):
        value = row.get(key)
        if isinstance(value, list):
            answers.extend(normalize_answer(answer) for answer in value if str(answer).strip())
    for key in ("initial_raw", "final_raw", "transcript_raw"):
        value = row.get(key)
        if isinstance(value, list):
            for entry in value:
                if isinstance(entry, dict):
                    answer = normalize_answer(entry.get("answer", ""))
                    if answer:
                        answers.append(answer)
    return answers


def _select_phase2b_items(phase2b_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered: dict[str, dict[str, Any]] = {}
    for row in phase2b_rows:
        metadata = row.get("metadata", {})
        if not isinstance(metadata, dict):
            continue
        item_id = str(metadata.get("base_item_id", ""))
        if not item_id or item_id in ordered:
            continue
        gold = normalize_answer(metadata.get("gold", row.get("answer", "")))
        target_wrong = normalize_answer(metadata.get("target_wrong_answer", ""))
        if not gold or not target_wrong:
            continue
        ordered[item_id] = {
            "id": item_id,
            "question": _original_question_from_phase2b_prompt(str(row.get("question", ""))),
            "answer": gold,
            "difficulty": row.get("difficulty", "unknown"),
            "metadata": metadata,
            "target_wrong_answer": target_wrong,
            "target_wrong_source": str(metadata.get("target_wrong_source", "raw_lookup")),
        }
    return [ordered[item_id] for item_id in sorted(ordered)]


def _original_question_from_phase2b_prompt(question: str) -> str:
    text = question.strip()
    if text.startswith("Problem:"):
        text = text[len("Problem:") :].lstrip()
    marker = "\n\nPrevious debate answers:"
    if marker in text:
        text = text.split(marker, 1)[0].rstrip()
    return text


def _format_instruction(prompt_format: str) -> str:
    if prompt_format == "answer_tag":
        return "Return only the final answer inside <answer>...</answer>."
    if prompt_format == "json":
        return 'Return JSON only, with this exact schema: {"answer": "..."}.\nThe answer should be a string.'
    if prompt_format == "plain_final":
        return "Return only the final numeric answer. Do not include explanation."
    raise ValueError(f"unknown prompt_format: {prompt_format}")


def _format_previous_debate(context_answers_by_round: dict[int, list[str]]) -> str:
    lines = ["Previous debate answers:"]
    for round_index in sorted(context_answers_by_round):
        lines.append(f"Round {round_index}:")
        for agent_index, answer in enumerate(context_answers_by_round[round_index], start=1):
            lines.append(f"- Agent {agent_index}: {answer}")
        lines.append("")
    return "\n".join(lines).rstrip()


def _majority(answers: list[str]) -> str:
    if not answers:
        return ""
    counts = Counter(answers)
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]


def _prefix_answer_counts(context_answers_by_round: dict[int, list[str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for answers in context_answers_by_round.values():
        for answer in answers:
            counts[answer] = counts.get(answer, 0) + 1
    return dict(sorted(counts.items()))


def build_question(
    original_question: str,
    context_answers_by_round: dict[int, list[str]],
    *,
    format_instruction: str,
) -> str:
    problem = _problem_without_final_instruction(original_question)
    lines = ["Problem:", problem, ""]
    if context_answers_by_round:
        lines.extend([_format_previous_debate(context_answers_by_round), "", "Now solve the original problem independently.", "The previous answers may be right or wrong.", format_instruction])
    else:
        lines.extend(["Now solve the original problem independently.", format_instruction])
    return "\n".join(lines)


def build_dataset(*, phase2b_data: list[dict[str, Any]], replicates: int = DEFAULT_REPLICATES) -> list[dict[str, Any]]:
    if replicates <= 0:
        raise ValueError("replicates must be positive")

    items = _select_phase2b_items(phase2b_data)
    if not items:
        raise ValueError("no eligible Phase 2b items found")

    rows: list[dict[str, Any]] = []
    for item in items:
        item_id = str(item["id"])
        gold = normalize_answer(item["answer"])
        target_wrong = normalize_answer(item["target_wrong_answer"])
        source_metadata = item["metadata"]
        for prompt_format in PROMPT_FORMAT_ORDER:
            format_instruction = _format_instruction(prompt_format)
            for condition in CONDITION_ORDER:
                if condition == "baseline_no_prefix":
                    context: dict[int, list[str]] = {}
                elif condition == "single_round_correct_consensus":
                    context = {0: [gold, gold, gold]}
                else:
                    context = {0: [target_wrong, target_wrong, target_wrong]}
                latest_round_answers = context[max(context)] if context else []
                latest_majority = _majority(latest_round_answers)
                condition_family = "baseline" if condition == "baseline_no_prefix" else "single_round"
                for replicate_index in range(replicates):
                    rows.append(
                        {
                            "id": f"{item_id}__phase2c_{prompt_format}_{condition}_sample_{replicate_index:03d}",
                            "type": "gsm8k_synthetic_prefix_phase2c",
                            "difficulty": item.get("difficulty", "unknown"),
                            "question": build_question(
                                str(item["question"]),
                                context,
                                format_instruction=format_instruction,
                            ),
                            "answer": gold,
                            "metadata": {
                                "base_item_id": item_id,
                                "condition": condition,
                                "prompt_format": prompt_format,
                                "replicate_index": replicate_index,
                                "gold": gold,
                                "target_wrong_answer": target_wrong,
                                "target_wrong_source": str(item["target_wrong_source"]),
                                "synthetic_prefix": True,
                                "phase": PHASE,
                                "condition_family": condition_family,
                                "context_rounds_included": sorted(context),
                                "context_answers_by_round": {str(key): value for key, value in sorted(context.items())},
                                "prefix_answer_counts": _prefix_answer_counts(context),
                                "latest_round_answers": latest_round_answers,
                                "latest_round_majority": latest_majority,
                                "source_metadata": source_metadata,
                            },
                        }
                    )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a GSM8K synthetic-prefix phase 2c dataset.")
    parser.add_argument("--phase2b-data", required=True, help="Phase 2b JSONL dataset containing the selected items.")
    parser.add_argument("--out", required=True, help="Output JSONL dataset path.")
    parser.add_argument("--replicates", type=int, default=DEFAULT_REPLICATES)
    args = parser.parse_args()

    phase2b_rows = load_jsonl(Path(args.phase2b_data))
    rows = build_dataset(phase2b_data=phase2b_rows, replicates=args.replicates)
    write_jsonl(Path(args.out), rows)
    selected_item_ids = sorted({str(row["metadata"]["base_item_id"]) for row in rows})
    summary = {
        "phase": PHASE,
        "items": len(selected_item_ids),
        "conditions": CONDITION_ORDER,
        "prompt_formats": PROMPT_FORMAT_ORDER,
        "replicates": args.replicates,
        "rows": len(rows),
        "selected_item_ids": selected_item_ids,
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
