# Extraction method

How `/code-map` turns a repository into the nodes and edges the viewer draws. The method is language-agnostic; §9 gives per-language starting points and §10 the editor link schemes. Read this before discovering scope (runbook Step 2) and keep it open while extracting (Step 3).

## 1. Languages and repository root

Detect languages from manifests first, file extensions second. The repository root is the nearest ancestor with a VCS directory or a top-level manifest. Record it once for editor links; every node path is relative to it, with forward slashes.

## 2. Entry points

Look in this order and stop at the first class that yields candidates:

1. Executable entry: `main` functions, `if __name__ == "__main__"`, `fn main`, `func main`, `public static void main`, scripts named `main.*`, `run.*`, `cli.*`, `app.*`, `train.*`, `serve.*`
2. Declared entry: `[project.scripts]`, `bin` in `package.json`, `[[bin]]`, `cmd/*` directories, `Makefile` or `justfile` default targets, `Dockerfile` `CMD` / `ENTRYPOINT`
3. Server routes and handlers: route decorators, router registrations, controller classes
4. Exported public API: the package `__init__`, `index.*`, `lib.rs`, `mod.rs`, public headers
5. Tests: the most-imported module under test is a proxy for the core API

`--entry` always wins. When several candidates remain, one is primary if the others call it, the README or manifest names it, or it has the largest fan-out into the repository. If none of those separates them, that is the ambiguity the runbook asks about.

## 3. Modules and import edges (layer 2)

A module is a source file, or a package or crate when files are too fine (C++ translation units, Java packages, Go packages). One node per module in scope.

An import edge runs from the importing module to the imported one, with the `path:line` of the import statement as evidence. Resolve relative and aliased imports to a path in the repository. Third-party and standard-library imports are not nodes; name the notable ones in the module's purpose sentence when they define what the module is.

Confidence:

- `seen`: a static import, include, `use`, `require`, or `mod` line that resolves to a repository file
- `inferred`: dynamic imports (`importlib`, `require(variable)`, `dlopen`, reflection), string-based module names, plugin registries, conditional imports you could not resolve

## 4. Pipeline and stages (layer 3)

Trace from the primary entry point's input to its final output. A stage is one top-level transformation on that path: usually a function the entry point calls directly, or a clearly delimited block (a loop body, a phase behind a comment banner). One stage per transformation that changes the data's shape or meaning: fold steps that are only plumbing into the stage they serve, split a stage that hides two unrelated transformations. The test is whether a reader can hold the whole pipeline in one view.

For each stage record the input and the output: type first, then one line on meaning. Types come from annotations, signatures, or declared struct types; when absent, infer from construction and use (`dict[str, Tensor]`, `list of Row`) and mark `inferred`. The output type of stage N is normally the input type of stage N+1; when it is not, say why in the stage purpose.

## 5. Functions and call edges (layer 4)

Only functions reached from a stage are nodes: the stage's own function, the repository functions it calls, and deeper levels only where they explain how the stage works (a helper that carries the real logic, a callback that decides the data's shape). A call edge carries the `path:line` of the call site.

Confidence:

- `seen`: a direct call to a resolvable definition in the repository
- `inferred`: dynamic dispatch (virtual methods, duck typing, callbacks, `getattr`, function tables, signals and slots, DI containers), calls through an interface with several implementations, decorated or generated functions

Record per function: `signature` verbatim on one line, `line` and `endLine`, `fanIn` (distinct calling functions in the repository, seen edges only), `length` (`endLine - line + 1`).

## 6. Hotspot flags

| Flag | Rule | Why the user cares |
|---|---|---|
| `no-doc` | No docstring or doc comment on the definition | first place to add comments |
| `untyped` | Public function with no type information on parameters or return | first place to add types |
| `high-fan-in` | Called from more places than most functions in scope, or from more than one subsystem | changing it touches many callers |
| `long` | Markedly longer than its neighbors in the same module, or long enough to hold more than one responsibility | refactor candidate |
| `todo` | `TODO`, `FIXME`, `HACK`, or `XXX` in the body or leading comments | the author already flagged it |
| `no-callers` | `fanIn` is 0 and the function is not an entry point | possibly dead, possibly dynamic; check before deleting |

Flags describe the code; they never change scope.

## 7. Stable IDs

IDs keep a user's notes attached across regenerations, so they derive only from the code's own identity:

