from __future__ import annotations

import re

_NUMERIC_RE = re.compile(
    r"""
    (?<![\w/])
    [+-]?
    (?:
        (?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?
        |
        \.\d+
    )
    %?
    (?![\w/])
    """,
    re.VERBOSE,
)

_ANSWER_TAG_RE = re.compile(r"<answer>.*?</answer>", re.IGNORECASE | re.DOTALL)
_ANSWER_LINE_RE = re.compile(
    r"(?im)^(?P<prefix>\s*(?:[-*]\s*)?(?:peer\s+\w+:\s*)?(?:final\s+answer|answer)\s*:\s*)(?P<value>.+?)\s*$"
)
_ANSWER_LINE_IS_RE = re.compile(
    r"(?im)^(?P<prefix>\s*(?:[-*]\s*)?(?:peer\s+\w+:\s*)?the\s+answer\s+is\s*)(?P<value>.+?)\s*$"
)
_ANSWER_CLAUSE_RE = re.compile(r"(?im)\b(the answer is)\s+(.+?)([.?!]?\s*)$")


def mask_numeric_tokens(text: str) -> str:
    return _NUMERIC_RE.sub("[NUM]", text)


def hide_final_answer(text: str) -> str:
    replaced = _ANSWER_TAG_RE.sub("<answer>[ANSWER_HIDDEN]</answer>", text)

    def _replace_line(match: re.Match[str]) -> str:
        return f"{match.group('prefix')}[ANSWER_HIDDEN]"

    replaced = _ANSWER_LINE_RE.sub(_replace_line, replaced)
    replaced = _ANSWER_LINE_IS_RE.sub(_replace_line, replaced)

    def _replace_clause(match: re.Match[str]) -> str:
        return f"{match.group(1)} [ANSWER_HIDDEN]{match.group(3)}"

    return _ANSWER_CLAUSE_RE.sub(_replace_clause, replaced)


def apply_peer_context_policy(text: str, policy: str) -> str:
    if policy == "full_context":
        return text
    if policy == "answer_hidden":
        return hide_final_answer(text)
    if policy == "numeric_masked":
        return mask_numeric_tokens(text)
    if policy == "answer_hidden_numeric_masked":
        return mask_numeric_tokens(hide_final_answer(text))
    raise ValueError(f"unknown policy: {policy}")
