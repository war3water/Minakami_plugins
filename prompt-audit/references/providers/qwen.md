# Qwen (Alibaba) — prompt guidance

Cite as `[ref: providers/qwen.md §<section>]`. Universal patterns are in `general.md`; universal guidance for tool-using agents is in `agentic.md`.

**How to read this file.** Alibaba's Model Studio prompt guide is written for all Qwen text models. The sections under "All Qwen models" apply to each of them. When the user named a model in the table below, also read its model file and apply it.

## Models

Status is the vendor's, checked on 2026-11-21; "newest" marks the newest model of its series.

| Model | Id | Series | Model file | Status |
|---|---|---|---|---|
| Qwen3.6 | `qwen3.6-27b`, `qwen3.6-35b-a3b` (open weights) | Qwen3.6 | `providers/qwen/qwen3-6.md` | Active |
| Qwen3.5 | `qwen3.5-27b`, `qwen3.5-397b-a17b`, … (open weights) | Qwen3.5 | `providers/qwen/qwen3-5.md` | Active |

Served, with no model-specific guidance, so this file is their whole basis: Qwen4-Max (`qwen4-max`, newest), Qwen3.7-Plus, Qwen3.8-Flash, Qwen3.8-Max, the Qwen3.8 open-weight models, and the older Max, Plus and Flash versions. Qwen4-Max-Preview is retired after 2026-11-25.

## All Qwen models

### Structure and wording

- The guide recommends a prompt framework that names the context, objective, style, tone, audience and response format. Style, tone and audience are what general prompts most often leave out; when the output is read by people and the prompt says nothing about them, that is a D7 gap.
- For separators, the guide recommends character runs that are rare in natural text, such as `###`, `===` or `>>>`, so they read as boundaries rather than punctuation.
- Ambiguous words should be replaced with precise ones; the guide's example replaces "language" with "language type" because the model read "language" as written versus spoken.
- Give direct instructions rather than descriptions, state constraints explicitly ("do not modify original text"), and include output examples; the guide calls examples "the most effective way to prevent model hallucinations".

### Reasoning in the output

- Unlike `general.md`'s no-op entry, Qwen's guide recommends asking the model to write out its reasoning before the result ("First output the thinking and judgment process for each requirement"), and prompt chaining for tasks that break down along fixed steps. For Qwen, don't flag such a request as reasoning boilerplate.

### JSON output

- In JSON Object mode the system or user message must contain the word "JSON"; otherwise the API rejects the request ("'messages' must contain the word 'json' in some form"). A JSON-mode prompt for Qwen without the word fails outright: Critical when the product depends on that call.
- Describe the expected schema in the prompt: field names, types, required or optional, format constraints such as date formats, and examples. "Return user information" alone gives unpredictable structures.
