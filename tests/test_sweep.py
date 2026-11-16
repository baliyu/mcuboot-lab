# AI-assisted: drafted with Claude, checked by the author.
import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import sweep  # noqa: E402


class FakeIO:
    def __init__(self, version="1.0.1", app_port="COM14", boot_port=None,
                 bl="COM7", flash=True):
        self.version, self.app_port, self.boot_port = version, app_port, boot_port
        self.bl, self.flash_result = bl, flash
        self.cuts = []

    def enter_bootloader(self):
        return self.bl

    def flash(self, port):
        return self.flash_result

    def cut(self, us):
        self.cuts.append(us)

    def observe(self):
        return {"version": self.version, "app_port": self.app_port,
                "bootloader_port": self.boot_port, "app_port_s": 3.4}


def test_classify_cases():
    assert sweep.classify("1.0.1", "COM14", None) == "updated"
    assert sweep.classify("1.0.0", "COM14", None) == "old"
    assert sweep.classify("0.9.0", "COM14", None) == "other"
    assert sweep.classify(None, "COM14", None) == "silent"
    assert sweep.classify(None, None, "COM7") == "bootloader"
    assert sweep.classify(None, None, None) == "dead"


def test_parse_version_takes_the_last():
    text = "mcuboot-lab: app v1.0.0 running\nmcuboot-lab: app v1.0.1 running"
    assert sweep.parse_version(text) == "1.0.1"
    assert sweep.parse_version("nothing here") is None


def test_flash_ok():
    assert sweep.flash_ok("Verify 327680 bytes\nVerify successful\n")
    assert not sweep.flash_ok("Verify failed")


def test_cut_times_inclusive_and_validated():
    assert sweep.cut_times(1000, 3000, 1000) == [1000, 2000, 3000]
    with pytest.raises(ValueError):
        sweep.cut_times(1000, 500, 100)
    with pytest.raises(ValueError):
        sweep.cut_times(1000, 2000, 0)


def test_run_trial_updated():
    io = FakeIO()
    row = sweep.run_trial(1500000, io)
    assert row[1:] == [1500000, "updated", "1.0.1", "3.40"]
    assert io.cuts == [1500000]


def test_run_trial_setup_and_flash_failures_do_not_cut():
    io = FakeIO(bl=None)
    assert sweep.run_trial(1, io)[2] == "setup_fail"
    io = FakeIO(flash=False)
    assert sweep.run_trial(1, io)[2] == "flash_fail"
    assert io.cuts == []


def test_run_sweep_writes_rows_and_done_times_retries_failures(tmp_path):
    out = tmp_path / "s.csv"
    sweep.run_sweep([1000, 2000], FakeIO(), out, log=lambda s: None)
    sweep.run_sweep([3000], FakeIO(flash=False), out, log=lambda s: None)
    rows = list(csv.DictReader(open(out, newline="")))
    assert [r["cut_us"] for r in rows] == ["1000", "2000", "3000"]
    assert sweep.done_times(out) == {1000, 2000}


def test_main_refuses_existing_output_without_resume(tmp_path, monkeypatch):
    out = tmp_path / "s.csv"
    out.write_text("x\n")

    def boom(*a):
        raise AssertionError("hardware must not be opened")

    monkeypatch.setattr(sweep, "WindowsIO", boom)
    args = ["--start-us", "1", "--stop-us", "2", "--step-us", "1",
            "--out", str(out), "--image", "i", "--bossac", "b"]
    assert sweep.main(args) == 1


def test_main_resume_skips_done_times(tmp_path, monkeypatch):
    out = tmp_path / "s.csv"
    sweep.run_sweep([1000], FakeIO(), out, log=lambda s: None)
    fake = FakeIO()
    monkeypatch.setattr(sweep, "WindowsIO", lambda *a: fake)
    args = ["--start-us", "1000", "--stop-us", "3000", "--step-us", "1000",
            "--out", str(out), "--image", "i", "--bossac", "b", "--resume"]
    assert sweep.main(args) == 0
    assert fake.cuts == [2000, 3000]
