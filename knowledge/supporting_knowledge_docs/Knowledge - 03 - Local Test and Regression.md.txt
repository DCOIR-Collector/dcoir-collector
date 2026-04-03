# Knowledge - 03 - Local Test and Regression

_How the local harness works and when to use each suite_

**Summary:** The local harness exists to test the stable collector line from a local repo-style layout without changing the collector engine for every test case.

| Source class | Authoritative basis |
| --- | --- |
| Project sources | run_DCOIR_Tests.ps1.txt; run_DCOIR_Tests.cmd.txt; DOC-01_AFRICOM_SOC_IR_Project_Setup_and_Workflow.txt; DOC-03_DCOIR_Repository_Layout_Spec_v1_0_0.txt |
| Official external sources | Not required for this page |
| Scope note | This page explains the uploaded Project-readable source files and the runtime/downloaded filenames that repo mode emits. |

## Why these files exist

- The uploaded Project-readable source for the PowerShell regression harness is run_DCOIR_Tests.ps1.txt; the downloaded runtime filename in repo mode is run_DCOIR_Tests.ps1.
- The uploaded Project-readable source for the one-command wrapper is run_DCOIR_Tests.cmd.txt; the downloaded runtime filename in repo mode is run_DCOIR_Tests.cmd.
- In repo mode, the final runtime files are run_DCOIR_Tests.ps1 and run_DCOIR_Tests.cmd because bundle generation strips only the final .txt where the layout rules allow that.
- The harness design assumes the collector runtime file sits beside the harnesses in stable/, while DCOIR_Collector.zip sits in stable/assets/.

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
| Run the default full-regression wrapper | .\run_DCOIR_Tests.cmd |
| Run the Core suite directly | powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_DCOIR_Tests.ps1 -Suite Core |
| Run the Retrieval suite directly | powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_DCOIR_Tests.ps1 -Suite Retrieval |
| Run the QuickAliases suite directly | powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_DCOIR_Tests.ps1 -Suite QuickAliases |
| Run the full regression directly | powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_DCOIR_Tests.ps1 -Suite FullRegression |

## What the harness actually does

- Restages the working DCOIR_Collector.zip from the master ZIP before each suite.
- Invokes the stable collector runtime with -Quick aliases rather than inventing separate test-only code paths.
- Writes logs and summary outputs under the run output root.
- Lets the operator leave artifacts in place with -SkipCleanup when needed for debugging.
> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
