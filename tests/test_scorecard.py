# AI-assisted: drafted with Claude, checked by the author.
import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import scorecard as sc  # noqa: E402

HEADER = ["step", "topic", "hits", "misses", "unscored",
          "miss_notes", "unscored_notes", "other_notes"]


def write(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        w.writerows(rows)


GOOD = [[1, "First", 2, 2, 0, "A: wrong | B: wrong", "", ""],
        [2, "Second", 3, 0, 1, "", "C: no data", "a slip"]]


def test_split_notes():
    assert sc.split_notes("A | B") == ["A", "B"]
    assert sc.split_notes("") == []


def test_load_refuses_miss_count_mismatch(tmp_path):
    f = tmp_path / "s.csv"
    write(f, [[1, "X", 1, 2, 0, "only one note", "", ""]])
    with pytest.raises(ValueError):
        sc.load(f)


def test_load_refuses_unscored_count_mismatch(tmp_path):
    f = tmp_path / "s.csv"
    write(f, [[1, "X", 1, 0, 2, "", "one note", ""]])
    with pytest.raises(ValueError):
        sc.load(f)


def test_totals_sums_columns(tmp_path):
    f = tmp_path / "s.csv"
    write(f, GOOD)
    assert sc.totals(sc.load(f)) == {"hits": 5, "misses": 2, "unscored": 1}


def test_render_lists_every_miss_and_the_totals(tmp_path):
    f = tmp_path / "s.csv"
    write(f, GOOD)
    text = sc.render(sc.load(f))
    assert "5 hits, 2 misses and 1 not scored" in text
    assert "- Step 1, A: wrong" in text
    assert "- Step 1, B: wrong" in text
    assert "- Step 2, C: no data" in text
    assert "a slip" in text


def test_main_writes_file_and_prints_totals(tmp_path, capsys):
    f, out = tmp_path / "s.csv", tmp_path / "S.md"
    write(f, GOOD)
    assert sc.main([str(f), "--out", str(out)]) == 0
    assert "5 hits, 2 misses, 1 not scored" in capsys.readouterr().out
    assert out.exists()


def test_committed_scorecard_is_internally_consistent():
    rows = sc.load(ROOT / "docs" / "scorecard.csv")
    assert len(rows) >= 41
