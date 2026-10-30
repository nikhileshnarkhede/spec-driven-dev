---
name: dev-0-split
description: Step 0 (once per project) — break one complete spec into small, buildable sub-specs under spec/, each with a build contract (scope, decisions, interfaces, acceptance checks, risks) so every later step builds and tests the same thing; plus project conventions and a handoff ledger. On a project that is already split, it upgrades instead — writes the missing contracts without re-splitting.
argument-hint: "[master-spec.md]"
disable-model-invocation: true
model: opus
effort: xhigh
---

Work as a requirements architect preparing work for a team that never talks to each other: an implementer, an independent test writer and two reviewers will each read your output separately. Your goal is that all four build and judge exactly the same thing, so a sub-spec passes its tests and reviews in one round.

Extra rounds come almost entirely from what a sub-spec leaves open. When the requirements don't settle a choice, the implementer guesses one way, the test writer another and a reviewer a third, and each mismatch costs a full implement–test–review cycle. Every decision you settle here, while the whole spec is in view, is a cycle saved later. Small units help for the same reason: fewer moving parts, fewer guesses, a shorter review.

This skill runs on Opus at xhigh effort (this file's frontmatter), which has two consequences:
- The override lasts only for the current turn; the session's own model and effort return on the user's next typed prompt. Do the whole job — analyse, decide, write, verify, commit — in this one turn, taking every answer through the AskUserQuestion tool, whose answer arrives inside the turn. A plain-text question would end the turn, and the files would then be written by the session's model.
- When the session isn't already on Opus, this turn is a model switch that re-reads the whole conversation without the prompt cache, so it belongs at the start of a session.

Requested spec path (may be empty): $ARGUMENTS

## 1. Locate the spec and choose the mode

Use the requested path if one was given; otherwise the `.md` file in `Complete spec/` at the project root. If that folder is missing or empty, tell the user to put their finished spec there and stop. If it holds more than one `.md`, ask which is current — except a companion `<name>-api-protocol.md` written by `/dev-spec`, which is not a second spec: read it alongside, and fix contract interfaces from it. Never modify `Complete spec/`; it stays the canonical record.

- **New split** — `spec/` doesn't exist: do every step below.
- **Upgrade** — `spec/` exists: never re-split, never edit a `sub-spec.md`, never touch a unit that is `done` or `pre-existing`. Write `spec/CONVENTIONS.md` and `spec/HANDOFFS.md` if missing, and a `contract.md` for every unfinished unit that lacks one or fails the contract check. Skip step 3. Say which mode you are in before starting.

Templates for the three new files are in `${CLAUDE_SKILL_DIR}/templates/`.

## 2. Analyse

Read the whole spec (in upgrade mode also every unfinished `sub-spec.md`, the `test-report.md` of every done unit, and the project's `CLAUDE.local.md`), then work out:

- **Units of work.** One concern each, behind a clear interface, small enough to build in one pass: aim for at most 12 acceptance checks, 6 new public functions or classes and about 400 source lines, with hard limits of 16 checks and 700 estimated source lines that the contract check enforces without override (on SCANIA the three units over 20 checks or 1,200 lines took 36% of all tokens). Headings are a starting point, not the answer. Split a large section along its own seams. Build a socket or plug-in framework separately from its first plug-in, and for a family of interchangeable components, build the shared contract plus one reference implementation first, then each further one as its own unit. Merge small sections that can't be verified apart. When in doubt, prefer two small units to one large one: an extra unit costs one short cycle, an oversized one costs whole extra rounds.
- **Cross-cutting sections.** Configuration listings, test or acceptance tables, glossaries, layout trees and build-order sections constrain many units rather than being buildable themselves. Don't make them sub-specs. Copy the relevant part of each into every sub-spec it constrains, so each sub-spec is self-contained.
- **Dependencies.** Unit B depends on unit A when B consumes something A defines — a data contract, an interface, an output format — and so can't be implemented or verified without it. Being related or adjacent isn't a dependency.
- **Build order.** Strictly by dependency: a unit's dependencies always carry lower numbers (topological sort, most independent first). The spec's own build order, milestones or phases break ties between independent units and nothing more; where the spec's order contradicts a dependency, say so and follow the dependency. The contract check refuses an index in which a unit depends on a later number.
- **Ownership.** Give every config key and every requirement exactly one owning unit. Other units that mention it either consume it (read it, depend on its behaviour) or carry it (it appears in their excerpts but they must not act on it). A key that sits in a unit's excerpts with no clear role there is a decision to settle.
- **Open questions.** Explicit open questions, CHECK or TODO markers, values marked required but left unset, and statements that contradict each other — each attached to the unit it blocks.
- **Interactions between sections.** For each unit, find the statements in *other* sections that touch the same value, data or metric, and check they are compatible. These conflicts are invisible when each section is read alone, and they are what reviewers find. Typical cases:
  - an ablation compared on a metric that includes the term being ablated;
  - a feature toggle next to a plug-in or derived feature that reads the features;
  - a value fitted or scaled in one unit and consumed in another in different units;
  - an experiment override that leaves another setting free to change between the two runs being compared;
  - a default that makes a gate in another section fail.
- **What the spec leaves to the implementer.** List the choices an implementer would otherwise guess: names and signatures where the spec gives none, which existing function supplies each input, error types, tie-breaking, numeric conventions, file locations, what happens on empty or degenerate input. Project-wide choices become conventions; unit-specific ones become decisions or acceptance checks.
- **Existing work.** Look for evidence that some units are already built: the `CLAUDE.local.md` log, or code that clearly implements a unit. Propose `pre-existing` only for units that look fully built, citing the evidence; a partly built unit stays `not-started` with a note on what exists. In upgrade mode, also collect **handoffs**: every accepted finding, resolution line or log entry in a done unit that obliges a later unit to do something ("05 must…", "note for 09", "handoff to …").

## 3. Propose and confirm the split (new split only)

Print the proposal as text: the units in build order, each with a one-line description, the spec sections it draws on (cross-cutting excerpts included), its dependencies, its estimated number of acceptance checks and source lines, and its proposed status. Note any disagreement with the spec's own build order, and list the spec text you intend to leave out (title, purpose, background). Confirm through AskUserQuestion; on adjustments, re-propose and ask again.

In upgrade mode, an unfinished unit over a hard limit is split into lettered units (`13a`, `13b`) with the user's agreement — done units keep their numbers, and each letter unit's dependencies must still come earlier in the index; redistribute its excerpts verbatim and update `INDEX.md`. There is no size override.

## 4. Settle the decisions with the user

Collect every open question, every interaction conflict, every unclear ownership, and every implementer choice that changes observable behaviour. Then:
- Ask in batches through AskUserQuestion: up to 4 questions per call, 2–4 options each, your recommendation first and labelled "(Recommended)", and a one-line consequence per option. Continue until nothing is open.
- Decide yourself only choices with no observable behaviour (file names inside a package, private helper structure); record them as `By: splitter (no behaviour change)`.
- A decision may be deferred only with a default and an owner unit (`[deferred] … → default: …; owner: NN`).
- Propose the conventions: in a project with code, derive them from two or three representative modules and the decisions in `CLAUDE.local.md`; otherwise start from the template. Confirm in one question, listing what you changed from the template and why.

## 5. Write

**Sub-specs (new split only).** Number units in the confirmed dependency order, zero-padded (`01`, `02`, …), so every `Depends on` entry is a lower number. For each, create `spec/NN-slug/` (`slug` is short kebab-case) containing:

`sub-spec.md` — a short header, then verbatim excerpts, each under a marker naming its source section:

```markdown
# NN — <title>

Depends on: <NN, NN or none>
Open questions:
- §x.y — <question>

<!-- source: §5.2 LSTM -->
<excerpt copied exactly from the master spec>
```

With no open questions, the header line reads `Open questions: none`. Everything after a `<!-- source: … -->` marker must match the master spec character for character — no summarising, rewording or reformatting — because a lossy copy becomes a silent spec change for everything downstream. A partial excerpt from inside a code block may be wrapped in its own fence for readability.

`test-report.md`:

```markdown
# Test report — sub-spec NN: <title>

## Verification
_not yet run_

## Review
_not yet run_
```

Then `spec/INDEX.md`:

```markdown
# Sub-spec index

| # | Title | Folder | Depends on | Status |
|---|---|---|---|---|
| 01 | <title> | spec/01-<slug>/ | none | not-started |
```

`Depends on` in the index mirrors each sub-spec header. Status starts as `not-started`, or `pre-existing` where the user confirmed it. After this, only `/dev-1-select` (to `in-progress`) and `/dev-6-final` (to `done`) change statuses.

**`spec/CONVENTIONS.md`** from the template, as confirmed in step 4. Keep the `C<n>` and `HZ<n>` numbering; drop hazards that can't occur in this project, and add project-specific ones.

**`spec/HANDOFFS.md`** from the template. In upgrade mode, add one row per collected handoff: `open` if the receiving unit isn't built yet, `done (NN, how)` if a later done unit already did it (check its code), `dropped (reason)` if the spec no longer needs it. An obligation that belongs to the user rather than a unit becomes a decision in the unit that owns the topic; if no unit owns it, list it in the report.

**`spec/NN-slug/contract.md`** for every unfinished unit, from the template:
- **Scope**: what the unit builds, what it must not build (with the owning unit), and any statement that can't be checked offline, with the reason. End it with `Estimated size: ~N source lines` (tests excluded; the check refuses more than 700).
- **Ownership**: every config key and file in the unit's excerpts, with its role here.
- **Decisions**: everything from step 4 for this unit. A decision that answers the k-th header question cites `(Qk)`.
- **Interfaces**: fix them now where the spec or the API protocol names them, each with one `Example:` line (literal call → literal result or shape) that the test writer turns into a fixture. Otherwise keep the `TO BE FIXED AT START` line; the start of the unit fixes exact signatures against the code that exists by then. List every earlier unit's function this unit changes or extends as an `Extends:` line (`- Extends: pkg.mod.fn (NN) — <what changes>`, the function name in backticks): that is where locked tests break, and the select step plans the stub updates from it. In upgrade mode, name the existing functions that supply each input, from the code of the done units.
- **Acceptance checks**: one per falsifiable behaviour, concrete enough to become a test without guessing — given/when/then with literal values, the tolerance, the error type and message content, and where each input comes from. Cover every falsifiable statement in the sub-spec and every behaviour-changing decision; fold the spec's own test-table rows in rather than repeating them. Tag each with its source: `[§x.y]`, `[D<n>]`, `[C<n>]`, `[HZ<n>]` (a hazard it proves is handled) or `[HO-<n>]`.
- **Robustness checks**: under a `### Robustness` heading inside Acceptance checks, one check tagged `[HZ<n>]` for every hazard in the register that applies to this unit — stale outputs, provenance, invalid or empty input, NaN in padding, and whatever else the register names. They count toward the size limit and are built in round 1 with everything else. On SCANIA, 18 of 19 units spent an extra round and about an eighth of all tokens adding exactly these after review.
- **Risks**: only the hazards from the register that genuinely apply to this unit, each with the required behaviour and the acceptance check that proves it.
- **Incoming handoffs**: the open rows of `HANDOFFS.md` addressed to this unit, each mapped to the acceptance check that discharges it.

Keep contracts short and plain: the fewest words that leave nothing to guess. A contract longer than its sub-spec usually means the unit should be split.

## 6. Verify

```
python "${CLAUDE_SKILL_DIR}/scripts/check_fidelity.py" "<master spec path>" spec
python "${CLAUDE_SKILL_DIR}/scripts/check_contracts.py" spec --stage split
```

The first checks that every excerpt is an exact substring of the master spec and lists master text no sub-spec covers (new split, or after a lettered split in upgrade mode). Re-copy every `NOT VERBATIM` excerpt and re-run until it reports no problems; then read each uncovered range — anything stating a requirement must land in a sub-spec.

The second checks every unfinished unit's contract: all sections present, no open decision, every header question decided, every source tag resolving to a real section, decision, convention, hazard or handoff, the size within budget, and the index in dependency order. Fix every ERROR and re-run until it exits cleanly; a size error is fixed by splitting, never overridden.

## 7. Baseline commit

Sub-spec branches must start from a main branch that already contains `spec/` and `Complete spec/`; otherwise every `/dev-1-select` trips over untracked files. Run the `no-claude-footprint` skill, then offer through AskUserQuestion a commit on the main branch: `Complete spec/` and `spec/` for a new split; `spec/CONVENTIONS.md`, `spec/HANDOFFS.md`, the new contracts and any `INDEX.md` change for an upgrade. If uncommitted work exists for units the user marked `pre-existing`, offer to include it, in the same commit or a separate one. Stage paths by name, show `git status` before committing, and write the message in the project's own style with no attribution line.

## 8. Report

- The units, each with its number of acceptance checks and decisions.
- The decisions: how many the user made, how many you made as no-behaviour choices, and every deferred one with its default and owner.
- Handoffs recorded (upgrade mode), and any user-level item that no unit owns.
- The fidelity and contract-check results, the framing text left out on purpose, and the commit (or that it was declined).

Don't start implementing — that's the user's call. End with `Next: /dev-1-select NN` (or `/dev-auto NN`) for the first unit that is `not-started` with all dependencies met.
