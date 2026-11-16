# AI-assisted: drafted with Claude, checked by the author.
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import cutter  # noqa: E402

SKETCH = (ROOT / "feather" / "rst_cutter" / "rst_cutter.ino").read_text()


class FakeSerial:
    def __init__(self, replies):
        self.sent = []
        self.replies = list(replies)

    def write(self, data):
        self.sent.append(data)

    def readline(self):
        return self.replies.pop(0)


def test_cut_line_formats_microseconds():
    assert cutter.cut_line(1500) == b"CUT 1500\n"


def test_cut_line_rejects_out_of_range():
    for bad in (-1, 60_000_001):
        with pytest.raises(ValueError):
            cutter.cut_line(bad)


def test_ping_sends_ping_and_accepts_pong():
    fake = FakeSerial([b"PONG\n"])
    cutter.Cutter(fake).ping()
    assert fake.sent == [b"PING\n"]


def test_bad_reply_raises():
    with pytest.raises(RuntimeError):
        cutter.Cutter(FakeSerial([b"ERR\n"])).reset()


def test_cut_sends_line_and_accepts_ok():
    fake = FakeSerial([b"OK\n"])
    cutter.Cutter(fake).cut(2500)
    assert fake.sent == [b"CUT 2500\n"]


def test_sketch_knows_every_command():
    for word in ("PING", "PONG", "RESET", "BOOTLOADER", "CUT ", "OK", "ERR"):
        assert word in SKETCH


def test_sketch_never_drives_rst_high():
    assert "HIGH" not in SKETCH


def test_cli_ping(monkeypatch):
    fake = FakeSerial([b"PONG\n"])
    monkeypatch.setattr(cutter, "open_cutter", lambda port: cutter.Cutter(fake))
    assert cutter.main(["ping"]) == 0
