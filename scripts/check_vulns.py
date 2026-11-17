"""Check the SBOM against OSV and compare the answers with docs/triage.csv.

AI-assisted: drafted with Claude, checked by the author.

OSV is asked by git commit, because two of the three components have no
release number. Exit codes: 0 every finding is already triaged, 1 a new
finding (or any affected one with --strict), 2 OSV could not be reached.
"""
import argparse
import csv
import json
import re
import sys
import urllib.request
from pathlib import Path

from spdx_tools.spdx.parser.parse_anything import parse_file

OSV_URL = "https://api.osv.dev/v1/query"
STATUSES = ("affected", "not_affected", "under_investigation", "fixed")
COMMIT_RE = re.compile(r"@([0-9a-f]{40})$")
REPO = Path(__file__).resolve().parent.parent


def components(sbom):
    """Return sorted (name, commit) for packages with a git+url@commit location."""
    out = []
    for p in parse_file(str(sbom)).packages:
        m = COMMIT_RE.search(str(p.download_location))
        if m:
            out.append((p.name, m.group(1)))
    return sorted(out)


def osv_ids(commit, timeout=25):
    body = json.dumps({"commit": commit}).encode()
    req = urllib.request.Request(OSV_URL, data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.load(r)
    except Exception as e:
        raise RuntimeError(
            f"OSV query failed for {commit[:10]}: {type(e).__name__}: {e}") from e
    if data.get("next_page_token"):
        raise RuntimeError(f"OSV returned more than one page for {commit[:10]}; "
                           "paging is not handled")
    return sorted(v["id"] for v in data.get("vulns", []))


def read_triage(path):
    with open(path, newline="", encoding="utf-8") as f:
        return {row["id"]: row for row in csv.DictReader(f)}


def check(sbom, triage, fetch=osv_ids):
    findings = []
    for name, commit in components(sbom):
        for vid in fetch(commit):
            t = triage.get(vid)
            findings.append({"component": name, "id": vid,
                             "status": t["status"] if t else "NEW",
                             "reason": t["reason"] if t else "not triaged yet"})
    return findings


def main(argv=None, fetch=osv_ids):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--sbom", default=str(REPO / "sbom" / "mcuboot-lab.spdx"))
    p.add_argument("--triage", default=str(REPO / "docs" / "triage.csv"))
    p.add_argument("--strict", action="store_true",
                   help="also fail on affected or under_investigation findings")
    a = p.parse_args(argv)
    try:
        triage = read_triage(a.triage)
        findings = check(a.sbom, triage, fetch)
    except (RuntimeError, FileNotFoundError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    n = len(components(a.sbom))
    print(f"checked {n} components, {len(findings)} findings")
    for f in findings:
        print(f"  {f['component']:<11} {f['id']:<16} {f['status']:<19} {f['reason']}")
    stale = sorted(set(triage) - {f["id"] for f in findings})
    if stale:
        print("triage rows with no current finding: " + ", ".join(stale))
    if any(f["status"] == "NEW" for f in findings):
        print("NEW findings need triage: add them to docs/triage.csv")
        return 1
    if a.strict and any(f["status"] in ("affected", "under_investigation")
                        for f in findings):
        print("strict: some findings are affected or under investigation")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
