from types import SimpleNamespace

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
