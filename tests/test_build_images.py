# AI-assisted: drafted with Claude, checked by the author.
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import build_images as bi  # noqa: E402

TEMPLATE = ("VERSION_MAJOR = 1\nVERSION_MINOR = 0\nPATCHLEVEL = 0\n"
            "VERSION_TWEAK = 0\nEXTRAVERSION =\n")


def test_version_text_rewrites_three_fields():
    out = bi.version_text(TEMPLATE, "1.0.1")
    assert "PATCHLEVEL = 1" in out
    assert "VERSION_MAJOR = 1" in out
    assert "VERSION_MINOR = 0" in out


def test_version_text_keeps_other_lines():
    out = bi.version_text(TEMPLATE, "0.9.0")
    assert "VERSION_TWEAK = 0" in out
    assert "EXTRAVERSION =" in out


def test_version_text_rejects_missing_field():
    with pytest.raises(ValueError):
        bi.version_text("VERSION_MAJOR = 1\n", "1.0.1")


def test_prepare_source_copies_sources_not_secrets(tmp_path):
    repo = tmp_path / "repo"
    for d in ("src", "boards", "sysbuild", "keys", ".git"):
        (repo / d).mkdir(parents=True)
    for f in ("CMakeLists.txt", "prj.conf", "sysbuild.conf",
              "src/main.c", "boards/x.overlay", "sysbuild/mcuboot.conf",
              "keys/k.pem", ".git/config"):
        (repo / f).write_text("x\n")
    (repo / "VERSION").write_text(TEMPLATE)
    bi.prepare_source(repo, tmp_path / "dest", "1.0.1")
    d = tmp_path / "dest" / "mcuboot-lab"
    assert (d / "src" / "main.c").exists()
    assert not (d / "keys").exists()
    assert not (d / ".git").exists()
    assert "PATCHLEVEL = 1" in (d / "VERSION").read_text()


def test_dry_run_prints_one_command_per_version(tmp_path, capsys):
    rc = bi.main(["--dry-run", "--out", str(tmp_path), "1.0.0", "1.0.1"])
    lines = capsys.readouterr().out.strip().splitlines()
    assert rc == 0
    assert len(lines) == 2
    assert all(l.startswith("west build") and "--sysbuild" in l for l in lines)
