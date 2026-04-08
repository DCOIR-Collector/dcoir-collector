# Knowledge - 08 - Troubleshooting

_Common operational, packaging, and lane-separation issues on the current DCOIR line_

**Summary:** Use this page when the local harness, collector package, current GitHub-readable source line, or tool-backed enrichment actions do not behave as expected.

| Source class | Authoritative basis |
| --- | --- |
| Project sources | project_sources/DOC-01_AFRICOM_SOC_IR_Project_Setup_and_Workflow.txt; project_sources/DCOIR_Collector.ps1; project_sources/run_DCOIR_Tests.ps1; project_sources/LOG-01_DCOIR_Todo_Log.txt |
| Official external sources | Microsoft Learn / Sysinternals tool pages; Microsoft Learn / PowerShell help references; Elastic Docs / endpoint response actions |
| Scope note | This page focuses on current durable lessons rather than speculative fixes. |

## First things to verify

- Reason from the current GitHub-readable source paths in the repo, but run the native runtime filenames the operator will actually use.
- The local harness can find `./DCOIR_Collector.ps1` and `./assets/DCOIR_Collector.zip` from the repo-style or local test layout.
- You are using PowerShell 5.1-compatible syntax and not assuming PowerShell 7 features.
- You are not mixing Elastic response-console syntax with local workstation or local regression syntax.
- The current governed line does not include a default `run_DCOIR_Tests.cmd` harness wrapper, so local regression should use `run_DCOIR_Tests.ps1` unless the control plane later restores a wrapper.

## Known safety and usability lessons

- Native Windows and PowerShell collection is the safest baseline foundation.
- Some tools that can trigger blocked-driver behavior should not be part of unattended baseline collection.
- Local regression is safer as a separate harness than as ad hoc edits to the collector engine.
- GitHub Desktop manual repo-update bundles and batched skill-install waves reduce operator friction when the changed set is already known and compatible.
- Full-refresh bundles are simpler than partial replace lists only when the change truly touches current project-source breadth, not by default for every small docs or skill fix.

## When documentation is too ambiguous

- Do not guess what a new function, flag, quick alias, or wrapper branch is supposed to do.
- Ask for targeted clarification or ask the main project workflow to add clearer comment-based help or parameter descriptions.
- Prefer exact parameter names, accepted values, emitted markers, and observed command examples over prose interpretation.
- When multiple current docs preserve the same stale source-name or removed-wrapper assumption, refresh the whole affected doc cluster together instead of leaving related pages misleading.
> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
