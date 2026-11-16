"""Plot sweep CSVs: cut time against how long the Nano took to come back.

AI-assisted: drafted with Claude, checked by the author.

Reads one or more files written by sweep.py. Rows with no app port (for
example a bootloader outcome) are drawn on the zero line.
"""
import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

STYLE = {
    "updated": ("#1f77b4", "o"),
    "old": ("#ff7f0e", "s"),
    "other": ("#9467bd", "D"),
    "silent": ("#8c564b", "v"),
    "bootloader": ("#2ca02c", "X"),
    "dead": ("#d62728", "P"),
    "setup_fail": ("#7f7f7f", "x"),
    "flash_fail": ("#7f7f7f", "+"),
}


def load_rows(paths):
    rows = []
    for path in paths:
        with open(path, newline="") as f:
            for r in csv.DictReader(f):
                app = r["app_port_s"]
                rows.append({"cut_s": int(r["cut_us"]) / 1e6,
                             "outcome": r["outcome"],
                             "app_s": float(app) if app else None})
    return rows


def summarize(rows):
    return dict(Counter(r["outcome"] for r in rows))


def plot(rows, out_png):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for outcome in sorted({r["outcome"] for r in rows}):
        colour, marker = STYLE.get(outcome, ("#000000", "*"))
        pts = [r for r in rows if r["outcome"] == outcome]
        ax.scatter([p["cut_s"] for p in pts],
                   [0 if p["app_s"] is None else p["app_s"] for p in pts],
                   c=colour, marker=marker, s=28,
                   label=f"{outcome} ({len(pts)})")
    ax.set_xlabel("cut time after the first reset (s)")
    ax.set_ylabel("seconds from the cut until the app port appeared")
    ax.set_title("MCUboot overwrite-only: power cut during the update")
    ax.grid(alpha=0.3)
    ax.legend(title="outcome")
    fig.tight_layout()
    fig.savefig(out_png, dpi=150)
    plt.close(fig)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("csv", nargs="+")
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    missing = [c for c in a.csv if not Path(c).exists()]
    if missing:
        print(f"refused: missing {missing[0]}", file=sys.stderr)
        return 1
    rows = load_rows(a.csv)
    plot(rows, a.out)
    print(f"{len(rows)} trials: {summarize(rows)}")
    print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
