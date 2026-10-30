---
name: dev-spec
description: Step before the split (once per project) — turn a brainstorm into two documents the workflow builds from: an API protocol (architecture, structural flow, every public interface, config keys, data contracts, extension sockets) and a complete spec whose sections are already the future sub-specs, numbered in dependency order and sized for one-round builds. Writes into Complete spec/; the user confirms each stage. Pass notes or a project name, e.g. /dev-spec "DLP engine" or /dev-spec notes.md.
argument-hint: "[project name | notes file]"
disable-model-invocation: true
model: opus
effort: high
allowed-tools: Read Grep Glob Write(./Complete spec/**) Edit(./Complete spec/**) Bash(git status *) Bash(git log *) Bash(python "${CLAUDE_SKILL_DIR}/../dev-3-test/scripts/interface_surface.py" *)
---

Work as the architect who writes the document a team will build from without talking to you again: every interface named, every value literal, every section small enough to build and verify in one pass. `/dev-0-split` will cut this spec into sub-specs by its sections and fix contract interfaces from the API protocol, so what is vague here becomes an extra round there. The user stays in control: each stage ends with a checkpoint and a confirmation before the next starts, and nothing here writes code.

Input: $ARGUMENTS — a project name, a path to brainstorm notes, or nothing (then ask for the idea in one question). Run from the repository root; create `Complete spec/` if missing. Never overwrite a spec that already exists there without asking.

## 1. Gather

Read the notes if a file was given, `README.md`, `CLAUDE.md`/`CLAUDE.local.md`, and any existing code's public surface (`python "${CLAUDE_SKILL_DIR}/../dev-3-test/scripts/interface_surface.py" <files>`) so the protocol reuses what exists. Then interview in AskUserQuestion batches (up to 4 questions each, 2–4 options, your recommendation first), until nothing below is open:
- purpose, users and the one result that makes the project a success;
- inputs and outputs: data sources, formats, sizes, labels, what arrives live;
- the components and the flow between them, in the user's words;
- quality bars: metrics, tolerances, thresholds, what "correct" means offline;
- constraints: language, frameworks, hardware, time, budget, what must stay unchanged;
- non-goals, and what is already built;
- extension points: what will be swapped, compared or added later.

Checkpoint: **Known** (one line per answered area) · **Open** (what you will decide yourself, with the default) · **Next** (the protocol).

## 2. API protocol — `Complete spec/<name>-api-protocol.md`

The software's contract, written before any requirement prose. Sections, in this order:
1. **Architecture in one page**: the principles that shape the design (why these components, what each one must never do), and a structural-flow diagram in a fenced block: each stage on its own line, inputs → stage → outputs, with the shapes or record types on the arrows.
2. **Layout**: the package tree with one line per module saying what it owns.
3. **Interfaces**: every public function and class, grouped by module — exact signature with types, shapes, dtypes and units; what it raises and when; one `Example:` line (literal call → literal result or shape). Signatures named here are fixed: `/dev-0-split` copies them into contracts, the test writer builds fixtures from the examples, and later units extend them through declared `Extends:` lines.
4. **Data contracts**: every file, record or table that crosses a module boundary — fields, dtypes, units, ordering, where it is written and read, what validates it on load.
5. **Configuration**: a table of every key — name, type, default, allowed values, the section that owns it, who reads it.
6. **Conventions**: errors (what raises, message content), logging, numerics, randomness and seeds, persistence and provenance — what the project's `CONVENTIONS.md` will say.
7. **Extension sockets**: registries, plug-in folders and the contract each plug-in must meet; one reference implementation named for each.

Keep it literal: no "appropriate", "robust" or "as needed". Where a choice is open, pick one, mark it `[chosen]`, and list it in the checkpoint. Confirm through AskUserQuestion (approve / change these points), and iterate until approved.

Checkpoint: **Written** (file, counts of interfaces, data contracts, config keys) · **Chosen for you** (the `[chosen]` decisions) · **Next** (the spec).

## 3. Complete spec — `Complete spec/<name>.md`

Sections are the future sub-specs, so write them that way:
- **Order by dependency**: a section only depends on earlier sections; the most independent component comes first (data before models, models before training, training before evaluation). State each section's `Depends on:` in its first line.
- **Size for one pass**: each section describes one concern behind one interface, with at most 12 falsifiable requirements (hard limit 16) and about 400 source lines of implementation. A section that would exceed this is split along its own seams, into a socket and its first plug-in, or a reference implementation and each further variant.
- **Each section contains**: purpose (two lines); requirements, each a falsifiable sentence with literal values, tolerances and error behaviour; the interfaces it implements (by name, from the protocol); the config keys it owns; the robustness it must have (which hazards from the conventions apply, and what the code does about each); and an acceptance table with one row per requirement: `ID | given | when | then | tolerance`.
- **Cross-cutting sections at the end**: the configuration listing (every key once), the full acceptance table, the layout tree, the build order (the section order, with the dependency graph), extension points, a glossary, and `Open questions` (ideally "none"; anything left names the section it blocks).
- Write in plain prose and lists that survive verbatim copying: no table inside a code fence, section numbers stable (`§3.2`), one requirement per line.

Checkpoint: **Written** (sections, requirements, acceptance rows) · **Over budget** (any section above 12 requirements, with the proposed split) · **Open questions** · **Next** (the self-check).

## 4. Self-check

Run through the spec and report a table, one row per section: requirements, acceptance rows, config keys owned, dependencies, and whether it is within budget. Then check: every interface in the protocol appears in exactly one section; every config key has one owner; every requirement has an acceptance row; the dependency graph has no cycle and every dependency points backwards; no sentence uses "appropriate", "robust", "handle" or "etc." as a requirement. Fix what fails, re-run, and show the clean table.

## 5. Report

Files written, the counts, the decisions you made for the user (the `[chosen]` list) and anything still open. Don't start the split or write code. End with `Next: /dev-0-split "Complete spec/<name>.md"` — it reads the protocol alongside the spec, numbers the units in the order you set, and writes the contracts.
