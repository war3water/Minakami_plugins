# Reference source registry

Read by the `/prompt-audit:check-sources` command (`check-sources` skill in Codex). It records two things: where each family's official prompting guidance is **discovered** — the vendor's machine-readable page index plus its hub page, so a newly published model page is found by listing it, not by remembering it — and which pages have been **distilled** into `references/`, with what was taken, so the next check can tell "new guidance" from "already covered". Every reference-refresh release updates the matching rows in the same commit. To add a family, add one discovery row and register its family-wide page; the runbook needs nothing else.

## Lifecycle of a source

1. **Found.** `check-sources` lists a family's index and hub page, applies the match rule, and reports any page not in the known-matches list. Its report ends with a ready-to-paste registry patch.
2. **Registered.** The maintainer pastes the patch: the page gets a row in the registered-sources table with status `found`, and the known-matches list gains it. Nothing in `references/` changes yet.
3. **Distilled.** A reference-refresh release reads the page, distills the durable family-level claims into `references/`, records them in the coverage notes, snapshots the page's section outline, sets status `distilled`, and updates the last-reviewed date. That release runs the eval sweep.
4. **Retired or moved.** When a page 404s or redirects, the next check reports it; the release that follows either updates the URL or sets status `retired`, keeping the coverage notes so distilled claims stay traceable.

A source may stay `found` indefinitely — for example a model page whose guidance is all version-specific and adds nothing durable. Its coverage note says so, and the next check does not re-raise it.

## Evergreen test — what gets distilled

The reference files carry family-level, durable guidance only. A claim qualifies when the family-wide page states it, or when it holds across the family's currently listed model pages. If two current model pages of the same family point in opposite directions (one model spawns subagents readily, its sibling spawns few), the claim is version-specific: exclude it, and name it in the coverage notes so it is not re-evaluated every run.

## Discovery indexes

One row per index. `check-sources` fetches the index, applies the match rule, and diffs the result against the known matches below. It reads the hub page in the same run, not only as a fallback: on 2026-09-22 a model page published that day was in the Claude hub table hours before it appeared in the llms.txt. If the index cannot be fetched, the hub page is the first fallback and a web search naming the vendor's docs domain the second — and the report says which was used. A failed fetch never becomes "no new pages".

| Family | Index (machine-readable) | Match rule | Hub page (read every run) | Markdown variant of any page |
|---|---|---|---|---|
| claude | <https://platform.claude.com/llms.txt> — llms.txt listing every docs page with title and URL, no dates; lags new pages on launch day | path contains `/prompt-engineering/` | the "Model-specific guidance" table on the prompting best practices page — one row per current per-model guide | append `.md` to the page URL |
| gpt-codex (Cookbook) | <https://raw.githubusercontent.com/openai/openai-cookbook/main/registry.yaml> — YAML, one entry per Cookbook article with `title`, `path`, `date`, `tags`, and optional `archived` / `redirects` | title contains "prompting guide"; skip image, video, audio, realtime, and ChatGPT-product guides — not coding models | <https://developers.openai.com/cookbook/llms.txt> (a partial listing), then the Cookbook site search | page URL is `https://developers.openai.com/cookbook/` + `path` without its extension; append `.md` for markdown |
| gpt-codex (API docs) | <https://developers.openai.com/api/docs/llms.txt> — llms.txt of the API guides, entries end in `.md`, no dates; the per-model "Using GPT-x" guides and prompt-guidance pages live here, not in the Cookbook | path contains `guides/latest-model/`, `guides/prompt-guidance`, `guides/prompt-engineering`, or `guides/prompting`; skip live, voice, realtime, and frontend prompt pages and the caching, generation, and optimizer tool pages | <https://developers.openai.com/api/docs/guides/latest-model> — model selector listing the current generation | append `.md` to the page URL |
| gemini | <https://aistudio.google.com/llms.txt> — llms.txt for the Gemini API docs (the old `ai.google.dev/gemini-api/docs/llms.txt` 301-redirects here); entries already end in `.md`, no dates | title contains "prompt", or names a model generation with "developer guide"; skip media prompt guides (image, video, music, speech), release-note "what's new" pages, and the "Latest Gemini models" overview | the "Topic-specific prompt guides" section of the prompt design strategies page, plus <https://aistudio.google.com/docs/models> | append `.md` to the page URL |

