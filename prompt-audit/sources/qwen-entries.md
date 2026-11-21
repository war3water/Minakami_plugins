# Qwen (Alibaba): model entries (source)

The one place each model-specific entry is written. Audits never read this file. `scripts/build-model-files.py` copies every entry into the built file of each model its *Applies to* names (one file per model name, named by the rule in the script), under `references/providers/qwen/`, and its check fails when a built file is out of date. Edit here, then rebuild; never edit a built file.

An entry starts with `- *Applies to:* <model>, <model>.` using names from the table below, and says everything it needs on its own: a built file shows it without the other models' entries. Conditions such as an effort level go in the entry text, not in the *Applies to* list.

## Models

| Model | Also covers |
|---|---|
| Qwen3.5 | Qwen3.6 |

## Thinking switches

- *Applies to:* Qwen3.5, Qwen3.6. The model cards say these models do "not officially support the soft switch of Qwen3, i.e., `/think` and `/nothink`". A prompt that relies on `/think`, `/no_think` or `/nothink` lines to turn thinking on or off depends on unsupported behavior; remove the lines and use the runtime's thinking setting.

## Benchmark prompts

- *Applies to:* Qwen3.5, Qwen3.6. For benchmark runs the model cards give fixed answer formats: for math, "Please reason step by step, and put your final answer within oxed{}."; for multiple choice, a JSON `answer` field holding only the choice letter. Suggest them only when the prompt's purpose is benchmarking.
