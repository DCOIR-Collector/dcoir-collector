# Knowledge - 08 - Troubleshooting

_Common operational, packaging, and lane-separation issues on the current DCOIR line_

**Summary:** Current collector, harness, packaging, and lane-separation failure patterns, with bounded troubleshooting habits grounded in the active line.

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

## Troubleshooting posture

Troubleshooting on the current DCOIR line should stay bounded, lane-aware, and source-grounded. The goal is not to improvise around every ambiguous symptom with speculative fixes. The goal is to identify whether the issue is a layout problem, a lane mistake, a packaging mismatch, a harness invocation problem, a tool-backed action misunderstanding, or a genuine runtime defect.

## First checks that save the most time

Before deeper debugging, confirm:
- the current readable source line is the one being reasoned from
- the runtime filename being executed is the actual runtime filename the operator is supposed to use
- the current lane is correct: endpoint response action versus local PowerShell
- the expected asset or ZIP is present where the runtime or harness expects it
- the operator is not assuming PowerShell 7-only behavior in a PowerShell 5.1 line
- the collector output already on disk has actually been inspected before another run is attempted

## Symptom: command looked right but produced the wrong lane behavior

The most common root cause is lane mixing. A local PowerShell example pasted into the endpoint response console is not the same command operationally. The inverse mistake also happens when an operator adds a response-action wrapper to a local test command and then wonders why the workstation run makes no sense.

## Symptom: local regression cannot find the collector or asset paths

This is usually a repo-layout or working-directory problem before it is a collector problem. Check whether:
- the current shell is in the expected repo-style layout
- `DCOIR_Collector.ps1` exists at the path the operator actually invoked
- `run_DCOIR_Tests.ps1` is being used directly when the current line does not carry a default CMD wrapper
- `assets/DCOIR_Collector.zip` exists where the harness expects the master ZIP

## Symptom: tool-backed enrichment action behaved unexpectedly

Treat tool-backed actions as a combination of collector behavior and bundled utility behavior. Verify that the action itself is supported as currently exposed. Then, if interpretation still depends on the exact behavior of the underlying utility, consult the official Sysinternals documentation rather than inventing flags or side effects.

## Symptom: packaging or bundle contents do not look like the repo changes

Packaging problems often come from one of four causes:
- the wrong source tree was treated as authoritative
- a stored-source compile path was expected but an older generated surface was used
- a patch-style bundle omitted a needed supporting file such as a manifest or map update
- the operator is reading a retained ZIP as though it were the current editable source

## Gemini-related troubleshooting cues

Gemini bundle issues on the current line usually come from one of these:
- stored-source runtime files drifting thinner than intended
- attachment sets changing without corresponding map or manifest refresh
- mixing design-time comparative references with runtime source without promoting accepted text into the stored-source tree
- packaging the wrong source surface instead of compiling the current runtime tree

## Good troubleshooting habits

- state the symptom in one sentence
- state which lane it happened in
- identify whether the failure is before execution, during execution, or during interpretation
- verify the current source assumption before editing anything
- preserve the narrowest possible fix
- when documentation is ambiguous, ask for the exact parameter names, accepted values, emitted markers, or command examples rather than inventing prose-based meaning

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

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

