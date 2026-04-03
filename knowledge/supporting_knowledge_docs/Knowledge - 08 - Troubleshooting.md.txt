# Knowledge - 08 - Troubleshooting

_Common operational and packaging issues on the current DCOIR line_

**Summary:** Use this page when the local harness, collector package, uploaded readable source files, or tool-backed enrichment actions do not behave as expected.

| Source class | Authoritative basis |
| --- | --- |
| Project sources | LOG-02_DCOIR_Lessons_Learned_Log.txt; DOC-01_AFRICOM_SOC_IR_Project_Setup_and_Workflow.txt; DCOIR_Collector.314.ps1.txt; run_DCOIR_Tests.ps1.txt |
| Official external sources | Microsoft Learn / Sysinternals tool pages; Microsoft Learn / PowerShell help references; Elastic Docs / endpoint response actions |
| Scope note | This page focuses on current durable lessons rather than speculative fixes. |

## First things to verify

- Reason over the uploaded readable source files in Project, but run the native runtime/downloaded files in the repo bundle or local test folder.
- The local harness can find .\DCOIR_Collector.ps1 and .\assets\DCOIR_Collector.zip from the stable/ layout.
- You are using PowerShell 5.1-compatible syntax and not assuming PowerShell 7 features.
- You are not mixing endpoint response-console syntax with local workstation syntax.

## Known safety and usability lessons

- Native Windows and PowerShell collection is the safest baseline foundation.
- Some tools that can trigger blocked-driver behavior should not be part of unattended baseline collection.
- Local regression is safer as a separate harness than as ad hoc edits to the collector engine.
- Full refresh bundles are simpler than partial replace lists when syncs include broad source changes.

## When documentation is too ambiguous

- Do not guess what a new function, flag, or wrapper branch is supposed to do.
- Ask for targeted clarification or ask the main project workflow to add clearer comment-based help or parameter descriptions.
- Prefer exact parameter names, accepted values, and observed command examples over prose interpretation.
> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
