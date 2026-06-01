from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from smdebate.config import load_config
from smdebate.lmstudio import create_local_chat_model, invoke_text
from smdebate.metrics import normalize_answer, summarize_rows
from smdebate.protocol import AgentResponse, debate_prompt, extract_answer, initial_prompt
from smdebate.storage import load_items, write_json, write_jsonl


def majority_vote(values: list[str]) -> str:
    if not values:
        raise ValueError("values must not be empty")

    counts = Counter(normalize_answer(value) for value in values)
    best_key = counts.most_common(1)[0][0]
    for value in values:
        if normalize_answer(value) == best_key:
            return value
    raise RuntimeError("unreachable majority vote state")


def _invoke_agent(model, prompt: str, *, agent_id: int, round_index: int) -> AgentResponse:
    raw = invoke_text(model, prompt)
    answer, failed = extract_answer(raw)
    return AgentResponse(
        agent_id=agent_id,
        round_index=round_index,
        raw_text=raw,
        answer=answer,
        extraction_failed=failed,
    )


def run_item(item, model, config) -> dict:
    initial: list[AgentResponse] = []

    for agent_id in range(1, config.agent_count + 1):
        prompt = initial_prompt(
            item,
            agent_id,
            model_family=config.model_family,
            reasoning_mode=config.reasoning_mode,
        )
        initial.append(_invoke_agent(model, prompt, agent_id=agent_id, round_index=0))

    if config.condition == "independent":
        current = initial
    else:
        rounds = 1 if config.condition == "debate_1r" else config.rounds
        current = initial
        for round_index in range(1, rounds + 1):
            next_round: list[AgentResponse] = []
            for response in current:
                visible = [other for other in current if other.agent_id != response.agent_id]
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
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run same-model debate experiments locally.")
    parser.add_argument("--data", default="data/smoke.jsonl", help="Path to JSONL dataset.")
    parser.add_argument("--out", default=None, help="Output directory. Defaults to runs/<utc-id>.")
    parser.add_argument(
        "--condition",
        default="debate_1r",
        choices=["independent", "debate_1r", "debate_3r_full_context"],
    )
    args = parser.parse_args()

    config = load_config(condition=args.condition)
    model = create_local_chat_model(config)
    items = load_items(Path(args.data))

    rows = [run_item(item, model, config) for item in items]
    summary = summarize_rows(rows)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(args.out) if args.out else Path("runs") / run_id

    write_jsonl(out_dir / "raw.jsonl", rows)
    write_json(out_dir / "summary.json", asdict(summary))
    write_json(out_dir / "config.json", config.to_public_dict())

    print(asdict(summary))


if __name__ == "__main__":
    main()
