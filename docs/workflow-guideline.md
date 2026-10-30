# Spec-Driven Development Workflow — Guideline

A Claude Code framework for building a project from one complete spec, one sub-spec at a time, with independent testing and review before anything is committed. It installs as a Claude Code plugin (`/plugin install spec-driven-dev@nikhileshnarkhede`), so the commands, agents and hooks work in any project.

Every command starts with `/dev-` and carries its step number, so typing `/dev-` lists them in order and the next step is always the next number. Every command ends its report with a `Next: /dev-…` line.

---

## 1. The flow at a glance

```
Brainstorm ─► /dev-spec ──────────► Complete spec/<spec>.md + <spec>-api-protocol.md
              (interview → API protocol → spec whose sections are the units,
               in dependency order, at most 12 requirements each)
                    │
                    ▼
            /dev-0-split ─────────► spec/INDEX.md, CONVENTIONS.md, HANDOFFS.md
            (once per project;       + spec/NN-slug/{sub-spec.md, contract.md, test-report.md}
             settles decisions        + baseline commit on main
             with you)               units numbered in dependency order, ≤16 checks / ~700 lines each
                    │
                    ▼
     ┌─────────────────────────────────────────────────────────────────────────────────────┐
     │ for each sub-spec NN, in index order (dependencies first):                          │
     │                                                                                     │
     │ /dev-1-select NN      select it: check contract → branch → refresh it               │
     │       │                                                                             │
     │ /dev-2-write NN       write it: interfaces with examples → your approval → code,    │
     │       │                 robustness checks built with the rest                       │
     │ /dev-3-test NN        test it: writer agent → runner agent                          │
     │       │                 (not built / wrong behaviour → back to 2)                   │
     │ /dev-4-review NN      review it: 2 reviewer agents in parallel, each with a budget  │
     │       │                 (all clean → skip to 6)                                     │
     │ /dev-5-fix-review NN  work on the review: fix / accept / reject                     │
     │       │                 (anything fixed → back to 3, then a focused re-review in 4) │
     │ /dev-6-final NN       finalize it: prove reports current → close handoffs → commit  │
     │                         → push → merge → "done" → one row in the usage ledger       │
     │                                                                                     │
     │ /dev-save             any time you stop mid-way                                     │
     └─────────────────────────────────────────────────────────────────────────────────────┘
                    │                              ▲
                    ▼                              │ every few units
          All INDEX rows "done" → full spec on main   /dev-retro: reads the ledger, proposes
                                                   workflow changes, you approve each

  Hands-off alternative for steps 1–5: /dev-auto NN  (section 12)
```

Convention: one sub-spec per session; rename the session after the sub-spec (`/rename 04-shared-head`).

---

## 2. Project layout it creates

```
<repo root>/
├── Complete spec/
│   ├── <master spec>.md          # you write this (or /dev-spec does); never modified by the tools
│   └── <master spec>-api-protocol.md   # from /dev-spec: every public interface, data contract and config key
├── spec/
│   ├── INDEX.md                   # | # | Title | Folder | Depends on | Status |
│   ├── CONVENTIONS.md             # house rules + hazard register, decided once (C1…, HZ1…)
│   ├── HANDOFFS.md                # obligations one unit leaves for a later one (HO-1…)
│   └── NN-slug/
│       ├── sub-spec.md            # header + verbatim excerpts of the master spec
│       ├── contract.md            # what the excerpts leave open, settled (section 3)
│       └── test-report.md         # ## Verification, ## Review, ## Review resolutions
├── CLAUDE.local.md                # your private progress/decision log (gitignored)
├── tests/stubs/<unit-slug>.py     # fakes for a unit's interfaces, owned by that unit (C9)
└── <your code and tests>
```

Outside the repo, `~/.claude/workflow-metrics/` holds the usage ledger (`LEDGER.md`, `ledger.jsonl`, `findings.jsonl`, `escaped.jsonl`) and `CHANGES.md`, the log of workflow changes made from it (section 13).

