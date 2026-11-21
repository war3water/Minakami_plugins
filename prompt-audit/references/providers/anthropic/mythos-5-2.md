<!-- Built by scripts/build-model-files.py from prompt-audit/sources/anthropic-entries.md. Do not edit by hand: edit the source and rebuild. -->

# Mythos 5.2: model guidance

Applies only to Mythos 5.2. Read it with `providers/anthropic.md`; where an entry here disagrees with that file or with `general.md`, the entry here wins. Cite as `[ref: providers/anthropic/mythos-5-2.md §<section>]`.

## Subagent delegation

- Leave the subagent tool's description alone unless the model starts more subagents than the task needs. If it does, look first for standing "delegate" lines in the system prompt, skills, and agent files, and make the tool description say what a subagent costs and when delegation is worth it.

## Chat prompts: earlier answers

- Chat-prompt lines telling the model to treat an earlier answer as done and focus on the new message make it far less likely to point out mistakes in its earlier answers. Flag them where the product needs the model to keep re-examining its answers; elsewhere, say to test that it still corrects itself.

## Code ownership

- The model pays close attention to who owns the code. Told the code base is its own ("You are the owner and long-term maintainer of this codebase …"), it consolidates duplicated code and makes related changes nobody asked for, at much higher output cost; told nothing, it adds to the existing structure. A scope-limiting rule ("no drive-by refactors") does not cancel the ownership sentence. Flag the pair as a D5 collision when both appear; suggest the sentence only when the user wants structural improvement.

## Writing and output

- Follows writing style rules closely, so a hard limit ("one instruction per sentence, 20 words or fewer") makes prose choppy. Flag hard numeric style limits; prefer a description of the reader and the style.
- A token budget written into the prompt changes how much the model spends; a large one raised cost with no gain in Anthropic's tests. Suggest removing it and testing.
