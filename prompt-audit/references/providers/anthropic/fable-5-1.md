<!-- Built by scripts/build-model-files.py from prompt-audit/sources/anthropic-entries.md. Do not edit by hand: edit the source and rebuild. -->

# Fable 5.1: model guidance

Applies only to Fable 5.1. Read it with `providers/anthropic.md`; where an entry here disagrees with that file or with `general.md`, the entry here wins. Cite as `[ref: providers/anthropic/fable-5-1.md §<section>]`.

## Thinking-depth lines

- The model usually follows "answer directly without deliberating": the line works.

## Writing and output

- Under-formats rather than over-formats: anti-formatting rules written for earlier models push it further. Replace them with a rule for when lists and other formatting help.
- When summarizing documents, more likely to reproduce source passages without marking them as quotes. A summarizing prompt should include one complete example of a correct response (request, response, and why it's correct).
- Tends to rewrite whole files for small edits. If that matters, add a line saying to edit files surgically when it won't change the result.

## Search and tool use

- At `low` effort it searches less and answers from memory more. A prompt nudge helps: a name it doesn't confidently recognize, or one from a fast-moving field, is the thing to verify, so search it as the user wrote it.

## Chatbots and safeguards

- Safeguard false positives are likelier with compile-check phrasing ("Does this program compile without errors?" — ask "Are there any bugs in this program?") and with lesser-known programming languages (give context on the language).
