# NN — <title>: build contract

Sub-spec: `spec/NN-<slug>/sub-spec.md` holds the requirements, word for word. This file settles everything the requirements leave open, so the implementer, the test writer and both reviewers build and judge the same thing. Every line cites its source: a spec section (§), a decision (D), a convention (C), a hazard (HZ) or a handoff (HO).

## Scope
- Builds: <one line per deliverable>
- Out of scope: <item> → <owning sub-spec NN>
- Not checkable offline: <statement> — <reason>   (omit the line if there is none)
- Estimated size: ~<N> source lines (tests excluded; at most 700)

## Ownership
| Item (config key, file, statement) | Role here | Owner |
|---|---|---|
| `<CONFIG_KEY>` | implements / consumes / carries | NN |

## Decisions
- D1 [decided] (Q1) <the question, in one line> → <the answer>. By: user, YYYY-MM-DD.
- D2 [decided] <implementation choice with no visible behaviour> → <choice>. By: splitter (no behaviour change).
- D3 [deferred] <question> → default: <value>; owner: NN; revisit when <trigger>.

## Interfaces
TO BE FIXED AT START — replaced with exact signatures before any code is written (by /dev-1-select, /dev-2-write, or the /dev-auto implementer). Where the spec names an interface, it is fixed here already.
- `<package.module.function>(<arg>: <type>, …) -> <type>` — <what it does>. Shapes, dtypes, units: … Raises: `ValueError` when … Inputs from: `<existing.module.function>(…)["<key>"]`. Example: `function(<literal args>)` → <literal result or shape>.
- Extends: `<earlier.module.function>` (NN) — <what this unit changes or adds>   (one line per earlier unit's function this unit changes; omit if none)

## Acceptance checks
- AC1 [§x.y] Given <setup with literal values>, when <call>, then <observable result> (tolerance <t>).
- AC2 [D1] …
- AC3 [C2] …

### Robustness
- AC4 [HZ<n>] Given <the hazard constructed with literal values>, when <call>, then <raises `ValueError` naming … | output unchanged | …>.   (one per hazard that applies; built in round 1 with the rest)

## Risks
- R1 [HZ<n>] <how this hazard shows up in this unit> → required: <behaviour>; checked by AC<n>.

## Incoming handoffs
- none

## Late decisions
- none yet. Decisions made during implementation go here, each with its reason and the spec text it interprets.