Verified 2026-09-22: `https://ai.google.dev/llms.txt` returns 404 and `https://ai.google.dev/sitemap.xml` exceeds what a fetch tool returns, so the Gemini API docs llms.txt is the index to use; `cookbook.openai.com` URLs 308-redirect to `developers.openai.com/cookbook/`; `https://developers.openai.com/api/llms.txt` is only a routing page pointing at the API docs index above; the OpenAI Cookbook registry is the only index that carries publication dates, so "published after last review" is exact for that index and "first seen this run" for the others.

Verified 2026-11-10: the Gemini docs moved from `ai.google.dev/gemini-api/docs/…` to `aistudio.google.com/docs/…` (301); `gemini-api/docs/gemini-3.md.txt` now redirects to `docs/latest-model` (the Gemini 4 overview) and `gemini-api/docs/gemini-3` to `docs/whats-new-gemini-3.6`, neither with a prompting section. For content comparison, the Web Archive (`web.archive.org/cdx/search/cdx?url=<page>`) usually holds a copy of each page near its last-reviewed date; a sentence-level diff of two archived HTML copies separates real guidance changes from link and wording edits.

### Known matches at last discovery (2026-11-10)

What the match rule returned. A page in the index but not here is "new page found"; a page here but absent from the index is "retired or moved". A legacy-API or localized mirror of the same page counts once.

- **claude** (all under `/docs/en/build-with-claude/prompt-engineering/`): `overview` (hub page, not registered), `claude-prompting-best-practices`, `prompting-claude-fable-5`, `prompting-claude-fable-5-1`, `prompting-claude-fable-5-2` (first seen 2026-11-10), `prompting-claude-haiku-5-5` (first seen 2026-11-10), `prompting-claude-opus-4-8`, `prompting-claude-opus-5`, `prompting-claude-opus-5-5` (first seen 2026-09-22 via the hub table; not yet in llms.txt that day), `prompting-claude-sonnet-5`, `prompting-claude-sonnet-5-5` (first seen 2026-11-10).
- **gpt-codex, Cookbook** (`path`, registry `date`): `examples/gpt4-1_prompting_guide` (2025-04-14; present before 2026-09-22, missed by that discovery), `examples/gpt-5/gpt-5_prompting_guide` (2025-08-07), `examples/gpt-5/gpt-5-1_prompting_guide` (2025-11-13), `examples/gpt-5/gpt-5-2_prompting_guide` (2025-12-11), `examples/gpt-5/codex_prompting_guide` (2026-02-25). The GPT-5 and GPT-5.1 guides carry `archived: true` (already on 2026-09-18) and still serve. Skipped by the rule: Realtime, Sora 2, GPT Image, Whisper, and ChatGPT Enterprise prompting guides.
- **gpt-codex, API docs** (under `/api/docs/guides/`): `prompt-engineering`, `prompting`, `prompting/migrate-from-prompt-object` (first seen 2026-11-10), `prompt-guidance-gpt-5p6`, `latest-model/gpt-4.1`, `latest-model/gpt-5`, `latest-model/gpt-5.1`, `latest-model/gpt-5.2`, `latest-model/gpt-5.3-codex`, `latest-model/gpt-5.4`, `latest-model/gpt-5.5`, `latest-model/gpt-5.6`, `latest-model/gpt-6-astra` ("Using GPT-6", which since 2026-11 also covers GPT-6.1 Sol and GPT-6.1 Terra; no separate pages). Skipped by the rule: `live-prompting`, `voice-prompting`, `frontend-prompt`, `prompt-caching`, `prompt-generation`, `prompt-optimizer`. Seen, not registered individually: the "Using GPT-5.x" guides — superseded by Using GPT-6 for current guidance, and the 5.1 and 5.2 Cookbook guides cover those generations; `prompting` is a short landing page for the guides listed here.
- **gemini** (under `aistudio.google.com/docs/`): `prompting-strategies`. Gone since 2026-09-22: `gemini-3` (see its retired row). Skipped by the rule: `lyria-prompt-guide`, `latest-model`, the image and video prompt sections, and the "What's new in Gemini 3.6 / 3.7 / 3.8" release notes. Gemini 4 Argon and Gemini 4 Carbon have model pages but no prompting guide.

