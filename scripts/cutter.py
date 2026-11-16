"""Host side of the RST cutter on the Feather M0.

AI-assisted: drafted with Claude, checked by the author.

Talks to feather/rst_cutter/rst_cutter.ino over USB serial. Run it on
Windows, where the COM ports are.
"""
import argparse
import sys

DEFAULT_PORT = "COM3"
BAUD = 115200
MAX_US = 60_000_000


def cut_line(us):
    us = int(us)
    if us < 0 or us > MAX_US:
        raise ValueError(f"cut time must be 0 to {MAX_US} us, got {us}")
    return f"CUT {us}\n".encode()


class Cutter:
    def __init__(self, ser):
        self.ser = ser

    def _send(self, line, expect):
        self.ser.write(line)
        reply = self.ser.readline().decode().strip()
        if reply != expect:
            raise RuntimeError(f"expected {expect!r}, got {reply!r}")

    def ping(self):
        self._send(b"PING\n", "PONG")

    def reset(self):
        self._send(b"RESET\n", "OK")

    def bootloader(self):
        self._send(b"BOOTLOADER\n", "OK")

    def cut(self, us):
        self._send(cut_line(us), "OK")


def open_cutter(port=DEFAULT_PORT, timeout=30):
    import serial
    return Cutter(serial.Serial(port, BAUD, timeout=timeout))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("action", choices=["ping", "reset", "bootloader", "cut"])
    p.add_argument("us", nargs="?", type=int)
    p.add_argument("--port", default=DEFAULT_PORT)
    a = p.parse_args(argv)
    try:
        c = open_cutter(a.port)
        if a.action == "cut":
            if a.us is None:
                p.error("cut needs a time in microseconds")
            c.cut(a.us)
        else:
            getattr(c, a.action)()
    except (ValueError, RuntimeError) as e:
        print(f"refused: {e}", file=sys.stderr)
        return 1
    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
