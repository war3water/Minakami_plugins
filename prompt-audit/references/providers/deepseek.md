# DeepSeek — prompt guidance

Cite as `[ref: providers/deepseek.md §<section>]`. Universal patterns are in `general.md`; universal guidance for tool-using agents is in `agentic.md`.

**How to read this file.** DeepSeek publishes no prompting guide. Its API guides carry one piece of prompt-text advice, for JSON output, which applies to every DeepSeek model. Everything else comes from the universal files.

## Models

Status is the vendor's, checked on 2026-11-21. No DeepSeek model has a model file.

| Model | Id | Series | Model file | Status |
|---|---|---|---|---|
| DeepSeek V4.1 Flash | `deepseek-flash` | V4 | — | Active, newest |
| DeepSeek V4 Pro | `deepseek-v4-pro` | V4 | — | Active |

Retired: `deepseek-v4-flash` and `deepseek-v4-flash-vision-exp` (the names are still accepted and served by V4.1 Flash), `deepseek-chat` and `deepseek-reasoner` (retired 2026-07-24).

## All DeepSeek models

### JSON output

- With JSON output on (`response_format` of type `json_object`), DeepSeek's guide says to "Include the word "json" in the system or user prompt, and provide an example of the desired JSON format". When the output cannot be parsed as JSON, the API replaces it with spaces, so a reply can arrive blank; the guide's fix is to change the prompt. A JSON-mode prompt for DeepSeek that lacks the word or an example is a D1 gap on the output contract.