## Registered sources

| Family | Source | URL | Status | Last reviewed | Coverage notes — topics distilled, and what was excluded as version-specific |
|---|---|---|---|---|---|
| claude | Anthropic — Claude prompting best practices | <https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices> | distilled | 2026-11-10 | structure and tags; rule priority for collisions; motivation improves adherence; describe tools over scripting call order; model self-knowledge (state model identity and ids when the task depends on them); blanket defaults replaced by targeted conditions; overeagerness and scope; autonomy boundaries (confirm destructive, irreversible, or visible actions); long-horizon state tracking; investigate-before-answering and general-solution rules recorded as real levers, not no-ops; reasoning boilerplate as a no-op. Excluded: effort and thinking parameters, prefill migration, LaTeX and document creation, vision and computer-use specifics, the migration section. 2026-11-10: the reasoning-echo refusal is now stated on this family-wide page (the manual chain-of-thought fallback no longer recommends `<thinking>`/`<answer>` tags; a prompt asking for reasoning in `<thinking>` tags might be declined) — distilled into the reasoning-echo entry, which now covers tag scaffolds; multishot examples presented as problem, method, and expected answer (no change needed). Excluded: the medication-dosing blocks (verbatim per-model safety text), thinking-on-by-default API notes, the Sonnet 5.5 migration subsection |
| claude | Anthropic — Prompting Claude Opus 5 | <https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5> | distilled | 2026-11-10 | instructed re-verification no-op; scope-expansion bounds; explicit length contract; narration cadence via positive examples; review-prompt conservatism lowers recall; full task specification up front. Excluded: subagent-spawning caps (the Opus 4.8 page says the opposite), artifacts when thinking is disabled, effort recommendations. 2026-11-10: new "Reasoning in the response" section corroborates the reasoning-echo entry and its outlet (a short explanation or a summary of actions is fine) |
| claude | Anthropic — Prompting Claude Fable 5.1 | <https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1> | distilled | 2026-11-10 | forced narration scaffolding ("hold all findings for the final response") removed in favor of a described cadence; finish-the-whole-task and autonomous-run instructions as completion criteria; writing density over compression; keep changes and tests to what the task asks for; say what a compaction summary must preserve. Excluded: effort levels, append-only history and thinking-block rules (API), the tool-call batching nudge (harness message), the quoting-sources example, search triggering at low effort, safeguard false positives, targeted edits, long-output token notes, asynchronous subagent harness, vision tools. 2026-11-10: adds the reasoning-extraction note with the same outlet (corroboration). Excluded: thinking-block prefix binding, cache pricing |
| claude | Anthropic — Prompting Claude Fable 5 | <https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5> | distilled | 2026-11-10 | give the reason, not only the request; ground progress claims in tool results; state the boundaries; a brief instruction beats enumerating behaviors (older skills too prescriptive); final-summary readability (complete sentences, no working shorthand); a notes or memory file as a place for state; reasoning-echo instructions trigger the reasoning-extraction refusal. Excluded: effort, longer turns, early-stopping and context-budget reassurance snippets, send-to-user tool, memory bootstrapping prompt, verifier-subagent scaffolding. 2026-11-10: adds the short-explanation outlet, distilled into the reasoning-echo entry. Excluded: fallback retry rules for reasoning_extraction |
| claude | Anthropic — Prompting Claude Sonnet 5 | <https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5> | distilled | 2026-11-10 | literal instruction following (state an instruction's scope); positive examples over negative instructions for verbosity; forced interim status scaffolding removed; review harnesses ask for coverage, not filtering; task specification up front in interactive coding. Excluded: effort and thinking calibration, tokenizer and token-limit notes, sampling parameters, design defaults, computer use |
| claude | Anthropic — Prompting Claude Opus 4.8 | <https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-4-8> | distilled | 2026-11-10 | corroborates the Sonnet 5 page section for section (literal following, verbosity via positive examples, review-harness coverage, task specification up front); its subagent direction contradicts Opus 5 and marks that topic version-specific. Excluded: effort, thinking-off default, tone specifics, design house style |
| claude | Anthropic — Prompting Claude Opus 5.5 | <https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5> | distilled | 2026-11-10 | found 2026-09-22 via the hub table on its publication day; unattended runs need a completion checklist and evidence-based end-of-turn handling; reasoning-depth lines in chat prompts are removable; reasoning-echo refusal; generic prohibitions swap one default for another, so name the pattern; random-id tags for pasted text recorded as corroboration of the delimiter rule in `general.md`, not distilled separately. Excluded: medium effort default, thinking always on, time-budget signals, the multi-app exploration sentence, progress-update display settings, safeguard categories, visual-input tools, the frontend snippet. 2026-11-10: verified unchanged apart from wording and API notes; its "reasoning-depth lines are removable" claim, with Fable 5.2, Sonnet 5.5, and Haiku 5.5, now backs the think-less no-op in `general.md` |
| claude | Anthropic — Prompting Claude Fable 5.2 | <https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2> | distilled | 2026-11-10 | found and distilled 2026-11-10; approval rules apply as written, so name the actions; absolute rules in memory, notes, and instruction files pile up — state scope and reason, put the exception inside the rule (a separate line or a general "act more freely" barely moves it); persistence text separates ordinary obstacles from deliberate blockers and keeps the risky-action confirmation; think-less lines no-op (`general.md`); reasoning-echo refusal (corroboration); final-report readability (corroborates Fable 5). Excluded: the code-ownership sentence, the cost-first subagent tool description, the "treat that answer as done" lines (contradicts Opus 5.5's advice), token budgets written into the prompt, hard numeric style limits (corroborates writing density), effort calibration, progress-update display and harness reminders, prefix binding |
| claude | Anthropic — Prompting Claude Sonnet 5.5 | <https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5-5> | distilled | 2026-11-10 | found and distilled 2026-11-10; a concrete coding-check paragraph is a completion criterion, not instructed re-verification (narrows the Opus 5 claim in `claude-family.md`); blanket tool-discouraging wording suppresses needed checks; persistence plus scope-stop pair (corroborates the scope statement); think-less lines no-op; reasoning-echo outlet; removing "hold all findings for the final response" (corroborates forced narration). Excluded: the JSON "think the problem through" line and last-JSON-value parsing, `between_tools`, the extra-review-round stopper at xhigh and max, ideas-then-stop for open requests, mid-turn user-message placement (API), tolerant tool-call handling (harness), effort |
| claude | Anthropic — Prompting Claude Haiku 5.5 | <https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-haiku-5-5> | distilled | 2026-11-10 | found and distilled 2026-11-10; the same concrete coding-check paragraph as Sonnet 5.5; blanket search instructions over-trigger (with Sonnet 5.5, the tool-wording entry in `claude-family.md`); persistence plus scope-stop pair; "answer directly" lines don't reduce thinking. Excluded: the current date in the search tool and the search nudge (single model; Gemini 3 Flash has a similar clause), the chatbot system-prompt adherence text, the JSON-with-tools line, mid-turn user-message placement (API), effort |
| gpt-codex | OpenAI — GPT-5 prompting guide | <https://developers.openai.com/cookbook/examples/gpt-5/gpt-5_prompting_guide> (moved from `cookbook.openai.com`, 308, verified 2026-09-19) | distilled | 2026-11-10 | literal instruction-following and explicit defaults/stop conditions; single persistence stance; contradiction sensitivity; literal format specs; tool preambles as a cadence lever. Excluded: reasoning-effort values, Responses API context reuse, frontend stack recommendations, the Cursor case study, appendix prompts. 2026-11-10: marked `archived` in the Cookbook registry (already so on 2026-09-18); page still serves |
| gpt-codex | OpenAI — GPT-5.1 Prompting Guide | <https://developers.openai.com/cookbook/examples/gpt-5/gpt-5-1_prompting_guide> | distilled | 2026-11-10 | persist end to end and treat ambiguous directives as permission to proceed (stance); tool descriptions carry explicit must and must-not usage rules; counted update cadences work in this family. Excluded: the none reasoning mode, apply_patch and shell tool types, design-token enforcement, plan-tool mechanics, the metaprompting workflow. 2026-11-10: outline verified (no archived copy for a content diff); marked `archived` in the Cookbook registry |
| gpt-codex | OpenAI — GPT-5.2 Prompting Guide | <https://developers.openai.com/cookbook/examples/gpt-5/gpt-5-2_prompting_guide> | distilled | 2026-11-10 | explicit length targets; scope-drift prevention ("no extra features"); ambiguity handling (ask, or state the interpretation); updates clamped to outcome-based sentences. Excluded: compaction, the outline-first long-context technique (single page), structured extraction and Office workflows, the web-research prompt |
| gpt-codex | OpenAI — Codex Prompting Guide | <https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide> | distilled | 2026-11-10 | starter-prompt section structure (autonomy and persistence, implementation, editing constraints, exploration, presenting work); meta-commentary "announce the plan" instructions cause premature stopping; a final-answer style contract; personality is a choice, not a default. Excluded: tool schemas, compaction, the phase parameter, the new-features section, preamble cadence numbers |
| gpt-codex | OpenAI — Prompting guidance for GPT-5.6 Sol | <https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6> | distilled | 2026-11-10 | found 2026-09-22; simplify prompts first; outcome-first prompts and stopping conditions; autonomy and approval boundaries; tool routing (what, when, what not); check work before finishing; the suggested prompt structure (role, personality, goal, success criteria, constraints, tools, output, stop rules). Excluded: the verbosity parameter, programmatic tool calling, retrieval budgets, the reasoning-effort sweep, the migration workflow |
| gpt-codex | OpenAI — Using GPT-6 (model guide with prompting best practices; Astra, 6.1 Sol, 6.1 Terra, Sol, Luna) | <https://developers.openai.com/api/docs/guides/latest-model/gpt-6-astra> | distilled | 2026-11-10 | found 2026-09-22; bias to action with completion; user instructions take precedence over skill files (state the precedence); request the writing style explicitly (paragraphs versus lists); test scope for trivial reversible changes; delegation guidance for multi-agent harnesses. As of 2026-11-10 the page is titled "Using GPT-6", covers GPT-6 Astra, GPT-6.1 Sol, GPT-6.1 Terra, GPT-6 Sol, and GPT-6 Luna, and states its prompts are a starting point across the GPT-6 family (behavior observed on Astra), so its claims count as family-level for GPT-6; no separate per-model prompting pages exist. Excluded: the none reasoning effort on Sol and Luna, the migration quickstart, the model-behavior list, per-model `none` effort support |
| gpt-codex | OpenAI — Prompt engineering (API docs, family-wide) | <https://developers.openai.com/api/docs/guides/prompt-engineering> | distilled | 2026-11-10 | found 2026-09-22; the family-wide page for the evergreen test alongside the GPT-5 Cookbook guide; developer versus user role split (function definition versus arguments); headed sections identity, instructions, examples, context; reasoning models want high-level guidance where earlier GPT models wanted explicit steps; keep prompts in code with fixtures and tests (maintenance advice, Info level). Excluded: API parameter names, model-choice advice. 2026-11-10: outline snapshot corrected (it had omitted "Few-shot learning" and "Include relevant context information", present since before 2026-09-20) |
| gpt-codex | OpenAI developer blog — Rethinking skills and prompts for GPT-6 Astra | <https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra> | distilled | 2026-11-10 | found 2026-09-22 (blog, recorded as corroboration); over-specified skills; conditional file references in agent-instruction files; over-restrictive decision boundaries halt work; persistence with completion criteria |
| gpt-codex | OpenAI — GPT-4.1 Prompting Guide (Cookbook) | <https://developers.openai.com/cookbook/examples/gpt4-1_prompting_guide> | found | 2026-11-10 | found 2026-11-10 (dated 2025-04-14, missed by the 2026-09-22 discovery); superseded generation; nothing to distill — do not re-raise |
| gpt-codex | OpenAI — Migrate from prompt objects | <https://developers.openai.com/api/docs/guides/prompting/migrate-from-prompt-object> | found | 2026-11-10 | found 2026-11-10; API deprecation how-to (`v1/prompts` shuts down 2026-11-30); corroborates "keep prompts in code"; nothing to distill — do not re-raise |
| gemini | Google — Gemini prompt design strategies | <https://aistudio.google.com/docs/prompting-strategies> (moved from `ai.google.dev/gemini-api/docs/prompting-strategies`, 301, verified 2026-11-10) | distilled | 2026-11-10 | concise directives; end-of-context constraint repetition; explicit output schema; few-shot examples lever; one consistent delimiter style; define ambiguous parameters; verbosity is opt-in; chain-of-thought scaffolds unnecessary while a short depth request remains a lever; agentic system-instruction dimensions (reasoning strategy, execution and persistence and risk, interaction and verbosity). Excluded: Gemini 3 Flash temporal-context tactics, model parameters, grounding and code-execution tool sections, fallback responses. 2026-11-10: "Experiment with model parameters" now says Gemini 4 and 3.6+ ignore temperature, top_p, and top_k (already excluded as model parameters) |
| gemini | Google — Gemini 3 developer guide | <https://ai.google.dev/gemini-api/docs/gemini-3> | retired | 2026-11-10 | found 2026-09-19; corroborates precise instructions, verbosity opt-in, and question-after-context anchoring; FAQ: replace chain-of-thought prompting with the thinking setting. Excluded: API features, migration, OpenAI compatibility, the model list. Retired 2026-11-10: dropped from the index; the old URLs redirect to `docs/latest-model` and `docs/whats-new-gemini-3.6`, neither with a prompting section. Its distilled claims remain on the strategies page's "Gemini 3 › Core prompting principles", so no coverage is lost |

## Outline snapshots

Section headings of each distilled page, for the outline half of the compare step. Captured 2026-09-22 on the same day as the distillation, so the next run has a true baseline; re-captured 2026-11-10 for the pages that changed or were added that day. When comparing, ask the fetch tool to quote heading lines verbatim with their hash marks; summarized heading lists fold levels and produce false "changed" signals.

**Claude prompting best practices** (H2 › H3):

- Model-specific guidance
- General principles › Be clear and direct; Add context to improve performance; Use examples effectively; Structure prompts with XML tags; Give Claude a role; Long context prompting; Model self-knowledge
- Output and formatting › Communication style and verbosity; Control the format of responses; LaTeX output; Document creation; Migrating away from prefilled responses
- Tool use › Tool usage; Optimize parallel tool calling
- Thinking and reasoning › Overthinking and excessive thoroughness; Leverage thinking and interleaved thinking capabilities
- Agentic systems › Long-horizon reasoning and state tracking; Balancing autonomy and safety; Research and information gathering; Subagent orchestration; Chain complex prompts; Reduce file creation in agentic coding; Overeagerness; Avoid focusing on passing tests and hardcoding; Minimizing hallucinations in agentic coding
- Capability-specific tips › Improved vision capabilities; Frontend design; Medication dosing
- Migration considerations › Migrating to Claude Sonnet 5.5
- Next steps

**Prompting Claude Opus 5** (H2):

- Capability improvements; Response length and verbosity; User-facing progress updates; Written deliverable length; Task scope and over-verification; Controlling subagent spawning; Self-correction; Running with thinking disabled; Reasoning in the response

**Prompting Claude Fable 5.1** (H2):

- Consider all effort levels; Ask for user-facing progress updates; Batch independent tool calls in agent loops; Keep the conversation history append-only; Writing density; Formatting in chat; Quoting retrieved sources; Finish the whole task; Tell the model what to preserve in compaction summaries; Keep changes and tests to what the task asks for; Search triggering at low effort; Reduce safeguard false positives; Prefer targeted edits over whole-file rewrites; Leave room for long outputs at xhigh and max effort; Let the lead agent keep working while subagents run; Give vision work tools to crop and zoom

**Prompting Claude Fable 5** (H2):

- Capability improvements; Longer turns by default; Consider all effort levels; Strong instruction following; Ground progress claims during long runs; State the boundaries; Parallel subagents; Construct a memory system; Rare cases of early stopping; Rare cases of context-budget concern; Give the reason, not only the request; Readability when communicating with the user; Create a send-to-user tool; Recommended scaffolding changes

**Prompting Claude Sonnet 5** (H2):

- Response length and verbosity; Calibrating effort and thinking depth; Tool use triggering; User-facing progress updates; More literal instruction following; Tone and writing style; Design and frontend defaults; Interactive coding products; Code review harnesses; Computer use

**Prompting Claude Opus 4.8** (H2):

- Response length and verbosity; Calibrating effort and thinking depth; Tool use triggering; User-facing progress updates; More literal instruction following; Tone and writing style; Controlling subagent spawning; Design and frontend defaults; Interactive coding products; Code review harnesses; Computer use

**Prompting Claude Opus 5.5** (H2):

- Capabilities relevant to prompting; Calibrate effort; Prompts written for thinking disabled; Unattended agentic runs; Safeguard refusals; User-facing progress updates; Explore context in multiapp workflows; Time signals for multiagent harnesses; Thinking instructions in chat system prompts; Mark pasted text in user messages; Tools for complex visual inputs; Frontend design defaults

**Prompting Claude Fable 5.2** (H2 › H3):

- Calibrate effort; Finish the whole task › Approvals; Say who owns the code; Keep users informed during long turns; Set expectations for subagents; Keep caution from piling up; Review instructions written for earlier models; Make reports easy to follow; Safeguard refusals; Where to start

**Prompting Claude Sonnet 5.5** (H2):

- Calibrate effort; Steer initiative and scope; Running without up-front thinking; Reasoning tasks with JSON output; User-facing progress updates; Tool use in chat and knowledge work; Mid-turn user messages; Verification on coding tasks; Tolerant tool-call handling; Tools for complex visual inputs; Safeguard refusals

**Prompting Claude Haiku 5.5** (H2):

- Use effort to control thinking; Accurate search results; Use adaptive thinking with JSON output and your own tools; Prevent early stopping in long agent prompts; Tell coding agents to verify their changes; Mid-turn user messages; Keep chatbots to their system prompt; Keep reasoning out of user-facing text; Safeguard refusals

**GPT-5 prompting guide** (H2 › H3 › H4):

- Agentic workflow predictability › Controlling agentic eagerness (H4: Prompting for less eagerness; Prompting for more eagerness); Tool preambles; Reasoning effort; Reusing reasoning context with the Responses API
- Maximizing coding performance, from planning to execution › Frontend app development (H4: Zero-to-one app generation; Matching codebase design standards); Collaborative coding in production: Cursor's GPT-5 prompt tuning (H4: System prompt and parameter tuning)
- Optimizing intelligence and instruction-following › Steering (H4: Verbosity); Instruction following; Minimal reasoning; Markdown formatting; Metaprompting
- Appendix › SWE-Bench verified developer instructions; Agentic coding tool definitions; Taubench-Retail minimal reasoning instructions; Terminal-Bench prompt

**GPT-5.1 Prompting Guide** (H2):

- Introduction; Migrating to GPT-5.1; Agentic steerability; Optimizing intelligence and instruction-following; Maximizing coding performance from planning to execution; New tool types in GPT-5.1; How to metaprompt effectively; What's next

**GPT-5.2 Prompting Guide** (H2):

- Introduction; Key behavioral differences; Prompting patterns; Compaction (Extending Effective Context); Agentic steerability & user updates; Tool-calling and parallelism; Structured extraction, PDF, and Office workflows; Prompt Migration Guide to GPT 5.2; Web search and research; Conclusion; Appendix

**Codex Prompting Guide** (H2 › H3):

- Getting Started › Recommended Starter Prompt
- Prompting › Autonomy and Persistence; Code Implementation; Editing constraints; Exploration and reading files; Plan tool; Special user requests; Frontend tasks; Presenting your work and final message; Final answer structure and style guidelines; Mid-Rollout User Updates; Using agents.md
- Compaction
- Tools › Apply_patch; Shell_command; Update Plan; View_image; Dedicated terminal-wrapping tools; Other Custom Tools; Parallel Tool Calling; Tool Response Truncation
- New features in GPT-5.3 Codex › Phase; Values; Preambles & Personality; Friendly; Pragmatic; Troubleshooting & Metaprompting

**Prompting guidance for GPT-5.6 Sol** (H2):

- Simplify prompts first; Outcome-first prompts and stopping conditions; Personality, collaboration, and response length; Define autonomy and approval boundaries; Tool routing; Programmatic Tool Calling; Grounding, citations, and retrieval budgets; Long-running workflows and state; Reasoning effort; Frontend and visual tasks; Check work before finishing; Suggested prompt structure; Prompt migration workflow

**Using GPT-6** (H2 › H3):

- What's new; Limitations
- Prompting best practices › GPT-6 Astra behavior; Initiative and follow-through; Instruction following; Personality and writing style; Subagent delegation; Testing and verification
- Migration quickstart › Migrate with Codex; Update API and model parameters

**Prompt engineering (OpenAI API docs)** (H2 › H3 › H4):

- Choosing a model; Prompt engineering; Message roles and instruction following; Version prompts in code; Message formatting with Markdown and XML (H4: Save on cost and latency with prompt caching); Few-shot learning; Include relevant context information (H4: Planning for the context window)
- Prompting current models › Prompting best practices for the latest model (H4: Coding; Front-end engineering; Agentic tasks)
- Prompting reasoning models; Next steps; Other resources

**Rethinking skills and prompts for GPT-6 Astra** (H2):

- Better skills; Up-to-date AGENTS.md; Decision boundaries; Persistence

**Gemini prompt design strategies** (H2 › H3):

- Topic-specific prompt guides
- Clear and specific instructions › Input; Partial input completion; Constraints; Response format; Format responses with the completion strategy
- Zero-shot vs few-shot prompts › Optimal number of examples; Consistent formatting
- Add context; Break down prompts into components; Experiment with model parameters; Prompt iteration strategies; Fallback responses; Grounding and code execution
- Gemini 3 › Core prompting principles; Gemini 3 Flash strategies; Enhancing reasoning and planning; Structured prompting examples; Example template combining best practices
- Agentic workflows › Reasoning and strategy; Execution and reliability; Interaction and output; System instruction template
- Next steps

**Gemini 3 developer guide** (H2 › H3; retired 2026-11-10, kept for traceability):

- Meet the Gemini 3 series; New API features in Gemini 3; Migration from Gemini 2.5; OpenAI compatibility
- Prompting best practices › Precise instructions; Output verbosity; Context management
- FAQ
