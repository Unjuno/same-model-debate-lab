from smdebate.metrics import is_correct, summarize_rows


def test_is_correct_normalizes_simple_answers() -> None:
    assert is_correct(" 42 ", "42")
    assert is_correct("H2O", "h2o")
    assert is_correct("1,000", "1000")
    assert not is_correct("41", "42")


def test_summarize_detects_answer_loss_and_same_error_agreement() -> None:
    rows = [
        {
            "gold": "42",
            "initial_answers": ["42", "40", "41"],
            "final_answers": ["40", "40", "40"],
            "final_answer": "40",
            "extraction_failures": 1,
            "extraction_total": 6,
        }
    ]

    summary = summarize_rows(rows)

    assert summary.n == 1
    assert summary.accuracy == 0.0
    assert summary.oracle_at_k == 1.0
    assert summary.answer_loss_rate == 1.0
    assert summary.same_error_agreement_rate == 1.0
    assert summary.diversity_drop == 2.0
    assert summary.extraction_failure_rate == 1 / 6
