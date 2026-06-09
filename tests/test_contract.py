import sys
from io import StringIO
from types import SimpleNamespace

import pytest

import smdebate.cli as cli
from smdebate.protocol import Item


def _config(condition: str):
    return SimpleNamespace(
        agent_count=3,
        rounds=3,
        condition=condition,
        model_family="qwen3",
        reasoning_mode="no_think",
    )


def test_independent_contract_uses_only_initial_answers(monkeypatch) -> None:
    calls: list[str] = []
    scripted = iter([
        "<answer>42</answer>",
        "<answer>40</answer>",
        "<answer>41</answer>",
    ])

    def fake_invoke_text(model, prompt: str) -> str:
        calls.append(prompt)
        return next(scripted)

    monkeypatch.setattr(cli, "invoke_text", fake_invoke_text)

    item = Item(id="q1", type="arith", question="What is 19+23?", answer="42")
    row = cli.run_item(item, model=object(), config=_config("independent"))

    assert row["initial_answers"] == ["42", "40", "41"]
    assert row["final_answers"] == ["42", "40", "41"]
    assert row["final_answer"] == "42"
    assert row["condition"] == "independent"
    assert len(calls) == 3
    assert all("debate round" not in prompt.lower() for prompt in calls)


def test_debate_contract_shares_context_and_can_measure_answer_loss(monkeypatch) -> None:
    calls: list[str] = []
    scripted = iter([
        "<answer>42</answer>",
        "<answer>40</answer>",
        "<answer>41</answer>",
        "<answer>40</answer>",
        "<answer>40</answer>",
        "<answer>40</answer>",
    ])

    def fake_invoke_text(model, prompt: str) -> str:
        calls.append(prompt)
        return next(scripted)

    monkeypatch.setattr(cli, "invoke_text", fake_invoke_text)

    item = Item(id="q1", type="arith", question="What is 19+23?", answer="42")
    row = cli.run_item(item, model=object(), config=_config("debate_1r"))

    assert row["initial_answers"] == ["42", "40", "41"]
    assert row["final_answers"] == ["40", "40", "40"]
    assert row["final_answer"] == "40"
    assert row["condition"] == "debate_1r"
    assert len(calls) == 6
    assert any("other agents' responses" in prompt.lower() for prompt in calls[3:])
    assert any("<answer>42</answer>" in prompt for prompt in calls[3:])


def test_debate_three_round_contract_invokes_expected_number_of_calls(monkeypatch) -> None:
    calls: list[str] = []

    def fake_invoke_text(model, prompt: str) -> str:
        calls.append(prompt)
        return f"<answer>{len(calls)}</answer>"

    monkeypatch.setattr(cli, "invoke_text", fake_invoke_text)

    item = Item(id="q1", type="arith", question="What is 1?", answer="1")
    row = cli.run_item(item, model=object(), config=_config("debate_3r_full_context"))

    assert len(calls) == 12
    assert sum("debate round" in prompt.lower() for prompt in calls) == 9
    assert len(row["transcript_raw"]) == 12


def test_full_context_condition_reuses_earlier_round_transcript(monkeypatch) -> None:
    calls: list[str] = []
    scripted = iter([
        "<answer>init_a</answer>",
        "<answer>init_b</answer>",
        "<answer>init_c</answer>",
        "<answer>r1_a</answer>",
        "<answer>r1_b</answer>",
        "<answer>r1_c</answer>",
        "<answer>r2_a</answer>",
        "<answer>r2_b</answer>",
        "<answer>r2_c</answer>",
        "<answer>r3_a</answer>",
        "<answer>r3_b</answer>",
        "<answer>r3_c</answer>",
    ])

    def fake_invoke_text(model, prompt: str) -> str:
        calls.append(prompt)
        return next(scripted)

    monkeypatch.setattr(cli, "invoke_text", fake_invoke_text)

    item = Item(id="q1", type="arith", question="What is 1?", answer="1")
    cli.run_item(item, model=object(), config=_config("debate_3r_full_context"))

    round_three_prompts = calls[9:12]
    assert any("init_b" in prompt for prompt in round_three_prompts)
    assert any("r1_b" in prompt for prompt in round_three_prompts)
    assert any("r2_b" in prompt for prompt in round_three_prompts)


