# Pictures on the cards

Read this while you write the cards.

## What a picture is for

SKILL.md (step 2) decides whether a card needs more than its words; this file is about making a picture once it does, and checking it. A picture helps when the reader sees the point in it faster and more surely than in words, and hurts when it only restates the words or needs its own explanation. Say its point in one sentence: that sentence is the caption.

A picture shows what words show slowly: where each part sits, in what order, and how much. It can carry its numbers, each written on the part it belongs to (the three-day wait on the step that causes it), so no table has to repeat them.

Let the form follow what the options differ in: how much, where in a process, when, or how it looks. Some common cases, and a form that often helps:

- how much an effect changes across the sizes, volumes or times that really occur, and whether it matters for their cases or only for the one in your example: a chart over that range, with this project's case marked;
- how a mechanism or flow works, where it fails, or where in it each option acts: its real parts drawn in their real order (the files, services, steps), with what passes between them, the failure marked where it happens and each option where it acts;
- when a risk bites: a timeline of the real events, to scale;
- why numbers disagree: the numbers worked through line by line, in a table or a text sketch, until the cause shows;
- what a result will look like, or how it feels to use: screenshots of the real thing, one per option, or a live demo.

Combine forms, or use another, when the case calls for it.

- Show what the options do to real cases, not the options themselves, which the option list already shows.
- Put things at their real values: times on a time axis to scale, sizes to scale, steps in their real order.
- Each picture makes one point. Leave out what the point does not need (heavy gridlines, frames, shadows, 3D, colours that mean nothing), and keep what the reader needs to read it.
- Put the picture that makes the card's point in `figures` or the example, where it shows without a click. Working that supports it can fold under `more`.

## Readable cold

The reader meets the picture with no one to explain it. Look at it as they will:

- Each axis says what it measures and in what unit, with enough values marked to read a point off it.
- Each line, bar, dot and arrow says what it is, on the picture itself, and a difference says what it is measured against.
- The facts the numbers rest on are on the card, so the reader does not have to guess them back from the result.
- A range is described in the reader's terms, not in the terms of how you worked it out.
- The caption says what to see, not how you drew it.
- Its words are in the page's language, and use the same names for things as the card.

When a few labels cannot make a picture read cold, rework it, or choose another form that does.

## Fair and true

- Draw every option with the same care, on the same scale and axes. Being recommended does not make an option bigger, brighter or first.
- Start each axis where it honestly should: bars start at zero, and no cropped range turns a small difference into a large one.
- When a picture or a sentence sums up a range, work it out over the whole range the reader's cases fall in: a few points you picked can hide or inflate how often the options differ.
- When a script computes the example's figures, let the same script draw its chart. Mark a made-up, estimated or assumed value on the picture itself or in its caption.

## How to make each kind

A picture is a file in the task folder, next to `shots/`, and a card refers to it as a figure (format: `questions-format.md`, "Figures"). Use what the project and the machine already have, and ask the user before installing anything.

**A drawing (`.svg`)** suits charts, schematics, pipelines, timelines and diagrams. Write it by hand, or with a script that uses a plotting library or Graphviz when one is installed. The page places the drawing into itself, so:

- Give it a `viewBox`, and draw it at about the width it will show at: around 720 units for the full card width, with text at 12 to 14 units. On a phone, a wide drawing scrolls inside its box, and every drawing opens full size. Keep it as short as its point allows, so the options stay in view: a chain of steps usually fits in one row.
- Colour it with the page's colours, so it reads in both light and dark:
  - `var(--ink)` (or `currentColor`) for text and lines;
  - `var(--muted)` for secondary text;
  - `var(--line)` for axes, gridlines and frames;
  - `var(--panel)` for a fill that matches the card;
  - `var(--s1)` to `var(--s4)` for options or series, used in that order: the order is checked for colour-blind readers.

  They work in attributes (`fill="var(--s1)"`) and in `style`. A plotting library writes fixed colours instead. Give it the light series colours `#2a78d6 #eb6834 #1baf7a #6250d6`, a transparent background, and text kept as text (in matplotlib, `svg.fonttype = "none"`), or replace its colours with the variables afterwards.
- A few lines of plain Python are often enough. Whatever the form, the file the page receives has this outline; the shapes, values and layout inside it are yours to choose for the case:

  ```svg
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 240">
    <text x="8" y="18" font-size="13" fill="var(--muted)">a label, in the page's language</text>
    <g data-option="first-option-id"><!-- this option's parts, in var(--s1) --></g>
    <g data-option="second-option-id"><!-- this option's parts, in var(--s2) --></g>
  </svg>
  ```
- Put `data-option="<option id>"` on the parts that belong to one option. When the reader chooses that option, the page dims the rest, so they see what their choice means.
- Leave out scripts, event attributes, `foreignObject` and links to outside files; put any image inside as a `data:` URI. A `<style>` inside the drawing applies to that drawing only. `build` refuses anything the page cannot show safely.

**A screenshot**: run the real code or page and capture it, with a headless browser when one is installed, then crop it to what matters. For a visible change, show before and after. When the options look different, give each option its own `figure`.

**A live demo (`.html`)** is a small self-contained page, for when trying something beats looking at it: a slider over the range that matters, or a working mockup of each option.

- It runs in a sealed frame, with no network, no browser storage and no access to the page or its answers. Put its scripts, styles, data and images (as `data:` URIs) in the file.
- The page sets the same colour variables inside it.
- The page also tells it the reader's choice: `addEventListener("decision-page-choice", e => ...)`, where `e.detail` is the option id or null, and the same id on `document.documentElement.dataset.choice`.
- The frame grows to fit the demo; `height` sets its size until it loads.
- Given as each option's `figure`, the demos stay off the card and open in a floating window, one at a time: use that for a working mockup of each option, so the card stays as short as a text card.
- Keep it small, since it travels with the page.

**Worked numbers** go in a `table` or a text sketch.

- A table row can belong to an option (`{"cells": [...], "option": "<id>"}`), and it stands out when that option is chosen.
- A text sketch is a block of lines between two ```` ``` ```` lines. It keeps its spacing, for a calculation or a small layout drawn in characters.

## Check before you send the link

- `build` or `serve` passes with no warning about a picture.
- Look at the page with its pictures in it, in a headless browser screenshot when you have one:
  - each picture shows its caption's point at a glance, and reads cold (above);
  - no label overlaps another, spills out of its box or runs off the edge;
  - text stays readable at phone width;
  - choosing each option highlights the right parts.
- Read each caption against its picture: the same numbers and the same names as on the card.
- Read the card with its picture covered: the words alone still say what happens and why.
- Without a browser, the build's checks are your look: fix what they report.

## Spend tokens where they help

Make each picture once, as a file, and check a generated one through its render and the build's checks above rather than by reading the file back.
