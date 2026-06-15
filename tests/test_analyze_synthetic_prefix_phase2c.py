import math
from pathlib import Path

from tools.analyze_synthetic_prefix_phase2c import analyze_synthetic_prefix_phase2c, write_markdown
from tools.build_synthetic_prefix_phase2c_dataset import build_dataset


def _phase2b_row(item_id: str, gold: str, wrong: str, condition: str) -> dict:
    prefix = {
        "baseline_no_prefix": [],
        "single_round_correct_consensus": [gold, gold, gold],
        "single_round_wrong_consensus": [wrong, wrong, wrong],
    }[condition]
    return {
        "id": f"{item_id}__slot_00_{condition}_sample_000",
        "type": "gsm8k_synthetic_prefix_phase2b",
        "difficulty": "unknown",
        "question": f"Problem {item_id}.\n\nReturn only the final answer inside <answer>...</answer>.",
        "answer": gold,
        "metadata": {
            "base_item_id": item_id,
            "condition": condition,
            "replicate_index": 0,
            "gold": gold,
            "target_wrong_answer": wrong,
            "target_wrong_source": "raw_lookup",
            "synthetic_prefix": True,
            "phase": "phase2b_multi_item",
            "condition_family": "baseline" if condition == "baseline_no_prefix" else "single_round",
            "context_rounds_included": [] if not prefix else [0],
            "context_answers_by_round": {} if not prefix else {"0": prefix},
            "prefix_answer_counts": {} if not prefix else {gold if condition == "single_round_correct_consensus" else wrong: 3},
            "latest_round_answers": [] if not prefix else prefix,
            "latest_round_majority": "" if not prefix else (gold if condition == "single_round_correct_consensus" else wrong),
            "source_metadata": {"source": "gsm8k/main"},
        },
    }


def _phase2b_data() -> list[dict]:
    rows = []
    for index in range(2):
        item_id = f"gsm8k_test_{index:06d}"
        gold = str(index + 1)
        wrong = str(index + 10)
        rows.extend(
            [
                _phase2b_row(item_id, gold, wrong, "baseline_no_prefix"),
                _phase2b_row(item_id, gold, wrong, "single_round_correct_consensus"),
                _phase2b_row(item_id, gold, wrong, "single_round_wrong_consensus"),
            ]
        )
    return rows


def _raw_row(row_id: str, answers: list[object], *, prompt_format: str) -> dict:
    entries = []
    for agent_id, answer in enumerate(answers, start=1):
        if answer is None:
            entries.append({"agent_id": agent_id, "round_index": 0, "answer": "", "extraction_failed": True})
            continue
        if prompt_format == "json":
            raw_text = f'{{"answer": "{answer}"}}'
            extraction_failed = True
            parsed_answer = ""
        elif prompt_format == "plain_final":
            raw_text = str(answer)
            extraction_failed = True
            parsed_answer = ""
        else:
            raw_text = f"<answer>{answer}</answer>"
            extraction_failed = False
            parsed_answer = answer
        entries.append(
            {
                "agent_id": agent_id,
                "round_index": 0,
                "raw_text": raw_text,
                "answer": parsed_answer,
                "extraction_failed": extraction_failed,
            }
        )
    return {"id": row_id, "final_raw": entries, "initial_raw": entries}


def test_analyzer_recovery_by_format_and_effects(tmp_path: Path) -> None:
    data_rows = build_dataset(phase2b_data=_phase2b_data(), replicates=1)
    data_path = tmp_path / "data.jsonl"
    from tools.build_synthetic_prefix_phase2c_dataset import write_jsonl
    write_jsonl(data_path, data_rows)

    raw_rows = []
    for row in data_rows:
        prompt_format = row["metadata"]["prompt_format"]
        condition = row["metadata"]["condition"]
        gold = row["metadata"]["gold"]
        wrong = row["metadata"]["target_wrong_answer"]
        if condition == "baseline_no_prefix":
            answers = [gold, wrong, "99"]
        elif condition == "single_round_correct_consensus":
            answers = [gold, gold, gold]
        else:
            answers = [wrong, wrong, wrong]
        if prompt_format == "json":
            raw_rows.append(_raw_row(row["id"], answers, prompt_format="json"))
        elif prompt_format == "plain_final":
            raw_rows.append(_raw_row(row["id"], answers, prompt_format="plain_final"))
        else:
            raw_rows.append(_raw_row(row["id"], answers, prompt_format="answer_tag"))
    raw_path = tmp_path / "raw.jsonl"
    write_jsonl(raw_path, raw_rows)

    report = analyze_synthetic_prefix_phase2c(data_path=data_path, raw_path=raw_path)
    assert report["summary"]["n_items"] == 2
    assert report["summary"]["n_conditions"] == 3
    assert report["summary"]["n_prompt_formats"] == 3
    assert report["by_format_condition"]["json"]["baseline_no_prefix"]["format_recovered_count"] >= 1
    assert report["by_format_condition"]["plain_final"]["baseline_no_prefix"]["format_recovered_count"] >= 1
    assert report["by_format_condition"]["answer_tag"]["baseline_no_prefix"]["raw_extraction_failure_rate"] == 0.0
    assert report["aggregate_by_condition"]["single_round_correct_consensus"]["correct_rate"] > report["aggregate_by_condition"]["baseline_no_prefix"]["correct_rate"]
    assert "format_recovery_useful" in report["summary"]["qualitative_labels"] or "inconclusive" in report["summary"]["qualitative_labels"]
    assert math.isfinite(report["format_effects"]["json"]["delta_correct_rate"])


def test_analyzer_markdown_includes_sections_and_no_raw_text(tmp_path: Path) -> None:
    data_rows = build_dataset(phase2b_data=_phase2b_data(), replicates=1)
    from tools.build_synthetic_prefix_phase2c_dataset import write_jsonl
    data_path = tmp_path / "data.jsonl"
    write_jsonl(data_path, data_rows)
    raw_path = tmp_path / "raw.jsonl"
    write_jsonl(raw_path, [_raw_row(data_rows[0]["id"], ["21", "10", "11"], prompt_format="json")])
    report = analyze_synthetic_prefix_phase2c(data_path=data_path, raw_path=raw_path)
    out_md = tmp_path / "report.md"
    write_markdown(report, out_md)
    text = out_md.read_text(encoding="utf-8")
    assert "# GSM8K Synthetic Prefix Phase 2c Prompt-Format Robustness Analysis" in text
    assert "## By Prompt Format and Condition" in text
    assert "## Aggregate by Prompt Format" in text
    assert "## Aggregate by Condition" in text
    assert "## Format Effects" in text
    assert "No raw model text is included." in text