def test_full_context_rounds_follow_configured_value(monkeypatch) -> None:
    calls: list[str] = []

    def fake_invoke_text(model, prompt: str) -> str:
        calls.append(prompt)
        return f"<answer>{len(calls)}</answer>"

    monkeypatch.setattr(cli, "invoke_text", fake_invoke_text)

    item = Item(id="q1", type="arith", question="What is 1?", answer="1")

    row_r1 = cli.run_item(item, model=object(), config=SimpleNamespace(
        agent_count=3,
        rounds=1,
        condition="debate_3r_full_context",
        model_family="qwen3",
        reasoning_mode="no_think",
    ))
    assert len(row_r1["transcript_raw"]) == 6

    calls.clear()
    row_r2 = cli.run_item(item, model=object(), config=SimpleNamespace(
        agent_count=3,
        rounds=2,
        condition="debate_3r_full_context",
        model_family="qwen3",
        reasoning_mode="no_think",
    ))
    assert len(row_r2["transcript_raw"]) == 9

    calls.clear()
    row_r3 = cli.run_item(item, model=object(), config=SimpleNamespace(
        agent_count=3,
        rounds=3,
        condition="debate_3r_full_context",
        model_family="qwen3",
        reasoning_mode="no_think",
    ))
    assert len(row_r3["transcript_raw"]) == 12


def test_debate_one_round_ignores_configured_rounds(monkeypatch) -> None:
    calls: list[str] = []

    def fake_invoke_text(model, prompt: str) -> str:
        calls.append(prompt)
        return f"<answer>{len(calls)}</answer>"

    monkeypatch.setattr(cli, "invoke_text", fake_invoke_text)

    item = Item(id="q1", type="arith", question="What is 1?", answer="1")
    row = cli.run_item(item, model=object(), config=SimpleNamespace(
        agent_count=3,
        rounds=8,
        condition="debate_1r",
        model_family="qwen3",
        reasoning_mode="no_think",
    ))

    assert len(row["transcript_raw"]) == 6


def test_role_independent_injects_role_text(monkeypatch) -> None:
    calls: list[str] = []

    def fake_invoke_text(model, prompt: str) -> str:
        calls.append(prompt)
        return f"<answer>{len(calls)}</answer>"

    monkeypatch.setattr(cli, "invoke_text", fake_invoke_text)

    item = Item(id="q1", type="arith", question="What is 1?", answer="1")
    cli.run_item(item, model=object(), config=_config("role_independent"))

    assert len(calls) == 3
    assert "Role: solver." in calls[0]
    assert "Role: skeptic/error-checker." in calls[1]
    assert "Role: alternative-solver." in calls[2]


def test_role_debate_full_context_injects_role_text(monkeypatch) -> None:
    calls: list[str] = []

    def fake_invoke_text(model, prompt: str) -> str:
        calls.append(prompt)
        return f"<answer>{len(calls)}</answer>"

    monkeypatch.setattr(cli, "invoke_text", fake_invoke_text)

    item = Item(id="q1", type="arith", question="What is 1?", answer="1")
    cli.run_item(item, model=object(), config=_config("role_debate_3r_full_context"))

    assert len(calls) == 12
    assert any("Role: solver." in prompt for prompt in calls[:3])
    assert any("Role: skeptic/error-checker." in prompt for prompt in calls[:3])
    assert any("Role: alternative-solver." in prompt for prompt in calls[:3])
    assert any("Role: solver." in prompt for prompt in calls[3:])
    assert any("Role: skeptic/error-checker." in prompt for prompt in calls[3:])
    assert any("Role: alternative-solver." in prompt for prompt in calls[3:])


def test_existing_debate_prompt_text_is_unchanged(monkeypatch) -> None:
    calls: list[str] = []

    def fake_invoke_text(model, prompt: str) -> str:
        calls.append(prompt)
        return f"<answer>{len(calls)}</answer>"

    monkeypatch.setattr(cli, "invoke_text", fake_invoke_text)

    item = Item(id="q1", type="arith", question="What is 1?", answer="1")
    cli.run_item(item, model=object(), config=_config("debate_3r_full_context"))

    assert all("Role:" not in prompt for prompt in calls)


