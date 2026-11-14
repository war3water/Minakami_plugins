# Pictures on the cards

Read this while you write the cards.

## What a picture is for

The page exists so the user understands what you mean before they choose. A picture helps when the reader sees the point in it faster and more surely than in words. It hurts when it only restates the words or needs its own explanation. So start from the reader, not from the form: read the card as a newcomer and find where they would slow down, re-read or reach for a pen. Then pick what makes that spot plain, whether a sentence, a worked example, a table or a picture, and say its point in one sentence; for a picture, that sentence is the caption.

A picture takes the place of words; it is not added to them. When it shows the point, cut the table and the sentences that say the same, so the options stay in view. When the card is already plain without it, leave the picture out.

You know the project and the reader does not, so judge by where they would get stuck, not by how clear your own words feel. Words tend to struggle when the case has to be seen to be understood, or when the logic links more parts, steps or conditions than a reader can hold while reading; there, consider a chart, plot, schematic, pipeline or flow, timeline, table, or whatever shows it most clearly. Some common cases, and a form that often helps:

- how much an effect changes across the sizes, volumes or times that really occur, and whether it matters for their cases or only for the one in your example: a chart over that range, with this project's case marked;
- how a mechanism or flow works, or why it fails: its real parts drawn (the files, services, steps), with what passes between them;
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
- Compute every number in a picture with a command, from the project's own code or data, just as for the example. When a script computes the example, let the same script draw its chart.
- On the picture or in its caption, mark anything made up, estimated or assumed.

## How to make each kind

A picture is a file in the task folder, next to `shots/`, and a card refers to it as a figure (format: `questions-format.md`, "Figures"). Use what the project and the machine already have, and ask the user before installing anything.

**A drawing (`.svg`)** suits charts, schematics, pipelines, timelines and diagrams. Write it by hand, or with a script that uses a plotting library or Graphviz when one is installed. The page places the drawing into itself, so:

- Give it a `viewBox`, and draw it at about the width it will show at: around 720 units for the full card width, with text at 12 to 14 units. On a phone, a wide drawing scrolls inside its box, and every drawing opens full size.
- Colour it with the page's colours, so it reads in both light and dark:
  - `var(--ink)` (or `currentColor`) for text and lines;
  - `var(--muted)` for secondary text;
  - `var(--line)` for axes, gridlines and frames;
  - `var(--panel)` for a fill that matches the card;
  - `var(--s1)` to `var(--s4)` for options or series, used in that order: the order is checked for colour-blind readers.

  They work in attributes (`fill="var(--s1)"`) and in `style`. A plotting library writes fixed colours instead. Give it the light series colours `#2a78d6 #eb6834 #1baf7a #6250d6`, a transparent background, and text kept as text (in matplotlib, `svg.fonttype = "none"`), or replace its colours with the variables afterwards.
- A few lines of plain Python are often enough. This one shows the parts the page needs (the `viewBox`, the colour variables, `data-option`) and labelled axes, for two pricing options over 0 to 2,000 users; the form and the values are yours to choose for the case:

  ```python
  W, H, L, R, T, B = 720, 260, 64, 110, 24, 210      # width, height, and the plot's left, right, top and bottom edges
  users = range(0, 2001, 50)
  plans = {"flat": ("Flat fee", lambda u: 400), "seat": ("Per seat", lambda u: 0.3 * u)}  # option id: label, cost
  x = lambda u: L + u * (W - L - R) / 2000
  y = lambda c: B - c * (B - T) / 600
  t = lambda X, Y, s, a="middle": f'<text x="{X:.0f}" y="{Y:.0f}" font-size="12" fill="var(--muted)" text-anchor="{a}">{s}</text>'
  out = [f'<path d="M{L},{T} V{B} H{W - R}" fill="none" stroke="var(--line)"/>', t(L, T - 10, "cost per month", "start"),
         t((L + W - R) / 2, B + 38, "users")]
  out += [t(x(u), B + 18, f"{u:,}") for u in range(0, 2001, 500)] + [t(L - 8, y(c) + 4, f"€{c}", "end") for c in (0, 200, 400, 600)]
  for (oid, (label, f)), colour in zip(plans.items(), ("--s1", "--s2")):
      pts = " ".join(f"{x(u):.1f},{y(f(u)):.1f}" for u in users)
      out.append(f'<g data-option="{oid}"><polyline points="{pts}" fill="none" stroke="var({colour})" stroke-width="2"/>'
                 f'<text x="{x(2000) + 6:.0f}" y="{y(f(2000)) + 4:.0f}" font-size="12" fill="var(--ink)">{label}</text></g>')
  open("pics/cost.svg", "w", encoding="utf-8").write(
      f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">' + "".join(out) + "</svg>")
  ```
- Put `data-option="<option id>"` on the parts that belong to one option. When the reader chooses that option, the page dims the rest, so they see what their choice means.
- Leave out scripts, event attributes, `foreignObject` and links to outside files; put any image inside as a `data:` URI. A `<style>` inside the drawing applies to that drawing only. `build` refuses anything the page cannot show safely.

**A screenshot**: run the real code or page and capture it, with a headless browser when one is installed, then crop it to what matters. For a visible change, show before and after. When the options look different, give each option its own `figure`.

**A live demo (`.html`)** is a small self-contained page, for when trying something beats looking at it: a slider over the range that matters, or a working mockup of each option.

- It runs in a sealed frame, with no network, no browser storage and no access to the page or its answers. Put its scripts, styles, data and images (as `data:` URIs) in the file.
- The page sets the same colour variables inside it.
- The page also tells it the reader's choice: `addEventListener("brief-choice", e => ...)`, where `e.detail` is the option id or null, and the same id on `document.documentElement.dataset.choice`.
- The frame grows to fit the demo; `height` sets its size until it loads.
- Keep it small, since it travels with the page.

**Worked numbers** go in a `table` or a text sketch.

- A table row can belong to an option (`{"cells": [...], "option": "<id>"}`), and it stands out when that option is chosen.
- A text sketch is a block of lines between two ```` ``` ```` lines. It keeps its spacing, for a calculation or a small layout drawn in characters.

## Check before you send the link

- `build` or `serve` passes with no warning about a picture.
- Look at the page with its pictures in it, in a headless browser screenshot when you have one:
  - each picture shows its caption's point at a glance, and reads cold (above);
  - no label overlaps another or runs off the edge;
  - text stays readable at phone width;
  - choosing each option highlights the right parts.
- Read each caption against its picture: the same numbers and the same names as on the card.
- Without a browser, the build's checks are your look: fix what they report.

## Spend tokens where they help

Make each picture once, as a file. Never paste it into the chat, and never read a generated one back whole.
