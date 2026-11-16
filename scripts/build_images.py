"""Build the lab app at one or more versions from a single source tree.

AI-assisted: drafted with Claude, checked by the author.

Each version gets a temporary copy of the sources with only VERSION changed,
so v1.0.0 and v1.0.1 differ in nothing else.
"""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

BOARD = "arduino_nano_33_ble"
PROJECT_NAME = "mcuboot-lab"
COPY_ITEMS = ["CMakeLists.txt", "prj.conf", "sysbuild.conf", "VERSION",
              "boards", "src", "sysbuild"]


def version_text(template, version):
    major, minor, patch = (int(x) for x in version.split("."))
    out = template
    for key, val in (("VERSION_MAJOR", major), ("VERSION_MINOR", minor),
                     ("PATCHLEVEL", patch)):
        out, n = re.subn(rf"^{key}\s*=[^\r\n]*$", f"{key} = {val}", out,
                         flags=re.M)
        if n != 1:
            raise ValueError(f"{key} not found exactly once in VERSION")
    return out


def prepare_source(repo, dest, version):
    repo, dest = Path(repo), Path(dest)
    src = dest / PROJECT_NAME
    if src.exists():
        shutil.rmtree(src)
    src.mkdir(parents=True)
    for item in COPY_ITEMS:
        s = repo / item
        if s.is_dir():
            shutil.copytree(s, src / item)
        else:
            shutil.copy2(s, src / item)
    with open(repo / "VERSION", newline="") as f:
        template = f.read()
    with open(src / "VERSION", "w", newline="") as f:
        f.write(version_text(template, version))
    return src


def build_cmd(src, outdir):
    return ["west", "build", "-p", "always", "-b", BOARD, "--sysbuild",
            "-d", str(outdir), str(src)]


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("versions", nargs="+", help="for example 1.0.0 1.0.1")
    p.add_argument("--repo", default=str(Path(__file__).resolve().parent.parent))
    p.add_argument("--out", required=True,
                   help="folder for sources, builds and logs")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args(argv)
    out = Path(a.out)
    for v in a.versions:
        tag = "v" + v.replace(".", "")
        src = out / "src" / tag / PROJECT_NAME
        cmd = build_cmd(src, out / tag)
        if a.dry_run:
            print(" ".join(cmd))
            continue
        try:
            prepare_source(a.repo, out / "src" / tag, v)
        except ValueError as e:
            print(f"refused: {e}", file=sys.stderr)
            return 1
        log = out / (tag + ".log")
        with open(log, "w") as f:
            rc = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT).returncode
        print(f"{tag}: exit {rc}, log {log}")
        if rc != 0:
            return rc
    return 0


if __name__ == "__main__":
    sys.exit(main())
