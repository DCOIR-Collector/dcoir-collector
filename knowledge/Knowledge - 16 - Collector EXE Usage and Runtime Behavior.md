# Knowledge - 16 - Collector EXE Usage and Runtime Behavior

_Optional EXE execution, validation, and PS1 behavior differences_

**Summary:** Use this page when building, running, or interpreting the optional DCOIR Collector EXE.

---

## What the EXE is

The optional EXE is a packaged execution form of the same maintained collector source. It is built by GitHub Actions from the collector runtime and embedded support-tool payload.

The EXE is not a separate product line and is not the editing surface. Source changes belong in the collector source and harness files.

---

## Build workflow

Use GitHub Actions workflow:

```text
manual-collector-optional-exe-build
```

Key input:

```text
exe_validation_suite
```

Supported suites include Core, MajorVersion, Retrieval, QuickAliases, SessionBehavior, TargetedCollection, ChunkingOversizeArtifact, ChunkingReconstructionMetadata, FailureGates, and FullRegression.

Run one suite at a time.

---

## Local EXE examples

Tier 1 collect:

```powershell
.\DCOIR_Collector.exe -Mode Collect -Tier T1 -Hours 24 -OutRoot C:\Temp
```

Targeted collection:

```powershell
.\DCOIR_Collector.exe -Mode Collect -Targeted -TargetProfile PopupWindow -WindowStart "2026-04-30T08:00:00" -WindowEnd "2026-04-30T09:00:00" -OutRoot C:\Temp
```

Help and version:

```powershell
.\DCOIR_Collector.exe -ShowHelp
.\DCOIR_Collector.exe -ShowVersion
```

---

## PS1 versus EXE behavior

| Area | PS1 | EXE |
| --- | --- | --- |
| Runtime path | Script metadata | May resolve through executable process path |
| Parameter binding diagnostics | Native PowerShell behavior visible | Wrapper may hide or reshape diagnostics |
| FailureGates bind-reject behavior | Strict native checks | EXE-aware interpretation required |
| Output contract on successful runs | Must remain stable | Must remain stable |

Do not treat EXE wrapper differences as collector defects unless functional behavior, artifacts, or the output contract are wrong.

---

## FailureGates rule

FailureGates and FullRegression must be interpreted with runtime mode in mind:

- PS1 mode: strict native bind-reject expectations;
- EXE mode: wrapper-limited bind-reject probes may be expected.

---

## Gemini interpretation

When an EXE run fails, Gemini should classify the failure before recommending a fix:

1. workflow/build failure;
2. packaging failure;
3. harness execution failure;
4. EXE wrapper limitation;
5. real collector runtime behavior regression.

---

## Validation expectations

After EXE-facing changes, verify:

- optional EXE workflow still builds;
- selected harness suite passes;
- FailureGates and FullRegression remain EXE-aware;
- Knowledge 03, 08, 09, and 15 remain aligned if behavior changed.

---

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
