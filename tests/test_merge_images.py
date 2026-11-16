# AI-assisted: drafted with Claude, checked by the author.
import sys
from pathlib import Path

import pytest
from intelhex import IntelHex

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import merge_images as mi  # noqa: E402


def block(addr, data):
    ih = IntelHex()
    ih.puts(addr, data)
    return ih


def test_merge_without_update_pads_gaps():
    out = mi.merge(block(0x10000, b"\x01" * 100), block(0x20000, b"\x02" * 200))
    assert len(out) == 0x10000 + 200
    assert out[0] == 0x01
    assert out[100] == 0xFF
    assert out[0x10000] == 0x02


def test_merge_with_update_fills_to_end_of_slot1():
    upd = block(0x40000, b"\x03" * 50)
    out = mi.merge(block(0x10000, b"\x01"), block(0x20000, b"\x02"), upd)
    assert len(out) == 0x50000
    assert out[0x30000] == 0x03
    assert out[0x30000 + 50] == 0xFF


def test_mcuboot_must_start_at_0x10000():
    with pytest.raises(ValueError):
        mi.merge(block(0x10010, b"\x01"), block(0x20000, b"\x02"))


def test_app_must_end_below_0x40000():
    with pytest.raises(ValueError):
        mi.merge(block(0x10000, b"\x01"), block(0x20000, b"\x02" * 0x20001))


def test_update_must_fit_slot1():
    upd = block(0x40000, b"\x03" * 0x20001)
    with pytest.raises(ValueError):
        mi.merge(block(0x10000, b"\x01"), block(0x20000, b"\x02"), upd)


def test_cli_writes_image(tmp_path):
    block(0x10000, b"\x01" * 10).write_hex_file(str(tmp_path / "m.hex"))
    block(0x20000, b"\x02" * 10).write_hex_file(str(tmp_path / "a.hex"))
    (tmp_path / "u.bin").write_bytes(b"\x03" * 10)
    out = tmp_path / "img.bin"
    rc = mi.main(["--mcuboot", str(tmp_path / "m.hex"),
                  "--app", str(tmp_path / "a.hex"),
                  "--update", str(tmp_path / "u.bin"),
                  "--out", str(out)])
    assert rc == 0
    assert out.stat().st_size == 0x50000
