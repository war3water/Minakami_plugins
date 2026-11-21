# DeepSeek — source detail

Read by `check-sources` when it compares DeepSeek's pages. Each page section states what is distilled now, at which scope, and what is excluded; it is rewritten, never appended to, when the page changes (see "Keeping the registry bounded" in `SOURCES.md`). "All models" means `references/providers/deepseek.md`.

## Known matches at last discovery (2026-11-21)

From the sitemap: `guides/json_mode`, `guides/thinking_mode`, `guides/function_calling`, `guides/multi_round_chat`, `guides/chat_prefix_completion`, `guides/fim_completion`, `guides/vision`, `guides/latest_reminder`, `quick_start/pricing`, `updates`.

## Seen, not registered

- The other `guides/*` pages (thinking mode, tool calls, multi-round chat, prefix completion, FIM, vision, file parsing, web tools, the user metadata marker): API parameters and message structure only; no prompt text.
- Hugging Face cards `deepseek-ai/DeepSeek-V4.1-Flash-1017` and `DeepSeek-V4-Pro-0813`: sampling, context window, and chat-template tooling only.
- DeepSeek publishes no prompting guide; the old `/prompt-library/` path returns the site's fallback page.

## JSON Output

- **Distilled (all models):** in JSON output mode, include the word "json" and an example of the desired JSON in the prompt; a blank reply can be fixed by changing the prompt (§JSON output). With Moonshot and Qwen, the basis of `general.md` "JSON output mode states the shape".
- **Excluded:** the `response_format` parameter, `max_tokens` advice, retry handling in code.
- **Outline (H1 › H2):** JSON Output › Notice; Sample Code
