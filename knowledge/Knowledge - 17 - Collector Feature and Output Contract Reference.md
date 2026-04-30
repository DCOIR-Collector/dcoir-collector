# Knowledge - 17 - Collector Feature and Output Contract Reference

_Collector feature map and output contract reference_

**Summary:** Use this page to identify collector modes, major feature families, validation coverage, and stable output expectations across PS1 and EXE runtimes.

---

## Core modes

| Mode | Purpose |
| --- | --- |
| Collect | Baseline or targeted host evidence collection |
| Enrich | Follow-on bounded enrichment tied to a session |
| Cleanup | Cleanup after evidence is safe |

---

## Tier model

| Tier | Purpose |
| --- | --- |
| T1 | First-pass baseline collection |
| T2 | Deeper persistence and configuration context |

---

## Major feature families

| Feature family | Examples |
| --- | --- |
| Baseline collection | host, identity, process, service, task, network, registry, log, Defender-relevant context |
| Targeted collection | profile, explicit window, focus process/path/indicator/user report |
| Enrichment | session start/add/finalize, action families, retrieval-oriented follow-up |
| Runtime support | package output, artifact paths, cleanup guidance, diagnostic context |
| Validation | harness suites, validator, failure gates, full regression |

---

## Common parameters

| Parameter | Purpose |
| --- | --- |
| `-Mode` | Select Collect, Enrich, or Cleanup |
| `-Tier` | Select T1 or T2 collection depth |
| `-Hours` | Lookback window |
| `-OutRoot` | Output root |
| `-Quick` | Quick alias |
| `-Targeted` | Enable targeted collection posture |
| `-TargetProfile` | Select targeted profile |
| `-WindowStart` / `-WindowEnd` | Explicit event window |
| `-EnrichSessionId` | Continue an enrichment session |
| `-NewEnrichSession` | Start an enrichment session |
| `-FinalizeEnrichSession` | Finalize an enrichment session |
| `-ShowHelp` / `-ShowVersion` | Print help or version information |

---

## Output contract

Successful runs should emit enough structured output for an operator or Gemini to identify:

- `STATUS`;
- `RUN_ID`;
- collection or enrichment bundle path;
- retrieval guidance when applicable;
- cleanup guidance when applicable;
- diagnostic or context artifacts when produced.

Console text alone is not proof. Referenced artifacts must exist when the run claims artifact output.

---

## Failure behavior

Failure behavior is validated by FailureGates. PS1 and EXE can render failure surfaces differently. Use Knowledge 16 for EXE-specific interpretation.

---

## Validation map

| Suite | Coverage |
| --- | --- |
| Core | baseline function |
| Retrieval | artifact movement and retrieval |
| QuickAliases | quick alias mappings |
| SessionBehavior | enrichment session lifecycle |
| TargetedCollection | targeted collection behavior |
| ChunkingOversizeArtifact | oversized artifact handling |
| ChunkingReconstructionMetadata | reconstruction metadata |
| FailureGates | negative-path behavior |
| FullRegression | combined confidence pass |

---

## Cross-reference boundaries

- Use this page for feature families, common parameters, output contract, failure behavior, and validation map.
- Use Knowledge 04 and 05 for collection procedure.
- Use Knowledge 06 for enrichment workflow.
- Use Knowledge 16 for optional EXE behavior.

---

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
