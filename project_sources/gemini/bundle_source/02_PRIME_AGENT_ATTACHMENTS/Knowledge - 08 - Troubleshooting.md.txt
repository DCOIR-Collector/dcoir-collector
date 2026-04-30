# Knowledge - 08 - Troubleshooting

_Common DCOIR execution, packaging, validation, and interpretation failures_

**Summary:** Use this page to separate lane mistakes, staging problems, packaging issues, wrapper limitations, and real collector defects.

---

## First checks

Before editing source or rerunning broad validation, confirm:

- execution lane: Elastic endpoint, local workstation, GitHub Actions, PS1, or EXE;
- runtime path and filename;
- staged package or asset state;
- current branch/ref used by GitHub Actions;
- whether output already exists and should be reviewed or retrieved;
- whether the symptom is build, packaging, runtime, harness, or interpretation.

---

## Lane mixing

| Symptom | Check |
| --- | --- |
| Local command fails in Elastic | Missing `execute --command` wrapper or quoting issue |
| Endpoint command pasted locally | Response-action syntax used in wrong lane |
| Valid command gives unexpected context | Wrong runtime path or working directory |

Use Knowledge 02 for endpoint command syntax.

---

## Local regression path failures

Check:

- `run_DCOIR_Tests.ps1` is the harness being used;
- `DCOIR_Collector.ps1` or EXE path exists at `-CollectorPath`;
- master ZIP exists at `-MasterZipPath`;
- current directory matches the command examples;
- PowerShell 5.1 compatibility is preserved.

---

## EXE-specific failures

The optional EXE can differ from PS1 in native PowerShell diagnostic behavior.

Expected EXE differences may include:

- missing native bind-reject text;
- different exit-code behavior;
- wrapper-limited failure output.

Do not treat those as collector defects unless the output contract, artifact creation, or functional behavior is wrong. Use Knowledge 16 for EXE-specific interpretation.

---

## Repeated collect runs

Before rerunning collection:

- review or retrieve existing output first;
- verify staging state;
- re-stage when uncertain;
- name the new question the rerun must answer.

---

## Targeted collection expectations

Targeted mode narrows intent and output emphasis. Do not claim exact filtering unless that specific path has validated exact filtering behavior.

If targeted output is broader than expected, decide whether this is:

- documentation/expectation drift;
- a validated limitation;
- or a new implementation requirement.

---

## Large output and chunking

Synthetic chunking reconstruction is validated for the regression fixture. That does not prove every real large output chunks automatically.

Treat large monolithic live output as a retrieval/review or implementation-boundary issue unless exact live chunking has been validated.

---

## Packaging and bundle issues

Common causes:

- wrong source treated as authoritative;
- manifest/map not updated with new files;
- generated attachment edited instead of maintained source;
- retained ZIP read as current source;
- workflow required-surface checks not updated.

---

## Troubleshooting pattern

1. State the symptom.
2. Identify the lane.
3. Identify failure stage: build, packaging, execution, validation, or interpretation.
4. Check source and staging assumptions.
5. Apply the narrowest fix.
6. Validate the specific behavior before broad regression.

---

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
