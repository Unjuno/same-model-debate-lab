from smdebate.protocol import AgentResponse, Item, debate_prompt, extract_answer, initial_prompt


def test_extract_answer_uses_answer_tags() -> None:
    answer, failed = extract_answer("Reasoning... <answer>42</answer>")
    assert answer == "42"
    assert failed is False


def test_extract_answer_falls_back_to_full_text() -> None:
    answer, failed = extract_answer("42")
    assert answer == "42"
    assert failed is True


def test_qwen_no_think_prefix_is_added() -> None:
    item = Item(id="x", type="arith", question="What is 1+1?", answer="2")
    prompt = initial_prompt(item, 1, model_family="qwen3", reasoning_mode="no_think")
    assert prompt.startswith("/no_think")


def test_qwen_think_prefix_is_added() -> None:
    item = Item(id="x", type="arith", question="What is 1+1?", answer="2")
    prompt = initial_prompt(item, 1, model_family="qwen3", reasoning_mode="think")
    assert prompt.startswith("/think")


def test_non_qwen_no_prefix() -> None:
    item = Item(id="x", type="arith", question="What is 1+1?", answer="2")
    prompt = initial_prompt(item, 1, model_family="llama3.2", reasoning_mode="no_think")
    assert not prompt.startswith("/")


def test_debate_prompt_contains_visible_responses() -> None:
    item = Item(id="x", type="arith", question="What is 1+1?", answer="2")
    own = AgentResponse(1, 0, "<answer>2</answer>", "2", False)
    other = AgentResponse(2, 0, "<answer>3</answer>", "3", False)
    prompt = debate_prompt(item, 1, own, [other], 1)
    assert "Agent 2" in prompt
    assert "<answer>3</answer>" in prompt
