"""Power-cut sweep: flash the pending image, cut at a chosen time, record what boots.

AI-assisted: drafted with Claude, checked by the author.

Run on Windows (COM ports, bossac). One CSV row per trial, written as it
goes, so an interrupted sweep keeps its rows and --resume skips times
already done. app_port_s is seconds from the end of the cut command until
the app's USB port appeared.
"""
import argparse
import csv
import re
import subprocess
import sys
import time
from pathlib import Path

BOOT_VID, BOOT_PID = 0x2341, 0x005A
APP_VID, APP_PID = 0x2FE3, 0x0004
OLD, NEW = "1.0.0", "1.0.1"
FIELDS = ["time", "cut_us", "outcome", "version", "app_port_s"]
RETRY = ("setup_fail", "flash_fail")
VERSION_RE = re.compile(r"app v(\d+\.\d+\.\d+)")


def parse_version(text):
    found = VERSION_RE.findall(text)
    return found[-1] if found else None


def classify(version, app_port, bootloader_port):
    if version == NEW:
        return "updated"
    if version == OLD:
        return "old"
    if version is not None:
        return "other"
    if app_port:
        return "silent"
    if bootloader_port:
        return "bootloader"
    return "dead"


def flash_ok(output):
    return "Verify successful" in output


def flash_report(output, n=3):
    lines = [x.strip() for x in output.splitlines() if x.strip()]
    return " / ".join(lines[-n:]) if lines else "(no output)"


def cut_times(start_us, stop_us, step_us):
    if step_us <= 0 or stop_us < start_us:
        raise ValueError("need step > 0 and stop >= start")
    return list(range(start_us, stop_us + 1, step_us))


def done_times(path):
    path = Path(path)
    if not path.exists():
        return set()
    with open(path, newline="") as f:
        return {int(r["cut_us"]) for r in csv.DictReader(f)
                if r["outcome"] not in RETRY}


def run_trial(us, io):
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S")
    port = io.enter_bootloader()
    if port is None:
        return [stamp, us, "setup_fail", "", ""]
    if not io.flash(port):
        return [stamp, us, "flash_fail", "", ""]
    io.cut(us)
    obs = io.observe()
    outcome = classify(obs["version"], obs["app_port"], obs["bootloader_port"])
    t = "" if obs["app_port_s"] is None else f"{obs['app_port_s']:.2f}"
    return [stamp, us, outcome, obs["version"] or "", t]


def run_sweep(times, io, out_path, log=print):
    out_path = Path(out_path)
    new_file = not out_path.exists()
    with open(out_path, "a", newline="") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(FIELDS)
            f.flush()
        for us in times:
            row = run_trial(us, io)
            w.writerow(row)
            f.flush()
            log(f"{us:>8} us  {row[2]:<10} {row[3] or '-':<6} app_port_s={row[4] or '-'}")


class WindowsIO:
    def __init__(self, cutter_port, bossac, image):
        import cutter
        self.cutter = cutter.open_cutter(cutter_port)
        self.bossac = bossac
        self.image = image

    def _find(self, vid, pid):
        from serial.tools import list_ports
        for p in list_ports.comports():
            if p.vid == vid and p.pid == pid:
                return p.device
        return None

    def enter_bootloader(self):
        self.cutter.bootloader()
        end = time.perf_counter() + 5
        while time.perf_counter() < end:
            port = self._find(BOOT_VID, BOOT_PID)
            if port:
                return port
            time.sleep(0.05)
        return None

    def flash(self, port):
        r = subprocess.run([self.bossac, f"--port={port}", "-U", "-i", "-e",
                            "-w", "-v", self.image],
                           capture_output=True, text=True)
        text = r.stdout + r.stderr
        ok = flash_ok(text)
        if not ok:
            print(f"  flash failed (exit {r.returncode}), bossac said: {flash_report(text)}")
        return ok

    def cut(self, us):
        self.cutter.cut(us)

    def _read_version(self, port, read_s):
        import serial
        ser = None
        for _ in range(10):
            try:
                ser = serial.Serial(port, 115200, timeout=0.1)
                break
            except serial.SerialException:
                time.sleep(0.5)
        if ser is None:
            return None
        text = ""
        end = time.perf_counter() + read_s
        while time.perf_counter() < end and not parse_version(text):
            text += ser.read(256).decode(errors="replace")
        ser.close()
        return parse_version(text)

    def observe(self, timeout=15, read_s=5):
        t0 = time.perf_counter()
        app_port = None
        while time.perf_counter() - t0 < timeout:
            app_port = self._find(APP_VID, APP_PID)
            if app_port:
                break
            time.sleep(0.05)
        t_app = None if app_port is None else time.perf_counter() - t0
        version = self._read_version(app_port, read_s) if app_port else None
        return {"version": version, "app_port": app_port,
                "bootloader_port": self._find(BOOT_VID, BOOT_PID),
                "app_port_s": t_app}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--start-us", type=int, required=True)
    p.add_argument("--stop-us", type=int, required=True)
    p.add_argument("--step-us", type=int, required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--image", required=True)
    p.add_argument("--bossac", required=True)
    p.add_argument("--cutter-port", default="COM3")
    p.add_argument("--resume", action="store_true")
    a = p.parse_args(argv)
    try:
        times = cut_times(a.start_us, a.stop_us, a.step_us)
    except ValueError as e:
        print(f"refused: {e}", file=sys.stderr)
        return 1
    out = Path(a.out)
    if out.exists() and not a.resume:
        print("refused: output exists, use --resume to continue it", file=sys.stderr)
        return 1
    if a.resume:
        skip = done_times(out)
        times = [t for t in times if t not in skip]
    io = WindowsIO(a.cutter_port, a.bossac, a.image)
    run_sweep(times, io, out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
