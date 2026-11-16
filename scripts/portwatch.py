"""Log changes in the set of COM ports, with times.

AI-assisted: drafted with Claude, checked by the author.

Run on Windows. With --reset it first sends RESET through the cutter, so
time zero is the moment the reset was requested.
"""
import argparse
import sys
import time


def watch(list_ports, clock, sleep, seconds, step=0.05, t0=None):
    """Yield (elapsed, sorted port names) at the start and at every change."""
    if t0 is None:
        t0 = clock()
    prev = None
    while True:
        elapsed = clock() - t0
        if elapsed > seconds:
            return
        now = tuple(sorted(list_ports()))
        if now != prev:
            yield elapsed, now
            prev = now
        sleep(step)


def comports():
    from serial.tools import list_ports
    return [p.device for p in list_ports.comports()]


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--reset", action="store_true")
    p.add_argument("--seconds", type=float, default=20)
    p.add_argument("--cutter-port", default="COM3")
    a = p.parse_args(argv)
    c = None
    if a.reset:
        import cutter
        c = cutter.open_cutter(a.cutter_port)
    t0 = time.perf_counter()
    if c is not None:
        c.reset()
    for t, ports in watch(comports, time.perf_counter, time.sleep,
                          a.seconds, t0=t0):
        print(f"{t:6.2f} s  {','.join(ports) or '(none)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
