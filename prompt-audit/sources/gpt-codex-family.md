# GPT–Codex family — source detail

Read by `check-sources` when it compares the GPT–Codex family. Each page section states what is distilled now and what is excluded; it is rewritten, never appended to, when the page changes (see "Keeping the registry bounded" in `SOURCES.md`).

## Known matches at last discovery (2026-11-17)

- **Cookbook** (`path`, registry `date`): `examples/gpt4-1_prompting_guide` (2025-04-14), `examples/gpt-5/gpt-5_prompting_guide` (2025-08-07), `examples/gpt-5/gpt-5-1_prompting_guide` (2025-11-13), `examples/gpt-5/gpt-5-2_prompting_guide` (2025-12-11), `examples/gpt-5/codex_prompting_guide` (2026-02-25). The GPT-5, GPT-5.1, and GPT-5.2 guides carry `archived: true` in the registry and are still served. Skipped by the rule: the Realtime, Sora 2, GPT Image, Whisper, and ChatGPT Enterprise prompting guides.
- **API docs** (under `/api/docs/guides/`): `prompt-engineering`, `prompting`, `prompting/migrate-from-prompt-object`, `prompt-guidance-gpt-5p6`, `latest-model/gpt-4.1`, `latest-model/gpt-5`, `latest-model/gpt-5.1`, `latest-model/gpt-5.2`, `latest-model/gpt-5.3-codex`, `latest-model/gpt-5.4`, `latest-model/gpt-5.5`, `latest-model/gpt-5.6`, `latest-model/gpt-6-astra` ("Using GPT-6", also covering GPT-6.1 Sol and GPT-6.1 Terra), `latest-model/gpt-6.2-astra` ("Using GPT-6.2", GPT-6.2 Astra and Sol; the `latest-model` hub serves this page). Skipped by the rule: `live-prompting`, `voice-prompting`, `frontend-prompt`, `prompt-caching`, `prompt-generation`, `prompt-optimizer`.

## Seen, not registered

- `examples/gpt4-1_prompting_guide` — a superseded generation; nothing to distill.
- `prompting/migrate-from-prompt-object` — an API deprecation how-to (`v1/prompts` shuts down 2026-11-30); corroborates "keep prompts in code"; nothing to distill.
- `latest-model/gpt-4.1` through `latest-model/gpt-5.6` ("Using GPT-5.x") — superseded by Using GPT-6 and Using GPT-6.2 for current guidance; the 5.1 and 5.2 Cookbook guides cover those generations.
- `prompting` — a short landing page for the guides listed here.

## GPT-5 prompting guide (Cookbook)

The family-wide guide for the evergreen test, together with the API docs' Prompt engineering page.

- **Distilled:** literal instruction-following, with explicit defaults and stop conditions; a single persistence stance; sensitivity to contradictions; literal format specs; tool preambles as a cadence lever.
- **Excluded:** reasoning-effort values, Responses API context reuse, frontend stack recommendations, the Cursor case study, the appendix prompts.
- **Outline (H2 › H3 › H4):**
  - Agentic workflow predictability › Controlling agentic eagerness (H4: Prompting for less eagerness; Prompting for more eagerness); Tool preambles; Reasoning effort; Reusing reasoning context with the Responses API
  - Maximizing coding performance, from planning to execution › Frontend app development (H4: Zero-to-one app generation; Matching codebase design standards); Collaborative coding in production: Cursor's GPT-5 prompt tuning (H4: System prompt and parameter tuning)
  - Optimizing intelligence and instruction-following › Steering (H4: Verbosity); Instruction following; Minimal reasoning; Markdown formatting; Metaprompting
  - Appendix › SWE-Bench verified developer instructions; Agentic coding tool definitions (plain text, not a heading, in the `.md` variant); Taubench-Retail minimal reasoning instructions; Terminal-Bench prompt

## GPT-5.1 Prompting Guide (Cookbook)

- **Distilled:** persist end to end and treat ambiguous directives as permission to proceed (stance); tool descriptions carry explicit must and must-not usage rules; counted update cadences work in this family.
- **Excluded:** the none reasoning mode, the apply_patch and shell tool types, design-token enforcement, plan-tool mechanics, the metaprompting workflow.
- **Outline (H2):** Introduction; Migrating to GPT-5.1; Agentic steerability; Optimizing intelligence and instruction-following; Maximizing coding performance from planning to execution; New tool types in GPT-5.1; How to metaprompt effectively; What's next

## GPT-5.2 Prompting Guide (Cookbook)

- **Distilled:** explicit length targets; scope-drift prevention ("no extra features"); ambiguity handling (ask, or state the interpretation); updates clamped to outcome-based sentences.
- **Excluded:** compaction, the outline-first long-context technique (single page), structured extraction and Office workflows, the web-research prompt.
- **Outline (H2):** Introduction; Key behavioral differences; Prompting patterns; Compaction (Extending Effective Context); Agentic steerability & user updates; Tool-calling and parallelism; Structured extraction, PDF, and Office workflows; Prompt Migration Guide to GPT 5.2; Web search and research; Conclusion; Appendix

## Codex Prompting Guide (Cookbook)

