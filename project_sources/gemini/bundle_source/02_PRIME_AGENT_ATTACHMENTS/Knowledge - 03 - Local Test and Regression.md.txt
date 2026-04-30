# Knowledge - 03 - Local Test and Regression

_How to run and interpret collector validation locally across PS1 and EXE modes_

**Summary:** Defines the local validation model, harness usage, suite intent, and how to interpret results without duplication or drift. Aligns with Knowledge 16 (EXE behavior) and Knowledge 17 (feature/output contract).

---

## Core principle

The harness exists to test the **collector**, not to introduce alternative behavior.

- One collector line
- One harness
- Repeatable execution

All validation must map back to:
- a defined test objective
- an observable output contract

---

## Runtime modes

### PS1 (authoritative behavior)
- Direct PowerShell execution
- Full parameter-binding visibility
- Strict FailureGates expectations

### EXE (packaged behavior)
- Wrapper-limited diagnostics
- May not surface native PowerShell bind-reject errors
- Requires EXE-aware interpretation (see Knowledge 16)

**Rule:**
- Do not treat EXE diagnostic differences as regressions unless output contract or runtime behavior is actually broken

---

## Harness entry

Primary file:
```
project_sources/collector/harness/run_DCOIR_Tests.ps1
```

Key parameters:

| Parameter | Purpose |
|----------|--------|
| `-Suite` | Select validation surface |
| `-CollectorPath` | Runtime under test (PS1 or EXE) |
| `-MasterZipPath` | Restaging source |
| `-OutputRoot` | Evidence location |
| `-SkipCleanup` | Preserve artifacts |

---

## Suite intent (non-duplicated)

| Suite | What it proves |
|------|---------------|
| Core | Baseline functionality |
| Retrieval | Artifact movement |
| QuickAliases | Shortcut correctness |
| SessionBehavior | Enrich lifecycle |
| TargetedCollection | Targeted output correctness |
| Chunking* | Large artifact handling |
| FailureGates | Negative-path behavior |
| FullRegression | Combined confidence |

---

## EXE-specific validation rule

For FailureGates and FullRegression:

- PS1 mode → strict failure expectations
- EXE mode → allow wrapper-limited behavior

Valid EXE outcomes may include:
- missing native bind-reject text
- exit code differences

Invalid EXE outcomes:
- incorrect output contract
- missing required artifacts
- incorrect functional behavior

---

## Restaging rule

Each run must:
- start from a clean runtime state
- avoid artifact contamination

If results differ across runs:
- verify restaging before investigating logic

---

## Manual validation pattern (condensed)

1. Define objective (from Airtable test case)
2. Run one bounded command
3. Verify output contract
4. Verify artifacts exist
5. Apply validator if needed
6. Record result honestly

---

## Output contract focus

Always verify:

- `STATUS`
- `RUN_ID`
- artifact paths
- next-step guidance

Console output alone is not sufficient.

---

## Common failure misinterpretations

| Symptom | Likely cause |
|--------|-------------|
| Missing bind error (EXE) | Wrapper limitation |
| Inconsistent results | No restaging |
| Pass without artifacts | Misread output |
| Packaging success | Not runtime proof |

---

## Operator discipline

After every run ask:

1. What did this prove?
2. What did it not prove?
3. What artifact matters next?
4. What is the next bounded step?

---

## Relationship to other docs

- EXE behavior → Knowledge 16
- Features/contract → Knowledge 17
- Troubleshooting → Knowledge 08

---

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
