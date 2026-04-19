# Knowledge - 03 - Local Test and Regression

_How the local harness works, how to run manual validation cleanly, and when to use each lane_

**Summary:** Local harness behavior, suite selection, restaging logic, manual-test-driver standards, and practical regression use from a repo-style layout.

| Source class | Authoritative basis |
| --- | --- |
| Project sources | project_sources/run_DCOIR_Tests.ps1; project_sources/DCOIR_Collector.ps1; project_sources/validate_DCOIR_Run.ps1; project_sources/DOC-01_AFRICOM_SOC_IR_Project_Setup_and_Workflow.txt; project_sources/DOC-03_DCOIR_Repository_Layout_Spec_v1_0_0.txt; project_sources/DOC-12_DCOIR_Collector_Runtime_Packaging_Pipeline_v1_0_0.txt |
| Official external sources | Not required for this page |
| Scope note | This page explains the current GitHub-readable harness source, the runtime filenames the operator will actually use in a local repo-style layout, and the standard manual test-driver pattern that should align with Airtable Validation Test Cases. |

## Why these files exist

- The current GitHub-readable harness source is `project_sources/run_DCOIR_Tests.ps1`.
- The current runtime collector filename remains `DCOIR_Collector.ps1`.
- The current standalone validation-gates script is `project_sources/validate_DCOIR_Run.ps1`.
- The harness is designed to restage and exercise the stable collector line from a local repo-style layout without inventing a separate test-only engine.
- The current governed line does not carry a separate default CMD wrapper for the harness.
- The local manual lane should reuse the same governed runtime and validation surfaces rather than drifting into ad hoc one-off steps that only exist in chat history.

## Harness parameters

| Parameter | Purpose | Current default |
| --- | --- | --- |
| `-Suite` | Select Core, Retrieval, QuickAliases, SessionBehavior, TargetedCollection, ChunkingOversizeArtifact, ChunkingReconstructionMetadata, MajorVersion, FullRegression, or FailureGates | Core |
| `-CollectorPath` | Path to the local runtime collector | `.\DCOIR_Collector.ps1` |
| `-OutputRoot` | Directory for test outputs | `.\TestResults` |
| `-MasterZipPath` | Path to the master collector ZIP used for restaging | `.\assets\DCOIR_Collector.zip` |
| `-LiveResponseMode` | Remap paths to the live-response-style temp layout | off |
| `-ContinueOnError` | Keep running even if a step fails | off |
| `-SkipCleanup` | Leave DCOIR run output in place for inspection | off |

## Common local commands

| Use case | Command |
| --- | --- |
| Run the Core suite directly | `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_DCOIR_Tests.ps1 -Suite Core` |
| Run the Retrieval suite directly | `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_DCOIR_Tests.ps1 -Suite Retrieval` |
| Run the QuickAliases suite directly | `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_DCOIR_Tests.ps1 -Suite QuickAliases` |
| Run the SessionBehavior suite directly | `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_DCOIR_Tests.ps1 -Suite SessionBehavior` |
| Run the TargetedCollection suite directly | `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_DCOIR_Tests.ps1 -Suite TargetedCollection` |
| Run the FailureGates suite directly | `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_DCOIR_Tests.ps1 -Suite FailureGates` |
| Run the full regression directly | `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_DCOIR_Tests.ps1 -Suite FullRegression` |

## What the harness actually does

- Restages the working `DCOIR_Collector.zip` from the master ZIP before each suite.
- Invokes the stable collector runtime with quick aliases rather than inventing separate test-only code paths.
- Writes per-step logs plus suite summary text and JSON under the run output root.
- Verifies output-contract and failure-gate surfaces that are currently implemented in the harness.
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

### SessionBehavior
The SessionBehavior suite proves enrich-session creation, reuse, and finalize semantics.

### TargetedCollection
The TargetedCollection suite proves the current targeted output surfaces and time-window carry-through behavior. It does not, by itself, prove true same-host subset narrowing unless that comparison is run explicitly.

### FailureGates
The FailureGates suite is the negative-path lane. It is where bind rejects, malformed quick input, degraded explicit-window behavior, and similar failure-family assertions belong.

### FullRegression
FullRegression is the deep confidence pass. It is the choice when multiple related behaviors changed, when packaging or runtime behavior changed materially, or when a release-minded operator wants the deeper confidence pass before calling a change ready.

## Restaging and repeatability

Restaging is one of the most important harness behaviors. The harness is not just launching commands; it is resetting the test surface so one run does not silently contaminate the next. That keeps results comparable and makes it easier to distinguish a real regression from leftover output or an already-modified working folder.

## Parameters that matter operationally

The current parameter set is small, but each one changes the meaning of the run:
- `-Suite` chooses the testing surface and therefore the expected breadth of validation
- `-CollectorPath` decides which runtime file is actually under test
- `-OutputRoot` determines where evidence about the run will accumulate
- `-MasterZipPath` controls the restaging source for runtime packaging
- `-LiveResponseMode` swaps into the temp-path execution model when that is the lane under test
- `-ContinueOnError` changes whether the run behaves like a strict gate or an exploratory sweep
- `-SkipCleanup` changes whether the run leaves artifacts available for post-run inspection

## How to read harness output

