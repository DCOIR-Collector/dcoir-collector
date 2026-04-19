# DCOIR Manual Test Plan

Richer contextual help has been officially queued as a follow-on feature.
This plan tests the **current real help** now and leaves the richer per-area help feature out of scope for this run.

| Order | Test | What it checks | Pass | Fail | Grade |
|---:|---|---|---|---|---|
| 1 | Git prerequisite | Git exists or can be installed automatically | Git is ready | Git cannot be used | PASS / FAIL / ACTION |
| 2 | Python prerequisite | Python exists or can be installed automatically | Python is ready | Python cannot be used | PASS / FAIL / ACTION |
| 3 | Repo fetch/update | The repo can be cloned or updated locally | Repo is present and required files exist | Git operation fails or files are missing | PASS / FAIL |
| 4 | Package validation | Current package rules are valid | Validator exits cleanly | Validator fails | PASS / FAIL |
| 5 | Package build | Delivery package builds | Zip is created | Build fails | PASS / FAIL |
| 6 | Runtime restore/stage | The combined collector PS1 and live-style zip are staged next to the framework | `DCOIR_Collector.ps1` and `DCOIR_Collector.zip` are present | Staging is incomplete | PASS / FAIL |
| 7 | Top-level help | `-Help` prints the main help text | Main help is shown | Help is missing or broken | PASS / FAIL |
| 8 | Quick help | `-Quick help` prints quick examples | Quick examples are shown | Quick help is missing or broken | PASS / PARTIAL / FAIL |
| 9 | Bad quick fallback | Bad quick command fails clearly and shows help | Clear error + help | Confusing failure | PASS / FAIL |
| 10 | Non-admin collect | Full live-style collect in normal PowerShell | Key output markers and bundle appear | Hard fail or missing outputs | PASS / PARTIAL / FAIL |
| 11 | Non-admin validator | Validator grades the non-admin run honestly | Validator passes | Validator fails or crashes | PASS / FAIL |
| 12 | Non-admin targeted collect | Targeted collect emits targeted outputs | Scope and plan are present | Targeted outputs missing | PASS / PARTIAL / FAIL |
| 13 | Non-admin enrich lifecycle | Start/add/finalize session behavior | Session behaves correctly | Session behavior breaks | PASS / PARTIAL / FAIL |
| 14 | Non-admin bad inputs | Mistyped/bad commands fail clearly | Failures are clear and honest | Failures are confusing | PASS / PARTIAL / FAIL |
| 15 | Admin phase launch | Elevated phase opens | Admin phase starts | UAC launch fails | PASS / FAIL |
| 16 | Admin collect | Full live-style collect under admin | Key output markers and bundle appear | Hard fail or missing outputs | PASS / PARTIAL / FAIL |
| 17 | Admin validator | Validator grades the admin run honestly | Validator passes | Validator fails or crashes | PASS / FAIL |
| 18 | Admin vs non-admin compare | Elevation-related differences are visible | Differences are visible and explainable | Comparison data missing or unclear | PASS / PARTIAL / FAIL |
| 19 | FullRegression harness | Deep regression against the staged runtime | FullRegression passes | FullRegression fails | PASS / FAIL |
| 20 | Package parity recheck | Package rules still pass after the run | Recheck passes | Recheck fails | PASS / FAIL |
| 21 | Cleanup | Cleanup works after evidence is saved | Cleanup completes | Cleanup is incomplete | PASS / PARTIAL / FAIL |
| 22 | Final signoff | One final verdict is produced | Ready / Ready with reservations / Not ready | No verdict | PASS / PARTIAL |
