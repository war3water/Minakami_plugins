# Reference source registry

Read by the `/prompt-audit:check-sources` command (`check-sources` skill in Codex). It records where each family's official prompting guidance is **discovered**, meaning the vendor's machine-readable page index plus its hub page, so a newly published model page is found by listing rather than by memory. It also records which pages have been **distilled** into `references/`. Audits never read these files.

The registry has three parts, so a check loads only what it compares:

- **This file:** the lifecycle, the evergreen test, how the registry stays bounded, the discovery indexes, and one line per registered page.
- **`sources/<family>-family.md`** (`claude-family.md`, `gpt-codex-family.md`, `gemini-family.md`; the suffix keeps them clear of the `CLAUDE.md` and `GEMINI.md` instruction files the runtimes auto-load): the family's known matches at the last discovery, the pages seen but not registered, and for each registered page its coverage note (what is distilled into which reference file, what is excluded) and outline snapshot. Open a family file when that family is being compared.
- **`sources/history/<date>.md`:** one file per check, holding that check's freshness report and anything the following release moved out of the registry. Read it only to trace why something changed. Checks before 2026-11-17 are recorded in the git history of this file.

## Lifecycle of a source

1. **Found.** `check-sources` lists a family's index and hub page, applies the match rule, and reports any page missing from the family's known matches. Its report ends with a registry patch, which it offers to apply.
2. **Registered.** Once the patch is applied, the page has a row below with status `found`, and its family file lists it among the known matches and gives it a section with the first candidate claims. Nothing in `references/` changes yet.
3. **Distilled.** A reference-refresh release reads the page and distills the durable family-level claims into `references/`. It rewrites the page's coverage note and outline in the family file, sets status `distilled` and the last-reviewed date, and runs the eval sweep.
4. **Moved or retired.** When a page redirects or returns 404, the next check reports it. The release that follows either corrects the URL, or moves the page's row and section into that check's history file, so distilled claims stay traceable.

A page whose guidance is all version-specific, or which a later page supersedes, is not registered. Its family file lists it under "Seen, not registered" with the reason, so the next check does not raise it again.

## Keeping the registry bounded

The registry describes the current state. Its size follows the number of guide pages the vendors currently list, not the number of checks that have run.

- **Rewrite, don't append.** When a page changes, its coverage note is rewritten to say what is distilled and excluded now. What changed, and on which day, goes into that check's history file. Test: a sentence in this file or a family file that starts with a date, or contrasts "before" with "now", belongs in the history file.
- **Pages that leave, leave.** When a vendor stops listing a page, or a later page supersedes it and no distilled claim rests on it alone, the next refresh release moves its row and section into the history file.
- **One history file per check.** Each check adds exactly one file under `sources/history/`; nothing else grows with time.

## Evergreen test — what gets distilled

The reference files carry family-level, durable guidance only. A claim qualifies when the family-wide page states it, or when it holds across the family's currently listed model pages. If two current model pages of the same family point in opposite directions (one model spawns subagents readily, its sibling spawns few), the claim is version-specific: exclude it, and name it in the page's coverage note so it is not re-evaluated every run.

## Discovery indexes

One row per index. `check-sources` fetches the index, applies the match rule, and diffs the result against the family's known matches. It reads the hub page in the same run, not only as a fallback, because a launch-day model page can appear in the hub before the index lists it. If the index cannot be fetched, the hub page is the first fallback and a web search naming the vendor's docs domain the second, and the report says which was used. A failed fetch never becomes "no new pages".

| Family | Index (machine-readable) | Match rule | Hub page (read every run) | Markdown variant of any page |
|---|---|---|---|---|
| claude | <https://platform.claude.com/llms.txt> — llms.txt listing every docs page with title and URL, no dates; lags new pages on launch day | path contains `/prompt-engineering/` | the "Model-specific guidance" table on the prompting best practices page — one row per current per-model guide | append `.md` to the page URL |
| gpt-codex (Cookbook) | <https://raw.githubusercontent.com/openai/openai-cookbook/main/registry.yaml> — YAML, one entry per Cookbook article with `title`, `path`, `date`, `tags`, and optional `archived` / `redirects` | title contains "prompting guide"; skip image, video, audio, realtime, and ChatGPT-product guides — not coding models | <https://developers.openai.com/cookbook/llms.txt> (a partial listing), then the Cookbook site search | page URL is `https://developers.openai.com/cookbook/` + `path` without its extension; append `.md` for markdown |
| gpt-codex (API docs) | <https://developers.openai.com/api/docs/llms.txt> — llms.txt of the API guides, entries end in `.md`, no dates; the per-model "Using GPT-x" guides and prompt-guidance pages live here, not in the Cookbook | path contains `guides/latest-model/`, `guides/prompt-guidance`, `guides/prompt-engineering`, or `guides/prompting`; skip live, voice, realtime, and frontend prompt pages and the caching, generation, and optimizer tool pages | <https://developers.openai.com/api/docs/guides/latest-model> — model selector listing the current generation | append `.md` to the page URL |
| gemini | <https://aistudio.google.com/llms.txt> — llms.txt for the Gemini API docs; entries already end in `.md`, no dates | title contains "prompt", or names a model generation with "developer guide"; skip media prompt guides (image, video, music, speech), release-note "what's new" pages, and the "Latest Gemini models" overview | the "Topic-specific prompt guides" section of the prompt design strategies page, plus <https://aistudio.google.com/docs/models> | append `.md` to the page URL |

