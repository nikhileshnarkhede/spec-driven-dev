"""Workflow usage ledger: measure what one sub-spec cost, and keep the record across projects.

Reads Claude Code session transcripts (~/.claude/projects/*/*.jsonl and their subagents/),
attributes every model call made while the unit was being built, and stores one record per
(project, unit) in ~/.claude/workflow-metrics/ledger.jsonl. LEDGER.md is regenerated from it.

    python usage_ledger.py record --repo . --unit 06 --mode auto --rounds 3 --first-run 66/0/0 \
        --test-defects 0 --findings fixed=9,accepted=6,handed_off=5,rejected=2 \
        --causes fragile=2 --note "..."
    python usage_ledger.py render

Window: from the last `/dev-1-select NN` or `/dev-auto NN` before the `start NN` commit (else the
commit minus 10 min) until now, or `--since/--until` (UTC ISO). Sessions: those that ran a dev
command for NN in the window, plus the most recently written session of this repo, or `--session`.
Only calls whose working directory is inside the repo count.

Cost units weight tokens by price ratios so different models compare: Fable 2.5, Opus input = 1, Sonnet 0.6,
Haiku 0.2; cache write x1.25, cache read x0.1, output x5. Relative, not a bill.
"""
import sys
import argparse
import json
import re
import subprocess
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

HOME = Path.home() / ".claude"
OUT = HOME / "workflow-metrics"
# Relative weights by model family (Opus 5.5 input = 1). Fable 5.1 lists at $10/$50 per MTok vs Opus 5.5 $4/$20,
# so 2.5; Sonnet and Haiku keep the weights the first rows were measured with, for continuity. Unknown
# families count at 1.0 rather than being dropped.
PRICE = {"mythos": 2.5, "fable": 2.5, "opus": 1.0, "sonnet": 0.6, "haiku": 0.2, "other": 1.0}
FIELDS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")
DEV_CMD = re.compile(r"<command-name>/(dev-[\w-]+)</command-name>.*?<command-args>([^<]*)</command-args>", re.S)


def iso(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, encoding="utf-8").stdout.strip()


def commit(repo, pattern):
    """(sha, utc iso) of the newest commit whose subject matches pattern, or (None, None)."""
    for line in git(repo, "log", "--all", "--format=%h %cI %s").splitlines():
        sha, when, subject = line.split(" ", 2)
        if re.match(pattern, subject, re.I):
            return sha, iso(datetime.fromisoformat(when))
    return None, None


def in_repo(cwd, repo):
    return bool(cwd) and str(Path(cwd).resolve()).lower().startswith(str(repo).lower())


def family(model):
    """Model family for pricing; None for synthetic/empty models, "other" for an unknown real model."""
    if not model or model.startswith("<"):
        return None
    return next((k for k in PRICE if k != "other" and k in model), "other")


def read(path):
    for line in path.open(encoding="utf-8", errors="replace"):
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def calls(path, lo, hi, repo, role):
    """{message id: call} for assistant calls in [lo, hi) made inside the repo."""
    out = {}
    for d in read(path):
        m = d.get("message")
        ts = (d.get("timestamp") or "")[:19]
        if d.get("type") != "assistant" or not isinstance(m, dict) or not lo <= ts < hi:
            continue
        if not in_repo(d.get("cwd"), repo) or family(m.get("model")) is None:
            continue
        mid = m.get("id") or d.get("uuid")
        u = m.get("usage") or {}
        prev = out.get(mid, {"usage": dict.fromkeys(FIELDS, 0)})["usage"]
        out[mid] = {"role": role, "model": m["model"], "effort": d.get("effort") or "?",
                    "usage": {k: max(prev[k], u.get(k) or 0) for k in FIELDS}}
    return out


def task_text(path):
    """First 100 characters of the prompt a subagent was launched with."""
    for d in read(path):
        if d.get("type") == "user":
            c = d.get("message", {}).get("content")
            text = c if isinstance(c, str) else " ".join(x.get("text", "") for x in c if isinstance(x, dict))
            return " ".join(text.split())[:100]
    return ""


