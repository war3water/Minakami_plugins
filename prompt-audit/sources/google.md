# Google — source detail

Read by `check-sources` when it compares Google's pages. Each page section states what is distilled now, at which scope, and what is excluded; it is rewritten, never appended to, when the page changes (see "Keeping the registry bounded" in `SOURCES.md`).

## Known matches at last discovery (2026-11-17)

Under `https://aistudio.google.com/docs/`: `prompting-strategies`. Skipped by the rule: `lyria-prompt-guide`, `latest-model`, the image and video prompt sections, and the "What's new" release notes (Gemini 3.6, 3.7, 3.8 and Gemini 4 Argon, Carbon, Hydrogen).

## Seen, not registered

- Gemini 4 Argon, Carbon, and Hydrogen have model pages and "What's new" release notes but no prompting guide. Hydrogen's migration checklist says to declare tools natively rather than prompt for raw-text JSON tool calls, which is API guidance, not prompt guidance.

## Gemini prompt design strategies

The provider-wide page; its general sections apply to all Gemini models. Archived copies of `aistudio.google.com` pages carry no text, so content is compared by reading the live page against this note, and the outline against the snapshot.

- **Distilled (all models):** concise directives; end-of-context constraint repetition; explicit output schema; few-shot examples as a lever; one consistent delimiter style; define ambiguous parameters; verbosity is opt-in; chain-of-thought scaffolds are unnecessary while a short depth request remains a lever; the agentic system-instruction dimensions (reasoning strategy; execution, persistence, and risk; interaction and verbosity). Its "Gemini 3 › Core prompting principles" also carries precise instructions, verbosity opt-in, and question-after-context anchoring.
- **Distilled (scoped, Gemini 3 Flash):** §Current date and grounding (current date and year for search queries, knowledge cutoff, the strict grounding clause).
- **Excluded:** model parameters (Gemini 4 and 3.6+ ignore temperature, top_p, and top_k), the grounding and code-execution tool sections, fallback responses.
- **Outline (H2 › H3):**
  - Topic-specific prompt guides
  - Clear and specific instructions › Input; Partial input completion; Constraints; Response format; Format responses with the completion strategy
  - Zero-shot vs few-shot prompts › Optimal number of examples; Consistent formatting
  - Add context; Break down prompts into components; Experiment with model parameters; Prompt iteration strategies; Fallback responses; Grounding and code execution
  - Gemini 3 › Core prompting principles; Gemini 3 Flash strategies; Enhancing reasoning and planning; Structured prompting examples; Example template combining best practices
  - Agentic workflows › Reasoning and strategy; Execution and reliability; Interaction and output; System instruction template
  - Next steps
