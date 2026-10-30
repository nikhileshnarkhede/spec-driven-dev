"""Check build contracts are complete before work starts.

  check_contracts.py SPEC_DIR [--unit NN] [--stage split|start|test]

  split  (default) every unit that isn't done or pre-existing: contract present, all sections,
         no open decision, every header question decided, every tag resolves, size within budget
         (at most 16 acceptance checks and 700 estimated source lines, no override), Extends lines
         naming real units; and the index in dependency order (every dependency a lower number).
  start  as split, and every open handoff addressed to the unit is listed in its contract.
  test   as start, and the Interfaces section is fixed (no placeholder left).

Prints ERROR / WARN lines and a summary per unit; exits 1 if there is any ERROR.
"""
import argparse
import re
import sys
from pathlib import Path

SECTIONS = ["Scope", "Ownership", "Decisions", "Interfaces", "Acceptance checks",
            "Risks", "Incoming handoffs", "Late decisions"]
PLACEHOLDER = "TO BE FIXED AT START"
AC_TARGET, AC_LIMIT, SRC_LIMIT = 12, 16, 700
FINISHED = {"done", "pre-existing"}

DECISION = re.compile(r"^- (D\d+) \[(decided|open|deferred)\]\s*(.*)$")
AC_LINE = re.compile(r"^- (AC\d+) \[([^\]]+)\]\s*(\S.*)$")
RISK_LINE = re.compile(r"^- (R\d+) \[(HZ\d+)\]\s*(\S.*)$")
CONVENTION = re.compile(r"^- (C\d+)\b")
HAZARD = re.compile(r"^- (HZ\d+)\b")
EXTENDS = re.compile(r"^- Extends:\s*`([^`]+)`\s*\((\d+[a-z]?)\)")
SIZE_LINE = re.compile(r"^- Estimated size:\s*~?\s*(\d[\d,]*)\s*source lines", re.MULTILINE | re.IGNORECASE)
HANDOFF_ROW = re.compile(r"^\|\s*(HO-\d+)\s*\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|\s*$")
TAG = re.compile(r"^(§.+|D\d+|C\d+|HZ\d+|HO-\d+)$")
QUESTION_REF = re.compile(r"\bQ(\d+)\b")


class Report:
    def __init__(self) -> None:
        self.errors = self.warnings = 0

    def error(self, unit: str, message: str) -> None:
        self.errors += 1
        print(f"ERROR  {unit:<4} {message}")

    def warn(self, unit: str, message: str) -> None:
        self.warnings += 1
        print(f"WARN   {unit:<4} {message}")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def index_rows(spec_dir: Path) -> list[dict]:
    rows = []
    for line in read(spec_dir / "INDEX.md").split("\n"):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 5 and re.fullmatch(r"\d+[a-z]?", cells[0]):
            rows.append({"nn": cells[0], "title": cells[1], "folder": cells[2].rstrip("/"),
                         "depends": re.findall(r"\d+[a-z]?", cells[3]) if cells[3].lower() != "none" else [],
                         "status": cells[4].lower()})
    return rows


def order_key(nn: str) -> tuple[int, str]:
    """Sort key for unit numbers: 7 < 07a < 07b < 8."""
    m = re.fullmatch(r"(\d+)([a-z]?)", nn)
    return (int(m.group(1)), m.group(2)) if m else (10**9, nn)


def check_index_order(rows: list[dict], report: Report) -> None:
    """Every dependency must come earlier in the index: units are numbered in dependency order."""
    known = {r["nn"] for r in rows}
    for row in rows:
        for dep in row["depends"]:
            if dep not in known:
                report.error(row["nn"], f"depends on {dep}, which is not in INDEX.md")
            elif order_key(dep) >= order_key(row["nn"]):
                report.error(row["nn"], f"depends on {dep}, which comes later in the index: number units in dependency order")


def sections(text: str) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    current = None
    for line in text.split("\n"):
        if line.startswith("## "):
            current = line[3:].strip()
            found[current] = []
        elif current is not None:
            found[current].append(line)
    return found


def header_questions(sub_spec: str) -> int:
    lines = sub_spec.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("Open questions:"):
            rest = line.split(":", 1)[1].strip().lower()
            if rest and rest.startswith("none"):
                return 0
            count = 0
            for nxt in lines[i + 1:]:
                if nxt.startswith("- "):
                    count += 1
                elif nxt.strip() == "" or not nxt.startswith(" "):
                    break
            return count
    return 0