A harness run produces more than a pass or fail feeling. Useful interpretation asks:
- which suite ran
- whether restaging succeeded before execution started
- which collector paths or quick aliases were exercised
- where logs and staged results landed
- whether failures happened before runtime execution, during invocation, or during output evaluation
- whether leftover artifacts were intentionally preserved or accidentally left behind

## Standard local manual test-driver pattern

This is the current reusable manual-driver standard for collector local validation. Use it when the test case lives in Airtable `Validation Test Cases` and the intent is one bounded operator-visible proof, not a broad exploratory sweep.

### Step 1: name the exact test objective
Before running anything, identify the Airtable test row or create the equivalent local note with:
- the exact behavior under test
- the execution lane (`Local Manual`, `Harness`, or `Live Response`)
- the command or method
- the pass criteria
- the fail criteria
- the evidence that must be captured

A local manual test is not complete just because the collector prints a plausible-looking block of text. It is complete only when the observed result can be checked against a named expected outcome.

### Step 2: prepare the run surface
For collect-style local tests, confirm:
- the runtime file is the intended one under test
- the working ZIP or runtime package is staged if the scenario requires it
- the output root is known before execution
- you already know whether cleanup should be skipped to preserve evidence

If the scenario is likely to need post-run review, leave evidence in place first and clean up afterward.

### Step 3: run one bounded command
Use one bounded command that matches the test objective. Good manual-driver runs are narrow enough that the operator can say exactly what was proven.

Examples:
- run a single local collect flow
- run one targeted collect with an explicit time window
- run one enrich start/add/finalize chain for a specific action family
- run the standalone validation-gates script against one completed run

### Step 4: verify emitted contract markers and artifacts
For collector runs, check the output markers and then confirm the referenced artifacts really exist on disk.

Typical markers include:
- `STATUS`
- `RUN_ID`
- `COLLECT_BUNDLE_PATH` or `ENRICH_BUNDLE_PATH`
- `NEXT_GET_FILE`
- `NEXT_OPTIONS`
- `CLEANUP_COMMAND`
- `DELETE_SCRIPT_COMMAND`
- `GEMINI_UPLOAD_GUIDANCE`
- current diagnostic or overview surfaces such as execution-context, audit-policy, analyst-overview, or parallel-proof paths when that branch is in scope

A marker-only pass is not enough when the test claims artifact behavior. The referenced files must exist and match the expected semantics.

### Step 5: run validation-gates when the branch calls for it
When the test is collect-output or run-surface oriented, use the standalone validator rather than relying only on human inspection.

Typical commands:
- `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\project_sources\validate_DCOIR_Run.ps1 -RunRoot <run_root>`
- `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\project_sources\validate_DCOIR_Run.ps1 -RunRoot <run_root> -PushMode`
- add `-Json` when the output needs to be preserved or machine-compared

Use this lane when the question is whether the run emitted the expected governed diagnostic, overview, or bundle surfaces. Do not use packaging success alone as proof that the runtime behavior is correct.

### Step 6: capture evidence in Airtable honestly
Update the Airtable row with one of these only:
- `Passed`
- `Partial`
- `Failed`
- `Blocked`
- leave as `Not Run` if the execution never really happened

The note should say exactly what was observed and what remains unresolved. If the run passed the narrow objective but exposed another issue, preserve both facts instead of flattening the result into a vague success or failure.

### Step 7: clean up only after evidence is safe
If the run created artifacts that still matter for review, keep them until the evidence is captured. Cleanup is the end of the manual-driver cycle, not the middle.

## Recommended manual-test row shape

A good collector manual row should answer these questions without requiring chat reconstruction:
- What exact behavior is under test?
- Which execution lane is being used?
- What exact command or method should be run?
- What counts as a pass?
- What counts as a fail?
- What evidence path or artifact should be inspected?
- What follow-on action should happen if the test fails?

If a row cannot answer those questions, it is not yet a good reusable manual driver.

## Practical local testing patterns

### Fast sanity pass after a small edit
Run the smallest suite or single manual command that exercises the changed behavior first. Do not start with FullRegression when the only question is whether one alias still points to the correct path.

### Debugging a packaging or staging issue
Favor leaving artifacts in place, keeping the output root obvious, and checking whether restaging actually produced the expected runtime surface before blaming the collector logic.

### Output-contract or bundle-surface proof
Run one bounded collect or enrich flow, then use `validate_DCOIR_Run.ps1` or direct artifact inspection to verify the exact claimed surfaces.

### Regression after grouped collector changes
Use a wider suite once the narrow behavior passes. Local manual proof and harness proof should complement one another, not compete.

## Common local mistakes

- running from a directory that does not contain the expected runtime file and asset paths
- assuming the current governed line still carries a default CMD wrapper when the direct PowerShell harness is the current source
- interpreting every failure as collector logic breakage instead of checking layout, staging, or path assumptions
- leaving artifacts around accidentally and then misreading later runs as fresh evidence
- using local syntax examples when the real next operator move is endpoint-side, or vice versa
- treating package build success as proof of runtime correctness
- claiming a pass from console text alone without checking whether the referenced files were actually created

## Manual testing note

For current manual validation work, Airtable `Validation Test Cases` is the dynamic manual-testing surface. GitHub remains the engineering authority for the collector runtime, the harness, the standalone validator, and the packaging source line. The most useful habit is to let Airtable track what was tested and observed while GitHub remains the place where durable source changes land.

## Operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
