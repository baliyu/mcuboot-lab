"""Tests for scripts/make_sbom.py.

AI-assisted: drafted with Claude, checked by the author.
"""
import sys
from datetime import datetime
from pathlib import Path

import pytest
from spdx_tools.spdx.model import (Actor, ActorType, Checksum, ChecksumAlgorithm,
                                   CreationInfo, Document, File, Package,
                                   Relationship, RelationshipType,
                                   SpdxNoAssertion)
from spdx_tools.spdx.parser.parse_anything import parse_file
from spdx_tools.spdx.validation.document_validator import \
    validate_full_spdx_document
from spdx_tools.spdx.writer.write_anything import write_file

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import make_sbom as m  # noqa: E402

MCU = ("mcuboot", "6d3b3d2", "git+https://example.com/mcuboot@6d3b3d2")
ZEP = ("zephyr", "4.4.2", "NOASSERTION")


def _pkg(spdx_id, name, version, download):
    return Package(spdx_id=spdx_id, name=name, version=version,
                   download_location=download, files_analyzed=False,
                   license_concluded=SpdxNoAssertion(),
                   license_declared=SpdxNoAssertion(),
                   copyright_text=SpdxNoAssertion())


def _file(spdx_id):
    return File(name="./" + spdx_id + ".c", spdx_id=spdx_id,
                checksums=[Checksum(ChecksumAlgorithm.SHA1, "0" * 40)])


def _write_zephyr(path, with_mcuboot):
    info = CreationInfo(spdx_version="SPDX-2.3", spdx_id="SPDXRef-DOCUMENT",
                        name="fixture",
                        document_namespace="https://example.com/fixture",
                        creators=[Actor(ActorType.TOOL, "fixture")],
                        created=datetime(2026, 1, 1))
    pk = [_pkg("SPDXRef-zephyr", "zephyr", "4.4.2", SpdxNoAssertion()),
          _pkg("SPDXRef-acpica-sources", "acpica-sources", "abc",
               "git+https://example.com/acpica@abc")]
    files = [_file("SPDXRef-File-a")]
    rels = [Relationship("SPDXRef-DOCUMENT", RelationshipType.DESCRIBES, p.spdx_id)
            for p in pk]
    rels.append(Relationship("SPDXRef-zephyr", RelationshipType.CONTAINS,
                             "SPDXRef-File-a"))
    if with_mcuboot:
        pk.append(_pkg("SPDXRef-mcuboot-sources", "mcuboot-sources", MCU[1], MCU[2]))
        files.append(_file("SPDXRef-File-b"))
        rels.append(Relationship("SPDXRef-DOCUMENT", RelationshipType.DESCRIBES,
                                 "SPDXRef-mcuboot-sources"))
        rels.append(Relationship("SPDXRef-mcuboot-sources",
                                 RelationshipType.CONTAINS, "SPDXRef-File-b"))
    path.parent.mkdir(parents=True, exist_ok=True)
    write_file(Document(creation_info=info, packages=pk, files=files,
                        relationships=rels), str(path), validate=False)


def test_used_components_keeps_only_packages_with_files(tmp_path):
    _write_zephyr(tmp_path / "z.spdx", with_mcuboot=True)
    assert m.used_components(tmp_path / "z.spdx") == [MCU, ZEP]


def test_unused_module_is_left_out(tmp_path):
    _write_zephyr(tmp_path / "z.spdx", with_mcuboot=False)
    names = [c[0] for c in m.used_components(tmp_path / "z.spdx")]
    assert names == ["zephyr"]


def test_document_validates_and_describes_each_image():
    doc = m.build_document({"mcuboot-lab": [ZEP], "mcuboot": [MCU, ZEP]},
                           datetime(2026, 11, 17, 18, 0, 0))
    assert validate_full_spdx_document(doc) == []
    described = [r for r in doc.relationships
                 if r.relationship_type == RelationshipType.DESCRIBES]
    assert len(described) == 2


def test_shared_component_is_one_package_with_two_links():
    doc = m.build_document({"mcuboot-lab": [ZEP], "mcuboot": [MCU, ZEP]},
                           datetime(2026, 11, 17, 18, 0, 0))
    assert [p.name for p in doc.packages].count("zephyr") == 1
    links = [r for r in doc.relationships
             if r.relationship_type == RelationshipType.CONTAINS
             and "zephyr" in r.related_spdx_element_id]
    assert len(links) == 2