def phase_of(role, task):
    """Workflow phase of a subagent launch, from its role and the first words of its prompt."""
    t = task.lower()
    if "re-review" in t or role.endswith("-recheck"):
        return "re-review"
    if role.startswith("dev-implementer"):
        return "hardening" if "hardening" in t else ("build" if ("mode: build" in t or "round 1" in t or "build" in t[:60]) and "mode: fix" not in t else "fix")
    return {"spec-verification-writer": "tests", "spec-verification-runner": "run",
            "spec-compliance-reviewer": "review", "pipeline-risk-reviewer": "review"}.get(role, "other")


def dev_commands(path, unit):
    """Timestamps of user-typed dev commands whose arguments start with the unit number."""
    for d in read(path):
        if d.get("type") != "user" or "<command-name>/dev-" not in json.dumps(d.get("message", "")):
            continue
        c = d["message"].get("content")
        text = c if isinstance(c, str) else " ".join(x.get("text", "") for x in c if isinstance(x, dict))
        for name, args in DEV_CMD.findall(text):
            if re.match(rf"0*{re.escape(unit.lstrip('0') or '0')}\b|{re.escape(unit)}\b", args.strip()):
                yield (d.get("timestamp") or "")[:19], name


def cost(fam, u):
    return PRICE[fam] * (u["input_tokens"] + 1.25 * u["cache_creation_input_tokens"]
                         + 0.1 * u["cache_read_input_tokens"] + 5 * u["output_tokens"])


def measure(repo, unit, since, until, sessions, kind="unit"):
    transcripts = [p for p in HOME.glob("projects/*/*.jsonl")]
    start_sha, start_ts = commit(repo, rf"start {re.escape(unit)}\b")
    done_sha, done_ts = commit(repo, rf"mark {re.escape(unit)} done")
    cmd_times = {p: list(dev_commands(p, unit)) for p in transcripts if not sessions}
    if since is None:
        if kind != "unit":
            since = "0000"          # a non-unit session counts from its first call
        elif start_ts is None:
            raise SystemExit(f"no 'start {unit}' commit; pass --since")
    if since is None:
        before = [ts for v in cmd_times.values() for ts, n in v if n in ("dev-1-select", "dev-auto") and ts <= start_ts]
        since = max(before) if before else iso(datetime.fromisoformat(start_ts + "+00:00") - timedelta(minutes=10))
    until = until or iso(datetime.now(timezone.utc))
    if sessions:
        chosen = [p for p in transcripts if any(p.stem.startswith(s) for s in sessions)]
    else:
        chosen = [p for p, v in cmd_times.items() if any(since <= ts <= until for ts, _ in v)]
        mine = [p for p in transcripts if any(in_repo(d.get("cwd"), repo) for d in read(p))]
        if mine:
            newest = max(mine, key=lambda p: p.stat().st_mtime)
            chosen += [newest] if newest not in chosen else []
    all_calls, per_session, launches = {}, {}, []
    for p in chosen:
        got = calls(p, since, until, repo, "main")
        sub = p.with_suffix("") / "subagents"
        for f in sub.glob("*.jsonl") if sub.exists() else []:
            meta = f.with_suffix(".meta.json")
            role = json.loads(meta.read_text(encoding="utf-8")).get("agentType", "agent") if meta.exists() else "agent"
            sub_calls = calls(f, since, until, repo, role)
            got.update({(f.stem, k): v for k, v in sub_calls.items()})
            if sub_calls:
                stamps = [d.get("timestamp", "")[:19] for d in read(f) if d.get("timestamp")]
                text = task_text(f)
                launches.append({"role": role, "start": min(stamps), "task": text, "phase": phase_of(role, text),
                                 "cost": round(sum(cost(family(c["model"]), c["usage"]) for c in sub_calls.values()))})
        if got:
            per_session[p.stem[:8]] = round(sum(cost(family(c["model"]), c["usage"]) for c in got.values()) / 1e6, 2)
        all_calls.update({(p.stem, k): v for k, v in got.items()})
    usage = defaultdict(lambda: defaultdict(float))
    peak = 0
    for c in all_calls.values():
        u, key = c["usage"], f'{c["role"]}|{c["model"].replace("claude-", "")}·{c["effort"]}'
        usage[key]["calls"] += 1
        usage[key]["output"] += u["output_tokens"]
        usage[key]["context"] += u["input_tokens"] + u["cache_creation_input_tokens"] + u["cache_read_input_tokens"]
        usage[key]["cost"] += cost(family(c["model"]), u)
        if c["role"] == "main":
            peak = max(peak, u["input_tokens"] + u["cache_creation_input_tokens"] + u["cache_read_input_tokens"])
    main = sum(v["cost"] for k, v in usage.items() if k.startswith("main|"))
    total = sum(v["cost"] for v in usage.values())
    work = {}
    if start_sha:
        end = done_sha or "HEAD"
        src = tests = 0
        for line in git(repo, "diff", "--numstat", f"{start_sha}..{end}").splitlines():
            a, _, path = line.split("\t")
            if path.endswith(".py") and a != "-":
                if "tests/" in path or Path(path).name.startswith("test_"):
                    tests += int(a)
                else:
                    src += int(a)
        work = {"src_lines": src, "test_lines": tests}
    contract = next(iter(Path(repo).glob(f"spec/{unit}-*/contract.md")), None)
    if contract:
        work["acs"] = len(re.findall(r"^- AC\d+", contract.read_text(encoding="utf-8"), re.M))
    phases = defaultdict(float)
    for l in launches:
        phases[l["phase"]] += l["cost"]
    phases["coordinator"] = main
    return {"window": [since, until], "sessions": per_session, "phases": {k: round(v) for k, v in phases.items()}, "launches": sorted(launches, key=lambda x: x["start"]),
            "usage": {k: {f: round(x) for f, x in v.items()} for k, v in sorted(usage.items())},
            "totals": {"main": round(main / 1e6, 2), "agents": round((total - main) / 1e6, 2),
                       "total": round(total / 1e6, 2), "peak_main_context": peak},
            "work": work}


