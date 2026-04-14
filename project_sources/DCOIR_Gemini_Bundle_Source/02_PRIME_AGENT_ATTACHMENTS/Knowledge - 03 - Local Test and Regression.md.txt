# Knowledge - 03 - Local Test and Regression

_How the local harness works and when to use each suite_

**Summary:** Local harness behavior, suite selection, restaging logic, and practical regression use from a repo-style layout.

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

## Local regression philosophy

The local regression harness exists so the collector can be exercised from a clean repo-style layout without turning the runtime itself into a tangle of one-off debug switches. The working idea is stability first. The collector remains the thing being tested, and the harness provides repeatable orchestration around that stable line.

That design is useful because it preserves one runtime filename and one collector model while still letting the operator restage, rerun, inspect artifacts, and compare behavior across changes. A good harness protects the collector from ad hoc edits that only exist to make one isolated test easier.

## Repo-style layout expectations

The local harness assumes a repo-style working layout. The important paths are not arbitrary:
- the collector runtime should be reachable at the runtime filename the operator actually uses
- the harness should be reachable directly in PowerShell
- the master collector ZIP should exist in the expected asset location so restaging works predictably
- the output root should be writable and easy to inspect after a run

When those assumptions break, the first debugging question is not always whether the collector logic is wrong. Often the failure is a layout mismatch, a missing asset, or an invocation from the wrong current working directory.

## Suite selection and what each suite is trying to prove

### Core
The Core suite is the fastest baseline confidence check. It is the right first choice when the question is whether the stable collector line still behaves like the operator expects at a broad level.

### Retrieval
The Retrieval suite exists for branches where staged files, output movement, or retrieval-related expectations are the focus.

### QuickAliases
The QuickAliases suite validates that the high-friction operator shortcuts still map to the expected underlying behavior.

### FullRegression
FullRegression is the wide confidence pass. It is the choice when multiple related behaviors changed, when packaging or runtime behavior changed materially, or when a release-minded operator wants the deeper confidence pass before calling a change ready.

## Restaging and repeatability

Restaging is one of the most important harness behaviors. The harness is not just launching commands; it is resetting the test surface so one run does not silently contaminate the next. That keeps results comparable and makes it easier to distinguish a real regression from leftover output or an already-modified working folder.

## Parameters that matter operationally

The current parameter set is small, but each one changes the meaning of the run:
- `-Suite` chooses the testing surface and therefore the expected breadth of validation
- `-CollectorPath` decides which runtime file is actually under test
- `-OutputRoot` determines where evidence about the run will accumulate
- `-MasterZipPath` controls the restaging source for runtime packaging
- `-ContinueOnError` changes whether the run behaves like a strict gate or an exploratory sweep
- `-SkipCleanup` changes whether the run leaves artifacts available for post-run inspection

## How to read harness output

A harness run produces more than a pass/fail feeling. Useful interpretation asks:
- which suite ran
- whether restaging succeeded before execution started
- which collector paths or quick aliases were exercised
- where logs and staged results landed
- whether failures happened before runtime execution, during invocation, or during output evaluation
- whether leftover artifacts were intentionally preserved or accidentally left behind

## Practical local testing patterns

### Fast sanity pass after a small edit
Run the smallest suite that exercises the changed behavior first. Do not start with FullRegression when the only question is whether one alias still points to the correct path.

### Debugging a packaging or staging issue
Favor leaving artifacts in place, keeping the output root obvious, and checking whether restaging actually produced the expected runtime surface before blaming the collector logic.

### Regression after grouped collector changes
Use a wider suite once the narrow behavior passes.

## Common local mistakes

- running from a directory that does not contain the expected runtime file and asset paths
- assuming the current governed line still carries a default CMD wrapper when the direct PowerShell harness is the current source
- interpreting every failure as collector logic breakage instead of checking layout, staging, or path assumptions
- leaving artifacts around accidentally and then misreading later runs as fresh evidence
- using local syntax examples when the real next operator move is endpoint-side, or vice versa

## Manual testing note

For current manual validation work, Airtable Validation Test Cases is the dynamic manual-testing surface. GitHub remains the engineering authority for the collector runtime, the harness, and the packaging source line. The most useful habit is to let Airtable track what was tested and observed while GitHub remains the place where durable source changes land.

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

