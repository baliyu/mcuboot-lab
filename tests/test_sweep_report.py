# AI-assisted: drafted with Claude, checked by the author.
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import sweep as sw  # noqa: E402


def test_flash_report_keeps_the_last_three_lines():
    assert sw.flash_report("a\n\n b \nc\nd\n") == "b / c / d"


def test_flash_report_handles_no_output():
    assert sw.flash_report("") == "(no output)"
    assert sw.flash_report(" \n \n") == "(no output)"


def test_flash_report_n_argument():
    assert sw.flash_report("x\ny\nz", n=2) == "y / z"


def _io():
    io = sw.WindowsIO.__new__(sw.WindowsIO)
    io.bossac = "bossac.exe"
    io.image = "image.bin"
    return io


def test_flash_prints_what_bossac_said_on_failure(monkeypatch, capsys):
    fake = SimpleNamespace(stdout="", stderr="No device found on COM7\n", returncode=1)
    monkeypatch.setattr(sw.subprocess, "run", lambda *a, **k: fake)
    assert _io().flash("COM7") is False
    assert "No device found on COM7" in capsys.readouterr().out


def test_flash_is_quiet_on_success(monkeypatch, capsys):
    fake = SimpleNamespace(stdout="Verify successful\n", stderr="", returncode=0)
    monkeypatch.setattr(sw.subprocess, "run", lambda *a, **k: fake)
    assert _io().flash("COM7") is True
    assert capsys.readouterr().out == ""
