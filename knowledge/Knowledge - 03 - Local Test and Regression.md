# Knowledge - 03 - Local Test and Regression

_How the local harness works and when to use each suite_

**Summary:** The local harness exists to test the stable collector line from a local repo-style layout without changing the collector engine for every test case.

| Source class | Authoritative basis |
| --- | --- |
| Project sources | project_sources/run_DCOIR_Tests.ps1; project_sources/DCOIR_Collector.ps1; project_sources/DOC-01_AFRICOM_SOC_IR_Project_Setup_and_Workflow.txt; project_sources/DOC-03_DCOIR_Repository_Layout_Spec_v1_0_0.txt |
| Official external sources | Not required for this page |
| Scope note | This page explains the current GitHub-readable harness source and the runtime filenames the operator will actually use in a local repo-style layout. |

## Why these files exist

- The current GitHub-readable harness source is `project_sources/run_DCOIR_Tests.ps1`.
- The current runtime collector filename remains `DCOIR_Collector.ps1`.
- The harness is designed to restage and exercise the stable collector line from a local repo-style layout without inventing a separate test-only engine.
- The current governed line does not carry a separate default CMD wrapper for the harness.

## Harness parameters

| Parameter | Purpose | Current default |
| --- | --- | --- |
| -Suite | Select Core, Retrieval, QuickAliases, or FullRegression | Core |
| -CollectorPath | Path to the local runtime collector | .\DCOIR_Collector.ps1 |
| -OutputRoot | Directory for test outputs | .\TestResults |
| -MasterZipPath | Path to the master collector ZIP used for restaging | .\assets\DCOIR_Collector.zip |
| -ContinueOnError | Keep running even if a step fails | off |
| -SkipCleanup | Leave DCOIR run output in place for inspection | off |

## Common local commands

| Use case | Command |
| --- | --- |
| Run the Core suite directly | powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_DCOIR_Tests.ps1 -Suite Core |
| Run the Retrieval suite directly | powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_DCOIR_Tests.ps1 -Suite Retrieval |
| Run the QuickAliases suite directly | powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_DCOIR_Tests.ps1 -Suite QuickAliases |
| Run the full regression directly | powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_DCOIR_Tests.ps1 -Suite FullRegression |

## What the harness actually does

- Restages the working `DCOIR_Collector.zip` from the master ZIP before each suite.
- Invokes the stable collector runtime with quick aliases rather than inventing separate test-only code paths.
- Writes logs and summary outputs under the run output root.
- Lets the operator leave artifacts in place with `-SkipCleanup` when needed for debugging.
> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