def ids(text: str, pattern: re.Pattern) -> set[str]:
    return {m.group(1) for line in text.split("\n") if (m := pattern.match(line))}


def handoff_ledger(path: Path, report: Report) -> dict[str, dict]:
    ledger = {}
    for line in read(path).split("\n"):
        m = HANDOFF_ROW.match(line.strip())
        if not m:
            continue
        hid, src, dst, obligation, status = (g.strip() for g in m.groups())
        state = status.split()[0].lower() if status else ""
        if state not in {"open", "done", "dropped"}:
            report.error("HO", f"{hid}: status must start with open, done or dropped (got '{status}')")
        ledger[hid] = {"from": src, "to": set(re.findall(r"\d+[a-z]?", dst)), "status": state}
    return ledger


def check_unit(row: dict, root: Path, stage: str, conventions: set[str], hazards: set[str],
               ledger: dict[str, dict], report: Report, index_units: set[str] = frozenset()) -> None:
    nn = row["nn"]
    errors_before = report.errors
    folder = root / row["folder"]
    contract_path = folder / "contract.md"
    if not contract_path.is_file():
        report.error(nn, f"no contract.md in {row['folder']}/ (run /dev-0-split to write it)")
        return
    contract = read(contract_path)
    parts = sections(contract)
    for name in SECTIONS:
        if name not in parts:
            report.error(nn, f"missing section '## {name}'")
    body = {name: "\n".join(parts.get(name, [])) for name in SECTIONS}

    if not any(l.startswith("- ") for l in parts.get("Scope", [])):
        report.error(nn, "Scope lists nothing")
    size = SIZE_LINE.search(body["Scope"])
    if size is None:
        report.warn(nn, "Scope has no 'Estimated size: ~N source lines' line")
    elif int(size.group(1).replace(",", "")) > SRC_LIMIT:
        report.error(nn, f"estimated size {size.group(1)} source lines (limit {SRC_LIMIT}): split the unit")
    for line in parts.get("Interfaces", []):
        m = EXTENDS.match(line)
        if m and index_units and m.group(2) not in index_units:
            report.error(nn, f"Extends `{m.group(1)}` names unit {m.group(2)}, which is not in INDEX.md")
    ownership = [l for l in parts.get("Ownership", []) if l.startswith("|") and not re.match(r"^\|[\s|:-]+\|$", l)]
    if "Ownership" in parts and len(ownership) < 2 and "none" not in body["Ownership"].lower():
        report.error(nn, "Ownership has no rows (write '- none' if the unit owns no config keys)")

    decisions = {}
    for line in parts.get("Decisions", []):
        if line.startswith("- "):
            m = DECISION.match(line)
            if not m:
                report.error(nn, f"decision not in '- D<n> [decided|open|deferred] …' form: {line[:70]}")
                continue
            did, state, text = m.groups()
            if did in decisions:
                report.error(nn, f"duplicate decision id {did}")
            decisions[did] = (state, text)
            if state == "open":
                report.error(nn, f"{did} is still open: {text[:70]}")
            if state == "deferred" and not ("default:" in text and "owner:" in text):
                report.error(nn, f"{did} is deferred without 'default:' and 'owner:'")
            owner = re.search(r"owner:\s*(\d+[a-z]?)\b", text)
            if state == "deferred" and owner and stage in {"start", "test"} \
                    and owner.group(1).lstrip("0") == nn.lstrip("0"):
                report.error(nn, f"{did} was deferred to this unit: decide it now — {text[:70]}")
    sub_spec = folder / "sub-spec.md"
    asked = header_questions(read(sub_spec)) if sub_spec.is_file() else 0
    answered = {int(q) for _, text in decisions.values() for q in QUESTION_REF.findall(text)}
    for q in range(1, asked + 1):
        if q not in answered:
            report.error(nn, f"open question Q{q} in the sub-spec header has no decision referencing (Q{q})")

    checks = []
    for line in parts.get("Acceptance checks", []):
        if not line.startswith("- "):
            continue
        m = AC_LINE.match(line)
        if not m:
            report.error(nn, f"check not in '- AC<n> [source] …' form: {line[:70]}")
            continue
        acid, tags, _ = m.groups()
        if acid in checks:
            report.error(nn, f"duplicate check id {acid}")
        checks.append(acid)
        for tag in (t.strip() for t in re.split(r"[,;]", tags)):
            if not TAG.match(tag):
                report.error(nn, f"{acid}: source tag '{tag}' is not §…, D<n>, C<n>, HZ<n> or HO-<n>")
            elif tag.startswith("HZ") and tag not in hazards:
                report.error(nn, f"{acid}: cites {tag}, which is not in CONVENTIONS.md")
            elif tag.startswith("D") and tag not in decisions:
                report.error(nn, f"{acid}: cites {tag}, which is not in Decisions")
            elif tag.startswith("C") and tag not in conventions:
                report.error(nn, f"{acid}: cites {tag}, which is not in CONVENTIONS.md")
            elif tag.startswith("HO-") and tag not in ledger:
                report.error(nn, f"{acid}: cites {tag}, which is not in HANDOFFS.md")
    if not checks:
        report.error(nn, "no acceptance checks")
    if len(checks) > AC_LIMIT:
        report.error(nn, f"{len(checks)} acceptance checks (limit {AC_LIMIT}, no override): split the unit")
    elif len(checks) > AC_TARGET:
        report.warn(nn, f"{len(checks)} acceptance checks (target {AC_TARGET}); consider splitting")

    for line in parts.get("Risks", []):
        if line.startswith("- ") and not line.lower().startswith("- none"):
            m = RISK_LINE.match(line)
            if not m:
                report.error(nn, f"risk not in '- R<n> [HZ<n>] …' form: {line[:70]}")
            elif m.group(2) not in hazards:
                report.error(nn, f"{m.group(1)}: cites {m.group(2)}, which is not in CONVENTIONS.md")

    if stage in {"start", "test"}:
        incoming = body["Incoming handoffs"]
        for hid, entry in ledger.items():
            if entry["status"] == "open" and nn.lstrip("0") in {t.lstrip("0") for t in entry["to"]} \
                    and hid not in incoming:
                report.error(nn, f"open handoff {hid} (from {entry['from']}) is addressed here but not listed")
    if stage == "test":
        interfaces = body["Interfaces"]
        if PLACEHOLDER in interfaces:
            report.error(nn, "Interfaces still say 'TO BE FIXED AT START': fix the signatures before tests are written")
        elif not re.search(r"`[^`]*\([^`]*`", interfaces):
            report.error(nn, "Interfaces has no signature in backticks, e.g. `pkg.mod.fn(x: int) -> float`")

    verdict = "OK" if report.errors == errors_before else "FAIL"
    print(f"{verdict:<6} {nn:<4} {len(checks)} acceptance checks, {len(decisions)} decisions")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("spec_dir")
    parser.add_argument("--unit", help="check only this sub-spec number")
    parser.add_argument("--stage", choices=["split", "start", "test"], default="split")
    args = parser.parse_args()

    spec_dir = Path(args.spec_dir)
    root = spec_dir.resolve().parent
    report = Report()
    if not (spec_dir / "INDEX.md").is_file():
        report.error("--", f"no {spec_dir}/INDEX.md")
        return 1

    conventions = hazards = set()
    conv_path = spec_dir / "CONVENTIONS.md"
    if conv_path.is_file():
        text = read(conv_path)
        conventions, hazards = ids(text, CONVENTION), ids(text, HAZARD)
        if not conventions:
            report.error("--", "CONVENTIONS.md has no '- C<n> …' entries")
    else:
        report.error("--", "no spec/CONVENTIONS.md")
    ledger_path = spec_dir / "HANDOFFS.md"
    ledger = handoff_ledger(ledger_path, report) if ledger_path.is_file() else {}
    if not ledger_path.is_file():
        report.error("--", "no spec/HANDOFFS.md")

    rows = index_rows(spec_dir)
    check_index_order(rows, report)
    index_units = {r["nn"] for r in rows}
    if args.unit:
        rows = [r for r in rows if r["nn"].lstrip("0") == args.unit.lstrip("0")]
        if not rows:
            report.error(args.unit, "not in INDEX.md")
    else:
        rows = [r for r in rows if r["status"] not in FINISHED]
    for row in rows:
        check_unit(row, root, args.stage, conventions, hazards, ledger, report, index_units)

    print(f"\n{len(rows)} units checked at stage '{args.stage}': {report.errors} errors, {report.warnings} warnings")
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
