# Reference source registry

Read by the `/prompt-audit:check-sources` command (`check-sources` skill in Codex). Each row records where a reference file's guidance comes from and what has already been distilled; every reference-refresh release updates the matching rows (last-reviewed date and coverage notes) in the same commit.

| Family | Source | URL | Last reviewed | Coverage notes — topics already distilled |
|---|---|---|---|---|
| claude | Anthropic — Claude prompting best practices | <https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices> | 2026-08-01 | structure and tags; rule priority for collisions; motivation improves adherence; describe tools over scripting call order |
| claude | Anthropic — Prompting Claude Opus 5 | <https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5> | 2026-08-01 | instructed re-verification no-op; scope-expansion bounds; explicit length contract; narration cadence via positive examples |
| gpt-codex | OpenAI — GPT-5 prompting guide, plus successor guides in the Cookbook | <https://cookbook.openai.com/examples/gpt-5/gpt-5_prompting_guide> | 2026-08-01 | literal instruction-following and explicit defaults/stop conditions; single persistence stance; contradiction sensitivity; literal format specs |
| gemini | Google — Gemini prompt design strategies | <https://ai.google.dev/gemini-api/docs/prompting-strategies> | 2026-08-01 | concise directives; end-of-context constraint repetition; explicit output schema; few-shot examples lever |
