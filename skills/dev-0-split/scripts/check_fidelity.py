"""Check sub-spec excerpts are verbatim from the master spec and list master text no sub-spec covers: check_fidelity.py MASTER SPEC_DIR"""
import re
import sys
from pathlib import Path

MARKER = re.compile(r"^<!-- source: (.*?) -->[ \t]*$", re.MULTILINE)
HEADING = re.compile(r"^#{1,6} ")


def normalize(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").split("\n"))


def excerpts(text: str):
    parts = MARKER.split(text)
    for label, block in zip(parts[1::2], parts[2::2]):
        block = block.strip("\n")
        if block.strip():
            yield label.strip(), block


def unfenced(block: str) -> str | None:
    lines = block.split("\n")
    if len(lines) > 2 and lines[0].lstrip().startswith("```") and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1])
    return None


def first_mismatch(block: str, master: str) -> str:
    for line in block.split("\n"):
        if line.strip() and line not in master:
            return line.strip()[:100]
    return "(every line exists, but not contiguously in this order)"


def uncovered_ranges(master: str, covered: list[bool]) -> list[tuple[int, int, str]]:
    ranges = []
    lines = master.split("\n")
    start = None
    start_heading = heading = "(start of document)"
    last_missing = 0
    in_fence = False
    offset = 0
    for lineno, line in enumerate(lines, start=1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        elif not in_fence and HEADING.match(line):
            heading = line.strip()
        end = offset + len(line)
        if line.strip():
            if not any(covered[offset:end]):
                if start is None:
                    start, start_heading = lineno, heading
                last_missing = lineno
            elif start is not None:
                ranges.append((start, last_missing, start_heading))
                start = None
        offset = end + 1
    if start is not None:
        ranges.append((start, last_missing, start_heading))
    return ranges


def main(master_path: str, spec_dir: str) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    master = normalize(Path(master_path).read_text(encoding="utf-8"))
    covered = [False] * len(master)
    problems = verbatim = 0
    for sub_spec in sorted(Path(spec_dir).glob("*/sub-spec.md")):
        blocks = list(excerpts(normalize(sub_spec.read_text(encoding="utf-8"))))
        if not blocks:
            problems += 1
            print(f"NO EXCERPTS   {sub_spec.parent.name}: no '<!-- source: ... -->' markers")
        for label, block in blocks:
            position = master.find(block)
            if position < 0 and (inner := unfenced(block)) is not None:
                position, block = master.find(inner), inner
            if position < 0:
                problems += 1
                print(f'NOT VERBATIM  {sub_spec.parent.name} [{label}] first differing line: "{first_mismatch(block, master)}"')
                continue
            verbatim += 1
            covered[position:position + len(block)] = [True] * len(block)
    for start, end, heading in uncovered_ranges(master, covered):
        print(f"UNCOVERED     lines {start}-{end} under {heading}")
    print(f"\n{verbatim} excerpts verbatim, {problems} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], sys.argv[2]))
