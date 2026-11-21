# Meta — source detail

Read by `check-sources` when it compares Meta's pages. Each page section states what is distilled now, at which scope, and what is excluded; it is rewritten, never appended to, when the page changes (see "Keeping the registry bounded" in `SOURCES.md`). "Scoped" means an entry in `sources/meta-entries.md`, named by its section; Meta has no all-models guidance.

## Known matches at last discovery (2026-11-21)

From `https://dev.meta.ai/llms.txt`: `docs/muse-spark-open/prompting.md`, `docs/muse-glimmer/prompting.md`, `docs/models.md`, `docs/media-understanding.md`, `docs/computer-use.md`. Llama 4 from Meta's GitHub `meta-llama/llama-models` (`models/llama4/MODEL_CARD.md`).

## Seen, not registered

- `dev.meta.ai/llama/docs/` returns 404, and the old llama.com prompting pages return 500; nothing to distill there.
- `docs/prompt-caching.md`: ordering for cache cost, not prompt quality.
- Hugging Face `meta-llama/*` cards are gated.

## Muse Spark Open prompting guide

- **Distilled (scoped, Muse Spark Open):** §System prompt structure (rules that must always hold go first; the structured template); §Tools and reasoning (no tool descriptions in the system prompt; the `Reasoning strength` line; media order). With Moonshot's Kimi K3 guide, the basis of `agentic.md` "Tool definitions live in the tool schema".
- **Excluded:** chat template, special tokens, `reasoning_effort`.
- **Outline (H2):** Structure a conversation; Write a system prompt; Control reasoning; Call tools; Send images, video, and audio; Next steps

## Muse Glimmer prompting guide

- **Distilled (scoped, Muse Glimmer):** §System prompt structure (specific task, constraints up front, no meta-instructions about internals); §Tools and reasoning (no step-by-step prompting).
- **Excluded:** chat template, special tokens, roles and recipients, sampling.
- **Outline (H2):** Chat template; Special tokens; Roles and recipients; System prompts; Reasoning and chain-of-thought; Tool calling; Multimodal input; Multi-turn conversations; Temperature and sampling; Common pitfalls; Next steps

## Image, video, and audio understanding; Build a computer-use agent

- **Distilled (scoped):** Muse Spark, §Images and computer use (one output shape, coordinate fields, point then count, a minimal system prompt); Muse Wonder, the strict computer-use system prompt.
- **Excluded:** image message structure, the computer tool setup, driver code.
- **Outline:** Images › Localize objects with perception grounding (Coordinate system; Prompt for structured coordinates; Some grounding modes: point, box, and count; Render annotation overlays). Computer use › How the observe-act loop works; Enable the computer tool; Provide a driver; Read and execute actions; Return a screenshot; Handle safety checks; Run the loop; Manage conversation state; Handle done and incomplete; Set a strict system prompt; Code execution as an alternative; Next steps

## Llama 4 model card (GitHub)

- **Distilled (scoped, Llama 4 Maverick and Scout):** §System prompt structure (a system prompt reduces false refusals and preachy phrasing; the banned-phrase list).
- **Excluded:** prompt format tokens, tool-call format.
- **Outline:** the "System Prompts" paragraph under Safeguards › Model level fine tuning.
