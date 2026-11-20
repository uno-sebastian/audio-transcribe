#!/usr/bin/env python3
"""Compare two transcripts (e.g. whisper vs parakeet) and list where they disagree.

Words are compared ignoring case and punctuation, so only real wording
differences show up. Each disagreement is listed with a timestamp so you can
jump to that spot in the audio and decide which engine got it right.

Usage:
    python compare.py transcripts/talk.whisper.txt transcripts/talk.parakeet.txt
    python compare.py a.txt b.txt --ignore-fillers --context 5
"""
import argparse
import difflib
import re
import sys
from pathlib import Path

LINE_RE = re.compile(r"^\[(\d+):(\d+):(\d+)\]\s*(.*)$")
FILLERS = {"um", "uh", "uhm", "umm", "mm", "hmm", "mhm", "ah", "er"}


def load(path: Path, ignore_fillers: bool):
    """Return list of (normalized_word, original_word, timestamp_seconds)."""
    words = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        m = LINE_RE.match(raw)
        if not m:
            continue
        ts = int(m[1]) * 3600 + int(m[2]) * 60 + int(m[3])
        for w in m[4].split():
            norm = re.sub(r"[^a-z0-9']", "", w.lower())
            if not norm or (ignore_fillers and norm in FILLERS):
                continue
            words.append((norm, w, ts))
    return words


def fmt(ts: int) -> str:
    return f"{ts // 3600:02d}:{ts % 3600 // 60:02d}:{ts % 60:02d}"


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("a", type=Path, help="first transcript")
    p.add_argument("b", type=Path, help="second transcript")
    p.add_argument("--ignore-fillers", action="store_true", help="skip um/uh/hmm when comparing")
    p.add_argument("--context", type=int, default=4, help="words of context before each difference")
    p.add_argument("--out", type=Path, help="save the report here (default: next to the first file)")
    args = p.parse_args()

    for f in (args.a, args.b):
        if not f.exists():
            sys.exit(f"File not found: {f}")

    A, B = load(args.a, args.ignore_fillers), load(args.b, args.ignore_fillers)
    sm = difflib.SequenceMatcher(None, [w[0] for w in A], [w[0] for w in B], autojunk=False)

    lines, n_diff = [], 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        n_diff += 1
        ts = A[i1][2] if i1 < len(A) else B[j1][2]
        before = " ".join(w[1] for w in A[max(0, i1 - args.context):i1])
        a_txt = " ".join(w[1] for w in A[i1:i2]) or "(nothing)"
        b_txt = " ".join(w[1] for w in B[j1:j2]) or "(nothing)"
        lines.append(f"[{fmt(ts)}] ...{before}")
        lines.append(f"    {args.a.name.split('.')[-2]:>9}: {a_txt}")
        lines.append(f"    {args.b.name.split('.')[-2]:>9}: {b_txt}")
        lines.append("")

    matched = sum(b.size for b in sm.get_matching_blocks())
    header = [
        f"A: {args.a.name} ({len(A)} words)",
        f"B: {args.b.name} ({len(B)} words)",
        f"Agreement: {matched / max(len(A), len(B), 1):.1%} | {n_diff} differing spots",
        "",
    ]
    report = "\n".join(header + lines)
    print(report)

    out = args.out or args.a.with_name(args.a.name.split(".")[0] + ".diff.txt")
    out.write_text(report, encoding="utf-8")
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
