"""Merge MCUboot, the app and an optional update into one flash image.

AI-assisted: drafted with Claude, checked by the author.

The Arduino bootloader flashes at 0x10000 by itself, so the output file
starts at 0x10000. Layout, set by the overlays: MCUboot 0x10000-0x1ffff,
slot 0 0x20000-0x3ffff, slot 1 0x40000-0x5ffff.
"""
import argparse
import sys

from intelhex import IntelHex, IntelHexError

BASE = 0x10000
MCUBOOT = (0x10000, 0x20000)
SLOT0 = (0x20000, 0x40000)
SLOT1 = (0x40000, 0x60000)


def check_region(name, ih, region):
    lo, hi = ih.minaddr(), ih.maxaddr() + 1
    if lo != region[0]:
        raise ValueError(f"{name} starts at {lo:#x}, expected {region[0]:#x}")
    if hi > region[1]:
        raise ValueError(f"{name} ends at {hi:#x}, limit {region[1]:#x}")


def load_update(path):
    ih = IntelHex()
    ih.loadbin(path, offset=SLOT1[0])
    return ih


def merge(mcuboot, app, update=None):
    check_region("mcuboot", mcuboot, MCUBOOT)
    check_region("app", app, SLOT0)
    out = IntelHex()
    out.merge(mcuboot, overlap="error")
    out.merge(app, overlap="error")
    if update is not None:
        check_region("update", update, SLOT1)
        out.merge(update, overlap="error")
        end = SLOT1[1]
    else:
        end = out.maxaddr() + 1
    return out.tobinstr(start=BASE, end=end - 1, pad=0xFF)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--mcuboot", required=True)
    p.add_argument("--app", required=True)
    p.add_argument("--update")
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    try:
        update = load_update(a.update) if a.update else None
        image = merge(IntelHex(a.mcuboot), IntelHex(a.app), update)
    except (ValueError, IntelHexError) as e:
        print(f"refused: {e}", file=sys.stderr)
        return 1
    with open(a.out, "wb") as f:
        f.write(image)
    print(f"wrote {len(image)} bytes to {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
