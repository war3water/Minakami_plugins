# Data contract

The JSON object the viewer (`templates/viewer.html`) reads from its `code-map-data` script block. Build exactly this shape in runbook Step 3; the integrity checks at the end are what Step 5 runs.

All paths are relative to the repository root with forward slashes. Lines are 1-based. Every `id` follows the stable-ID scheme in `extraction.md` §7. Every type object is `{ "type", "desc", "inferred" }` with a boolean `inferred`.

## Top level

| Field | Type | Meaning |
|---|---|---|
| `meta` | object | repository identity, editor scheme, scope summary (below) |
| `overview` | string | 3 to 5 sentence architecture summary of the scope |
| `subsystems` | array | layer 1 nodes |
| `modules` | array | layer 2 nodes |
| `moduleEdges` | array | layer 2 import edges |
| `pipeline` | object | layer 3: `entry` (a function id) and `stages` |
| `functions` | array | layer 4 nodes; call edges live inside each function's `calls` |

### `meta`

| Field | Type | Meaning |
|---|---|---|
| `repo` | string | display name, usually the root directory name |
| `repoRoot` | string | absolute path with forward slashes; used only to build editor links |
| `project` | string | project name for editor schemes that need one (JetBrains) |
| `editorScheme` | string | template with `{abs_path}`, `{rel_path}`, `{line}`, `{col}`, `{project}` placeholders |
| `generated` | string | ISO date |
| `lang` | string | language of the explanatory text |
| `scope` | object | `focus` (string or null), `entry` (function id), `kept` (one sentence), `cut` (names of everything left out of the map) |

### Subsystem

`id`, `name`, `summary` (1 to 2 sentences), `modules` (array of module ids).

### Module

`id`, `name`, `path`, `line` (1), `purpose` (one sentence), `subsystem` (subsystem id), `functions` (array: function ids for functions in scope, plain `name@line` strings for the rest), `flags` (array).

### Module edge

`from`, `to` (module ids), `kind` (`import`, `include`, `use`, or `dynamic`), `confidence` (`seen` or `inferred`), `evidence` (`path:line`).

### Stage

`id`, `name`, `purpose` (1 to 2 sentences), `path`, `line`, `input` and `output` (type objects), `functions` (array of function ids), `flags` (array, usually empty).

### Function

| Field | Type | Meaning |
|---|---|---|
| `id`, `name`, `path`, `line`, `endLine` | | identity and location |
| `module` | string | module id |
| `signature` | string | verbatim from the source, one line |
| `purpose` | string | one sentence |
| `inputs` | array | type objects with an extra `name` |
| `outputs` | array | type objects |
| `calls` | array | `{ "to": function id, "confidence", "evidence": "path:line" }` |
| `fanIn`, `length` | number | as defined in `extraction.md` §5 |
| `flags` | array | subset of `no-doc`, `untyped`, `high-fan-in`, `long`, `todo`, `no-callers` |
| `stage` | string or null | stage id when this is a stage's own function |

## Canonical example

One subsystem, two modules, one import edge, two stages, two functions. Every real map is this shape, larger.

