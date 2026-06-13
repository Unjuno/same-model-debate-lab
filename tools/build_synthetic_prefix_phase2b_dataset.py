from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from decimal import Decimal, InvalidOperation
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

PHASE = "phase2b_multi_item"
DEFAULT_ITEMS = "all"
DEFAULT_REPLICATES = 40

CONTEXT_BY_CONDITION: dict[str, dict[int, list[str]]] = {
    "baseline_no_prefix": {},
    "single_round_correct_consensus": {0: ["gold", "gold", "gold"]},
    "single_round_correct_majority": {0: ["gold", "gold", "target_wrong_answer"]},
    "single_round_wrong_majority": {0: ["target_wrong_answer", "target_wrong_answer", "gold"]},
    "single_round_wrong_consensus": {0: ["target_wrong_answer", "target_wrong_answer", "target_wrong_answer"]},
}

CONDITION_ORDER = list(CONTEXT_BY_CONDITION)


def _find_item(data_rows: list[dict[str, Any]], item_id: str) -> dict[str, Any] | None:
    for row in data_rows:
        if str(row.get("id")) == item_id:
            return row
    return None


def _problem_text(question: str) -> str:
    return _problem_without_final_instruction(question)


def _format_previous_debate(round_answers: list[str], *, target_wrong_answer: str, gold: str) -> str:
    lines = ["Previous debate answers:", "Round 0:"]
    for agent_index, answer in enumerate(round_answers, start=1):
        rendered = answer.replace("gold", gold).replace("target_wrong_answer", target_wrong_answer)
        lines.append(f"- Agent {agent_index}: {rendered}")
    return "\n".join(lines)


def build_question(original_question: str, context_answers_by_round: dict[int, list[str]], *, gold: str, target_wrong_answer: str) -> str:
    problem = _problem_text(original_question)
    lines = ["Problem:", problem]
    if context_answers_by_round:
        round_index = min(context_answers_by_round)
        lines.extend(
            [
                "",
                _format_previous_debate(
                    context_answers_by_round[round_index],
                    gold=gold,
                    target_wrong_answer=target_wrong_answer,
                ),
                "",
                "Now solve the original problem independently.",
                "The previous answers may be right or wrong.",
                "Return only the final answer inside <answer>...</answer>.",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "Now solve the original problem independently.",
                "Return only the final answer inside <answer>...</answer>.",
            ]
        )
    return "\n".join(lines)


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


def _derive_target_wrong_answer(item_id: str, raw_lookup: dict[str, list[dict[str, Any]]], gold: str) -> str | None:
    rows = raw_lookup.get(item_id, [])
    non_gold = [answer for row in rows for answer in _extract_answers_from_row(row) if answer != gold]
    if not non_gold:
        return None
    counts = Counter(non_gold)
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]


def _fallback_target_wrong_answer(gold: str) -> str:
    try:
        value = Decimal(gold.replace(",", ""))
    except InvalidOperation:
        return f"{gold}_wrong"
    if value == value.to_integral():
        return str(int(value) + 1)
    return format(value + Decimal("1"), "f").rstrip("0").rstrip(".")


def _fallback_selection_candidates(
    data_rows: list[dict[str, Any]],
    *,
    excluded_ids: set[str],
) -> list[tuple[dict[str, Any], str, str]]:
    candidates: list[tuple[dict[str, Any], str, str]] = []
    for row in sorted(data_rows, key=lambda candidate: str(candidate.get("id", ""))):
        item_id = str(row.get("id", ""))
        if not item_id or item_id in excluded_ids:
            continue
        gold = normalize_answer(row.get("answer", ""))
        candidates.append((row, _fallback_target_wrong_answer(gold), "fallback_numeric"))
    return candidates


