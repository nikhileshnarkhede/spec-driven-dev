# Changelog

All notable changes to this workflow. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions: a **minor** bump when a retro changes how the commands or agents behave, a **patch** bump for documentation and script fixes.

## [Unreleased]

## [0.4.4] - 2026-11-03

### Fixed

- The illustrated overview (`docs/workflow-article.html`): the ledger diagram's "why the extra rounds" text ran into the cost column and its footer and Retro caption were cut off or overlapped; three other labels (Spec, Split; the test writer's subtitle in both the wide and the phone diagram; the hardening-candidates caption) ran past the edge of their diagram and were clipped. Checked at desktop and phone width for overlapping or clipped text. Documentation only.

## [0.4.3] - 2026-11-03

### Changed

- Documentation de-duplicated and realigned; no behaviour change. The README is a landing page: the "Why" list is five points that link to the rules in guideline section 8, the unattended-mode and Docker paragraphs are pointers, and the command count is corrected (eleven `/dev-` commands plus the optional `/no-claude-footprint`). Guideline section 11 ("Sharing the framework") is removed because the README holds the install; unattended mode is now section 11 and the ledger, retro and spec section 12. Docker is explained once (section 6) and pointed to from the Commands and Quick start sections; the models section no longer repeats the tables.

### Moved here from the guideline

- Renamed from the earlier version: `/split-spec` is `/dev-0-split`, `/create-subspec` is `/dev-1-select`, `/verify-subspec` is `/dev-3-test`, `/review-subspec` is `/dev-4-review`, `/lock-subspec` is `/dev-6-final`, `/checkpoint` is `/dev-save`; `/dev-2-write`, `/dev-5-fix-review` and `/dev-auto` are new.
- What the first 25 units taught: verification became nearly one-pass once contracts existed (median one failing check, mostly fixture misreads by the writer); the extra rounds came from review findings and from a hardening round chosen after review in almost every unit; review was a third of all cost; three oversized units took a third more; most escapes were a later unit's contract breaking an earlier unit's locked test file. The rules that followed: robustness checks in the contract and built in round 1; reviewer budgets; the 16-check / 700-line limit and dependency-ordered index; `Example:` and `Extends:` lines; stubs in `tests/stubs/`.

## [0.4.2] - 2026-11-02

### Changed

- Docker gets its own heading everywhere it was only mentioned in passing: a "Docker" subsection in guideline section 6, a line in the Commands section and a Quick start step; a "Docker is the environment" section in the illustrated overview; a "Docker" section in the README. Documentation only.

## [0.4.1] - 2026-11-02

### Changed

- The illustrated overview (`docs/workflow-article.html`) describes the container as the environment the tests run in, matching the 0.4.0 guideline and conventions. Documentation only.

## [0.4.0] - 2026-11-02

### Added

- **The project's container is the environment** for both the test suite and the application. New convention C12 in the `CONVENTIONS.md` template: a pinned `Dockerfile` built from a lock file, an allow-list `.dockerignore`, `PYTHONPATH` instead of an editable install, a non-root user, `--network none` with data mounted read-only, the suite and application run commands in the Dockerfile header. `/dev-0-split` and `/dev-spec` make the container the first unit when a repository has none; `/dev-3-test`, `/dev-auto`, the implementer and `/dev-6-final` run the suite in the image and record which image the counts came from; the merged-main run in `/dev-6-final` rebuilds the image from the merged tree.
- **Hazard HZ13, machine-dependent tests**, with matching rules for the test writer: expectations come from the artifact or the fixture, never from the host (`cuda.is_available()`, an installed package, a run-state file the project edits); a stubbed interpreter intercepts every script the code can call; a skip carries its reason and its other branch is covered elsewhere; a held-out set the project locks is never opened by a check.
- **The runner accounts for every skip and every data folder**: it runs with `-rs`, lists each skip with its reason, names the folders the run mounted or read (a locked held-out set on its own line), treats an out-of-memory kill as an environment observation and reruns file by file, and ends its one-line total with the environment.
- Guideline section 6 gains the container recipe (allow-list, lock file, no editable install, read-only mounts, per-file runs under a memory limit, a GPU variant so no conditional test stays unrun between the two images, the Windows Git Bash and WSL notes) and rule 12; the README lists Docker as a requirement.

### Notes

- Drawn from the SCANIA project's clean-environment run of 2026-11-02 (7,345 CPU and 7,344 GPU checks over two images): a host-only suite had hidden an editable-install shadowing of a test's temporary `config` module, a device check that read the machine instead of the bundle, a script stub that let real preprocessing run when the data was present, a test pinning the approved-runs file, and an unexplained skip count.
- No `docker` command is pre-approved in `allowed-tools`, for the same reason `pytest` is not (0.3.2): a wildcard after it lets anything through. The build and the run ask once per turn; the runner agent runs them inside its own shell.

## [0.3.2] - 2026-10-31

### Changed

- `/dev-auto` no longer pre-approves `pytest` or `python -m pytest`: a wildcard after a test runner lets any command through, and the test runs happen in the runner agent anyway. `/dev-spec` no longer pre-approves file writes; you approve the two files it writes. Requested by the plugin directory's policy check.

## [0.3.1] - 2026-10-31

### Changed

- Skills run their scripts through `${CLAUDE_PLUGIN_ROOT}` instead of paths relative to the skill folder, and every `allowed-tools` rule uses the exact `command:*` form, naming each script file with no relative path or wildcard in it. Read-only `git branch` is narrowed to `git branch --show-current`. Requested by the plugin directory's policy check.

