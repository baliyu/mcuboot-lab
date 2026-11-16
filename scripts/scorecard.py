"""Tally the prediction scorecard and write docs/SCORECARD.md.

AI-assisted: drafted with Claude, checked by the author.

docs/scorecard.csv has one row per step: hits, misses, unscored, and a
written note for every miss and every unscored prediction, separated by
" | ". The tally is computed here and never typed, and a row is refused
when its counts and its notes disagree.
"""
import argparse
import csv
import sys

SEP = " | "


def split_notes(text):
    return [n.strip() for n in text.split(SEP) if n.strip()] if text.strip() else []


def load(path):
    rows = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            row = {"step": int(r["step"]), "topic": r["topic"],
                   "hits": int(r["hits"]), "misses": int(r["misses"]),
                   "unscored": int(r["unscored"]),
                   "miss_notes": split_notes(r["miss_notes"]),
                   "unscored_notes": split_notes(r["unscored_notes"]),
                   "other_notes": r["other_notes"].strip()}
            if min(row["hits"], row["misses"], row["unscored"]) < 0:
                raise ValueError(f"step {row['step']}: negative count")
            for count, notes, label in (("misses", "miss_notes", "misses"),
                                        ("unscored", "unscored_notes", "unscored")):
                if len(row[notes]) != row[count]:
                    raise ValueError(
                        f"step {row['step']}: {row[count]} {label} but "
                        f"{len(row[notes])} notes")
            rows.append(row)
    return rows


def totals(rows):
    return {k: sum(r[k] for r in rows) for k in ("hits", "misses", "unscored")}


def render(rows):
    t = totals(rows)
    out = ["# Prediction scorecard", "",
           "AI-assisted: drafted with Claude, checked by the author.", "",
           f"{t['hits']} hits, {t['misses']} misses and {t['unscored']} not scored, "
           f"across {len(rows)} steps. The tally is computed by scripts/scorecard.py "
           "from docs/scorecard.csv, and every miss is written down below.",
           "", "| Step | Topic | Hits | Misses | Not scored |",
           "|---|---|---|---|---|"]
    for r in rows:
        out.append(f"| {r['step']} | {r['topic']} | {r['hits']} | "
                   f"{r['misses']} | {r['unscored']} |")
    out += ["", "## Misses", ""]
    out += [f"- Step {r['step']}, {n}" for r in rows for n in r["miss_notes"]]
    out += ["", "## Not scored", ""]
    out += [f"- Step {r['step']}, {n}" for r in rows for n in r["unscored_notes"]]
    other = [r for r in rows if r["other_notes"]]
    if other:
        out += ["", "## Other errors that were not predictions", ""]
        out += [f"- Step {r['step']}: {r['other_notes']}" for r in other]
    return "\n".join(out) + "\n"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("csv")
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    try:
        rows = load(a.csv)
    except (ValueError, KeyError, OSError) as e:
        print(f"refused: {e}", file=sys.stderr)
        return 1
    with open(a.out, "w", newline="") as f:
        f.write(render(rows))
    t = totals(rows)
    print(f"{t['hits']} hits, {t['misses']} misses, {t['unscored']} not scored")
    print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
