# Model selection

Use `Qwen3-4B-GGUF` with `Q4_K_M` quantization first.

## Why this baseline

The first goal is not to find the strongest local model. The first goal is to test whether same-model agents sharing a debate context lose independence compared with independent same-model sampling.

A 3B-4B model is the right initial range:

- Small enough for local repeated runs.
- Strong enough that failures are not simply caused by a very weak base model.
- Practical for LM Studio.

## Initial recommendation

- Model family: Qwen3
- Parameter size: 4B
- Quantization: Q4_K_M
- Reasoning mode: no_think
- Context length requested: 8192
- Agents: 3
- Execution: sequential, not concurrent

## Avoid at first

- 1B or smaller models for the main experiment.
- 7B/8B models for the first version.
- Modified or unclear model releases.
- Running agents concurrently before the sequential baseline is stable.

## Record every run

Every result should save:

- LM Studio model identifier
- model family
- parameter size
- quantization
- reasoning mode
- requested context length
- temperature
- top_p
- agent count
- rounds
- condition
