# OpenAI (GPT, Codex): model entries (source)

The one place each model-specific entry is written. Audits never read this file. `scripts/build-model-files.py` copies every entry into the built file of each model its *Applies to* names (one file per model name, named by the rule in the script), under `references/providers/openai/`, and its check fails when a built file is out of date. Edit here, then rebuild; never edit a built file.

An entry starts with `- *Applies to:* <model>, <model>.` using names from the table below, and says everything it needs on its own: a built file shows it without the other models' entries. Conditions such as an effort level go in the entry text, not in the *Applies to* list.

## Models

| Model | Also covers |
|---|---|
| GPT-6 Astra | GPT-6 Sol, GPT-6 Luna, GPT-6.1 Sol, GPT-6.1 Terra |
| GPT-6.2 Astra | GPT-6.2 Sol |

## Writing style

- *Applies to:* GPT-6 Astra, GPT-6 Sol, GPT-6 Luna, GPT-6.1 Sol, GPT-6.1 Terra. Tends toward detailed, formatted answers (lists, tables, Markdown) and recurring stock phrases. A product that needs prose, or a particular structure, must say so; a missing style spec is a D6 gap when the output is read by people.
- *Applies to:* GPT-6.2 Astra, GPT-6.2 Sol. More concise and direct by default than earlier models. Revisit "be concise" lines written for earlier models: they push an already short default further. Ask instead for the reader's context to be kept (terminology, background an outside audience needs).

## Subagent delegation

- *Applies to:* GPT-6 Astra, GPT-6 Sol, GPT-6 Luna, GPT-6.1 Sol, GPT-6.1 Terra. May delegate less often than a multi-agent harness wants, and responds well to being told when and how much to use subagents for parallel work. A multi-agent prompt with no delegation guidance is a D1 gap for these models.

## Frontend design

- *Applies to:* GPT-6.2 Astra, GPT-6.2 Sol. When the interface needs a particular look, specify the imagery and typography (a typeface, when it matters), and keep interface copy to what people need to know or do.