```json
{
  "meta": {
    "repo": "imgpipe",
    "repoRoot": "/home/dev/imgpipe",
    "project": "imgpipe",
    "editorScheme": "vscode://file/{abs_path}:{line}:{col}",
    "generated": "2026-09-02",
    "lang": "English",
    "scope": { "focus": null, "entry": "fn:imgpipe/cli.py#main", "kept": "The CLI pipeline from an image folder to a metrics report.", "cut": ["tests/", "scripts/bench.py"] }
  },
  "overview": "imgpipe is a command-line image pipeline. The CLI parses arguments, loads a folder of images into arrays, runs a detector over each, and writes a metrics report. Loading and detection are separate modules so detectors can be swapped without touching I/O.",
  "subsystems": [
    { "id": "sub:imgpipe", "name": "imgpipe", "summary": "The package: CLI, loading, detection.", "modules": ["mod:imgpipe/cli.py", "mod:imgpipe/load.py"] }
  ],
  "modules": [
    { "id": "mod:imgpipe/cli.py", "name": "cli", "path": "imgpipe/cli.py", "line": 1, "purpose": "Argument parsing and the top-level run loop.", "subsystem": "sub:imgpipe", "functions": ["fn:imgpipe/cli.py#main"], "flags": [] },
    { "id": "mod:imgpipe/load.py", "name": "load", "path": "imgpipe/load.py", "line": 1, "purpose": "Reads image files into float arrays.", "subsystem": "sub:imgpipe", "functions": ["fn:imgpipe/load.py#load_folder", "_decode@34"], "flags": ["no-doc"] }
  ],
  "moduleEdges": [
    { "from": "mod:imgpipe/cli.py", "to": "mod:imgpipe/load.py", "kind": "import", "confidence": "seen", "evidence": "imgpipe/cli.py:3" }
  ],
  "pipeline": {
    "entry": "fn:imgpipe/cli.py#main",
    "stages": [
      { "id": "stage:01-main", "name": "Parse arguments", "purpose": "Turns argv into a Config.", "path": "imgpipe/cli.py", "line": 12,
        "input": { "type": "list[str]", "desc": "argv", "inferred": false },
        "output": { "type": "Config", "desc": "validated paths and thresholds", "inferred": false },
        "functions": ["fn:imgpipe/cli.py#main"], "flags": [] },
      { "id": "stage:02-load_folder", "name": "Load images", "purpose": "Reads every image under the input folder into memory.", "path": "imgpipe/load.py", "line": 8,
        "input": { "type": "Config", "desc": "input folder path", "inferred": false },
        "output": { "type": "list[ndarray]", "desc": "HxWx3 float32 images", "inferred": true },
        "functions": ["fn:imgpipe/load.py#load_folder"], "flags": [] }
    ]
  },
  "functions": [
    { "id": "fn:imgpipe/cli.py#main", "name": "main", "path": "imgpipe/cli.py", "line": 12, "endLine": 40, "module": "mod:imgpipe/cli.py",
      "signature": "def main(argv: list[str] | None = None) -> int",
      "purpose": "Parses arguments, then runs load, detect, and report in order.",
      "inputs": [ { "name": "argv", "type": "list[str] | None", "desc": "command line, defaults to sys.argv", "inferred": false } ],
      "outputs": [ { "type": "int", "desc": "process exit code", "inferred": false } ],
      "calls": [ { "to": "fn:imgpipe/load.py#load_folder", "confidence": "seen", "evidence": "imgpipe/cli.py:22" } ],
      "fanIn": 0, "length": 29, "flags": [], "stage": "stage:01-main" },
    { "id": "fn:imgpipe/load.py#load_folder", "name": "load_folder", "path": "imgpipe/load.py", "line": 8, "endLine": 31, "module": "mod:imgpipe/load.py",
      "signature": "def load_folder(folder)",
      "purpose": "Lists image files in a folder and decodes each into a float32 array.",
      "inputs": [ { "name": "folder", "type": "str | Path", "desc": "directory of images", "inferred": true } ],
      "outputs": [ { "type": "list[ndarray]", "desc": "decoded images", "inferred": true } ],
      "calls": [],
      "fanIn": 1, "length": 24, "flags": ["no-doc", "untyped"], "stage": "stage:02-load_folder" }
  ]
}
```

## Integrity checks (runbook Step 5)

1. The JSON parses, and the HTML file contains exactly one `code-map-data` script block whose content is that JSON.
2. Every id referenced anywhere (`subsystem`, `modules`, `functions` when not a plain `name@line` string, `from`, `to`, `calls[].to`, `pipeline.entry`, `stages[].functions`, `stage`) exists as a node.
3. Every node has `path` and `line`; every edge has `evidence` in `path:line` form.
4. Every edge has `confidence` equal to `seen` or `inferred`; every type object has a boolean `inferred`.
5. `meta.scope.cut` names everything left out of the map, so nothing disappears silently.
