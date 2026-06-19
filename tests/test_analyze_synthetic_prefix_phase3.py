from __future__ import annotations

import json
from pathlib import Path

from tools.analyze_synthetic_prefix_phase3 import analyze_synthetic_prefix_phase3, write_markdown
from tools.build_synthetic_prefix_phase3_dataset import build_dataset


def _phase2c_row(item_id: str, gold: str, wrong: str, condition: str) -> dict:
    return {
        "id": f"{item_id}__phase2c_plain_final_{condition}_sample_000",
        "type": "gsm8k_synthetic_prefix_phase2c",
        "difficulty": "unknown",
        "question": "Problem:\nExample.\n\nNow solve the original problem independently.\nReturn only the final numeric answer. Do not include explanation.",
        "answer": gold,
        "metadata": {
            "base_item_id": item_id,
            "condition": condition,
            "prompt_format": "plain_final",
            "replicate_index": 0,
            "gold": gold,
            "target_wrong_answer": wrong,
            "target_wrong_source": "raw_lookup",
            "synthetic_prefix": True,
            "phase": "phase2c_prompt_format",
            "condition_family": "baseline",
            "source_metadata": {"source": "gsm8k/main"},
        },
    }


def _phase2c_data() -> list[dict]:
    rows = []
    for item_id, gold, wrong in [("gsm8k_test_000001", "10", "20"), ("gsm8k_test_000002", "11", "21")]:
        for condition in [
            "baseline_no_prefix",
            "single_round_correct_consensus",
            "single_round_wrong_consensus",
        ]:
            rows.append(_phase2c_row(item_id, gold, wrong, condition))
    return rows


def _rationales() -> Path:
    payload = {
        "phase": "phase3_rationale_contamination",
        "items": [
            {
                "base_item_id": "gsm8k_test_000001",
                "gold": "10",
                "target_wrong_answer": "20",
                "correct_rationale": "Adds to 10.",
                "wrong_rationale": "A rough estimate points near twenty.",
            },
            {
                "base_item_id": "gsm8k_test_000002",
                "gold": "11",
                "target_wrong_answer": "21",
                "correct_rationale": "Adds to 11.",
                "wrong_rationale": "A rough estimate points near twenty-one.",
            },
        ],
    }
    path = Path("/tmp/phase3_rationales.json")
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _raw_row(row_id: str, answers: list[object], *, recovered: bool = False) -> dict:
    entries = []
    for agent_id, answer in enumerate(answers, start=1):
        entries.append(
            {
                "agent_id": agent_id,
                "round_index": 0,
                "raw_text": str(answer),
                "answer": "" if recovered else str(answer),
                "extraction_failed": recovered,
            }
        )
    return {"id": row_id, "final_raw": entries}


def test_analyzer_condition_effects_labels_and_markdown(tmp_path: Path) -> None:
    data_rows = build_dataset(phase2c_data=_phase2c_data(), rationales_path=_rationales(), replicates=1)
    data_path = tmp_path / "data.jsonl"
    from tools.build_synthetic_prefix_phase2c_dataset import write_jsonl
    write_jsonl(data_path, data_rows)
    raw_rows = [
        _raw_row("gsm8k_test_000001__phase3_baseline_no_prefix_sample_000", ["10", "20", "30"]),
        _raw_row("gsm8k_test_000001__phase3_wrong_answer_only_sample_000", ["20", "20", "10"]),
        _raw_row("gsm8k_test_000001__phase3_wrong_rationale_only_sample_000", ["20", "foo", "10"], recovered=True),
        _raw_row("gsm8k_test_000001__phase3_wrong_answer_plus_rationale_sample_000", ["20", "20", "20"]),
        _raw_row("gsm8k_test_000001__phase3_correct_answer_only_sample_000", ["10", "20", "30"]),
        _raw_row("gsm8k_test_000001__phase3_correct_answer_plus_rationale_sample_000", ["10", "10", "10"]),
        _raw_row("gsm8k_test_000002__phase3_baseline_no_prefix_sample_000", ["11", "21", "31"]),
        _raw_row("gsm8k_test_000002__phase3_wrong_answer_only_sample_000", ["21", "21", "11"]),
        _raw_row("gsm8k_test_000002__phase3_wrong_rationale_only_sample_000", ["21", "21", "11"], recovered=True),
        _raw_row("gsm8k_test_000002__phase3_wrong_answer_plus_rationale_sample_000", ["21", "21", "21"]),
        _raw_row("gsm8k_test_000002__phase3_correct_answer_only_sample_000", ["11", "21", "31"]),
        _raw_row("gsm8k_test_000002__phase3_correct_answer_plus_rationale_sample_000", ["11", "11", "11"]),
    ]
    raw_path = tmp_path / "raw.jsonl"
    write_jsonl(raw_path, raw_rows)
    report = analyze_synthetic_prefix_phase3(data_path=data_path, raw_path=raw_path)
    assert report["by_condition"]["wrong_answer_only"]["target_wrong_rate"] > report["by_condition"]["baseline_no_prefix"]["target_wrong_rate"]
    assert report["condition_effects"]["wrong_answer_delta_target_wrong"] > 0.10
    assert "numeric_anchor_consistent" in report["summary"]["qualitative_labels"]
    assert "rationale_contamination_consistent" in report["summary"]["qualitative_labels"]
    assert "answer_rationale_combination_consistent" in report["summary"]["qualitative_labels"]
    assert "correct_rationale_recovery_consistent" in report["summary"]["qualitative_labels"]
    assert report["by_condition"]["wrong_rationale_only"]["effective_extraction_failure_rate"] > 0.0

    out_md = tmp_path / "report.md"
    write_markdown(report, out_md)
    text = out_md.read_text(encoding="utf-8")
    assert "# GSM8K Synthetic Prefix Phase 3 Rationale-Contamination Analysis" in text
    assert "## By Condition" in text
    assert "## Condition Effects" in text
    assert "## Item-Level Effects" in text
    assert "No raw model text is included." in text


def test_analyzer_recovery_and_skip_tracking(tmp_path: Path) -> None:
    data_rows = build_dataset(phase2c_data=_phase2c_data(), rationales_path=_rationales(), replicates=1)
    from tools.build_synthetic_prefix_phase2c_dataset import write_jsonl
    data_path = tmp_path / "data.jsonl"
    write_jsonl(data_path, data_rows)
    raw_path = tmp_path / "raw.jsonl"
    write_jsonl(raw_path, [{"id": "missing", "final_raw": []}])
    report = analyze_synthetic_prefix_phase3(data_path=data_path, raw_path=raw_path)
    assert report["summary"]["skipped_raw_ids"] == ["missing"]
