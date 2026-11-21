# Meta (Muse, Llama): model entries (source)

The one place each model-specific entry is written. Audits never read this file. `scripts/build-model-files.py` copies every entry into the built file of each model its *Applies to* names (one file per model name, named by the rule in the script), under `references/providers/meta/`, and its check fails when a built file is out of date. Edit here, then rebuild; never edit a built file.

An entry starts with `- *Applies to:* <model>, <model>.` using names from the table below, and says everything it needs on its own: a built file shows it without the other models' entries. Conditions such as an effort level go in the entry text, not in the *Applies to* list.

## Models

| Model | Also covers |
|---|---|
| Muse Spark 1.3 | Muse Spark 1.2, Muse Spark 1.1 |
| Muse Wonder | — |
| Muse Spark Open | — |
| Muse Glimmer | — |
| Llama 4 Maverick | Llama 4 Scout |

## System prompt structure

- *Applies to:* Muse Spark Open. "Muse Spark Open pays more attention to the beginning of the system prompt, so put the rules that must always hold first." Meta's guide gives a structure: a specific role, then objective, priority rules, a scope check, a decision procedure, tools, output, and completion, with an explicit "unknown" answer when evidence is missing. Rules that must always hold but sit at the end of the prompt are a D6 finding.
- *Applies to:* Muse Glimmer. Be specific about the task ("You are a Python code reviewer" outperforms "You are a helpful assistant") and state output format, length and tone up front. Avoid instructions about how the model works internally.
- *Applies to:* Llama 4 Maverick, Llama 4 Scout. The Llama 4 model card says a system prompt is effective at "reducing false refusals and templated or "preachy" language patterns", and its suggested prompt bans phrases such as "it's important to", "it's crucial to" and "it's worth noting". A user-facing Llama 4 prompt with no such guidance can add it (Info).

## Tools and reasoning

- *Applies to:* Muse Spark Open. "You don't need to describe your tools in the system prompt": the chat template adds the definitions passed in `tools`. A line `Reasoning strength: <number>.` in the system prompt sets reasoning strength for every request and overrides the API setting; flag it when it contradicts the effort the user says they run.
- *Applies to:* Muse Glimmer. A reasoning model: its private chain of thought is built into the format, so prompts asking it to think step by step are unnecessary (D2).
- *Applies to:* Muse Spark Open. The model reads media in the order sent, so each image, video or audio part goes next to the text that refers to it.

## Images and computer use

- *Applies to:* Muse Spark 1.3, Muse Spark 1.2, Muse Spark 1.1. For locating objects in images, ask for one specific output shape and list the objects to find; state the coordinate fields and axis order and ask for JSON; to count, ask the model to point at every instance and then return the total. Put the grounding instruction in the user message next to the image and keep the system prompt minimal.
- *Applies to:* Muse Wonder. In a computer-use agent, the system prompt is "where you lock in the rules for batching, waiting, finishing, and declaring a task infeasible". Meta's example forbids batching actions across page loads and claiming completion unless the screenshot supports it. A computer-use prompt without those rules is a D8 gap.