REVIEWERS = (("compliance", "spec-compliance-reviewer"), ("pipeline", "pipeline-risk-reviewer"), ("risk", "pipeline-risk-reviewer"))


def reviewer_name(text):
    low = text.lower()
    return next((full for key, full in REVIEWERS if key in low), "?")


def parse_findings(report):
    """Raised findings (## Review) and their resolutions (## Review resolutions) from a test-report.md."""
    text = report.read_text(encoding="utf-8")
    sections = re.split(r"^## ", text, flags=re.M)
    review = next((x for x in sections if x.startswith("Review\n")), "")
    resolutions = next((x for x in sections if x.startswith("Review resolutions")), "")
    raised, who = [], "?"
    for line in review.splitlines():
        if line.startswith("### "):
            who = reviewer_name(line)
        m = re.match(r"- \[([\w-]+)\]", line)
        if m and who != "?" and m.group(1) != "clean":
            raised.append({"reviewer": who, "severity": m.group(1)})
    resolved, rnd = [], "?"
    for line in resolutions.splitlines():
        if line.startswith("### "):
            rnd = (re.match(r"### (Round \d+|[^\u2014\u00b7(]+)", line) or [None, "?"])[1].strip()
        m = re.match(r"- \[([^\]]+)\]\s*(.*)", line)
        if m:
            cls = m.group(1).split()[0].lower()
            cls = "hardening" if cls.startswith("fragile") else cls
            body = m.group(2)
            resolved.append({"round": rnd, "class": cls, "reviewer": reviewer_name(body[:40]),
                             "introduced_by_fix": bool(re.search(r"introduced (by|in) (a|the) (fix|round)", body, re.I)),
                             "handoff": (re.findall(r"HO-\d+", body) or [None])[-1]})
    return {"raised": raised, "resolved": resolved}


