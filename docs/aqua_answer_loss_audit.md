# AQuA-RAT Answer Loss Audit

This audit lists only the cases where a correct initial answer was lost by the final debate answer. It does not include prompts or raw transcript text.

| item_id | gold | initial_answers | final_answer |
|---|---|---|---|
| `aqua_test_0_000184` | `D` | `["D", "E", "E"]` | `E` |
| `aqua_test_1_000172` | `E` | `["E", "E", "D"]` | `D` |
| `aqua_test_1_000188` | `D` | `["C", "C", "D"]` | `C` |

There were 3 answer-loss cases in `runs/qwen3_8b_aqua_calibrated_11_debate_1r/raw.jsonl`.
