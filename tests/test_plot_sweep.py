# AI-assisted: drafted with Claude, checked by the author.
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import plot_sweep as ps  # noqa: E402


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["time", "cut_us", "outcome", "version", "app_port_s"])
        for us, outcome, app in rows:
            w.writerow(["t", us, outcome, "1.0.1" if app else "", app])


def test_load_rows_converts_types(tmp_path):
    f = tmp_path / "a.csv"
    write_csv(f, [(1500000, "updated", "3.40"), (400000, "bootloader", "")])
    rows = ps.load_rows([f])
    assert rows == [{"cut_s": 1.5, "outcome": "updated", "app_s": 3.4},
                    {"cut_s": 0.4, "outcome": "bootloader", "app_s": None}]


def test_summarize_counts():
    rows = [{"outcome": "updated"}, {"outcome": "updated"}, {"outcome": "dead"}]
    assert ps.summarize(rows) == {"updated": 2, "dead": 1}


def test_plot_writes_png(tmp_path):
    rows = [{"cut_s": 1.0, "outcome": "updated", "app_s": 3.4},
            {"cut_s": 0.4, "outcome": "bootloader", "app_s": None}]
    out = tmp_path / "f.png"
    ps.plot(rows, out)
    data = out.read_bytes()
    assert data[:4] == b"\x89PNG"
    assert len(data) > 1000


def test_main_reads_two_files(tmp_path, capsys):
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    write_csv(a, [(1000000, "updated", "3.40"), (2000000, "updated", "3.41")])
    write_csv(b, [(2500000, "updated", "1.25")])
    out = tmp_path / "f.png"
    assert ps.main([str(a), str(b), "--out", str(out)]) == 0
    assert "3 trials" in capsys.readouterr().out
    assert out.exists()


def test_main_refuses_missing_csv(tmp_path):
    assert ps.main([str(tmp_path / "nope.csv"), "--out", str(tmp_path / "f.png")]) == 1
