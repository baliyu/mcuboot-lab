"""Checks on the security documents.

AI-assisted: drafted with Claude, checked by the author.
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DOCS = [REPO / "SECURITY.md", REPO / "docs" / "VULNERABILITY_HANDLING.md"]


def test_security_policy_has_the_required_sections():
    text = (REPO / "SECURITY.md").read_text(encoding="utf-8")
    for heading in ("## Supported versions", "## Reporting a vulnerability",
                    "## What to expect", "## In scope", "## Out of scope"):
        assert heading in text, heading
    assert "SECURITY: mcuboot-lab" in text


def test_relative_links_point_at_real_files():
    for doc in DOCS:
        text = doc.read_text(encoding="utf-8")
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            path = (doc.parent / target.split("#")[0]).resolve()
            assert path.exists(), f"{doc.name} links to missing {target}"


def test_documents_have_no_em_dashes_or_home_paths():
    for doc in DOCS:
        text = doc.read_text(encoding="utf-8")
        assert chr(8212) not in text, doc.name
        assert "/home/" not in text, doc.name
