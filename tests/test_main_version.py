# AI-assisted: drafted with Claude, checked by the author.
import re
from pathlib import Path

SRC = (Path(__file__).resolve().parent.parent / "src" / "main.c").read_text()


def test_main_uses_generated_version():
    assert "APP_VERSION_STRING" in SRC
    assert "zephyr/app_version.h" in SRC


def test_main_has_no_hardcoded_version():
    assert not re.search(r"app v\d", SRC)
