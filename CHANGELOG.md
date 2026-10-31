# Changelog

All notable changes to this workflow. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions: a **minor** bump when a retro changes how the commands or agents behave, a **patch** bump for documentation and script fixes.

## [Unreleased]

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

[Unreleased]: https://github.com/nikhileshnarkhede/spec-driven-dev/compare/v0.3.1...HEAD
[0.3.1]: https://github.com/nikhileshnarkhede/spec-driven-dev/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/nikhileshnarkhede/spec-driven-dev/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/nikhileshnarkhede/spec-driven-dev/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/nikhileshnarkhede/spec-driven-dev/releases/tag/v0.1.0
