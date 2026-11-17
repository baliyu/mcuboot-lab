# Security policy

`mcuboot-lab` is a personal engineering project (a lab for MCUboot update and power-cut testing on an Arduino Nano 33 BLE), not a commercial product. I take security reports seriously and handle them on a best-effort basis.

## Supported versions
Only the latest commit on `main` is maintained.

## Reporting a vulnerability
Please do **not** open a public issue for a security problem.

1. Preferred: use GitHub's private vulnerability reporting (Security tab, then "Report a vulnerability").
2. Or email baliyu70@gmail.com with the subject `SECURITY: mcuboot-lab`.

Please include what you found, the affected files or commit, how to reproduce it, the impact you see, and whether you plan to publish it.

## What to expect
- I aim to acknowledge a report within 7 days. I work alone, so this is a target, not a guarantee.
- I will tell you whether I can reproduce it and agree a disclosure date with you (coordinated disclosure). I aim to fix or document the problem within 90 days.
- Once a fix exists I publish a GitHub security advisory with a description, the affected commits, the severity and what to do, and credit you if you wish.

## In scope
- Mistakes in the scripts that build, sign, merge or cut images (`scripts/`), for example anything that could leak or commit a signing key.
- Configuration in this repository that makes the boot or update check weaker than the README says.
- An update or power-cut sequence in my tests that leaves the board running an image it should have rejected.

## Out of scope
- Flaws in Zephyr, MCUboot or the Nordic HAL themselves. Please report those to the upstream projects. The versions this firmware contains are listed in the bill of materials, [sbom/mcuboot-lab.spdx](sbom/mcuboot-lab.spdx), and what I do when one of them is affected is in [docs/VULNERABILITY_HANDLING.md](docs/VULNERABILITY_HANDLING.md).
- Debugger and physical attacks on the board, and side-channel attacks. I have not assessed them.

## About this document
Drafted with AI assistance (Claude) and checked by the author.
