# Moonshot — source detail

Read by `check-sources` when it compares Moonshot's pages. Each page section states what is distilled now, at which scope, and what is excluded; it is rewritten, never appended to, when the page changes (see "Keeping the registry bounded" in `SOURCES.md`). "All models" means `references/providers/moonshot.md`; "scoped" means an entry in `sources/moonshot-entries.md`, named by its section.

## Known matches at last discovery (2026-11-21)

Under `https://platform.kimi.ai/docs/guide/`: `prompt-best-practice`, `use-json-mode-feature-of-kimi-api`, `response_format`, `use-kimi-k3-to-setup-agent`, `kimi-k3-tool-calling-best-practice`, `tool-call-repeat`, `use-partial-mode-feature-of-kimi-api`, `use-kimi-api-for-file-based-qa`, `use-thinking-models`; plus `/docs/models.md`.

## Seen, not registered

- `tool-call-repeat`: client-side repeated-call detection with a reminder appended by the harness; harness behavior.
- `use-thinking-models`: reasoning effort and passing back `reasoning_content`; API settings.

## Best Practices for Prompts

- **Distilled (all models):** length as paragraph or bullet counts rather than word counts; classify the query and give only that category's instructions; reference-text answers with a "not found" fallback; file content in the prompt, not a file id (§Instructions and output length). The rest (clear instructions, details, a role, delimiters, steps, examples, reference text, breaking down tasks) corroborates `general.md`.
- **Excluded:** the link to a Kimi chat share on system prompts (not a docs page).
- **Outline (H1 › H2 › H3):** Best Practices for Prompts › Write Clear Instructions (Including More Details…; Requesting the Model to Assume a Role…; Using Delimiters…; Clearly Define the Steps…; Provide Examples of Desired Output…; Specify the Desired Length…) › Provide Reference Text (Guide the Model to Use Reference Text…) › Break Down Complex Tasks (Categorize to Identify Instructions…; For Long-Running Dialog Applications…; Chunk and Recursively Build a Complete Summary…)

## Use Kimi API's JSON Mode; Use response_format to control model output format

- **Distilled (all models):** define field names and types with a concrete example and field meanings; JSON Mode returns objects only, so don't ask for an array; with a schema, still describe the task and data, and don't contradict the schema (§JSON output).
- **Excluded:** `response_format` and `strict` parameters, truncation handling.
- **Outline:** JSON Mode › Enable JSON Mode with response_format; Full example…; Troubleshoot truncated JSON output; Notes. response_format › basic structure; Advantages of Structured Output; Quick start; Parameter description; `strict` mode; Nested objects and arrays example; Comparison with JSON Mode; Notes; Common errors

## Build an Agent with Kimi K3; Kimi K3 API Tool Calling Best Practices

- **Distilled (scoped, Kimi K3 series):** §Tools and the system prompt (name the searchable tool domains; keep the system prompt to role, workflow, and quality boundaries). Keeping tool behavior out of the system prompt is, with Meta's Muse Spark Open guide, the basis of `agentic.md` "Tool definitions live in the tool schema".
- **Excluded:** `tool_choice`, on-demand tool injection, reasoning effort.
- **Outline:** Build an Agent › Break Down the Task; Design Tools; Design the Prompt; Configure the K3 API; Complete Agent Loop; Run and Troubleshoot; Custom Tools and Optimization. Tool Calling › Declare a search tool, not all your tools; Use tool_choice to force first-turn retrieval; Inject tool definitions on demand; Pick the reasoning effort for the task; The complete flow; Related reading

## Use Kimi API's Partial Mode; Use Kimi API for File-Based Q&A

- **Distilled (all models):** character description and situational guidance in role-play prompts (§Role-play and long conversations); file content, not a file id, in the prompt (§Instructions and output length).
- **Excluded:** `partial` mode, re-sending the system prompt (harness), one system message per file (message structure).
- **Outline:** Partial Mode › Make the model continue from a given prefix; Complete output truncated by max_tokens; Fix the character identity with the `name` field; Maintain character consistency in long conversations. File-Based Q&A › Q&A on Multiple Files; Best Practices for File Management
