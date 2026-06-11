from pathlib import Path

from tools.analyze_transient_correctness import analyze_transient_correctness, write_markdown


def _data_row(item_id: str, answer: str) -> dict:
    return {"id": item_id, "type": "aqua_rat", "question": "q", "answer": answer, "metadata": {}}


def test_transient_correctness_classifies_lost_unanimous_correct(tmp_path: Path) -> None:
    data_path = tmp_path / "data.jsonl"
    raw_path = tmp_path / "raw.jsonl"

    data_path.write_text(
        '{"id":"a","type":"aqua_rat","question":"q","answer":"E","metadata":{}}\n',
        encoding="utf-8",
    )
    raw_path.write_text(
        "\n".join(
            [
                '{"id":"a","transcript_raw":['
                '{"agent_id":1,"round_index":0,"answer":"E","extraction_failed":false},'
                '{"agent_id":2,"round_index":0,"answer":"A","extraction_failed":false},'
                '{"agent_id":3,"round_index":0,"answer":"A","extraction_failed":false},'
                '{"agent_id":1,"round_index":1,"answer":"E","extraction_failed":false},'
                '{"agent_id":2,"round_index":1,"answer":"E","extraction_failed":false},'
                '{"agent_id":3,"round_index":1,"answer":"A","extraction_failed":false},'
                '{"agent_id":1,"round_index":2,"answer":"E","extraction_failed":false},'
                '{"agent_id":2,"round_index":2,"answer":"E","extraction_failed":false},'
                '{"agent_id":3,"round_index":2,"answer":"E","extraction_failed":false},'
                '{"agent_id":1,"round_index":3,"answer":"A","extraction_failed":false},'
                '{"agent_id":2,"round_index":3,"answer":"E","extraction_failed":false},'
                '{"agent_id":3,"round_index":3,"answer":"A","extraction_failed":false}]}'
            ]
        ),
        encoding="utf-8",
    )

    report = analyze_transient_correctness(data_path=data_path, raw_path=raw_path)

    item = report["items"][0]
    assert item["gold"] == "E"
    assert item["majority_by_round"]["0"] == "A"
    assert item["majority_by_round"]["1"] == "E"
    assert item["majority_by_round"]["2"] == "E"
    assert item["majority_by_round"]["3"] == "A"
    assert item["category"] == "transient_correct_consensus_lost"
    assert item["any_round_majority_correct"] is True
    assert item["any_round_unanimous_correct"] is True
    assert item["initial_majority_correct"] is False
    assert item["final_majority_correct"] is False


def test_transient_correctness_classifies_majority_loss_and_preservation(tmp_path: Path) -> None:
    data_path = tmp_path / "data.jsonl"
    raw_path = tmp_path / "raw.jsonl"

    data_path.write_text(
        "\n".join(
            [
                '{"id":"lost","type":"aqua_rat","question":"q","answer":"B","metadata":{}}',
                '{"id":"keep","type":"aqua_rat","question":"q","answer":"A","metadata":{}}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    raw_path.write_text(
        "\n".join(
            [
                '{"id":"lost","transcript_raw":['
                '{"agent_id":1,"round_index":0,"answer":"B","extraction_failed":false},'
                '{"agent_id":2,"round_index":0,"answer":"A","extraction_failed":false},'
                '{"agent_id":3,"round_index":0,"answer":"A","extraction_failed":false},'
                '{"agent_id":1,"round_index":1,"answer":"B","extraction_failed":false},'
                '{"agent_id":2,"round_index":1,"answer":"B","extraction_failed":false},'
                '{"agent_id":3,"round_index":1,"answer":"A","extraction_failed":false},'
                '{"agent_id":1,"round_index":2,"answer":"A","extraction_failed":false},'
                '{"agent_id":2,"round_index":2,"answer":"A","extraction_failed":false},'
                '{"agent_id":3,"round_index":2,"answer":"A","extraction_failed":false}]}',
                '{"id":"keep","transcript_raw":['
                '{"agent_id":1,"round_index":0,"answer":"A","extraction_failed":false},'
                '{"agent_id":2,"round_index":0,"answer":"A","extraction_failed":false},'
                '{"agent_id":3,"round_index":0,"answer":"B","extraction_failed":false},'
                '{"agent_id":1,"round_index":1,"answer":"A","extraction_failed":false},'
                '{"agent_id":2,"round_index":1,"answer":"A","extraction_failed":false},'
                '{"agent_id":3,"round_index":1,"answer":"A","extraction_failed":false}]}',
            ]
        ),
        encoding="utf-8",
    )

    report = analyze_transient_correctness(data_path=data_path, raw_path=raw_path)
    by_id = {item["item_id"]: item for item in report["items"]}

    assert by_id["lost"]["category"] == "transient_correct_majority_lost"
    assert by_id["keep"]["category"] == "preserved_correct"


def test_markdown_includes_highlights(tmp_path: Path) -> None:
    report = {
        "category_counts": {
            "transient_correct_consensus_lost": 1,
            "transient_correct_majority_lost": 1,
        },
        "items": [
            {
                "item_id": "a",
                "gold": "E",
                "initial_majority": "A",
                "final_majority": "A",
                "any_round_majority_correct": True,
                "any_round_unanimous_correct": True,
                "category": "transient_correct_consensus_lost",
            },
            {
                "item_id": "b",
                "gold": "B",
                "initial_majority": "A",
                "final_majority": "A",
                "any_round_majority_correct": True,
                "any_round_unanimous_correct": False,
                "category": "transient_correct_majority_lost",
            },
        ],
    }
    out = tmp_path / "report.md"
    write_markdown(report, out)
    text = out.read_text(encoding="utf-8")
    assert "transient_correct_consensus_lost" in text
    assert "Highlighted Items" in text
