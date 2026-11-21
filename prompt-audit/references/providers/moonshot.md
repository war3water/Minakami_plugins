# Moonshot (Kimi) — prompt guidance

Cite as `[ref: providers/moonshot.md §<section>]`. Universal patterns are in `general.md`; universal guidance for tool-using agents is in `agentic.md`.

**How to read this file.** Moonshot's prompt guide is written for all Kimi models. The sections under "All Kimi models" apply to each of them. When the user named a model in the table below, also read its model file and apply it.

## Models

Status is the vendor's, checked on 2026-11-21; "newest" marks the newest model of its series.

| Model | Id | Series | Model file | Status |
|---|---|---|---|---|
| Kimi K3.1 Pro | `kimi-k3.1-pro` | K3 | `providers/moonshot/kimi-k3-1-pro.md` | Active, newest |
| Kimi K3.1 Pro high-speed | `kimi-k3.1-pro-highspeed` | K3 | `providers/moonshot/kimi-k3-1-pro-high-speed.md` | Active |
| Kimi K3 | `kimi-k3` | K3 | `providers/moonshot/kimi-k3.md` | Active |

Served, but with no model-specific guidance, so this file is their whole basis: Kimi K2.7 Code and K2.7 Code high-speed, and Kimi K2.6 (deprecated, retirement expected late December 2026); the older K2 preview and thinking ids (deprecated, no date). Retired: Kimi K2.5 and the `moonshot-v1` family.

## All Kimi models

### Instructions and output length

- Length is followed more precisely as a number of paragraphs or bullet points than as a number of words; the guide says word counts are "not highly precise". A length contract written in words is a Minor finding; the fix states paragraphs or bullets.
- For a prompt that carries many independent instructions for different scenarios, the guide recommends classifying the query first and giving only the instructions for that category. A long prompt that applies every scenario's rules to every query can be restructured that way (D2, Info or Minor).
- When answers must come from supplied reference text, say so and give the fallback, as in the guide's example: "If the answer is not found in the article, write "I can't find the answer.""
- For file questions, put the file's content in the prompt, not a file id.

### JSON output

- With JSON Mode on, define the format in the prompt with field names and types; "the best practice is to provide a concrete output example and explain the meaning of each field".
- JSON Mode returns JSON objects only: a prompt that asks for a bare JSON array conflicts with it (D5).
- With a response schema, the prompt still has to describe the task and the data source, and must not contradict the schema; a contradiction can produce incomplete JSON.

### Role-play and long conversations

- A character prompt should describe the character's personality, background and traits, and say how the character acts in the situations the product expects. For long conversations the guide re-sends the character settings in a system message every so often; that is harness behavior, so name it as an option rather than a prompt finding.