- subsystem: `sub:<directory-or-package>`
- module: `mod:<relative/path.ext>`
- function: `fn:<relative/path.ext>#<Qualified.name>` (class or namespace qualifiers joined with `.`)
- stage: `stage:<two-digit-index>-<slug-of-stage-function>` (the function slug keeps a moved stage recognizable even when its index changes)

## 8. Scope and readability

There is no fixed node budget. Scope is a judgment about what explains the architecture, made against one test: can a reader scan each layer in one view? Keep, in this order, what the entry point reaches, what has fan-in from more than one subsystem, and what the focus or the arguments name. Leave out vendored and generated code, tests, and one-off scripts unless named. When the repository is larger than one readable map, map the primary pipeline, name the other subsystems in the overview, and tell the user how to get each one with a focus argument. Everything left out is listed by name in `meta.scope.cut` and in the final summary, so nothing disappears silently.

## 9. Per-language starting points

Use tooling only when it is already present; never install. The last row covers everything not listed — the method does not depend on the language.

| Language | Manifests | Entry-point conventions | Import syntax to parse | Tooling, if present |
|---|---|---|---|---|
| Python | `pyproject.toml`, `setup.py`, `requirements*.txt` | `__main__`, `[project.scripts]`, `manage.py`, `cli.py` | `import x`, `from x import y` | `python -m ast`, `pydeps`, `pyan3`, `jedi` |
| TypeScript / JavaScript | `package.json`, `tsconfig.json` | `bin`, `main`, `index.*`, framework routes (`app/`, `pages/`, `routes/`) | `import ... from`, `require()`, `export ... from` | `tsc --listFiles`, `madge`, `dependency-cruiser`, `ts-morph` |
| C / C++ / CUDA | `CMakeLists.txt`, `Makefile`, `meson.build`, `compile_commands.json` | `main()`, `add_executable` targets, kernels launched from host code | `#include "..."` for repository headers; `<<<>>>` launches count as call edges | `clangd`, `clang -MM`, `cmake --graphviz`, `doxygen` XML |
| Rust | `Cargo.toml` | `fn main`, `[[bin]]`, `lib.rs` | `mod`, `use crate::` | `cargo metadata`, `cargo modules`, `rust-analyzer` |
| Go | `go.mod` | `func main` under `cmd/*`, `package main` | `import "module/path"` | `go list -deps`, `gopls` |
| Java / Kotlin | `pom.xml`, `build.gradle*` | `public static void main`, `@SpringBootApplication`, controllers | `import a.b.C` | `jdeps`, IDE indexes |
| C# | `*.csproj`, `*.sln` | `static void Main`, `Program.cs`, controllers | `using A.B` | `dotnet build` output, Roslyn |
| MATLAB | none; `startup.m`, `+package` folders | top-level scripts, `function` files named after the entry | calls by file name, `import pkg.*` | `matlab.codetools.requiredFilesAndProducts`, `depfun` |
| R / Julia | `DESCRIPTION`, `Project.toml` | `main.R`, `run.jl`, `NAMESPACE` exports | `source()`, `library()`, `using`, `include()` | `pkgdepends`, `PkgDependency` |
| Shell / Make / notebooks | none | the top-level script, the default target, the first cell | `source`, `.`, `include`, `%run` | none; read the files |
| Anything else | whatever declares dependencies | the file the README says to run | the language's import or include keyword, found by grep | none; read the files |

## 10. Editor link schemes

`--editor` selects the template the viewer fills for every node. Placeholders: `{abs_path}`, `{rel_path}`, `{line}`, `{col}`, `{project}`.

| `--editor` value | Template |
|---|---|
| `vscode` (default) | `vscode://file/{abs_path}:{line}:{col}` |
| `vscode-insiders` | `vscode-insiders://file/{abs_path}:{line}:{col}` |
| `cursor` | `cursor://file/{abs_path}:{line}:{col}` |
| `windsurf` | `windsurf://file/{abs_path}:{line}:{col}` |
| `jetbrains:<ide>` (`idea`, `pycharm`, `clion`, `webstorm`, `goland`, `rider`, `rustrover`) | `jetbrains://<ide>/navigate/reference?project={project}&path={rel_path}:{line}` — needs JetBrains Toolbox installed |
| anything else | used verbatim as the template |

The viewer always shows the `path:line` text beside the link, so navigation still works where the scheme is not registered (a hosted Artifact copy, another machine).
