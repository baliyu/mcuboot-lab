"""Log changes in the set of COM ports, with times.

AI-assisted: drafted with Claude, checked by the author.

Run on Windows. With --reset it first sends RESET through the cutter, so
time zero is the moment the reset was requested. With --cut US it sends
CUT US in the background instead.
"""
import argparse
import sys
import threading
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
    p.add_argument("--cut", type=int, help="microseconds; sends CUT instead of RESET")
    a = p.parse_args(argv)
    if a.reset and a.cut is not None:
        p.error("use --reset or --cut, not both")
    c = None
    worker = None
    if a.reset or a.cut is not None:
        import cutter
        c = cutter.open_cutter(a.cutter_port)
    t0 = time.perf_counter()
    if c is not None and a.cut is not None:
        worker = threading.Thread(target=c.cut, args=(a.cut,))
        worker.start()
    elif c is not None:
        c.reset()
    for t, ports in watch(comports, time.perf_counter, time.sleep,
                          a.seconds, t0=t0):
        print(f"{t:6.2f} s  {','.join(ports) or '(none)'}")
    if worker is not None:
        worker.join()
    return 0


if __name__ == "__main__":
    sys.exit(main())
