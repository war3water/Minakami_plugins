<!-- Built by scripts/build-model-files.py from prompt-audit/sources/moonshot-entries.md. Do not edit by hand: edit the source and rebuild. -->

# Kimi K3.1 Pro: model guidance

Applies only to Kimi K3.1 Pro. Read it with `providers/moonshot.md`; where an entry here disagrees with that file or with `general.md`, the entry here wins. Cite as `[ref: providers/moonshot/kimi-k3-1-pro.md §<section>]`.

## Tools and the system prompt

- When the harness loads tools on demand through a search tool, Moonshot's tool-calling guide says to name, in the system prompt, the domains the model can search ("advertise the domain tags the model can search … so it knows to call `search_tools` first when it needs a tool"). A system prompt for such a harness that never says what can be found is a D7 gap. Its agent guide keeps the system prompt to "the role, workflow, and quality boundaries" and leaves argument details to the tool schema.