def _load_raw_lookup() -> dict[str, list[dict[str, Any]]]:
    lookup: dict[str, list[dict[str, Any]]] = {}
    for path in [
        ROOT / "runs" / "qwen3_8b_gsm8k_test_300_independent" / "raw.jsonl",
        ROOT / "runs" / "qwen3_8b_gsm8k_partial9_debate_R3" / "raw.jsonl",
        ROOT / "runs" / "qwen3_8b_gsm8k_000234_synthetic_prefix_phase2_independent" / "raw.jsonl",
    ]:
        if path.exists():
            for row in load_jsonl(path):
                row_id = str(row.get("id", ""))
                if row_id:
                    lookup.setdefault(row_id, []).append(row)
    return lookup


def _eligible_items(
    data_rows: list[dict[str, Any]],
    raw_lookup: dict[str, list[dict[str, Any]]],
) -> list[tuple[dict[str, Any], str, str]]:
    eligible: list[tuple[dict[str, Any], str, str]] = []
    for row in data_rows:
        item_id = str(row.get("id", ""))
        if not item_id:
            continue
        gold = normalize_answer(row.get("answer", ""))
        target_wrong = _derive_target_wrong_answer(item_id, raw_lookup, gold)
        if target_wrong is None:
            continue
        eligible.append((row, target_wrong, "raw_lookup"))
    eligible.sort(key=lambda pair: str(pair[0]["id"]))
    return eligible


def _select_items(
    data_rows: list[dict[str, Any]],
    raw_lookup: dict[str, list[dict[str, Any]]],
    items: int | str,
    *,
    allow_fallback: bool,
) -> tuple[list[tuple[dict[str, Any], str, str]], list[str]]:
    eligible = _eligible_items(data_rows, raw_lookup)
    if items == "all":
        selected = eligible[:]
    else:
        selected = eligible[:items]
    selected_ids = {str(row.get("id", "")) for row, _, _ in selected}
    skipped_item_ids = [
        str(row.get("id", ""))
        for row in data_rows
        if str(row.get("id", ""))
        and str(row.get("id", "")) not in selected_ids
        and _derive_target_wrong_answer(
            str(row.get("id", "")),
            raw_lookup,
            normalize_answer(row.get("answer", "")),
        )
        is None
    ]

    if len(selected) < (len(eligible) if items == "all" else items):
        if not allow_fallback:
            target_desc = "all eligible items" if items == "all" else f"{items} eligible items"
            raise ValueError(
                f"fewer than {target_desc} available: {len(selected)}; "
                "use --items all or pass --allow-fallback"
            )
    if allow_fallback and items != "all" and len(selected) < items:
        fallback_candidates = _fallback_selection_candidates(data_rows, excluded_ids=selected_ids)
        for candidate in fallback_candidates:
            if len(selected) >= items:
                break
            selected.append(candidate)
            selected_ids.add(str(candidate[0].get("id", "")))

    if items == "all" and len(selected) < len(eligible):
        raise ValueError(f"fewer than all eligible items available: {len(selected)} of {len(eligible)}")
    if items != "all" and len(selected) < items:
        raise ValueError(f"fewer than {items} unique items available: {len(selected)}")

    selected.sort(key=lambda pair: str(pair[0].get("id", "")))
    return selected, skipped_item_ids