- **Distilled:** the starter-prompt section structure (autonomy and persistence, implementation, editing constraints, exploration, presenting work); meta-commentary "announce the plan" instructions cause premature stopping; a final-answer style contract; personality is a choice, not a default.
- **Excluded:** tool schemas, compaction, the phase parameter, the new-features section, preamble cadence numbers.
- **Outline (H2 › H3):**
  - Getting Started › Recommended Starter Prompt
  - Prompting › Autonomy and Persistence; Code Implementation; Editing constraints; Exploration and reading files; Plan tool; Special user requests; Frontend tasks; Presenting your work and final message; Final answer structure and style guidelines; Mid-Rollout User Updates; Using agents.md
  - Compaction
  - Tools › Apply_patch; Shell_command; Update Plan; View_image; Dedicated terminal-wrapping tools; Other Custom Tools; Parallel Tool Calling; Tool Response Truncation
  - New features in GPT-5.3 Codex › Preamble messages; Phase (H4: Values; Where it appears; How it's used downstream); Preambles & Personality (H4: Personality (Friendly vs Pragmatic)); Troubleshooting & Metaprompting (H4: Metaprompting for targeted fixes; Some examples)

## Prompting guidance for GPT-5.6 Sol

The only archived copy predates registration, so this page's content is compared against its coverage note by reading it, and its outline against the snapshot.

- **Distilled:** simplify prompts first; outcome-first prompts and stopping conditions; autonomy and approval boundaries; tool routing (what, when, what not); check work before finishing; the suggested prompt structure (role, personality, goal, success criteria, constraints, tools, output, stop rules).
- **Excluded:** the verbosity parameter, programmatic tool calling, retrieval budgets, the reasoning-effort sweep, the migration workflow.
- **Outline (H2):** Simplify prompts first; Outcome-first prompts and stopping conditions; Personality, collaboration, and response length; Define autonomy and approval boundaries; Tool routing; Programmatic Tool Calling; Grounding, citations, and retrieval budgets; Long-running workflows and state; Reasoning effort; Frontend and visual tasks; Check work before finishing; Suggested prompt structure; Prompt migration workflow

## Using GPT-6

Covers GPT-6 Astra, GPT-6.1 Sol, GPT-6.1 Terra, GPT-6 Sol, and GPT-6 Luna, and says its prompts are a starting point across the GPT-6 family (behavior observed on Astra), so its claims count as family-level for GPT-6. Only a `.md` capture exists in the Web Archive.

- **Distilled:** bias to action with completion; user instructions take precedence over skill files (state the precedence); request the writing style explicitly (paragraphs versus lists); test scope for trivial reversible changes; delegation guidance for multi-agent harnesses.
- **Excluded:** the none reasoning effort on Sol and Luna, per-model `none` support, the migration quickstart, the model-behavior list, the model intro and API notes.
- **Outline (H2 › H3):**
  - What's new; Limitations
  - Prompting best practices › GPT-6 Astra behavior; Initiative and follow-through; Instruction following; Personality and writing style; Subagent delegation; Testing and verification
  - Migration quickstart › Migrate with Codex; Update API and model parameters

## Using GPT-6.2

Says its prompts are a starting point across the GPT-6.2 family (Astra and Sol).

- **Distilled:** the final answer stands alone for a reader who skipped the progress updates, with no working shorthand from reasoning, tool calls, or subagent instructions (with Claude Fable 5 and 5.2, `agentic.md` §Universal "A final report for a cold reader"); ending with a plan, a suggested next step, or a routine-decision request counts as stopping, and the only reasons to stop are a significant scope change, a concrete block, a decision only the user can make, or an irreversible action (`agentic.md` §GPT–Codex "One persistence stance"); stating reasonable reversible assumptions and continuing corroborates the runbook entry and GPT-5.2's ambiguity handling; skipping new tests unless asked, required, or needed for a specific regression corroborates Using GPT-6's test scope.
- **Excluded:** concise-by-default writing ("revisit 'be concise'"), the rest of the coding-style block (reuse, readability, indirection), frontend imagery and typography, reasoning items dropped on prefix edits (API), the async question tool, reasoning effort and parameter migration.
- **Outline (H2 › H3):**
  - What's new
  - Prompting best practices › GPT-6.2 Astra behavior; Writing style; Task completion; Coding style; Frontend design
  - Migration quickstart › Update API and model parameters

## Prompt engineering (API docs, family-wide)

The family-wide page for the evergreen test, together with the GPT-5 Cookbook guide.

- **Distilled:** the developer versus user role split (function definition versus arguments); headed sections for identity, instructions, examples, and context; reasoning models want high-level guidance where earlier GPT models wanted explicit steps; keep prompts in code with fixtures and tests (maintenance advice, Info level).
- **Excluded:** API parameter names, model-choice advice.
- **Outline (H2 › H3 › H4):**
  - Choosing a model; Prompt engineering; Message roles and instruction following; Version prompts in code; Message formatting with Markdown and XML (H4: Save on cost and latency with prompt caching); Few-shot learning; Include relevant context information (H4: Planning for the context window)
  - Prompting current models › Prompting best practices for the latest model (H4: Coding; Front-end engineering; Agentic tasks)
  - Prompting reasoning models; Next steps; Other resources

## Rethinking skills and prompts for GPT-6 Astra (developer blog)

Recorded as corroboration.

- **Distilled:** over-specified skills; conditional file references in agent-instruction files; over-restrictive decision boundaries halt work; persistence with completion criteria.
- **Excluded:** —
- **Outline (H2):** Better skills; Up-to-date AGENTS.md; Decision boundaries; Persistence