### Fetch notes

- **Indexes that look right but aren't.** `https://ai.google.dev/llms.txt` returns 404, and `ai.google.dev/sitemap.xml` is too large for a fetch tool. The Gemini docs live under `aistudio.google.com/docs/…`, and old `ai.google.dev/gemini-api/docs/…` URLs 301-redirect there. `cookbook.openai.com` URLs 308-redirect to `developers.openai.com/cookbook/`. `https://developers.openai.com/api/llms.txt` is only a routing page to the API docs index above.
- **Dates.** The OpenAI Cookbook registry is the only index with publication dates, so "published after last review" is exact there and "first seen this run" everywhere else.
- **Outlines.** Take heading lines verbatim with their hash marks: download the markdown variant and list its heading lines outside code fences, or ask the fetch tool to quote them. Summarized heading lists fold levels and produce false "changed" signals. Formatting that differs between a page's HTML and its markdown variant (a heading exported as plain text) is not a change.
- **Content.** The Web Archive (`web.archive.org/cdx/search/cdx?url=<page>`) usually holds a copy near each page's last-reviewed date. Raw copies (`web.archive.org/web/<timestamp>id_/<page>`) come back compressed, so fetch them with `curl --compressed`. Diff the capture nearest the last review against the newest capture, or against the live page when there is none, sentence by sentence: that separates real guidance changes from link and wording edits. Archived `aistudio.google.com` pages are an empty JavaScript shell, so the Gemini strategies page is compared by outline only.

## Registered pages

Coverage notes and outlines are in the family file named in the last column.

| Family | Page | URL | Status | Last reviewed | Detail |
|---|---|---|---|---|---|
| claude | Claude prompting best practices | <https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices> | distilled | 2026-11-17 | `sources/claude-family.md` |
| claude | Prompting Claude Opus 5 | <https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5> | distilled | 2026-11-17 | `sources/claude-family.md` |
| claude | Prompting Claude Fable 5.1 | <https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1> | distilled | 2026-11-17 | `sources/claude-family.md` |
| claude | Prompting Claude Fable 5 | <https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5> | distilled | 2026-11-17 | `sources/claude-family.md` |
| claude | Prompting Claude Sonnet 5 | <https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5> | distilled | 2026-11-17 | `sources/claude-family.md` |
| claude | Prompting Claude Opus 4.8 | <https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-4-8> | distilled | 2026-11-17 | `sources/claude-family.md` |
| claude | Prompting Claude Opus 5.5 | <https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5> | distilled | 2026-11-17 | `sources/claude-family.md` |
| claude | Prompting Claude Fable 5.2 | <https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2> | distilled | 2026-11-17 | `sources/claude-family.md` |
| claude | Prompting Claude Sonnet 5.5 | <https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5-5> | distilled | 2026-11-17 | `sources/claude-family.md` |
| claude | Prompting Claude Haiku 5.5 | <https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-haiku-5-5> | distilled | 2026-11-17 | `sources/claude-family.md` |
| gpt-codex | GPT-5 prompting guide (Cookbook) | <https://developers.openai.com/cookbook/examples/gpt-5/gpt-5_prompting_guide> | distilled | 2026-11-17 | `sources/gpt-codex-family.md` |
| gpt-codex | GPT-5.1 Prompting Guide (Cookbook) | <https://developers.openai.com/cookbook/examples/gpt-5/gpt-5-1_prompting_guide> | distilled | 2026-11-17 | `sources/gpt-codex-family.md` |
| gpt-codex | GPT-5.2 Prompting Guide (Cookbook) | <https://developers.openai.com/cookbook/examples/gpt-5/gpt-5-2_prompting_guide> | distilled | 2026-11-17 | `sources/gpt-codex-family.md` |
| gpt-codex | Codex Prompting Guide (Cookbook) | <https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide> | distilled | 2026-11-17 | `sources/gpt-codex-family.md` |
| gpt-codex | Prompting guidance for GPT-5.6 Sol | <https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6> | distilled | 2026-11-10 | `sources/gpt-codex-family.md` |
| gpt-codex | Using GPT-6 | <https://developers.openai.com/api/docs/guides/latest-model/gpt-6-astra> | distilled | 2026-11-17 | `sources/gpt-codex-family.md` |
| gpt-codex | Using GPT-6.2 | <https://developers.openai.com/api/docs/guides/latest-model/gpt-6.2-astra> | distilled | 2026-11-17 | `sources/gpt-codex-family.md` |
| gpt-codex | Prompt engineering (API docs, family-wide) | <https://developers.openai.com/api/docs/guides/prompt-engineering> | distilled | 2026-11-17 | `sources/gpt-codex-family.md` |
| gpt-codex | Rethinking skills and prompts for GPT-6 Astra (developer blog) | <https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra> | distilled | 2026-11-17 | `sources/gpt-codex-family.md` |
| gemini | Gemini prompt design strategies | <https://aistudio.google.com/docs/prompting-strategies> | distilled | 2026-11-10 | `sources/gemini-family.md` |
