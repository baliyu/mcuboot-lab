# AI-assisted: drafted with Claude, checked by the author.
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = ["coarse_100ms.csv", "fine_2400_2500_5ms.csv", "sweep_20ms_600_3200.csv"]


def rows():
    out = []
    for name in FILES:
        with open(ROOT / "results" / name, newline="") as f:
            out += list(csv.DictReader(f))
    return out


def test_readme_counts_match_the_csv_files():
    r = rows()
    n = len(r)
    updated = sum(x["outcome"] == "updated" for x in r)
    flash_fail = sum(x["outcome"] == "flash_fail" for x in r)
    bootloader = sum(x["outcome"] == "bootloader" for x in r)
    text = (ROOT / "README.md").read_text()
    assert f"{n} trials: {updated} updated, {flash_fail} flash_fail, {bootloader} bootloader" in text


def test_readme_has_no_em_dash():
    assert "\u2014" not in (ROOT / "README.md").read_text()


def test_readme_rerun_counts_match_the_rerun_csv_files():
    r = []
    for path in sorted((ROOT / "results").glob("rerun_*.csv")):
        with open(path, newline="") as f:
            r += list(csv.DictReader(f))
    updated = sum(x["outcome"] == "updated" for x in r)
    flash_fail = sum(x["outcome"] == "flash_fail" for x in r)
    assert len(r) == updated + flash_fail
    text = (ROOT / "README.md").read_text()
    assert f"Rerun: {len(r)} trials: {updated} updated, {flash_fail} flash_fail" in text
