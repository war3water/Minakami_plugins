# Moonshot (Kimi): model entries (source)

The one place each model-specific entry is written. Audits never read this file. `scripts/build-model-files.py` copies every entry into the built file of each model its *Applies to* names (one file per model name, named by the rule in the script), under `references/providers/moonshot/`, and its check fails when a built file is out of date. Edit here, then rebuild; never edit a built file.

An entry starts with `- *Applies to:* <model>, <model>.` using names from the table below, and says everything it needs on its own: a built file shows it without the other models' entries. Conditions such as an effort level go in the entry text, not in the *Applies to* list.

## Models

| Model | Also covers |
|---|---|
| Kimi K3 | Kimi K3.1 Pro, Kimi K3.1 Pro high-speed |

## Tools and the system prompt

- *Applies to:* Kimi K3, Kimi K3.1 Pro, Kimi K3.1 Pro high-speed. When the harness loads tools on demand through a search tool, Moonshot's tool-calling guide says to name, in the system prompt, the domains the model can search ("advertise the domain tags the model can search … so it knows to call `search_tools` first when it needs a tool"). A system prompt for such a harness that never says what can be found is a D7 gap. Its agent guide keeps the system prompt to "the role, workflow, and quality boundaries" and leaves argument details to the tool schema.
