# Knowledge - 17 - Collector Feature and Output Contract Reference

_Canonical feature map and output contract for the DCOIR collector across PS1 and EXE runtimes_

**Summary:** This page defines the collector’s authoritative feature set, parameter model, and output contract expectations so all other knowledge docs can reference a single source of truth instead of duplicating feature descriptions.

| Source class | Authoritative basis |
| --- | --- |
| Project sources | project_sources/collector/source/DCOIR_Collector.ps1; project_sources/collector/source/parts/*.ps1; project_sources/collector/harness/run_DCOIR_Tests.ps1; project_sources/collector/harness/validate_DCOIR_Run.ps1 |
| Validation alignment | Airtable Validation Test Cases and harness suite coverage |
| Scope note | This page is authoritative for features and output expectations. Usage guidance belongs in other knowledge docs. |

## Core modes

| Mode | Purpose |
| --- | --- |
| Collect | Baseline or targeted collection of system state and artifacts |
| Enrich | Follow-on enrichment actions tied to a session |
| Cleanup | Post-run cleanup actions where implemented |

## Tier model

| Tier | Meaning |
| --- | --- |
| T1 | Baseline triage collection |
| T2 | Deeper collection for persistence and configuration context |

## Collection features

The collector currently includes:

- baseline collection and reporting
- targeted collection profiles
- explicit event window overrides
- bounded parallel runtime execution
- diagnostic context overrides
- artifact packaging and transport-safe output

Targeted collection parameters include:

- `-Targeted`
- `-TargetProfile`
- `-WindowStart`
- `-WindowEnd`
- `-IncludeArtifactCategory`
- focus fields such as process, path, indicator, and user report

## Enrichment features

The enrich lane includes:

- session creation (`-NewEnrichSession`)
- session continuation (`-EnrichSessionId`)
- session finalization (`-FinalizeEnrichSession`)
- action-driven enrichment using predefined action families

Action examples include:

- signature and binary inspection
- DLL enumeration
- registry and service inspection
- log extraction
- file retrieval and artifact capture

## Quick interface

The quick interface (`-Quick`) allows operator shortcuts that map to underlying collector behavior. These shortcuts must remain aligned with documented behavior and validated by the QuickAliases suite.

## Output contract (high level)

A successful collector run should emit structured output that includes at least:

- `STATUS`
- `RUN_ID`
- bundle or artifact paths
- next-step guidance such as retrieval or cleanup commands
- context or diagnostic surfaces when applicable

The exact structure may vary slightly by lane (collect vs enrich), but the high-level contract must remain stable enough for:

- Gemini interpretation
- harness validation
- operator decision-making

## Failure behavior

Failure surfaces are validated by the FailureGates suite. Failures may include:

- parameter binding issues
- invalid quick inputs
- degraded explicit-window behavior
- runtime or packaging errors

PS1 and EXE may present failures differently. This page defines the existence of failure classes, not the exact rendering in each runtime. Runtime-specific differences are documented in Knowledge - 16.

## Relationship to validation

Each major feature or behavior should map to at least one validation surface:

- Core → baseline functionality
- Retrieval → artifact movement and retrieval
- QuickAliases → quick interface correctness
- SessionBehavior → enrich-session lifecycle
- TargetedCollection → targeted output correctness
- Chunking suites → large artifact handling
- FailureGates → negative-path behavior
- FullRegression → combined confidence pass

A feature without a validation surface is a risk and should be addressed in Airtable Validation Test Cases.

## Relationship to other knowledge docs

- Usage guidance belongs in runbooks and EXE usage docs
- Troubleshooting belongs in Knowledge - 08
- FAQ belongs in Knowledge - 09
- Gemini behavior belongs in Knowledge - 14 and 15

This page should not duplicate those concerns. It defines what exists and what must be true.

## Maintenance rules

When collector features change:

1. Update this page first.
2. Update any usage or runbook pages that reference the changed feature.
3. Update validation expectations if behavior changes.
4. Verify EXE and PS1 parity or document differences.
5. Run validation suites and update Airtable evidence.

## Validation expectations

After changes to this page or collector features, verify:

- harness suites still align with documented features
- Gemini output interpretation still matches the contract
- EXE and PS1 behavior differences are documented where needed

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
