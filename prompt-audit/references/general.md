# General reference — universal failure modes

Family-independent guidance, cited as `[general]`. The runbook defines what a finding is; this file supplies the patterns and the severity calibration.

## Severity calibration

| Severity | Calibration examples |
|---|---|
| Critical | Two rules directly contradict on the main task path; the goal or output contract is absent and the output is machine-consumed; the prompt presupposes a file or tool that does not exist in the stated usage context |
| Major | The same rule appears three times in different wordings; a persistent prompt spends a large block on guidance the model follows unprompted; no stop condition on an open-ended agentic task |
| Minor | Filler phrases; one redundant courtesy sentence; emphasis on a low-stakes rule; a single stale example |
| Info | An available improvement that is not a defect — an escape hatch to add, a language trade-off to discuss, a restructure that would help future maintenance |

## Universal anti-patterns

- **Contradictory rules.** The model resolves the conflict unpredictably, and different runs resolve it differently; the runbook's D5 test decides whether a conflict is real.
- **Duplicate rules.** Restating a rule in new words reads as two rules, and over edits the copies drift apart and start to conflict.
- **Vague success criteria.** "Make it good", "be thorough" — the model optimizes for its own reading of good, which may not be the user's.
- **Negation-heavy rule lists.** Long chains of "don't X, never Y" leave the desired behavior unstated; say what to do instead.
- **Emphasis dilution.** When everything is bold, capitalized, or marked IMPORTANT, nothing is.
- **Examples that contradict instructions.** The model tends to follow the example over the stated rule.
- **Unbounded asks.** "Be comprehensive", "cover everything" with no stop condition or budget invites overlong, rambling output.
- **Presupposed context.** Files, tools, variables, or prior decisions the stated usage context doesn't provide send the model chasing phantoms — a direct hallucination trigger.
- **Undelimited or spoofable untrusted content.** External text (file contents, web results, user data) mixed with instructions is an injection surface. Delimiting it is not enough on its own: substituted content can imitate the closing delimiter or insert new-looking rules, so the prompt must declare the region inert — data, never instructions — and say that only the outermost harness-inserted delimiters count.
- **Micromanaged step order.** Scripting every micro-step where judgment would do better limits the model and breaks when the situation deviates from the script.
- **Stale workarounds.** Instructions that compensate for weaknesses of earlier models cost tokens and can fight the current model's better defaults. Prompts written for earlier models tend to be too prescriptive for current ones; when one underperforms, the first move is to simplify — remove repeated rules, redundant examples, and legacy scaffolding — before adding anything.

## Universal good patterns

- **Goal first.** The goal and the definition of done before the constraints.
- **Explicit output contract.** Format, length, and audience, stated once, precisely.
- **Positive phrasing.** Describe the desired behavior; keep prohibitions for real hard limits.
- **Stated rule priority.** Where rules can collide, say which wins.
- **Escape hatch.** "If the input is unclear or a constraint can't be met, say so and ask" — cheap insurance against confident wrong output.
- **Delimited data.** Fences, tags, or labeled sections: instructions outside, material inside.
- **One canonical example.** A single worked example that agrees with the rules beats several near-duplicates.
- **Explicit length contract.** Models don't reliably infer length preferences; an unstated one yields the model's own calibration, usually longer than wanted.
- **Explicit scope statement.** Current models expand scope on their own judgment — nearby fixes, extra tests, unrequested abstractions. Say what is in and out: deliver what was asked, at the scope intended, and report adjacent findings rather than acting on them. Applies where the model changes code or other artifacts; a prompt whose output is fully specified already bounds its scope.

## Known no-op patterns

These restate what current coding models do unprompted: they cost tokens without changing behavior, and some narrow it. Aspirations with no lever ("do not hallucinate", "be accurate"); reasoning boilerplate ("think step by step", "think carefully before answering", "reason at length first", "outline your reasoning first" — reasoning depth is a runtime setting, and the family files record the one exception); generic expert personas with no real constraint attached; threats, bribes, and emotional appeals; repeated courtesy; and restated baseline competence ("write clean code", "follow best practices") with no project-specific content. A streamlining claim outside this list can still be made, tagged `[hypothesis]`.

Not a no-op, for contrast: a rule tied to a concrete action — "read the file before describing it", "solve the general case, don't hard-code to the test inputs", "report incorrect tests instead of working around them", "report adjacent bugs instead of fixing them" — changes behavior and stays. The no-op is the bare aspiration; the lever is the action.

## Language

English is usually the most precisely interpreted language for technical instructions; team readability, domain terms that resist translation, and the language of the inputs and outputs the model handles can favor the original. The trade-off is situational — present it for the user to decide.

## Token-efficiency heuristics

All countable from the text, so they support approximate, honest claims: duplicated or near-duplicated blocks and rules; examples that dwarf the rules they illustrate, or several examples making one point; boilerplate before the first actionable instruction; and, the other way round, a prompt so sparse that the model must ask or guess, spending the saved tokens on round trips or rework.
