# AI-assisted: drafted with Claude, checked by the author.
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import make_update as mu  # noqa: E402


def test_sign_cmd_matches_build_args_plus_pad():
    cmd = mu.sign_cmd("1.0.1", "k.pem", "in.bin", "out.bin", imgtool="imgtool.py")
    joined = " ".join(cmd)
    assert "--version 1.0.1+0" in joined
    assert "--header-size 0x200" in joined
    assert "--slot-size 131072" in joined
    assert "--overwrite-only" in cmd
    assert "--align 1" in joined
    assert "--pad" in cmd


def test_sign_cmd_rejects_bad_version():
    with pytest.raises(ValueError):
        mu.sign_cmd("1.0", "k.pem", "in.bin", "out.bin")


def test_check_padded_accepts_slot_size(tmp_path):
    f = tmp_path / "a.bin"
    f.write_bytes(b"\xff" * 0x20000)
    mu.check_padded(f)


def test_check_padded_rejects_other_size(tmp_path):
    f = tmp_path / "a.bin"
    f.write_bytes(b"\xff" * 100)
    with pytest.raises(ValueError):
        mu.check_padded(f)
