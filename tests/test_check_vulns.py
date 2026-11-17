"""Tests for scripts/check_vulns.py and docs/triage.csv.

AI-assisted: drafted with Claude, checked by the author.
"""
import csv
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import check_vulns as cv  # noqa: E402
import make_sbom as m  # noqa: E402

OLD_ZEPHYR = "3f826560aaf81a444018293bd6acce3c339fe150"
OLD_MCUBOOT = "b69841820462fa0227d7fb407620405f6426bb4b"
EXPECTED_IDS = {"CVE-2026-127915", "CVE-2026-127916", "CVE-2026-128091",
                "CVE-2026-16659", "CVE-2026-16662", "CVE-2026-16664",
                "CVE-2026-16671"}


def _old_sbom(tmp_path):
    comps = [("zephyr", "2.7.0", m.ZEPHYR_URL + OLD_ZEPHYR)]
    path = tmp_path / "old.spdx"
    m.write_sbom(m.build_document({"img": comps}, datetime(2026, 11, 17)), path)
    return path


def _triage(tmp_path, rows):
    path = tmp_path / "triage.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["id", "component", "status", "reason", "checked"])
        w.writerows(rows)
    return path


def _fake(answers):
    return lambda commit: answers.get(commit, [])


def test_components_reads_the_committed_sbom():
    found = dict(cv.components(REPO / "sbom" / "mcuboot-lab.spdx"))
    assert set(found) == {"zephyr", "mcuboot", "hal_nordic"}
    assert all(len(c) == 40 for c in found.values())


def test_known_bad_commit_is_flagged_as_new(tmp_path, capsys):
    rc = cv.main(["--sbom", str(_old_sbom(tmp_path)),
                  "--triage", str(_triage(tmp_path, []))],
                 fetch=_fake({OLD_ZEPHYR: ["CVE-2023-0359"]}))
    out = capsys.readouterr().out
    assert rc == 1 and "CVE-2023-0359" in out and "NEW" in out


def test_triaged_finding_is_not_new(tmp_path, capsys):
    tri = _triage(tmp_path, [["CVE-2023-0359", "zephyr", "not_affected",
                              "feature off", "2026-11-17"]])
    rc = cv.main(["--sbom", str(_old_sbom(tmp_path)), "--triage", str(tri)],
                 fetch=_fake({OLD_ZEPHYR: ["CVE-2023-0359"]}))
    assert rc == 0 and "not_affected" in capsys.readouterr().out


def test_strict_fails_on_an_affected_finding(tmp_path):
    tri = _triage(tmp_path, [["CVE-2023-0359", "zephyr", "affected",
                              "code is compiled", "2026-11-17"]])
    args = ["--sbom", str(_old_sbom(tmp_path)), "--triage", str(tri)]
    fetch = _fake({OLD_ZEPHYR: ["CVE-2023-0359"]})
    assert cv.main(args, fetch=fetch) == 0
    assert cv.main(args + ["--strict"], fetch=fetch) == 1


def test_network_failure_is_exit_2_not_a_clean_result(tmp_path, capsys):
    def broken(commit):
        raise RuntimeError("no network")
    rc = cv.main(["--sbom", str(_old_sbom(tmp_path)),
                  "--triage", str(_triage(tmp_path, []))], fetch=broken)
    assert rc == 2 and "no network" in capsys.readouterr().err


def test_stale_triage_row_is_reported(tmp_path, capsys):
    tri = _triage(tmp_path, [["CVE-1999-0001", "zephyr", "fixed", "old", "2026-11-17"]])
    rc = cv.main(["--sbom", str(_old_sbom(tmp_path)), "--triage", str(tri)],
                 fetch=_fake({}))
    assert rc == 0 and "CVE-1999-0001" in capsys.readouterr().out


class _Resp:
    def __init__(self, payload):
        self._b = json.dumps(payload).encode()

    def read(self, *a):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_osv_ids_refuses_a_paged_answer_and_wraps_errors(monkeypatch):
    monkeypatch.setattr(cv.urllib.request, "urlopen", lambda *a, **k: _Resp(
        {"vulns": [{"id": "X"}], "next_page_token": "t"}))
    with pytest.raises(RuntimeError):
        cv.osv_ids("a" * 40)

    def boom(*a, **k):
        raise OSError("down")
    monkeypatch.setattr(cv.urllib.request, "urlopen", boom)
    with pytest.raises(RuntimeError):
        cv.osv_ids("a" * 40)


def test_triage_file_is_well_formed():
    path = REPO / "docs" / "triage.csv"
    text = path.read_text(encoding="utf-8")
    assert chr(8212) not in text
    rows = cv.read_triage(path)
    assert set(rows) == EXPECTED_IDS
    for r in rows.values():
        assert r["status"] in cv.STATUSES
        assert re.fullmatch(r"(CVE|GHSA)-[0-9A-Za-z-]+", r["id"])
        assert r["reason"].strip()
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", r["checked"])


@pytest.mark.skipif(os.environ.get("OSV_LIVE") != "1",
                    reason="set OSV_LIVE=1 to ask the real OSV")
def test_live_osv_flags_the_known_bad_commits():
    assert "CVE-2023-0359" in cv.osv_ids(OLD_ZEPHYR)
    assert cv.osv_ids(OLD_MCUBOOT)
