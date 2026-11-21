<!-- Built by scripts/build-model-files.py from prompt-audit/sources/qwen-entries.md. Do not edit by hand: edit the source and rebuild. -->

# Qwen3.5: model guidance

Applies only to Qwen3.5. Read it with `providers/qwen.md`; where an entry here disagrees with that file or with `general.md`, the entry here wins. Cite as `[ref: providers/qwen/qwen3-5.md §<section>]`.

## Thinking switches

- The model cards say these models do "not officially support the soft switch of Qwen3, i.e., `/think` and `/nothink`". A prompt that relies on `/think`, `/no_think` or `/nothink` lines to turn thinking on or off depends on unsupported behavior; remove the lines and use the runtime's thinking setting.

## Benchmark prompts

- For benchmark runs the model cards give fixed answer formats: for math, "Please reason step by step, and put your final answer within oxed{}."; for multiple choice, a JSON `answer` field holding only the choice letter. Suggest them only when the prompt's purpose is benchmarking.