**Statuses:** `not-started` → `in-progress` (set by `/dev-1-select`) → `done` (set by `/dev-6-final`). `pre-existing` marks work that existed before the split. Never edit statuses by hand.

**`test-report.md` sections:**
- `## Verification`: written by `/dev-3-test`, replaced on each run, with a code fingerprint.
- `## Review`: written by `/dev-4-review`, replaced on each run, with a code fingerprint.
- `## Review resolutions`: appended by `/dev-5-fix-review`, one round per pass; earlier rounds are never edited.

**`sub-spec.md` format:**
```markdown
# 04 — Shared head

Depends on: 01, 03
Open questions: none

<!-- source: §4.2 Shared head -->
<text copied exactly from the master spec>
```

---

## 3. Build contracts

**Why.** A sub-spec copies the requirements word for word, but requirements leave choices open: which unit owns a config key, how two sections interact, what a function is called and what it raises. The implementer, the independent test writer and the two reviewers never talk to each other, so each settles those choices their own way, and every mismatch costs a full implement–test–review round. In one measured run, every item that forced a second round, and both test defects, came from such open choices. The contract settles them once, before any code, so all four build and judge the same thing.

**What's in `contract.md`** (each line cites its source: `§` spec section, `D` decision, `C` convention, `HO` handoff):

