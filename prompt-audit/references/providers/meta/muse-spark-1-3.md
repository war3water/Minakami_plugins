<!-- Built by scripts/build-model-files.py from prompt-audit/sources/meta-entries.md. Do not edit by hand: edit the source and rebuild. -->

# Muse Spark 1.3: model guidance

Applies only to Muse Spark 1.3. Read it with `providers/meta.md`; where an entry here disagrees with that file or with `general.md`, the entry here wins. Cite as `[ref: providers/meta/muse-spark-1-3.md §<section>]`.

## Images and computer use

- For locating objects in images, ask for one specific output shape and list the objects to find; state the coordinate fields and axis order and ask for JSON; to count, ask the model to point at every instance and then return the total. Put the grounding instruction in the user message next to the image and keep the system prompt minimal.