def test_same_input_gives_same_bytes(tmp_path):
    when = datetime(2026, 11, 17, 18, 0, 0)
    for n in ("a", "b"):
        m.write_sbom(m.build_document({"mcuboot-lab": [ZEP], "mcuboot": [MCU, ZEP]},
                                      when), tmp_path / f"{n}.spdx")
    assert (tmp_path / "a.spdx").read_bytes() == (tmp_path / "b.spdx").read_bytes()


def test_written_file_reads_back(tmp_path):
    m.write_sbom(m.build_document({"mcuboot-lab": [ZEP], "mcuboot": [MCU, ZEP]},
                                  datetime(2026, 11, 17, 18, 0, 0)),
                 tmp_path / "s.spdx")
    names = {p.name for p in parse_file(str(tmp_path / "s.spdx")).packages}
    assert names == {"mcuboot-lab-image", "mcuboot-image", "mcuboot", "zephyr"}


def test_image_with_no_components_is_refused():
    with pytest.raises(ValueError):
        m.build_document({"mcuboot-lab": [], "mcuboot": [MCU]},
                         datetime(2026, 11, 17, 18, 0, 0))


def test_cli_from_spdx_writes_a_file(tmp_path):
    _write_zephyr(tmp_path / "spdx-mcuboot-lab" / "zephyr.spdx", False)
    _write_zephyr(tmp_path / "spdx-mcuboot" / "zephyr.spdx", True)
    out = tmp_path / "out" / "sbom.spdx"
    rc = m.main(["--from-spdx", str(tmp_path), "--out", str(out),
                 "--created", "2026-11-17T18:00:00"])
    assert rc == 0 and out.is_file()
    assert "mcuboot" in {p.name for p in parse_file(str(out)).packages}


def test_cli_refuses_a_missing_folder(tmp_path, capsys):
    assert m.main(["--from-spdx", str(tmp_path / "nope")]) == 1
    assert "refused" in capsys.readouterr().err


def test_package_names_are_unique():
    doc = m.build_document({"mcuboot-lab": [ZEP], "mcuboot": [MCU, ZEP]},
                           datetime(2026, 11, 17, 18, 0, 0))
    names = [p.name for p in doc.packages]
    assert len(names) == len(set(names))


def test_committed_sbom_is_valid_and_lists_the_components():
    path = Path(__file__).resolve().parent.parent / "sbom" / "mcuboot-lab.spdx"
    doc = parse_file(str(path))
    assert validate_full_spdx_document(doc) == []
    names = {p.name for p in doc.packages}
    assert {"zephyr", "mcuboot", "hal_nordic",
            "mcuboot-lab-image", "mcuboot-image"} <= names
    mcu = [p for p in doc.packages if p.name == "mcuboot"][0]
    assert len(mcu.version) == 40
    assert "/home/" not in path.read_text()


REPO = Path(__file__).resolve().parent.parent


class _Done:
    def __init__(self, rc):
        self.returncode = rc


def test_recipe_runs_init_before_build_with_the_meta_flags():
    cmds = m.recipe_commands(Path("s"), Path("b"), Path("w"))
    assert cmds[0][:3] == ["west", "spdx", "--init"]
    build = cmds[1]
    assert build[:2] == ["west", "build"] and "--sysbuild" in build
    assert build[build.index("-p") + 1] == "auto"
    assert all(flag in build for flag in m.META_FLAGS)
    for img in m.IMAGES:
        assert any(c[:2] == ["west", "spdx"] and c[-1].endswith("spdx-" + img)
                   for c in cmds)


def test_run_recipe_stops_at_first_failure(tmp_path):
    calls = []

    def fake(cmd, **kw):
        calls.append(cmd)
        return _Done(1 if len(calls) == 2 else 0)

    with pytest.raises(RuntimeError):
        m.run_recipe(REPO, tmp_path, tmp_path, run=fake)
    assert len(calls) == 2


def test_run_recipe_runs_every_step_in_the_workspace(tmp_path):
    seen = []

    def fake(cmd, **kw):
        seen.append(kw["cwd"])
        return _Done(0)

    m.run_recipe(REPO, tmp_path, tmp_path / "ws", run=fake)
    assert len(seen) == len(m.recipe_commands("s", "b", "w"))
    assert set(seen) == {str(tmp_path / "ws")}


def test_cli_needs_one_mode():
    with pytest.raises(SystemExit):
        m.main([])
