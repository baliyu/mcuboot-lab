"""Write a small SPDX bill of materials for the lab firmware.

AI-assisted: drafted with Claude, checked by the author.

west spdx lists every module in the west manifest (66 here). This script
keeps only the modules that have at least one compiled source file in an
image, so the bill of materials describes the firmware and not the SDK.
"""
import argparse
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
        images.append(_package(img_id, img, None, SpdxNoAssertion()))
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


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--from-spdx", required=True,
                   help="folder holding spdx-mcuboot-lab/ and spdx-mcuboot/")
    p.add_argument("--out", default=str(
        Path(__file__).resolve().parent.parent / "sbom" / "mcuboot-lab.spdx"))
    p.add_argument("--created", default=None,
                   help="UTC time such as 2026-11-17T18:10:09, default now")
    a = p.parse_args(argv)
    created = (datetime.fromisoformat(a.created) if a.created else
               datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None))
    try:
        by_image = read_images(a.from_spdx)
        write_sbom(build_document(by_image, created), a.out)
    except (FileNotFoundError, ValueError) as e:
        print(f"refused: {e}", file=sys.stderr)
        return 1
    for img, comps in by_image.items():
        print(f"{img}: {len(comps)} components: "
              + ", ".join(c[0] for c in comps))
    print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