| Section | Holds |
|---|---|
| Scope | what the unit builds, what it must leave to which other unit, what can't be checked offline |
| Ownership | every config key and file in the excerpts: implements / consumes / carries, and the owning unit |
| Decisions | open questions and conflicts between sections, settled with you (`D1 [decided] (Q1) … → …`) |
| Interfaces | exact signatures, shapes, dtypes, units, errors, which existing function supplies each input, one `Example:` call per interface (the test writer's fixtures), and `Extends:` lines naming the earlier units' functions this unit changes |
| Acceptance checks | `AC1 [§6.1] given … when … then …` with literal values and tolerances — the definition of done; a `### Robustness` group holds one check per applicable hazard (`[HZ<n>]`), built in round 1 |
| Risks | the hazards from the register that apply to this unit, each with the required behaviour and its check |
| Incoming handoffs | obligations earlier units left for this one |
| Late decisions | anything decided during implementation, with its reason |

**Size.** A unit aims for at most 12 acceptance checks, 6 new public functions or classes and about 400 source lines; the check refuses more than 16 checks or 700 estimated source lines (`Estimated size:` in Scope), with no override. Bigger units are split; an extra small unit costs one short cycle, an oversized one costs whole extra rounds (on SCANIA the three units over 20 checks or 1,200 lines took 36% of all tokens).

**Lifecycle.**

```
/dev-0-split   writes contracts, CONVENTIONS.md, HANDOFFS.md; settles decisions with you
/dev-1-select  checks the contract, adds incoming handoffs, corrects input sources against built code
/dev-2-write   fixes the Interfaces (or the /dev-auto implementer does), records late decisions
/dev-3-test    the writer tests each acceptance check; the runner maps failures to them
/dev-4-review  reviewers treat decisions as binding and check the registered risks first
/dev-5-fix-review, /dev-auto   accepted findings that oblige a later unit become handoffs
/dev-6-final   closes this unit's handoffs, shows the contract's changes, commits it with the code
```

**`check_contracts.py`** enforces the structure in code, at three stages:
- `split`: every section present, no open decision, every header question answered, every tag resolving to a real section, decision, convention, hazard or handoff, the size within budget, `Extends:` lines naming real units, and the index in dependency order (every dependency a lower number).
- `start`: also every open handoff addressed to the unit is listed.
- `test`: also the interfaces are fixed.

**Already-split projects.** Run `/dev-0-split` again: it detects `spec/`, never re-splits, and writes the missing conventions, ledger and contracts for unfinished units. Along the way it collects the obligations that earlier units' accepted findings left for later ones.

---

## 4. Commands

| Step | Command | Model / effort | What it does | Next |
|---|---|---|---|---|
| spec | `/dev-spec [name or notes]` | Opus / high | Once per project, before the split, when you have an idea rather than a spec. Interviews you in batches, writes the API protocol (architecture, structural flow, layout, every public interface with an example, data contracts, configuration, conventions, extension sockets), then the complete spec whose sections are the future units — one concern each, at most 12 requirements, every section depending only on earlier ones — and checks it (budgets, ownership, acyclic dependencies). Writes no code. | `/dev-0-split` |
| 0 | `/dev-0-split [path]` | Opus / xhigh | Once per project. Splits the master spec into small, buildable sub-specs numbered in dependency order (most independent first), reading the API protocol alongside when there is one, copying cross-cutting sections (config, test tables) into the sub-specs they constrain. Finds open questions and conflicts between sections, and settles them with you in batches. Writes a contract per unit — interfaces with examples, robustness checks from the hazard register, `Extends:` lines — plus the conventions and handoff ledger. Two scripts prove the excerpts are verbatim and the contracts complete, then it offers a baseline commit. On an already-split project it upgrades instead. | `/dev-1-select NN` |
| 1 | `/dev-1-select NN` | session / low | **Select it.** Checks status, dependencies, the contract and a clean tree. Creates branch `subspec/NN-slug` and marks the row `in-progress`. Brings the contract up to date: incoming handoffs, input sources checked against the built code. Briefs you on scope, decisions, acceptance checks and risks. Writes no code. | `/dev-2-write NN` |
| 2 | `/dev-2-write NN` | Opus / high | **Write it.** Treats the contract as settled. Proposes the exact interfaces and a plan mapping every acceptance check to the code. **Writes code only after you approve.** Then it writes the interfaces into the contract and builds to the acceptance checks, with unit tests named after them. Never touches the independent verification file and never commits. Also continues the work after a failed test run. | `/dev-3-test NN` |
| 3 | `/dev-3-test NN` | session / medium | **Test it.** Requires fixed interfaces. The **writer** agent writes tests for each acceptance check from the contract alone; a hook stops it reading the changed files. The **runner** agent runs them and maps each failure to its acceptance check. Results go into `test-report.md` with a code fingerprint. | pass → `/dev-4-review NN`; not built or wrong behaviour → `/dev-2-write NN` |
| 4 | `/dev-4-review NN` | session / low | **Review it.** Both **reviewer** agents run in parallel against the sub-spec, the contract and the conventions. Each brief carries a budget: the compliance reviewer returns a table with one verdict per acceptance check and at most 10 findings; the pipeline reviewer starts from the contract's risks and the hazard register, returns at most 8, and skips limitations already recorded. After fixes, a **focused re-review** checks only the fixed findings and what changed since the last review. It falls back to a full review when the fix is large or changes an interface. Fixes nothing. | clean → `/dev-6-final NN`; any finding → `/dev-5-fix-review NN` |
| 5 | `/dev-5-fix-review NN` | session / high | **Work on the review.** Checks each finding against the code and the contract (code that follows a decision isn't a defect), proving runtime claims with a script. You decide **fix / accept / reject** for each finding. Fixes go to the root cause and come with a regression test. Accepted findings that oblige a later unit become handoffs. | anything fixed → `/dev-3-test NN`, then `/dev-4-review NN`; nothing fixed → `/dev-6-final NN` |
| 6 | `/dev-6-final NN` | session / medium | **Finalize it.** Refuses if the reports are missing or stale, or if a finding has no resolution. Closes the unit's incoming handoffs and shows what changed in its contract. Then, asking you before each step: commits, pushes, opens a PR or merges, marks the row `done`, deletes the branch, writes a log entry and records the unit in the usage ledger (cost by role, model and effort; rounds; first-run failures by class; findings). It is the only command that touches git history. | `/dev-1-select` for the next unblocked NN |
| auto | `/dev-auto NN` | Sonnet / medium | Steps 1–5 unattended, in up to 3 rounds plus at most one hardening round you choose at the end; see section 12. | `/dev-6-final NN` |
| retro | `/dev-retro [project]` | Opus / high | Every few units. Reads the ledger and the test reports, traces each extra round to its cause (spec gap, test defect, wrong behaviour, hardening, a bug introduced by a fix, cost without rounds), checks whether earlier changes worked, and proposes at most five edits to the commands, agents, templates or conventions. You approve each; approved ones are logged in `CHANGES.md` with the evidence. | — |
| any | `/dev-save` | session / low | Writes a handoff entry to `CLAUDE.local.md`: branch, last commit, uncommitted files, report status, what was done, decisions, open items and the exact `/dev-…` command to resume with. | the resume line |
| — | `/no-claude-footprint` | session / low | Gitignores Claude Code files and installs git hooks that block committing them or crediting Claude in commit messages. Reports any existing traces. | — |

`/dev-spec`, steps 0 to 6, `/dev-auto` and `/dev-retro` are **user-only** (`disable-model-invocation`): Claude never starts them on its own.

---

## 5. Agents

Each agent's tool access enforces its role, not just its instructions.

| Agent | Used by | Model / effort | Tools | Role |
|---|---|---|---|---|
| `spec-verification-writer` | step 3 | Sonnet / high · 40 turns | Read, Write, Edit, Grep, Glob; no shell, no CLAUDE.md; a hook refuses reads of the changed files | Test engineer. At least one test per acceptance check (`test_ac3_…`), from the sub-spec, contract and conventions only. Builds fixtures from the contract's `Example:` lines; takes names and defaults from the interface surface; never pins other units' defaults or signatures, faking them through `tests/stubs/`. Uses boundary, invariant, equivalence, prohibition and seeded statistical tests; expected values come from the contract and spec, never from calling the code. |
| `spec-verification-runner` | step 3 | Sonnet / medium · 25 turns | Read, Bash, Grep; no write, no CLAUDE.md | Runs the checks and the full suite. Classifies each failure as **not built / wrong behaviour / test defect / spec contradiction / environment**, by acceptance check. Code that doesn't match the contract's interfaces counts as wrong behaviour. Never alters a check. |
| `spec-compliance-reviewer` | step 4 | Sonnet / medium · 40 turns | Read, Grep, Glob; read-only | Traces every spec statement, acceptance check and handoff to the change: implemented, missing, mismatch, contradicts a decision, or **silently relaxed**. Returns a table with one verdict per acceptance check, then at most 10 findings. Treats contract decisions as binding and uses the ownership table for scope. Has a re-review mode. |
| `pipeline-risk-reviewer` | step 4 (full review) | Opus / high · 40 turns | Read, Grep, Glob; read-only | Senior ML reviewer. Checks the contract's registered risks and robustness checks first, then the hazard register, then follows data across functions looking for leakage, broken evaluation, train/eval-mode and MC-dropout bugs, gradient flow, unit and scaling errors, nondeterminism, and boundary and copy-on-write traps. At most 8 findings; no finding for a limitation the contract, the handoff ledger or the resolutions already record. |
| `pipeline-risk-reviewer-recheck` | step 4 (focused re-review) | Opus / high · 30 turns | Read, Grep, Glob; read-only | The same reviewer for re-reviews: confirms fixed findings are fixed at the root and the changed code adds no new silent bug. |
| `dev-implementer` | `/dev-auto` rounds 1–3 | Sonnet / high · 120 turns | Read, Write, Edit, Grep, Glob, Bash; a hook blocks the verification file | Fixes the contract's interfaces and their `Example:` lines first, then builds to the acceptance checks (robustness checks included) without asking; writes plain code a developer edits by hand and never reverts the user's own edits; updates `tests/stubs/` rather than locked tests; records late decisions and handoffs; never commits. |
| `dev-implementer-max` | `/dev-auto` round 3, defects only | Opus / xhigh · 60 turns | same as above | Escalation round, used only for failing checks or confirmed defects round 2 couldn't close, with at most 5 work items per launch: first works out why earlier fixes failed. |

---

## 6. Supporting pieces

| Piece | Location | Purpose |
|---|---|---|
| `check_contracts.py` | `dev-0-split/scripts/` | Enforces contract completeness at the `split`, `start` and `test` stages (section 3). |
| `check_fidelity.py` | `dev-0-split/scripts/` | Confirms every sub-spec excerpt is word for word from the master spec, and lists master text no sub-spec covers. |
| Templates | `dev-0-split/templates/` | `contract.md` (with `Example:`, `Extends:` and `### Robustness`), `CONVENTIONS.md` (11 conventions, including C9's `tests/stubs/` rule and C11 readability, plus the ML hazard register) and `HANDOFFS.md`. |
| `usage_ledger.py` | `scripts/` (skills reach it as `${CLAUDE_SKILL_DIR}/../../scripts/`) | Measures a unit's cost from the session transcripts by role, model and effort; records rows, stopped runs, findings and escapes; renders `~/.claude/workflow-metrics/LEDGER.md` (section 13). |
| `changeset.py` | `dev-3-test/scripts/` | Lists everything the branch changed since main (committed, uncommitted and new files; `spec/` excluded) and prints a **fingerprint**; `/dev-6-final` refuses if the code changed after test or review. `--snapshot` records the reviewed state as a git tree object (no commit, branch or index change), and `--since` diffs against it for the focused re-review. |
| `interface_surface.py` | `dev-3-test/scripts/` | Prints function and class signatures and constant names, with no bodies and no values. |
| `hooks/hooks.json` | plugin root | Registers the three hooks below in every session the plugin is enabled in. Plugin agents can't carry hooks of their own, so the two guards read `agent_type` from the hook input and act only inside the agent they protect. |
| Writer guard | `hooks/guard-writer-independence.py` | Refuses the test writer's reads of the files the change touched, while `/dev-3-test` has them listed. |
| Verification-file guard | `hooks/guard-verification-file.py` | Blocks the implementer agents' edits to `test_subspec_NN_*.py`. |
| Save reminder | `hooks/checkpoint-reminder.py` (Stop hook) | If `CLAUDE.local.md` is more than 20 minutes old and the repo has uncommitted changes, reminds you to run `/dev-save`. |
| Git hooks | `.git/hooks/pre-commit`, `commit-msg` | Installed by `/no-claude-footprint`. |

---

## 7. Models and effort

- **Session default** (`~/.claude/settings.json`): whatever you set with `/model` and `/effort`.
- **How the overrides work** (Claude Code docs):
  - A skill's `model` applies only to the turn it runs in. Switching model re-reads the whole conversation without the prompt cache, so the Opus steps (0 and 2) belong early in a session.
  - A skill's `effort` costs nothing in cache terms.
  - A subagent's model is separate from the main session, so the agents' models never cause a switch.
- **Why each choice:**
  - **Opus** where reasoning decides correctness: writing the spec (`/dev-spec`), splitting it and settling decisions (0), planning and writing the code (2), the ML pipeline review, and the retro.
  - **Opus at high, not xhigh, for the pipeline review:** across 19 units xhigh cost 27% of all tokens and fixed 18 of 104 findings; the budget and the register-first scope matter more than the extra depth.
  - **Sonnet for the `/dev-auto` coordinator:** it routes work and triages findings, and its own calls were 17% of each unit's cost, so it runs on the cheaper model in a fresh session.
  - **Session model** for steps that coordinate agents or follow fixed procedures (1, 3, 4, 6), with effort sized to the job.
  - **Session model at high effort** for fixing review findings (5). It is debugging work, and it runs late in a long session, where a model switch would be expensive.
  - **No `max` anywhere.** The docs say it tends to overthink; `xhigh` is used instead.
  - **The runner is Sonnet, not Haiku.** Sorting a failure into the wrong class sends you down the wrong path.
- **Pre-approved commands:** read-only git (`status`, `log`, `diff`, `branch`, `rev-parse`) in steps 1 and 3 to 6, plus `python` commands in steps 1, 3 and 4 (to run the framework's scripts), through `allowed-tools`, for the turn the command runs in. Other writes still ask.
- **Turn limits:** `maxTurns` caps every agent, so a stuck agent returns a partial report marked incomplete instead of running on.

---

## 8. Rules the framework enforces

1. **Decide before you build:** open questions and conflicts are settled in the contract before any code, and the contract check refuses to start a unit with an open decision.
2. **Foundation first:** `/dev-1-select` stops if a dependency isn't `done` or `pre-existing`.
3. **Plan before code:** `/dev-2-write` writes nothing until you approve its interfaces and plan.
4. **Independent verification:** tests come from the spec and contract, not the code; a hook keeps the test writer away from the changed files. Whoever runs the tests can't edit them, and the reviewers can't edit or execute anything.
5. **Every finding gets an answer:** each review finding is fixed, accepted with a reason, or rejected with evidence, and the answer is recorded. Obligations it leaves for later units go into the handoff ledger and must be closed before those units ship.
6. **Evidence over claims:** reports carry a fingerprint of the exact code they checked, and stale reports block the commit.
7. **Confirm every irreversible step:** commit, push, merge and branch deletion each need an explicit yes.
8. **No Claude Code footprint:** Claude files are gitignored and blocked, and commit messages and PRs never credit Claude.
9. **Small units, in dependency order:** the contract check refuses more than 16 acceptance checks or 700 estimated source lines per unit, and an index whose unit depends on a later number.
10. **Robustness in round 1:** every contract carries robustness checks from the hazard register, so hardening is built with the feature, not in a round after review.
11. **It keeps its own record:** every finished unit and every stopped run is measured into the ledger, and `/dev-retro` changes the workflow only from that evidence, with your approval.

---

## 9. Quick start

**New project**
1. `git init` (if needed), then `/no-claude-footprint`.
2. Put your finished spec in `Complete spec/`, or run `/dev-spec` in a fresh session to turn a brainstorm into the API protocol and the spec.
3. New session → `/dev-0-split` → confirm the split and build order → answer the decision questions → accept the baseline commit.
4. New session per sub-spec: `/rename NN-slug` → `/dev-1-select NN` → `/dev-2-write NN` → `/dev-3-test NN` → `/dev-4-review NN` → `/dev-5-fix-review NN` → `/dev-6-final NN`, or `/dev-auto NN` → `/dev-6-final NN`.
   - Step 5 is skipped when the review is clean.
   - Steps 3 → 4 → 5 repeat until nothing more is fixed.
   - Every command's last line tells you which step comes next.
5. Stopping early? `/dev-save`. In the next session, read the newest `Resume:` line in `CLAUDE.local.md` and run that command.
6. Every few units: `/dev-retro`. It reads the ledger and proposes changes to the workflow; you approve each.

**Project split before contracts existed:** start a session and run `/dev-0-split`. It upgrades the unfinished units, then continue as above.

---

## 10. Which command next?

| Situation | Run |
|---|---|
| New project, only an idea or notes | `/dev-spec` |
| New project, spec finished | `/dev-0-split` |
| Split project without `spec/CONVENTIONS.md` or contracts | `/dev-0-split` (upgrade) |
| `spec/INDEX.md` exists, nothing `in-progress` | `/dev-1-select NN` (lowest `not-started` row whose dependencies are `done`) |
| The contract check reports an open decision | `/dev-1-select NN` settles it with you |
| Branch created, no code yet | `/dev-2-write NN` (or `/dev-auto NN`) |
| Code written, `## Verification` says "not yet run" or is stale | `/dev-3-test NN` |
| Test failures classed `not built` or `wrong behaviour` | `/dev-2-write NN`, then `/dev-3-test NN` |
| Test failures classed `test defect` or `spec contradiction` | Decide with Claude (fix the check, or settle the spec), then `/dev-3-test NN` |
| Verification passes, `## Review` not yet run or stale | `/dev-4-review NN` |
| Review has findings without an entry in `## Review resolutions` | `/dev-5-fix-review NN` |
| Fixes applied in step 5 | `/dev-3-test NN`, then `/dev-4-review NN` (focused re-review) |
| Reports current, every finding resolved | `/dev-6-final NN` |
| Leaving mid-way | `/dev-save` |
| Three or more units finished since the last `CHANGES.md` entry | `/dev-retro` |
| Not sure where you are | Read `spec/INDEX.md`, the sub-spec's `test-report.md`, and the newest `Resume:` line in `CLAUDE.local.md` |

---

## 11. Sharing the framework

The repository is a Claude Code plugin and its own marketplace (`.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`). Anyone installs it with two commands and receives each release through `/plugin update`:

```
/plugin marketplace add nikhileshnarkhede/spec-driven-dev
/plugin install spec-driven-dev@nikhileshnarkhede
```

Requirements: git, Python 3 on the `PATH` as `python` (the hooks call it by that name), and the project's own test framework (pytest in the examples). `gh` is needed only to open PRs from `/dev-6-final`. The model choices assume access to Opus and Sonnet; with an organisation allowlist that excludes one of them, Claude Code ignores that override and keeps the session model.

To change the workflow itself, clone the repository, add the checkout as the marketplace (`/plugin marketplace add /path/to/checkout`), edit, run `/reload-plugins`, then bump `version` in `plugin.json`, add a `CHANGELOG.md` entry and tag a release. `/dev-retro` follows the same path when it changes a command.

---

## 12. Unattended mode: `/dev-auto NN`

One command runs steps 1 to 5 for a sub-spec without asking you anything during the rounds, in up to three rounds plus at most one hardening round you choose at the end, and stops before step 6. Start it in a fresh session: it refuses a session that already carries other work (`--here` overrides), because every coordinator call re-reads the whole conversation.

```
/dev-auto NN
  contract check (open decision? → stop: it's yours)
  select ─► round 1: dev-implementer (Sonnet/high) fixes interfaces + examples, builds (robustness checks included)
                     ─► test ─► full review* (budgeted) ─► decide
            round 2: dev-implementer (Sonnet/high) fixes  ─► test ─► focused re-review* ─► decide
            round 3: dev-implementer (Sonnet/high), or dev-implementer-max (Opus/xhigh) only for failing checks
                     or confirmed defects round 2 couldn't close; ≤5 work items per launch
  ─► hardening candidates? one question to you: fix now (one more round) or hand off
  ─► report ─► Next: /dev-6-final NN  (you)
  * review runs only when every test passes
```

- **It needs a complete contract.** With an open decision it stops and sends you to `/dev-1-select NN`. With no contract it recommends `/dev-0-split`; `--no-contract` runs the older way, where it settles questions itself.
- **Decisions it makes for you, all recorded in `test-report.md` and the contract:**
  - Confirmed findings of medium severity or worse are fixed. Low ones are fixed when they stay inside one function; otherwise they are accepted with a reason. Each fix stays inside its finding: no new guards or checks the finding didn't ask for.
  - A `fragile` finding covered by a robustness check or a contract risk is wrong behaviour and is fixed. One the register didn't anticipate becomes a hardening candidate: defined exactly, offered to you once at the end, and noted as a `Register candidate` for the next retro.
  - Findings that turn out not to be defects, including code that follows a contract decision, are rejected with evidence.
  - Anything neither the spec nor the contract settles goes into the contract's `## Late decisions` for you to confirm.
  - Obligations for later units go into `spec/HANDOFFS.md`.
- **Escalation:** Opus at xhigh is used only for failing checks or confirmed defects round 2 couldn't close; minor leftovers stay on Sonnet. If round 2 closes nothing, it jumps straight to round 3 instead of repeating the same model.
- **When it stops and asks for you:**
  - an open decision or a missing contract;
  - a real spec contradiction;
  - a missing environment piece;
  - a denied permission prompt;
  - work still left after round 3.
- **What it never does:**
  - commit the implementation, push or merge;
  - edit or loosen the independent tests. A hook blocks the implementer agents from editing `test_subspec_NN_*.py`.
- **Tokens:** reviews are skipped while tests fail, the verification file is written once and reused, rounds 2–3 use the focused re-review, the coordinator summarises agent reports instead of copying them, and a stopped run is recorded in the ledger so its cost isn't lost.
- **Run it in auto mode,** because any permission prompt stalls an unattended run.
- **Afterwards:** read the report's late decisions to confirm, then run `/dev-6-final NN`.

**Renamed from the earlier version:** `/split-spec` → `/dev-0-split`, `/create-subspec` → `/dev-1-select`, `/verify-subspec` → `/dev-3-test`, `/review-subspec` → `/dev-4-review`, `/lock-subspec` → `/dev-6-final`, `/checkpoint` → `/dev-save`. `/dev-2-write`, `/dev-5-fix-review` and `/dev-auto` are new.

## 13. The ledger, `/dev-retro` and `/dev-spec`

**Ledger.** `scripts/usage_ledger.py` reads the Claude Code session transcripts and attributes every model call made while a unit was built: by role (coordinator, implementer, writer, runner, each reviewer), model and effort, weighted into comparable cost units (Fable 2.5, Opus 1, Sonnet 0.6, Haiku 0.2 on input; cache write ×1.25, cache read ×0.1, output ×5). `/dev-6-final` records one row per finished unit — mode, rounds, the first verification run and its failures by class, test defects, why each extra round happened, finding counts, lines and acceptance checks, cost by phase — and `/dev-auto` records stopped runs. `~/.claude/workflow-metrics/LEDGER.md` renders it all, with a reviewer-yield table (raised / fixed / accepted / rejected and cost per fixed finding) and an escapes table (defects and couplings found after a unit closed).

**Retro.** `/dev-retro` traces every round after the first to its cause — spec gap, test defect, wrong behaviour, hardening, a bug introduced by a fix, or cost without rounds — counts the causes across units, checks whether earlier changes worked, and proposes at most five edits to the commands, agents, templates or conventions, each with its expected effect and its risk. You approve each; approved changes are logged in `CHANGES.md` with the evidence and the units to check them against.

**What the first 25 units taught.** Verification became nearly one-pass once contracts existed (median one failing check, mostly fixture misreads by the writer). The extra rounds came from review findings and from a hardening round chosen after review in almost every unit; review was a third of all cost; three oversized units took a third more; most escapes were a later unit's contract breaking an earlier unit's locked test file. The current rules follow from that: robustness checks are written into the contract at split time and built in round 1; reviewers have budgets and skip limitations already recorded; the contract check refuses more than 16 acceptance checks or 700 estimated source lines, and refuses an index that isn't in dependency order; interfaces carry an `Example:` line the writer builds fixtures from and `Extends:` lines naming the earlier functions a unit changes; stubs for other units' interfaces live in `tests/stubs/`, so a legitimate change updates a stub instead of a locked file.

**Spec.** `/dev-spec` sits before the split: it interviews you, writes an API protocol (architecture, structural flow, every public interface with an example, data contracts, configuration, conventions, extension sockets) and then a complete spec whose sections are the future units — one concern each, at most 12 requirements, ordered so that every section depends only on earlier ones — and checks the result before handing it to `/dev-0-split`.

