# Agentic prompts — guidance for tool-using agents

Read this file when the prompt under audit drives a tool-using agent: system prompts or agent instructions with tools, runbooks, long-running or unattended runs. Cite as `[ref: agentic.md §<section>]`.

## Universal

- **Completion criteria and evidence-backed status.** State what done means — which checks must pass, which artifacts must exist — and require progress claims to point at tool results from the session. Without a stated completion condition the model picks its own stopping point; without the evidence rule, status reports drift from what was verified. When done means a test passes — whether the prompt says so or only the user's success criteria do — the prompt must say whether the test itself may be changed: otherwise the cheapest green run is editing, skipping, or weakening the test.
- **Autonomy boundaries.** Say which actions the model may take freely (local, reversible) and which need confirmation (destructive, hard to reverse, visible to others, scope expansions). Without the boundary the model over-asks and stalls, or takes unrequested actions; blanket caution language produces the stall.
- **The prompt under audit as a runbook.** Say what the agent does with an unclear request — ask, or proceed under a stated assumption — and with instructions that arrive inside tool results or data (inert unless the harness says otherwise).

## Claude family

- For long-running work, give the model a place to keep state — a checklist or notes file it updates — and say what must survive when context is summarized. An unattended run that ends a turn with open items resumes more reliably from a checklist than from prose.

## GPT–Codex family

- **One persistence stance.** Agentic prompts must pick exactly one — "keep going until resolved" or "stop and ask when uncertain" — and state it; both or neither produces erratic stopping. Over-restrictive approval or safety language makes current models stop early and ask; the cure is autonomy boundaries, not more caution. Left unspecified, the newest models lean toward asking.
- **Tool routing.** Tool descriptions carry the routing: say what each tool is for, when to use it, and when not to, and expose only task-relevant tools. A tool list without usage rules is routed unpredictably.
- **Update cadence.** Progress updates respond to an explicit cadence (a brief preamble before the first tool call, then sparse outcome-based updates at phase changes); counted cadences work in this family. Unstated, the model narrates routine steps or falls silent.
- **Instruction precedence.** When a prompt loads skills or agent-instruction files, say which wins on conflict — the vendor's guidance is that the user's instructions take precedence — or the model pauses on the contradiction.
- **Per-run reading cost.** Blanket "read all the docs before starting" rules in agent-instruction files are paid on every run; make file references conditional on the task that needs them.

## Gemini family

- An agentic system instruction separates three things: the reasoning strategy (how deeply to analyze and plan before acting), execution rules (when to adapt the plan, how persistently to retry, which actions count as risky), and interaction rules (when to ask versus assume, how verbose to be while working).
