# DCOIR Manual Test Plan

Richer contextual help is now part of the collector command/help surface.
This plan tests both the main help and the new per-area contextual help path.
It also checks the collector's tuned first-review surfaces and records the bounded manual T2-pathway mapping follow-on.

| Order | Test | What it checks | Pass | Fail | Grade |
|---:|---|---|---|---|---|
| 1 | Git prerequisite | Git exists or can be installed automatically | Git is ready | Git cannot be used | PASS / FAIL / ACTION |
| 2 | Python prerequisite | Python exists or can be installed automatically | Python is ready | Python cannot be used | PASS / FAIL / ACTION |
| 3 | Repo fetch/update | The repo can be cloned or updated locally | Repo is present and required files exist | Git operation fails or files are missing | PASS / FAIL |
| 4 | Package validation | Current package rules are valid | Validator exits cleanly | Validator fails | PASS / FAIL |
| 5 | Package build | Delivery package builds | Zip is created | Build fails | PASS / FAIL |
| 6 | Runtime restore/stage | The combined collector PS1 and live-style zip are staged next to the framework | `DCOIR_Collector.ps1` and `DCOIR_Collector.zip` are present | Staging is incomplete | PASS / FAIL |
| 7 | Top-level help | `-Help` prints the main help text | Main help is shown | Help is missing or broken | PASS / FAIL |
| 8 | Quick help | `-Quick help` prints quick examples | Quick examples are shown | Quick help is missing or broken | PASS / FAIL |
| 9 | Contextual help | `-Quick help-collect` prints per-area guidance | Collect-specific help is shown | Contextual help is missing or generic | PASS / FAIL |
| 10 | Bad quick fallback | Bad quick command fails clearly and shows help | Clear error + help | Confusing failure | PASS / FAIL |
| 11 | Non-admin collect | Full live-style collect in normal PowerShell | Key output markers and bundle appear | Hard fail or missing outputs | PASS / PARTIAL / FAIL |
| 12 | Non-admin validator | Validator grades the non-admin run honestly | Validator passes | Validator fails or crashes | PASS / FAIL |
| 13 | Review-surface tuning | Follow-up queue, high-signal summary, and overview reflect the recent tuning | Benign noise is suppressed and overview fields are present | Known benign noise remains or overview fields are missing | PASS / FAIL |
| 14 | Non-admin targeted collect | Targeted collect emits targeted outputs | Scope and plan are present | Targeted outputs missing | PASS / PARTIAL / FAIL |
| 15 | Non-admin enrich lifecycle | Start/add/finalize session behavior | Session behaves correctly | Session behavior breaks | PASS / PARTIAL / FAIL |
| 16 | Non-admin bad inputs | Mistyped/bad commands fail clearly | Failures are clear and honest | Failures are confusing | PASS / PARTIAL / FAIL |
| 17 | Admin phase launch | Elevated phase opens | Admin phase starts | UAC launch fails | PASS / FAIL |
| 18 | Admin collect | Full live-style collect under admin | Key output markers and bundle appear | Hard fail or missing outputs | PASS / PARTIAL / FAIL |
| 19 | Admin validator | Validator grades the admin run honestly | Validator passes | Validator fails or crashes | PASS / FAIL |
| 20 | Admin vs non-admin compare | Elevation-related differences are visible | Differences are visible and explainable | Comparison data missing or unclear | PASS / PARTIAL / FAIL |
| 21 | T2 pathway mapping note | Operator gets the bounded follow-on for explicit T2 pathway proof | Clear next action is recorded | No usable guidance is recorded | ACTION |
| 22 | FullRegression harness | Deep regression against the staged runtime | FullRegression passes | FullRegression fails | PASS / FAIL |
| 23 | Package parity recheck | Package rules still pass after the run | Recheck passes | Recheck fails | PASS / FAIL |
| 24 | Cleanup | Cleanup works after evidence is saved | Cleanup completes | Cleanup is incomplete | PASS / PARTIAL / FAIL |
| 25 | Final signoff | One final verdict is produced | Ready / Ready with reservations / Not ready | No verdict | PASS / PARTIAL |