## [0.3.0] - 2026-10-30

### Changed

- **Renamed the plugin to `contract-driven-dev`** (the GitHub repository keeps the name `spec-driven-dev`), because the old name matched another author's plugin in Anthropic's directory. The install id changes: run `/plugin uninstall spec-driven-dev@nikhileshnarkhede`, then `/plugin install contract-driven-dev@nikhileshnarkhede`. The commands are unchanged (`/dev-…`).
- Narrowed every skill's `allowed-tools`: `Bash(python *)` became the exact plugin scripts each skill runs, and `/dev-auto` and `/dev-spec` write only under `./spec/**` and `./Complete spec/**` (plus the writer denylist under `.git/`). Anything else asks first.
- Added a plugin icon and a Data handling section to the README.
- The illustrated overview is hosted on GitHub Pages at https://nikhileshnarkhede.github.io/spec-driven-dev/ (`docs/` on `main`), and the guideline at `/workflow-guideline.html`, rendered in the browser from the Markdown so the `.md` stays the single source.

## [0.2.0] - 2026-10-30

### Changed

- Distributed as a Claude Code plugin: `.claude-plugin/plugin.json` carries the version and `.claude-plugin/marketplace.json` makes this repository its own marketplace. Install with `/plugin marketplace add nikhileshnarkhede/spec-driven-dev` and `/plugin install spec-driven-dev@nikhileshnarkhede`; releases arrive through `/plugin update`.
- The two guards (verification file, writer independence) and the save reminder are registered in `hooks/hooks.json`. Plugin agents can't carry hooks of their own, so each guard reads `agent_type` from the hook input and blocks only inside the agent it protects.
- Skills reach the ledger script relative to themselves (`scripts/usage_ledger.py`); the ledger data stays in `~/.claude/workflow-metrics/`.
- `/dev-retro` edits the workflow's source checkout, bumps the plugin version and records the change in this file, so it ships as a release.

### Removed

- `install.sh`, `install.ps1` and `settings.example.json`: the copy-into-`~/.claude` install.

## [0.1.0] - 2026-10-30

First public release.

### Added

- **Commands** (`/dev-` prefix, numbered in order): `/dev-spec` (brainstorm → API protocol → complete spec), `/dev-0-split` (spec → sub-specs with build contracts, conventions and a handoff ledger), `/dev-1-select`, `/dev-2-write`, `/dev-3-test`, `/dev-4-review`, `/dev-5-fix-review`, `/dev-6-final`, `/dev-auto` (steps 1–5 unattended), `/dev-save` (handoff note), `/dev-retro` (reads the usage ledger and proposes workflow changes), and `/no-claude-footprint`.
- **Agents**: `spec-verification-writer`, `spec-verification-runner`, `spec-compliance-reviewer`, `pipeline-risk-reviewer` and its re-review variant, `dev-implementer` and `dev-implementer-max`. Each agent's tool access enforces its role.
- **Hooks**: a save reminder, a guard that keeps implementers out of the independent verification file, and a guard that keeps the test writer away from the changed files.
- **Build contracts**: ownership of every config key, decisions settled before code, exact interfaces with one example call each, `Extends:` lines for earlier units' functions a unit changes, numbered acceptance checks, robustness checks derived from the project's hazard register, risks and incoming handoffs. `check_contracts.py` enforces completeness, a hard size cap (16 acceptance checks, 700 estimated source lines) and an index in dependency order; `check_fidelity.py` proves every sub-spec excerpt is verbatim.
- **Usage ledger** (`scripts/usage_ledger.py`): measures what each unit cost from the session transcripts, by role, model and effort, with rounds, first-run failure classes, reviewer yield and escaped defects; `/dev-6-final` writes a row per unit and `/dev-retro` learns from it.
- **Docs**: an illustrated overview (`docs/workflow-article.html`) and the full guideline (`docs/workflow-guideline.md`).
- Installers for macOS/Linux/Git Bash (`install.sh`) and Windows PowerShell (`install.ps1`).

### Notes

- The workflow was run end to end on a 25-unit ML project before this release. The rules on robustness checks, reviewer budgets, unit size and dependency-ordered numbering come from that record; the guideline's section 13 explains how.
- The hazard register and the pipeline-risk reviewer are written for ML and data-pipeline code; adapt them for other domains.

[Unreleased]: https://github.com/nikhileshnarkhede/spec-driven-dev/compare/v0.4.4...HEAD
[0.4.4]: https://github.com/nikhileshnarkhede/spec-driven-dev/compare/v0.4.3...v0.4.4
[0.4.3]: https://github.com/nikhileshnarkhede/spec-driven-dev/compare/v0.4.2...v0.4.3
[0.4.2]: https://github.com/nikhileshnarkhede/spec-driven-dev/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/nikhileshnarkhede/spec-driven-dev/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/nikhileshnarkhede/spec-driven-dev/compare/v0.3.2...v0.4.0
[0.3.2]: https://github.com/nikhileshnarkhede/spec-driven-dev/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/nikhileshnarkhede/spec-driven-dev/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/nikhileshnarkhede/spec-driven-dev/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/nikhileshnarkhede/spec-driven-dev/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/nikhileshnarkhede/spec-driven-dev/releases/tag/v0.1.0
