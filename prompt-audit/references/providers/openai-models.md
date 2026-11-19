# OpenAI (GPT, Codex) — model-scoped guidance

Read this file only when the user named a specific model and it appears in the Models table of `providers/openai.md`. Each entry starts with *Applies to*; use an entry only when it names the target model. Where an entry here disagrees with `providers/openai.md` or `general.md`, this entry wins for the models it names. Cite as `[ref: providers/openai-models.md §<section> · <model>]`.

## Writing style

The two current generation pages point in opposite directions, so a style line can be right for one and wrong for the other.

- *Applies to:* GPT-6 Astra, GPT-6 Sol, GPT-6 Luna, GPT-6.1 Sol, GPT-6.1 Terra. Tends toward detailed, formatted answers (lists, tables, Markdown) and recurring stock phrases. A product that needs prose, or a particular structure, must say so; a missing style spec is a D6 gap when the output is read by people.
- *Applies to:* GPT-6.2 Astra, GPT-6.2 Sol. More concise and direct by default than earlier models. Revisit "be concise" lines written for earlier models: they push an already short default further. Ask instead for the reader's context to be kept (terminology, background an outside audience needs).

## Subagent delegation

- *Applies to:* GPT-6 Astra, GPT-6 Sol, GPT-6 Luna, GPT-6.1 Sol, GPT-6.1 Terra. May delegate less often than a multi-agent harness wants, and responds well to being told when and how much to use subagents for parallel work. A multi-agent prompt with no delegation guidance is a D1 gap for these models.

## Frontend design

- *Applies to:* GPT-6.2 Astra, GPT-6.2 Sol. When the interface needs a particular look, specify the imagery and typography (a typeface, when it matters), and keep interface copy to what people need to know or do.
