"""Write a small SPDX bill of materials for the lab firmware.

AI-assisted: drafted with Claude, checked by the author.

west spdx lists every module in the west manifest (66 here). This script
keeps only the modules that have at least one compiled source file in an
image, so the bill of materials describes the firmware and not the SDK.
"""
import argparse
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from spdx_tools.spdx.model import (Actor, ActorType, CreationInfo, Document,
                                   Package, Relationship, RelationshipType,
                                   SpdxNoAssertion)
from spdx_tools.spdx.parser.parse_anything import parse_file
from spdx_tools.spdx.validation.document_validator import \
    validate_full_spdx_document
from spdx_tools.spdx.writer.write_anything import write_file

import build_images

IMAGES = ("mcuboot-lab", "mcuboot")
NAMESPACE = "https://github.com/baliyu/mcuboot-lab/sbom/"
NOASSERT = "NOASSERTION"


def used_components(zephyr_spdx):
    """Return sorted (name, version, download) for modules with compiled files."""
    doc = parse_file(str(zephyr_spdx))
    pkgs = {p.spdx_id: p for p in doc.packages}
    file_ids = {f.spdx_id for f in doc.files}
    used = {}
    for r in doc.relationships:
        a, b = r.spdx_element_id, r.related_spdx_element_id
        if r.relationship_type != RelationshipType.CONTAINS:
            continue
        if isinstance(a, str) and isinstance(b, str) \
                and a in pkgs and b in file_ids:
            used[a] = pkgs[a]
    out = set()
    for p in used.values():
        name = p.name[:-len("-sources")] if p.name.endswith("-sources") else p.name
        out.add((name, p.version or NOASSERT, str(p.download_location)))
    return sorted(out)


def read_images(root):
    by_image = {}
    for img in IMAGES:
        path = Path(root) / f"spdx-{img}" / "zephyr.spdx"
        if not path.is_file():
            raise FileNotFoundError(f"missing {path}")
        by_image[img] = used_components(path)
    return by_image


def _safe(text):
    return "".join(c if c.isalnum() or c in ".-" else "-" for c in text)


def _package(spdx_id, name, version, download):
    return Package(spdx_id=spdx_id, name=name, version=version,
                   download_location=download, files_analyzed=False,
                   license_concluded=SpdxNoAssertion(),
                   license_declared=SpdxNoAssertion(),
                   copyright_text=SpdxNoAssertion())


def build_document(by_image, created):
    images, comps, rels = [], {}, []
    for img in sorted(by_image):
        if not by_image[img]:
            raise ValueError(f"{img}: no compiled components found")
        img_id = f"SPDXRef-image-{_safe(img)}"
        images.append(_package(img_id, f"{img}-image", None,
                               SpdxNoAssertion()))
        rels.append(Relationship("SPDXRef-DOCUMENT",
                                 RelationshipType.DESCRIBES, img_id))
        for name, ver, dl in by_image[img]:
            cid = f"SPDXRef-component-{_safe(name)}-{_safe(ver)[:12]}"
            if cid not in comps:
                comps[cid] = _package(
                    cid, name, None if ver == NOASSERT else ver,
                    SpdxNoAssertion() if dl == NOASSERT else dl)
            rels.append(Relationship(img_id, RelationshipType.CONTAINS, cid))
    info = CreationInfo(
        spdx_version="SPDX-2.3", spdx_id="SPDXRef-DOCUMENT",
        name="mcuboot-lab-firmware",
        document_namespace=NAMESPACE + created.strftime("%Y%m%dT%H%M%SZ"),
        creators=[Actor(ActorType.TOOL, "mcuboot-lab make_sbom.py")],
        created=created)
    return Document(creation_info=info, packages=images + list(comps.values()),
                    relationships=rels)


def write_sbom(doc, path):
    problems = validate_full_spdx_document(doc)
    if problems:
        raise ValueError("invalid SPDX: " + "; ".join(
            m.validation_message for m in problems[:3]))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    write_file(doc, str(path), validate=False)


META_FLAGS = ["-Dmcuboot-lab_CONFIG_BUILD_OUTPUT_META=y",
              "-Dmcuboot_CONFIG_BUILD_OUTPUT_META=y"]


def recipe_commands(src, build, work):
    """The commands, in order, that make west spdx work on a sysbuild build.

    west spdx needs a query file before the build (init), the module list
    that BUILD_OUTPUT_META writes, and a separate init and CMake run for each
    image folder, because sysbuild configures every image on its own.
    -p auto, not -p always: a pristine build would erase the init file.
    """
    src, build, work = Path(src), Path(build), Path(work)
    cmds = [["west", "spdx", "--init", "-d", str(build)],
            ["west", "build", "-p", "auto", "-b", build_images.BOARD,
             "--sysbuild", "-d", str(build), str(src), "--", *META_FLAGS]]
    for img in IMAGES:
        d = build / img
        cmds += [["west", "spdx", "--init", "-d", str(d)],
                 ["west", "build", "-d", str(d), "--cmake-only"],
                 ["west", "spdx", "-d", str(d), "-s", str(work / f"spdx-{img}")]]
    return cmds


def _repo_version(repo):
    text = (Path(repo) / "VERSION").read_text()
    parts = []
    for key in ("VERSION_MAJOR", "VERSION_MINOR", "PATCHLEVEL"):
        m = re.search(rf"^{key}\s*=\s*(\d+)", text, flags=re.M)
        if not m:
            raise ValueError(f"{key} not found in VERSION")
        parts.append(m.group(1))
    return ".".join(parts)


def run_recipe(repo, work, workspace, run=subprocess.run):
    work = Path(work)
    build = work / "build"
    shutil.rmtree(build, ignore_errors=True)
    for img in IMAGES:
        shutil.rmtree(work / f"spdx-{img}", ignore_errors=True)
    work.mkdir(parents=True, exist_ok=True)
    src = build_images.prepare_source(repo, work / "src", _repo_version(repo))
    log = work / "sbom.log"
    with open(log, "w") as f:
        for cmd in recipe_commands(src, build, work):
            f.write("$ " + " ".join(cmd) + "\n")
            f.flush()
            rc = run(cmd, cwd=str(workspace), stdout=f,
                     stderr=subprocess.STDOUT).returncode
            if rc != 0:
                raise RuntimeError(f"exit {rc} from: {' '.join(cmd[:4])} (log {log})")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--from-spdx",
                   help="folder holding spdx-mcuboot-lab/ and spdx-mcuboot/")
    g.add_argument("--build", metavar="WORKDIR",
                   help="run the whole recipe, working in WORKDIR (outside the repo)")
    p.add_argument("--workspace", default=str(Path.home() / "zephyrproject"),
                   help="west workspace to run west in")
    p.add_argument("--out", default=str(
        Path(__file__).resolve().parent.parent / "sbom" / "mcuboot-lab.spdx"))
    p.add_argument("--created", default=None,
                   help="UTC time such as 2026-11-17T18:10:09, default now")
    a = p.parse_args(argv)
    created = (datetime.fromisoformat(a.created) if a.created else
               datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None))
    try:
        root = a.from_spdx
        if a.build:
            run_recipe(Path(__file__).resolve().parent.parent, a.build,
                       a.workspace)
            root = a.build
        by_image = read_images(root)
        write_sbom(build_document(by_image, created), a.out)
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"refused: {e}", file=sys.stderr)
        return 1
    for img, comps in by_image.items():
        print(f"{img}: {len(comps)} components: "
              + ", ".join(c[0] for c in comps))
    print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
