from smdebate.mitigation import apply_peer_context_policy, hide_final_answer, mask_numeric_tokens


def test_mask_numeric_tokens_replaces_common_numeric_forms() -> None:
    text = "Values: 12, -3.5, 1,200, 99%, $42, and .25."
    masked = mask_numeric_tokens(text)
    assert masked.count("[NUM]") >= 5
    assert "Values:" in masked


def test_hide_final_answer_handles_tags_and_answer_lines() -> None:
    text = "Reasoning.\nFinal answer: 96\n<answer>42</answer>\nThe answer is 18."
    hidden = hide_final_answer(text)
    assert "[ANSWER_HIDDEN]" in hidden
    assert "<answer>[ANSWER_HIDDEN]</answer>" in hidden
    assert "Reasoning." in hidden


def test_apply_peer_context_policy_composes_transforms() -> None:
    text = "Answer: 96. The answer is 18."
    assert apply_peer_context_policy(text, "full_context") == text
    assert "[ANSWER_HIDDEN]" in apply_peer_context_policy(text, "answer_hidden")
    assert "[NUM]" in apply_peer_context_policy(text, "numeric_masked")
    combined = apply_peer_context_policy(text, "answer_hidden_numeric_masked")
    assert "[ANSWER_HIDDEN]" in combined
