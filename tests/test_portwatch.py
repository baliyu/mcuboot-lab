# AI-assisted: drafted with Claude, checked by the author.
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import cutter  # noqa: E402
import portwatch  # noqa: E402


class Clock:
    def __init__(self):
        self.now = 0.0

    def read(self):
        return self.now

    def sleep(self, s):
        self.now += s


def test_watch_yields_first_state_and_each_change():
    clk = Clock()

    def lister():
        if clk.now < 0.2:
            return ["COM3", "COM14"]
        if clk.now < 0.5:
            return ["COM3"]
        return ["COM14", "COM3"]

    events = list(portwatch.watch(lister, clk.read, clk.sleep, 1.0))
    assert [e[1] for e in events] == [("COM14", "COM3"), ("COM3",), ("COM14", "COM3")]
    assert abs(events[1][0] - 0.2) < 0.06
    assert abs(events[2][0] - 0.5) < 0.06


def test_watch_stops_after_duration():
    clk = Clock()
    events = list(portwatch.watch(lambda: ["COM3"], clk.read, clk.sleep, 0.5))
    assert len(events) == 1
    assert clk.now <= 0.6


def test_watch_uses_given_t0():
    clk = Clock()
    clk.now = 5.0
    events = list(portwatch.watch(lambda: ["COM3"], clk.read, clk.sleep, 10, t0=4.0))
    assert events[0][0] >= 1.0


class FakeCutter:
    def __init__(self):
        self.called = False

    def reset(self):
        self.called = True


def test_main_reset_sends_reset(monkeypatch, capsys):
    fake = FakeCutter()
    monkeypatch.setattr(cutter, "open_cutter", lambda port: fake)
    monkeypatch.setattr(portwatch, "comports", lambda: ["COM3"])
    assert portwatch.main(["--reset", "--seconds", "0.1"]) == 0
    assert fake.called
    assert "COM3" in capsys.readouterr().out


def test_main_without_reset_never_touches_cutter(monkeypatch):
    def boom(port):
        raise AssertionError("cutter must not be opened")

    monkeypatch.setattr(cutter, "open_cutter", boom)
    monkeypatch.setattr(portwatch, "comports", lambda: ["COM3"])
    assert portwatch.main(["--seconds", "0.1"]) == 0


class FakeCutterWithCut:
    def __init__(self):
        self.cut_us = None

    def reset(self):
        pass

    def cut(self, us):
        self.cut_us = us


def test_main_cut_sends_cut(monkeypatch):
    fake = FakeCutterWithCut()
    monkeypatch.setattr(cutter, "open_cutter", lambda port: fake)
    monkeypatch.setattr(portwatch, "comports", lambda: ["COM3"])
    assert portwatch.main(["--cut", "1500", "--seconds", "0.1"]) == 0
    assert fake.cut_us == 1500


def test_main_rejects_reset_and_cut_together():
    import pytest
    with pytest.raises(SystemExit):
        portwatch.main(["--reset", "--cut", "5"])
