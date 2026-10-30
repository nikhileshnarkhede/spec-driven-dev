# Changelog

All notable changes to this workflow. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions: a **minor** bump when a retro changes how the commands or agents behave, a **patch** bump for documentation and script fixes.

## [Unreleased]

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

[Unreleased]: https://github.com/nikhileshnarkhede/spec-driven-dev/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/nikhileshnarkhede/spec-driven-dev/releases/tag/v0.1.0
