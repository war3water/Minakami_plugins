# Qwen — source detail

Read by `check-sources` when it compares Qwen's pages. Each page section states what is distilled now, at which scope, and what is excluded; it is rewritten, never appended to, when the page changes (see "Keeping the registry bounded" in `SOURCES.md`). "All models" means `references/providers/qwen.md`; "scoped" means an entry in `sources/qwen-entries.md`, named by its section.

## Known matches at last discovery (2026-11-21)

Model Studio (`https://www.alibabacloud.com/help/en/model-studio/`): `prompt-engineering-guide`, `qwen-structured-output`, `deep-thinking`, `text-generation-model`, `model-list-text-generation`, `model-depreciation`. Hugging Face: `Qwen/Qwen3.5-27B`, `Qwen/Qwen3.6-27B`, the Qwen3.8 cards.

## Seen, not registered

- `qwen.readthedocs.io`: stale (Qwen3 and Qwen3-2507 only), no index.
- `deep-thinking`: its `/think` and `/no_think` prompt switches cover only the Qwen3 hybrid open-weight models and `qwen-plus-2025-04-28`, which are no longer current; the Qwen3.5 and 3.6 cards say the switch is unsupported (distilled from the cards below).
- Qwen3.8 cards: sampling, output length, and context settings only.

## Text-to-text prompt guide

- **Distilled (all models):** the context, objective, style, tone, audience, and response framework; rare-symbol separators; precise wording for ambiguous words; direct instructions, explicit constraints, output examples (§Structure and wording); asking for reasoning before the result, and prompt chaining (§Reasoning in the output, an exception to `general.md`'s no-op entry).
- **Excluded:** the console's automatic prompt optimizer.
- **Outline (H1 › H2 › H3):** Text-to-text prompt guide › Design prompts (Build clear and specific prompts; Use prompt frameworks) › Optimize prompts (Tip 1: Provide output examples; Tip 2: Set steps for tasks; Tip 3: Use separators to distinguish units; Tip 4: Guide the model to "think") › Prompt testing and iteration › Optimization case: multilingual content › Optimization case: Extracting multi-dimensional analysis results… and outputting JSON

## Structured output

- **Distilled (all models):** the word "JSON" is required in JSON Object mode (the API rejects the request otherwise); describe the schema with fields, types, required status, formats, and examples (§JSON output). With DeepSeek and Moonshot, the basis of `general.md` "JSON output mode states the shape".
- **Excluded:** `response_format`, `max_tokens`, JSON Schema mode setup.
- **Outline:** Structured output › Usage; Supported models; Getting started; Image and video data processing; Optimize prompts; Getting structured output (How to use; Configuration guide); Going live; Error codes

## Qwen3.5 and Qwen3.6 model cards (Hugging Face)

- **Distilled (scoped, Qwen3.5 and Qwen3.6):** §Thinking switches (the soft switch is unsupported); §Benchmark prompts (answer formats for math and multiple choice).
- **Excluded:** sampling, output length, YaRN, dropping thinking content from history (chat template).
- **Outline (H2):** Highlights; Model Overview; Benchmark Results; Quickstart; Agentic Usage; Processing Ultra-Long Texts; Best Practices
