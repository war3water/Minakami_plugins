# Meta (Muse, Llama) — prompt guidance

Cite as `[ref: providers/meta.md §<section>]`. Universal patterns are in `general.md`; universal guidance for tool-using agents is in `agentic.md`.

**How to read this file.** Meta's prompting guidance is written per model, so it all lives in the model files. This file only lists the models. When the user named a model in the table below, read its model file; for any other Meta model, the universal files are the whole basis.

## Models

Status is the vendor's, checked on 2026-11-21; "newest" marks the newest model of its series. Meta publishes no deprecation list.

| Model | Id | Series | Model file | Status |
|---|---|---|---|---|
| Muse Spark 1.3 | `muse-spark-1.3` | Muse Spark | `providers/meta/muse-spark-1-3.md` | Active, newest |
| Muse Spark 1.2 | `muse-spark-1.2` | Muse Spark | `providers/meta/muse-spark-1-2.md` | Active |
| Muse Spark 1.1 | `muse-spark-1.1` | Muse Spark | `providers/meta/muse-spark-1-1.md` | Active |
| Muse Wonder | `muse-wonder-1.0` | Muse Wonder | `providers/meta/muse-wonder.md` | Preview |
| Muse Spark Open | `meta-models/Muse-Spark-Open-816B-A42B` (open weights) | Muse Spark Open | `providers/meta/muse-spark-open.md` | Active |
| Muse Glimmer | `meta-models/Muse-Glimmer-30B` (open weights) | Muse Glimmer | `providers/meta/muse-glimmer.md` | Active |
| Llama 4 Maverick | `meta-llama/Llama-4-Maverick-17B-128E-Instruct` (open weights) | Llama 4 | `providers/meta/llama-4-maverick.md` | Not in Meta's current model list; open weights still published |
| Llama 4 Scout | `meta-llama/Llama-4-Scout-17B-16E-Instruct` (open weights) | Llama 4 | `providers/meta/llama-4-scout.md` | Not in Meta's current model list; open weights still published |

Served, with no model-specific prompting guidance: Muse Ember.