def build_dataset(
    *,
    data_rows: list[dict[str, Any]],
    items: int | str = DEFAULT_ITEMS,
    replicates: int = DEFAULT_REPLICATES,
    selected_item_ids: list[str] | None = None,
    skipped_item_ids: list[str] | None = None,
    raw_lookup: dict[str, list[dict[str, Any]]] | None = None,
    allow_fallback: bool = False,
) -> list[dict[str, Any]]:
    if items != "all" and int(items) <= 0:
        raise ValueError("items must be positive")
    if replicates <= 0:
        raise ValueError("replicates must be positive")

    raw_lookup = raw_lookup or _load_raw_lookup()
    selected, skipped_ids = _select_items(
        data_rows,
        raw_lookup,
        items,
        allow_fallback=allow_fallback,
    )
    if selected_item_ids is not None:
        selected_item_ids[:] = [str(row["id"]) for row, _, _ in selected]
    if skipped_item_ids is not None:
        skipped_item_ids[:] = skipped_ids

    rows: list[dict[str, Any]] = []
    for selection_index, (source, target_wrong, target_wrong_source) in enumerate(selected):
        item_id = str(source["id"])
        gold = normalize_answer(source.get("answer", ""))
        original_metadata = source.get("metadata", {})
        for condition in CONDITION_ORDER:
            context_template = CONTEXT_BY_CONDITION[condition]
            if condition == "baseline_no_prefix":
                context: dict[int, list[str]] = {}
            else:
                round_answers = {
                    round_index: [
                        gold if token == "gold" else target_wrong if token == "target_wrong_answer" else token
                        for token in tokens
                    ]
                    for round_index, tokens in context_template.items()
                }
                context = round_answers
            latest_round_answers = context[max(context)] if context else []
            latest_majority = _majority(latest_round_answers)
            condition_family = "baseline" if condition == "baseline_no_prefix" else "single_round"
            for replicate_index in range(replicates):
                rows.append(
                    {
                        "id": f"{item_id}__slot_{selection_index:02d}_{condition}_sample_{replicate_index:03d}",
                        "type": "gsm8k_synthetic_prefix_phase2b",
                        "difficulty": source.get("difficulty", "unknown"),
                        "question": build_question(
                            str(source["question"]),
                            context,
                            gold=gold,
                            target_wrong_answer=target_wrong,
                        ),
                        "answer": gold,
                        "metadata": {
                            "base_item_id": item_id,
                            "selection_slot": selection_index,
                            "condition": condition,
                            "replicate_index": replicate_index,
                            "gold": gold,
                            "target_wrong_answer": target_wrong,
                            "target_wrong_source": target_wrong_source,
                            "synthetic_prefix": True,
                            "phase": PHASE,
                            "condition_family": condition_family,
                            "context_rounds_included": sorted(context),
                            "context_answers_by_round": {
                                str(key): value for key, value in sorted(context.items())
                            },
                            "prefix_answer_counts": _prefix_answer_counts(context),
                            "latest_round_answers": latest_round_answers,
                            "latest_round_majority": latest_majority,
                            "source_metadata": original_metadata,
                        },
                    }
                )
    return rows


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a GSM8K synthetic-prefix phase 2b dataset.")
    parser.add_argument("--data", required=True, help="Input JSONL benchmark file containing candidate items.")
    parser.add_argument("--out", required=True, help="Output JSONL dataset path.")
    parser.add_argument("--items", default=DEFAULT_ITEMS, help='Number of items to select, or "all".')
    parser.add_argument("--replicates", type=int, default=DEFAULT_REPLICATES)
    parser.add_argument("--allow-fallback", action="store_true", help="Allow deterministic numeric fallback items.")
    args = parser.parse_args()

    items: int | str
    if args.items == "all":
        items = "all"
    else:
        items = int(args.items)

    selected_item_ids: list[str] = []
    skipped_item_ids: list[str] = []
    source_rows = load_jsonl(Path(args.data))
    rows = build_dataset(
        data_rows=source_rows,
        items=items,
        replicates=args.replicates,
        selected_item_ids=selected_item_ids,
        skipped_item_ids=skipped_item_ids,
        allow_fallback=args.allow_fallback,
    )
    write_jsonl(Path(args.out), rows)
    target_wrong_source_counts = Counter(
        row["metadata"].get("target_wrong_source", "") for row in rows if row.get("metadata")
    )
    summary = {
        "phase": PHASE,
        "requested_items": args.items,
        "items": len(set(selected_item_ids)),
        "conditions": CONDITION_ORDER,
        "replicates": args.replicates,
        "rows": len(rows),
        "selected_item_ids": selected_item_ids,
        "skipped_item_ids": skipped_item_ids,
        "target_wrong_source_counts": dict(sorted(target_wrong_source_counts.items())),
        "allow_fallback": args.allow_fallback,
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
