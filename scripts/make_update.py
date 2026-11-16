"""Sign and pad an update image for slot 1 with imgtool.

AI-assisted: drafted with Claude, checked by the author.

The arguments are the ones the Zephyr build used for the app (read from its
build.ninja on 16 Nov 2026), plus --pad, which fills the image to the slot
size and writes the "update waiting" marker at the end of the slot.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

IMGTOOL = Path.home() / "zephyrproject/bootloader/mcuboot/scripts/imgtool.py"
SLOT_SIZE = 0x20000
HEADER_SIZE = 0x200


def sign_cmd(version, key, unsigned_bin, out_bin, imgtool=IMGTOOL):
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError(f"version must look like 1.0.1, got {version!r}")
    return [sys.executable, str(imgtool), "sign",
            "--version", f"{version}+0",
            "--header-size", hex(HEADER_SIZE),
            "--slot-size", str(SLOT_SIZE),
            "--overwrite-only", "--align", "1", "--pad",
            "--key", str(key), str(unsigned_bin), str(out_bin)]


def check_padded(path):
    size = Path(path).stat().st_size
    if size != SLOT_SIZE:
        raise ValueError(f"{path} is {size} bytes, expected {SLOT_SIZE}")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("version", help="for example 1.0.1")
    p.add_argument("--key", required=True)
    p.add_argument("--bin", required=True, help="unsigned zephyr.bin of the update")
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    try:
        subprocess.run(sign_cmd(a.version, a.key, a.bin, a.out), check=True)
        check_padded(a.out)
    except (ValueError, subprocess.CalledProcessError) as e:
        print(f"refused: {e}", file=sys.stderr)
        return 1
    print(f"wrote {a.out} ({SLOT_SIZE} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