def test_progress_logging_is_stderr_only_and_formatted(monkeypatch) -> None:
    scripted = iter([
        "<answer>42</answer>",
        "<answer>40</answer>",
        "<answer>41</answer>",
        "<answer>40</answer>",
        "<answer>40</answer>",
        "<answer>40</answer>",
    ])
    stderr = StringIO()

    def fake_invoke_text(model, prompt: str) -> str:
        return next(scripted)

    monkeypatch.setattr(cli, "invoke_text", fake_invoke_text)
    monkeypatch.setenv("SMDEBATE_PROGRESS", "1")
    monkeypatch.setattr(sys, "stderr", stderr)

    item = Item(id="q1", type="arith", question="What is 19+23?", answer="42")
    cli.run_item(item, model=object(), config=_config("debate_1r"), item_index=2, total_items=10)

    lines = [line for line in stderr.getvalue().splitlines() if line]
    assert lines[0] == "item start 2/10 item_id=q1"
    assert any("initial answers complete" in line for line in lines)
    assert any("debate round 1 start" in line for line in lines)
    assert any("agent=1 start" in line for line in lines)
    assert any("answer='42'" in line for line in lines)
    assert any("extraction_failed=False" in line for line in lines)
    assert all("Question:" not in line for line in lines)
    assert all("<answer>40</answer>" not in line for line in lines)


def test_timeout_is_recorded_and_run_continues(monkeypatch) -> None:
    calls = 0

    def fake_invoke_text(model, prompt: str) -> str:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise TimeoutError("request timed out after 30s")
        return f"<answer>{calls}</answer>"

    monkeypatch.setattr(cli, "invoke_text", fake_invoke_text)

    item = Item(id="q1", type="arith", question="What is 1?", answer="1")
    row = cli.run_item(item, model=object(), config=_config("debate_1r"))

    assert len(row["initial_raw"]) == 3
    assert len(row["final_raw"]) == 3
    assert row["extraction_total"] == 6
    assert row["extraction_failures"] == 1
    assert row["initial_raw"][1]["extraction_failed"] is True
    assert row["initial_raw"][1]["answer"] == ""
    assert row["initial_raw"][1]["raw_text"].startswith("[TimeoutError")
    assert "traceback" not in row["initial_raw"][1]["raw_text"].lower()


def test_timeout_row_is_written_and_summary_counts_failure(tmp_path, monkeypatch) -> None:
    out_dir = tmp_path / "run"
    out_dir.mkdir()

    def fake_run_item(item, model, config, item_index=None, total_items=None):
        return {
            "id": item.id,
            "type": item.type,
            "difficulty": item.difficulty,
            "gold": item.answer,
            "condition": config.condition,
            "initial_answers": ["1", ""],
            "final_answers": ["1", ""],
            "final_answer": "1",
            "extraction_failures": 1,
            "extraction_total": 2,
            "initial_raw": [
                {"agent_id": 1, "round_index": 0, "raw_text": "<answer>1</answer>", "answer": "1", "extraction_failed": False},
                {"agent_id": 2, "round_index": 0, "raw_text": "[TimeoutError: request timed out]", "answer": "", "extraction_failed": True},
            ],
            "final_raw": [],
            "transcript_raw": [],
        }

    monkeypatch.setattr(cli, "run_item", fake_run_item)

    rows, summary = cli._run_experiment(
        items=[Item(id="a", type="arith", question="q", answer="1", difficulty="easy")],
        model=object(),
        config=_config("debate_1r"),
        out_dir=out_dir,
        resume=False,
    )

    raw_lines = (out_dir / "raw.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(raw_lines) == 1
    assert rows[0]["id"] == "a"
    assert summary.extraction_failure_rate == 0.5


def test_continue_on_error_false_preserves_fail_fast(monkeypatch) -> None:
    monkeypatch.setenv("SMDEBATE_CONTINUE_ON_ERROR", "0")

    calls = 0

    def fake_invoke_text(model, prompt: str) -> str:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise ValueError("boom")
        return f"<answer>{calls}</answer>"

    monkeypatch.setattr(cli, "invoke_text", fake_invoke_text)

    item = Item(id="q1", type="arith", question="What is 1?", answer="1")

    with pytest.raises(ValueError):
        cli.run_item(item, model=object(), config=_config("debate_1r"))
