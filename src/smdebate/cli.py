from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from smdebate.config import load_config
from smdebate.lmstudio import create_local_chat_model, invoke_text
from smdebate.metrics import normalize_answer, summarize_rows
from smdebate.protocol import AgentResponse, debate_prompt, extract_answer, initial_prompt
from smdebate.storage import load_items, write_json


def majority_vote(values: list[str]) -> str:
    if not values:
        raise ValueError("values must not be empty")

    counts = Counter(normalize_answer(value) for value in values)
    best_key = counts.most_common(1)[0][0]
    for value in values:
        if normalize_answer(value) == best_key:
            return value
    raise RuntimeError("unreachable majority vote state")


def _invoke_agent(model: Any, prompt: str, *, agent_id: int, round_index: int) -> AgentResponse:
    raw = invoke_text(model, prompt)
    answer, failed = extract_answer(raw)
    return AgentResponse(
        agent_id=agent_id,
        round_index=round_index,
        raw_text=raw,
        answer=answer,
        extraction_failed=failed,
    )


def _rounds_for_condition(condition: str, configured_rounds: int) -> int:
    if condition == "independent":
        return 0
    if condition == "debate_1r":
        return 1
    if condition == "debate_3r_full_context":
        return configured_rounds
    return configured_rounds


def _visible_responses_for_condition(
    *,
    condition: str,
    response: AgentResponse,
    current_round: list[AgentResponse],
    history: list[AgentResponse],
) -> list[AgentResponse]:
    if condition == "debate_3r_full_context":
        return [entry for entry in history if entry.agent_id != response.agent_id]
    return [entry for entry in current_round if entry.agent_id != response.agent_id]


def run_item(item: Any, model: Any, config: Any) -> dict[str, Any]:
    initial: list[AgentResponse] = []

    for agent_id in range(1, config.agent_count + 1):
        prompt = initial_prompt(
            item,
            agent_id,
            model_family=config.model_family,
            reasoning_mode=config.reasoning_mode,
        )
        initial.append(_invoke_agent(model, prompt, agent_id=agent_id, round_index=0))

    current = initial
    history = list(initial)
    for round_index in range(1, _rounds_for_condition(config.condition, config.rounds) + 1):
        next_round: list[AgentResponse] = []
        for response in current:
            visible = _visible_responses_for_condition(
                condition=config.condition,
                response=response,
                current_round=current,
                history=history,
            )
            prompt = debate_prompt(
                item=item,
                agent_id=response.agent_id,
                own_previous=response,
                visible_responses=visible,
                round_index=round_index,
                model_family=config.model_family,
                reasoning_mode=config.reasoning_mode,
            )
            next_round.append(
                _invoke_agent(model, prompt, agent_id=response.agent_id, round_index=round_index)
            )
        current = next_round
        history.extend(next_round)

    final_answers = [response.answer for response in current]
    extraction_failures = sum(int(response.extraction_failed) for response in [*initial, *current])
    extraction_total = len(initial) + len(current)

    return {
        "id": item.id,
        "type": item.type,
        "difficulty": item.difficulty,
        "gold": item.answer,
        "condition": config.condition,
        "initial_answers": [response.answer for response in initial],
        "final_answers": final_answers,
        "final_answer": majority_vote(final_answers),
        "extraction_failures": extraction_failures,
        "extraction_total": extraction_total,
        "initial_raw": [asdict(response) for response in initial],
        "final_raw": [asdict(response) for response in current],
        "transcript_raw": [asdict(response) for response in history],
    }


def _load_raw_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _write_summary_atomic(path: Path, summary: Any) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    write_json(tmp_path, asdict(summary))
    tmp_path.replace(path)


def _prepare_out_dir(out_dir: Path, *, force: bool, resume: bool) -> None:
    summary_path = out_dir / "summary.json"
    if out_dir.exists():
        if summary_path.exists():
            if force:
                shutil.rmtree(out_dir)
                return
            if resume:
                return
            raise FileExistsError(f"{out_dir} already contains summary.json; use --force to overwrite")
        if not (force or resume):
            print(f"warning: {out_dir} exists but summary.json is missing; this looks like an incomplete run")
            raise FileExistsError("incomplete run requires --resume or --force")
        if force:
            shutil.rmtree(out_dir)
        return
    out_dir.mkdir(parents=True, exist_ok=True)


def _resume_completed_ids(raw_path: Path) -> set[str]:
    return {row["id"] for row in _load_raw_rows(raw_path)}


def _run_experiment(
    *,
    items: list[Any],
    model: Any,
    config: Any,
    out_dir: Path,
    resume: bool,
) -> tuple[list[dict[str, Any]], Any]:
    raw_path = out_dir / "raw.jsonl"
    completed_ids = _resume_completed_ids(raw_path) if resume else set()
    raw_file = raw_path.open("a", encoding="utf-8")
    try:
        if raw_path.exists() and raw_path.stat().st_size > 0 and not resume:
            raise FileExistsError(f"{raw_path} already exists; use --resume or --force")
        rows: list[dict[str, Any]] = [] if not resume else _load_raw_rows(raw_path)
        for item in items:
            if item.id in completed_ids:
                continue
            row = run_item(item, model, config)
            rows.append(row)
            raw_file.write(json.dumps(row, ensure_ascii=False) + "\n")
            raw_file.flush()
        summary = summarize_rows(rows)
        return rows, summary
    finally:
        raw_file.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run same-model debate experiments locally.")
    parser.add_argument("--data", default="data/smoke.jsonl", help="Path to JSONL dataset.")
    parser.add_argument("--out", default=None, help="Output directory. Defaults to runs/<utc-id>.")
    parser.add_argument("--force", action="store_true", help="Delete existing output directory first.")
    parser.add_argument("--resume", action="store_true", help="Resume from existing raw.jsonl.")
    parser.add_argument(
        "--condition",
        default="debate_1r",
        choices=["independent", "debate_1r", "debate_3r_full_context"],
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=None,
        help="Override debate rounds for configurable conditions.",
    )
    args = parser.parse_args()

    config = load_config(condition=args.condition)
    if args.rounds is not None:
        from dataclasses import replace
        config = replace(config, rounds=args.rounds)
    model = create_local_chat_model(config)
    items = load_items(Path(args.data))

    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(args.out) if args.out else Path("runs") / run_id
    _prepare_out_dir(out_dir, force=args.force, resume=args.resume)

    rows, summary = _run_experiment(
        items=items,
        model=model,
        config=config,
        out_dir=out_dir,
        resume=args.resume,
    )
    _write_summary_atomic(out_dir / "summary.json", summary)
    write_json(out_dir / "config.json", config.to_public_dict())

    print(asdict(summary))


if __name__ == "__main__":
    main()