def load_extra(name):
    path = OUT / name
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()] if path.exists() else []


def save_extra(name, rows):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def store_findings(repo, project, unit):
    report = next(iter(Path(repo).glob(f"spec/{unit}-*/test-report.md")), None)
    if report is None:
        print(f"findings: no test-report.md for {unit}")
        return
    rows = [x for x in load_extra("findings.jsonl") if (x["project"], x["unit"]) != (project, unit)]
    got = parse_findings(report)
    save_extra("findings.jsonl", rows + [{"project": project, "unit": unit, **got}])
    print(f"findings {unit}: {len(got['raised'])} raised, {len(got['resolved'])} resolved")


def load():
    path = OUT / "ledger.jsonl"
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()] if path.exists() else []


def save(records):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "ledger.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")


def render():
    records = load()
    lines = ["# Workflow ledger", "",
             "One row per finished unit, written by `/dev-6-final`; stopped runs, selects and retros are logged with `--kind` (script: `~/.claude/scripts/usage_ledger.py`). "
             "`/dev-retro` reads it to find what makes units take extra rounds. Changes made from it: [CHANGES.md](CHANGES.md).", "",
             "Cost units (M): tokens weighted by price ratio — Fable 2.5, Opus 1, Sonnet 0.6, Haiku 0.2 on input; cache write ×1.25, "
             "cache read ×0.1, output ×5. Relative, not a bill. **Peak ctx** = largest main-session context; "
             "above ~250k means the unit ran in a session carrying other work.", ""]
    for project in sorted({r["project"] for r in records}):
        mine = [r for r in records if r["project"] == project]
        rows = sorted((r for r in mine if r.get("kind", "unit") == "unit"), key=lambda r: r["unit"])
        others = sorted((r for r in mine if r.get("kind", "unit") != "unit"), key=lambda r: r["window"][0])
        lines += [f"## {project}", "",
                  "| Unit | Date | Mode | Rounds | 1st test run | Test defects | Extra-round causes | Findings | Src / test lines | ACs "
                  "| Cost main / agents / total | Per 100 src lines | Peak ctx |",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in rows:
            o, w, t = r.get("outcome", {}), r.get("work", {}), r["totals"]
            per = f'{100 * t["total"] / w["src_lines"]:.2f}' if w.get("src_lines") else "—"
            lines.append(f'| {r["unit"]} | {r["date"]} | {o.get("mode", "—")} | {o.get("rounds", "—")} | {o.get("first_run", "—")} '
                         f'| {o.get("test_defects", "—")} | {o.get("causes", "—")} | {o.get("findings", "—")} '
                         f'| {w.get("src_lines", "—")} / {w.get("test_lines", "—")} | {w.get("acs", "—")} '
                         f'| {t["main"]} / {t["agents"]} / **{t["total"]}** | {per} | {t["peak_main_context"] // 1000}k |')
        lines += ["", "<details><summary>By role, model and effort</summary>", ""]
        for r in rows:
            parts = [f'{k.replace("|", " ")} {v["calls"]}× {v["cost"] / 1e6:.2f}M' for k, v in r["usage"].items()]
            lines.append(f'- **{r["unit"]}**: ' + "; ".join(parts) + (f' — {r["outcome"]["note"]}' if r.get("outcome", {}).get("note") else ""))
        lines += ["", "</details>", ""]
        with_launches = [r for r in rows if r.get("launches")]
        if with_launches:
            lines += ["<details><summary>Agent launches (why the agents cost what they did, in time order)</summary>", ""]
            for r in with_launches:
                lines.append(f'- **{r["unit"]}**: ' + "; ".join(
                    f'{l["start"][11:16]} {l["role"]} {l["cost"] / 1e6:.2f}M «{l["task"][:60]}»' for l in r["launches"]))
            lines += ["", "</details>", ""]
        phase_rows = [r for r in rows if r.get("phases")]
        if phase_rows:
            order = ["build", "tests", "run", "review", "re-review", "fix", "hardening", "other", "coordinator"]
            lines += ["Cost by phase (M units; agents by workflow phase, coordinator = main session):", "",
                      "| Unit | " + " | ".join(order) + " | total |", "|---|" + "---|" * (len(order) + 1)]
            for r in phase_rows:
                ph = r["phases"]
                lines.append(f'| {r["unit"]} | ' + " | ".join(f'{ph.get(k, 0) / 1e6:.2f}' if ph.get(k) else "-" for k in order)
                             + f' | **{r["totals"]["total"]}** |')
            lines.append("")
        classes = [r for r in rows if r.get("outcome", {}).get("first_run_classes")]
        if classes:
            lines += ["First verification run, failures by class:", "", "| Unit | 1st run | Classes |", "|---|---|---|"]
            lines += [f'| {r["unit"]} | {r["outcome"].get("first_run", "-")} | {r["outcome"]["first_run_classes"]} |' for r in classes]
            lines.append("")
        found = [f for f in load_extra("findings.jsonl") if f["project"] == project]
        if found:
            lines += ["Reviewer yield (units with parsed reports; cost = that reviewer's launches, `-recheck` included for the pipeline reviewer):", "",
                      "| Reviewer | Raised | Fixed | Hardening | Accepted | Rejected | Fix-introduced | Cost M | M per fixed |",
                      "|---|---|---|---|---|---|---|---|---|"]
            cost_by = defaultdict(float)
            for r in mine:
                for key, v in r.get("usage", {}).items():
                    cost_by[key.split("|")[0]] += v["cost"]
            for rv, roles in (("spec-compliance-reviewer", ("spec-compliance-reviewer",)),
                              ("pipeline-risk-reviewer", ("pipeline-risk-reviewer", "pipeline-risk-reviewer-recheck"))):
                raised = sum(1 for f in found for x in f["raised"] if x["reviewer"] == rv)
                res = [x for f in found for x in f["resolved"] if x["reviewer"] == rv]
                count = {c: sum(1 for x in res if x["class"] == c) for c in ("fixed", "hardening", "accepted", "rejected")}
                money = sum(cost_by[k] for k in roles) / 1e6
                per = f'{money / count["fixed"]:.2f}' if count["fixed"] else "-"
                lines.append(f'| {rv} | {raised} | {count["fixed"]} | {count["hardening"]} | {count["accepted"]} | {count["rejected"]} '
                             f'| {sum(1 for x in res if x["introduced_by_fix"])} | {money:.2f} | {per} |')
            lines += ["", "Caveat: resolution classes are parsed only from lines like `- [fixed] <reviewer> ...`; units whose reports use another format show raised findings but no resolutions, and resolutions that do not name a reviewer are not counted per reviewer, so Fixed/Accepted/Rejected undercount. Cost per fixed is an upper bound.", ""]
        esc = [e for e in load_extra("escaped.jsonl") if e["project"] == project]
        if esc:
            lines += ["Escaped defects and couplings (found after a unit was closed - what review and verification missed):", "",
                      "| Unit | Found in | Kind | Date | Note |", "|---|---|---|---|---|"]
            lines += [f'| {e["unit"]} | {e["found_in"]} | {e["kind"]} | {e["date"]} | {e["note"]} |'
                      for e in sorted(esc, key=lambda e: (e["unit"], e["date"]))]
            lines.append("")
        if others:
            lines += ["Sessions that did not finish a unit (stopped runs, selects, retros) — cost that the unit rows above do not include:", "",
                      "| Label | Kind | Date | Cost main / agents / total | Peak ctx | Why |", "|---|---|---|---|---|---|"]
            for r in others:
                t = r["totals"]
                lines.append(f'| {r["unit"]} | {r.get("kind")} | {r["date"]} | {t["main"]} / {t["agents"]} / **{t["total"]}** '
                             f'| {t["peak_main_context"] // 1000}k | {r.get("outcome", {}).get("note", "—")} |')
            lines.append("")
    (OUT / "LEDGER.md").write_text("\n".join(lines), encoding="utf-8")
    if not (OUT / "CHANGES.md").exists():
        (OUT / "CHANGES.md").write_text("# Workflow changes\n\nNewest first. Each entry: date, change, the ledger evidence, "
                                        "and the units to watch to see if it worked.\n", encoding="utf-8")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    rec = sp.add_parser("record")
    rec.add_argument("--repo", default=".")
    rec.add_argument("--unit", required=True)
    rec.add_argument("--project")
    rec.add_argument("--since")
    rec.add_argument("--until")
    rec.add_argument("--session", action="append", default=[])
    rec.add_argument("--kind", default="unit", choices=["unit", "stopped", "retro", "select", "other"],
                     help="unit = a sub-spec build; other kinds log a session that did not finish a unit (unit = a unique label)")
    for k in ("mode", "rounds", "first-run", "first-run-classes", "test-defects", "findings", "causes", "note", "src-lines", "test-lines", "acs"):
        rec.add_argument(f"--{k}")
    fnd = sp.add_parser("findings")
    fnd.add_argument("--repo", default=".")
    fnd.add_argument("--unit", required=True)
    fnd.add_argument("--project")
    esc = sp.add_parser("escaped")
    esc.add_argument("--project", default=Path(".").resolve().name)
    esc.add_argument("--unit", required=True, help="the unit whose work let the problem through")
    esc.add_argument("--found-in", required=True, help="unit, review or run that found it")
    esc.add_argument("--kind", required=True, choices=["defect", "spec-gap", "coupling"],
                     help="defect = wrong behaviour; spec-gap = contract/spec missed it; "
                          "coupling = a later unit forced an edit to this unit's locked files")
    esc.add_argument("--note", required=True)
    sp.add_parser("render")
    a = ap.parse_args()
    if a.cmd == "findings":
        repo = Path(a.repo).resolve()
        store_findings(repo, a.project or repo.name, a.unit)
    if a.cmd == "escaped":
        rows = load_extra("escaped.jsonl") + [{"project": a.project, "unit": a.unit, "found_in": a.found_in, "kind": a.kind,
                                                "note": a.note, "date": datetime.now().strftime("%Y-%m-%d")}]
        save_extra("escaped.jsonl", rows)
        print(f"escaped: {a.unit} <- {a.found_in} ({a.kind})")
    if a.cmd == "record":
        repo = Path(a.repo).resolve()
        project = a.project or repo.name
        r = measure(repo, a.unit, a.since, a.until, a.session, a.kind)
        for k in ("src_lines", "test_lines", "acs"):
            if getattr(a, k):
                r["work"][k] = int(getattr(a, k))
        r.update(project=project, unit=a.unit, date=r["window"][1][:10],
                 kind=a.kind,
                 outcome={k: v for k, v in {"mode": a.mode, "rounds": a.rounds, "first_run": a.first_run,
                                            "test_defects": a.test_defects, "findings": a.findings, "first_run_classes": a.first_run_classes,
                                            "causes": a.causes, "note": a.note}.items() if v})
        records = [x for x in load() if (x["project"], x["unit"]) != (project, a.unit)] + [r]
        save(records)
        if a.kind == "unit":
            store_findings(repo, project, a.unit)
        t = r["totals"]
        print(f'{project} {a.unit}: total {t["total"]}M (main {t["main"]}, agents {t["agents"]}), '
              f'peak main context {t["peak_main_context"] // 1000}k, window {r["window"][0]} to {r["window"][1]}, sessions {r["sessions"]}')
    render()
    print(f"ledger: {OUT / 'LEDGER.md'}")


if __name__ == "__main__":
    main()
