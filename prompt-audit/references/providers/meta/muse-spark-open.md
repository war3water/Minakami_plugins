<!-- Built by scripts/build-model-files.py from prompt-audit/sources/meta-entries.md. Do not edit by hand: edit the source and rebuild. -->

# Muse Spark Open: model guidance

Applies only to Muse Spark Open. Read it with `providers/meta.md`; where an entry here disagrees with that file or with `general.md`, the entry here wins. Cite as `[ref: providers/meta/muse-spark-open.md §<section>]`.

## System prompt structure

- "Muse Spark Open pays more attention to the beginning of the system prompt, so put the rules that must always hold first." Meta's guide gives a structure: a specific role, then objective, priority rules, a scope check, a decision procedure, tools, output, and completion, with an explicit "unknown" answer when evidence is missing. Rules that must always hold but sit at the end of the prompt are a D6 finding.

## Tools and reasoning

- "You don't need to describe your tools in the system prompt": the chat template adds the definitions passed in `tools`. A line `Reasoning strength: <number>.` in the system prompt sets reasoning strength for every request and overrides the API setting; flag it when it contradicts the effort the user says they run.
- The model reads media in the order sent, so each image, video or audio part goes next to the text that refers to it.
