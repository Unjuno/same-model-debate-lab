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
        return "<answer>1</answer>"

    monkeypatch.setattr(cli, "invoke_text", fake_invoke_text)

    item = Item(id="q1", type="arith", question="What is 1?", answer="1")
    row = cli.run_item(item, model=object(), config=_config("debate_3r_full_context"))

    assert row["final_answer"] == "1"
    assert len(calls) == 12
    assert sum("debate round" in prompt.lower() for prompt in calls) == 9
