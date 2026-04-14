# Knowledge - 07 - Artifact Review Guide

_How the current prompt-pack and combined-master-prompt line expects analysts to review DCOIR artifacts_

**Summary:** Evidence-first review order for baseline, enrichment, and retrieved artifacts, including wrapper-versus-evidence-carrier distinctions.

| Source class | Authoritative basis |
| --- | --- |
| Project sources | PP-01_System_Prompt_v1_0_1.txt; PP-02_Output_Schema_v1_0_0.txt; PP-03_Baseline_Triage_Prompt_v1_0_0.txt; PP-04_Enrichment_Review_Prompt_v0_1_1.txt; PP-05_Retrieved_Artifact_Review_Prompt_v0_1_1.txt; PP-06_Final_Case_Synthesis_Prompt_v0_1_1.txt; PP-07_Agent_Guardrails_v1_0_0.txt; PP-08_Combined_Analyst_Facing_Master_Prompt_v1_0_0.txt |
| Official external sources | Not required for this page |
| Scope note | This page is project-grounded; it does not redefine the schema or the prompts. |

## Current review sequence

- Review baseline collection output first.
- Review the merged baseline report and the flat final_artifacts output.
- Identify suspicious findings, notable absences, and the next best enrichment step.
- Review enrichment output as it is produced.
- Review retrieved files or raw exports in retrieved artifact review mode when they are staged.
- Treat scripts, configs, scheduled-task XML, registry exports, and event-log-derived excerpts as evidence-first artifact-review inputs rather than enrichment-only narrative.
- End with final case synthesis after enough reviewed evidence exists to support a case-level conclusion.

## Review posture

- Treat user-provided case artifacts as the primary source of truth.
- Separate observed evidence, inference, uncertainty, and recommendations.
- Do not overstate confidence, maliciousness, benignity, or batch completeness.
- Recommend one best next step when possible rather than shotgun lists.

## Common input priority

| Priority | Preferred artifact |
| --- | --- |
| 1 | Merged baseline report |
| 2 | Metadata report |
| 3 | Flat final_artifacts baseline outputs |
| 4 | Enrichment report content and staged retrieval handoff |
| 5 | Retrieved script, config, task XML, registry export, or event-log-derived excerpt |
| 6 | Final case synthesis only after the reviewed evidence chain is broad enough to justify case-level closure or decision support |

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.

## Artifact review posture

Artifact review is where DCOIR output becomes analytically useful. The central discipline is evidence-first reading. The operator should separate observed facts, inference, uncertainty, and recommendations instead of letting generated summaries or convenient filenames do the thinking. That posture matters because DCOIR produces both workflow-state artifacts and evidence-bearing artifacts, and they do not have the same meaning.

## Review sequence and why the order matters

The current sequence starts with baseline output, then enrichment output, then retrieved artifacts, and only later supports final case synthesis. That order is deliberate. Baseline review gives the operator the broadest initial evidence picture and usually reveals the narrowest useful follow-up lane. Enrichment review should be grounded in the baseline questions that prompted it. Retrieved artifacts often contain the highest-signal material, but they are easier to interpret correctly once the baseline and enrichment context already exist.

## Wrapper artifacts versus evidence carriers

One of the most important skills in DCOIR review is knowing when a file is a wrapper and when it is the thing that matters. Summary files, metadata files, upload-priority files, and follow-up queues are often extremely useful, but they frequently exist to point at the real evidence carrier rather than to replace it.

## Common artifact classes and how to read them

### Merged baseline report
Usually the best starting point because it organizes the first-pass evidence into a readable frame.

### Metadata report
Valuable for workflow-state awareness, run context, and understanding what the collector actually staged.

### Flat final_artifacts outputs
Often where the concrete details live once the summary has told the operator which evidence matters most.

### Enrichment reports
Should be read against the precise question that justified the enrich action.

### Retrieved scripts, configs, scheduled-task XML, registry exports, and event-derived excerpts
Often the evidence-rich materials that directly support or weaken a hypothesis.

## Evidence discipline during review

Review should preserve four distinct categories:
- observed evidence directly visible in the artifact
- inference drawn from that evidence
- uncertainty or missing context
- recommendations for the next evidence-producing move

Confusing those categories is the fastest way to create false confidence.

## Upload priority and attachment budgets

When upload limits matter, the operator should not treat every file equally. The right question is which artifact is most likely to answer the current question or materially change the investigation. That is why the current review posture prioritizes merged reports and high-signal evidence carriers rather than encouraging indiscriminate upload of every produced file.

## Retrieved artifact review techniques

### Scripts and command artifacts
Focus on what they do, what they reference, whether they align with the suspected behavior, and whether they appear administrative, installer-driven, scheduled, or suspicious in context.

### Config and XML artifacts
Focus on persistence, triggers, execution context, references to binaries or scripts, timing, and whether the configuration matches expected software behavior.

### Registry exports
Focus on path, scope, startup relevance, security relevance, and whether the values support persistence, policy, or expected system behavior.

## Common review mistakes

- reading a summary wrapper as if it were direct host evidence
- jumping to final synthesis before the actual evidence carrier has been reviewed
- ignoring what an artifact does not prove
- uploading or reading too many low-value files before the highest-signal file
- treating the existence of many artifacts as equivalent to severity

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

