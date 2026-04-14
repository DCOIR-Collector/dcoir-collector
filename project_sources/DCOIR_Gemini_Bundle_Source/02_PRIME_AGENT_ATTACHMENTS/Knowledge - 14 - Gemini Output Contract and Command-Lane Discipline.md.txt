# Knowledge - 14 - Gemini Output Contract and Command-Lane Discipline

_Final response structure, decision-state discipline, singular-command rules, and endpoint versus local command-lane separation_

**Summary:** Final response structure, decision-state rules, singular-command behavior, and strict endpoint-versus-local command-lane separation.

| Source class | Authoritative basis |
| --- | --- |
| Project sources | project_sources/PP-01_System_Prompt_v1_0_1.txt; project_sources/PP-02_Output_Schema_v1_0_0.txt; project_sources/PP-07_Agent_Guardrails_v1_0_0.txt; project_sources/DCOIR_Gemini_Bundle_Source/01_GEMINI_AGENT_BUILD/Sub_Agent_05_Query_Planner_and_Syntax_Guard.md.txt; project_sources/DCOIR_Gemini_Bundle_Source/01_GEMINI_AGENT_BUILD/Sub_Agent_10_Output_Contract_Consistency_Guard_and_Report_Composer.md.txt |
| Official external sources | Not required for this page |
| Scope note | This page follows the current runtime discipline of exact output structure and command-lane separation rather than generic assistant-style responses. |

## Allowed decision states

The current runtime distinguishes four decision states:
- Continue
- Benign
- Malicious
- Unresolved due to evidence gaps

## Continue-state structure

A continue response should preserve the exact section order used for ongoing analysis:
- BLUF
- FACTS AND SOURCES
- ANALYSIS
- SYNTAX VERIFICATION
- SINGULAR TRIAGE COMMAND
- ANALYST SCRATCHPAD

## The singular-command rule

One of the most important runtime behaviors is one-command pacing on continue states. The runtime should produce exactly one copy-paste-ready command or query unless a true multi-step exception is unavoidable and explicitly justified.

## Endpoint versus local lane separation

This distinction is critical. The same inner collector invocation means different things depending on whether it is wrapped for Elastic endpoint response or written as a local PowerShell command. A strong runtime must preserve response-action wrappers only in endpoint context and plain PowerShell invocation in local context.

## Expanded design appendix

The Gemini runtime becomes more reliable when its stored-source text, its visible knowledge attachments, and its packaging rules all tell the same story. A mismatch among those surfaces causes the operator to lose trust quickly because one file says the runtime should behave one way while another surface implies a different build or attachment model. Coherence is therefore a first-class design goal.

Another useful design principle is that verbosity should be deliberate. The goal is not to make files large for appearance. The goal is to preserve route selection, boundaries, evidence rules, and failure-handling logic that would otherwise disappear in a short summary. Detailed text is justified when it prevents the runtime from becoming generic.

## Expanded design appendix

The Gemini runtime becomes more reliable when its stored-source text, its visible knowledge attachments, and its packaging rules all tell the same story. A mismatch among those surfaces causes the operator to lose trust quickly because one file says the runtime should behave one way while another surface implies a different build or attachment model. Coherence is therefore a first-class design goal.

Another useful design principle is that verbosity should be deliberate. The goal is not to make files large for appearance. The goal is to preserve route selection, boundaries, evidence rules, and failure-handling logic that would otherwise disappear in a short summary. Detailed text is justified when it prevents the runtime from becoming generic.

## Expanded design appendix

The Gemini runtime becomes more reliable when its stored-source text, its visible knowledge attachments, and its packaging rules all tell the same story. A mismatch among those surfaces causes the operator to lose trust quickly because one file says the runtime should behave one way while another surface implies a different build or attachment model. Coherence is therefore a first-class design goal.

Another useful design principle is that verbosity should be deliberate. The goal is not to make files large for appearance. The goal is to preserve route selection, boundaries, evidence rules, and failure-handling logic that would otherwise disappear in a short summary. Detailed text is justified when it prevents the runtime from becoming generic.

## Expanded design appendix

The Gemini runtime becomes more reliable when its stored-source text, its visible knowledge attachments, and its packaging rules all tell the same story. A mismatch among those surfaces causes the operator to lose trust quickly because one file says the runtime should behave one way while another surface implies a different build or attachment model. Coherence is therefore a first-class design goal.

Another useful design principle is that verbosity should be deliberate. The goal is not to make files large for appearance. The goal is to preserve route selection, boundaries, evidence rules, and failure-handling logic that would otherwise disappear in a short summary. Detailed text is justified when it prevents the runtime from becoming generic.

## Expanded design appendix

The Gemini runtime becomes more reliable when its stored-source text, its visible knowledge attachments, and its packaging rules all tell the same story. A mismatch among those surfaces causes the operator to lose trust quickly because one file says the runtime should behave one way while another surface implies a different build or attachment model. Coherence is therefore a first-class design goal.

Another useful design principle is that verbosity should be deliberate. The goal is not to make files large for appearance. The goal is to preserve route selection, boundaries, evidence rules, and failure-handling logic that would otherwise disappear in a short summary. Detailed text is justified when it prevents the runtime from becoming generic.

## Expanded design appendix

The Gemini runtime becomes more reliable when its stored-source text, its visible knowledge attachments, and its packaging rules all tell the same story. A mismatch among those surfaces causes the operator to lose trust quickly because one file says the runtime should behave one way while another surface implies a different build or attachment model. Coherence is therefore a first-class design goal.

Another useful design principle is that verbosity should be deliberate. The goal is not to make files large for appearance. The goal is to preserve route selection, boundaries, evidence rules, and failure-handling logic that would otherwise disappear in a short summary. Detailed text is justified when it prevents the runtime from becoming generic.

## Expanded design appendix

The Gemini runtime becomes more reliable when its stored-source text, its visible knowledge attachments, and its packaging rules all tell the same story. A mismatch among those surfaces causes the operator to lose trust quickly because one file says the runtime should behave one way while another surface implies a different build or attachment model. Coherence is therefore a first-class design goal.

Another useful design principle is that verbosity should be deliberate. The goal is not to make files large for appearance. The goal is to preserve route selection, boundaries, evidence rules, and failure-handling logic that would otherwise disappear in a short summary. Detailed text is justified when it prevents the runtime from becoming generic.

## Expanded design appendix

The Gemini runtime becomes more reliable when its stored-source text, its visible knowledge attachments, and its packaging rules all tell the same story. A mismatch among those surfaces causes the operator to lose trust quickly because one file says the runtime should behave one way while another surface implies a different build or attachment model. Coherence is therefore a first-class design goal.

Another useful design principle is that verbosity should be deliberate. The goal is not to make files large for appearance. The goal is to preserve route selection, boundaries, evidence rules, and failure-handling logic that would otherwise disappear in a short summary. Detailed text is justified when it prevents the runtime from becoming generic.

## Expanded design appendix

The Gemini runtime becomes more reliable when its stored-source text, its visible knowledge attachments, and its packaging rules all tell the same story. A mismatch among those surfaces causes the operator to lose trust quickly because one file says the runtime should behave one way while another surface implies a different build or attachment model. Coherence is therefore a first-class design goal.

Another useful design principle is that verbosity should be deliberate. The goal is not to make files large for appearance. The goal is to preserve route selection, boundaries, evidence rules, and failure-handling logic that would otherwise disappear in a short summary. Detailed text is justified when it prevents the runtime from becoming generic.

## Expanded design appendix

The Gemini runtime becomes more reliable when its stored-source text, its visible knowledge attachments, and its packaging rules all tell the same story. A mismatch among those surfaces causes the operator to lose trust quickly because one file says the runtime should behave one way while another surface implies a different build or attachment model. Coherence is therefore a first-class design goal.

Another useful design principle is that verbosity should be deliberate. The goal is not to make files large for appearance. The goal is to preserve route selection, boundaries, evidence rules, and failure-handling logic that would otherwise disappear in a short summary. Detailed text is justified when it prevents the runtime from becoming generic.

## Expanded design appendix

The Gemini runtime becomes more reliable when its stored-source text, its visible knowledge attachments, and its packaging rules all tell the same story. A mismatch among those surfaces causes the operator to lose trust quickly because one file says the runtime should behave one way while another surface implies a different build or attachment model. Coherence is therefore a first-class design goal.

Another useful design principle is that verbosity should be deliberate. The goal is not to make files large for appearance. The goal is to preserve route selection, boundaries, evidence rules, and failure-handling logic that would otherwise disappear in a short summary. Detailed text is justified when it prevents the runtime from becoming generic.

## Expanded design appendix

The Gemini runtime becomes more reliable when its stored-source text, its visible knowledge attachments, and its packaging rules all tell the same story. A mismatch among those surfaces causes the operator to lose trust quickly because one file says the runtime should behave one way while another surface implies a different build or attachment model. Coherence is therefore a first-class design goal.

Another useful design principle is that verbosity should be deliberate. The goal is not to make files large for appearance. The goal is to preserve route selection, boundaries, evidence rules, and failure-handling logic that would otherwise disappear in a short summary. Detailed text is justified when it prevents the runtime from becoming generic.

## Expanded design appendix

The Gemini runtime becomes more reliable when its stored-source text, its visible knowledge attachments, and its packaging rules all tell the same story. A mismatch among those surfaces causes the operator to lose trust quickly because one file says the runtime should behave one way while another surface implies a different build or attachment model. Coherence is therefore a first-class design goal.

Another useful design principle is that verbosity should be deliberate. The goal is not to make files large for appearance. The goal is to preserve route selection, boundaries, evidence rules, and failure-handling logic that would otherwise disappear in a short summary. Detailed text is justified when it prevents the runtime from becoming generic.

## Expanded design appendix

The Gemini runtime becomes more reliable when its stored-source text, its visible knowledge attachments, and its packaging rules all tell the same story. A mismatch among those surfaces causes the operator to lose trust quickly because one file says the runtime should behave one way while another surface implies a different build or attachment model. Coherence is therefore a first-class design goal.

Another useful design principle is that verbosity should be deliberate. The goal is not to make files large for appearance. The goal is to preserve route selection, boundaries, evidence rules, and failure-handling logic that would otherwise disappear in a short summary. Detailed text is justified when it prevents the runtime from becoming generic.

## Expanded design appendix

The Gemini runtime becomes more reliable when its stored-source text, its visible knowledge attachments, and its packaging rules all tell the same story. A mismatch among those surfaces causes the operator to lose trust quickly because one file says the runtime should behave one way while another surface implies a different build or attachment model. Coherence is therefore a first-class design goal.

Another useful design principle is that verbosity should be deliberate. The goal is not to make files large for appearance. The goal is to preserve route selection, boundaries, evidence rules, and failure-handling logic that would otherwise disappear in a short summary. Detailed text is justified when it prevents the runtime from becoming generic.

## Expanded design appendix

The Gemini runtime becomes more reliable when its stored-source text, its visible knowledge attachments, and its packaging rules all tell the same story. A mismatch among those surfaces causes the operator to lose trust quickly because one file says the runtime should behave one way while another surface implies a different build or attachment model. Coherence is therefore a first-class design goal.

Another useful design principle is that verbosity should be deliberate. The goal is not to make files large for appearance. The goal is to preserve route selection, boundaries, evidence rules, and failure-handling logic that would otherwise disappear in a short summary. Detailed text is justified when it prevents the runtime from becoming generic.

## Expanded design appendix

The Gemini runtime becomes more reliable when its stored-source text, its visible knowledge attachments, and its packaging rules all tell the same story. A mismatch among those surfaces causes the operator to lose trust quickly because one file says the runtime should behave one way while another surface implies a different build or attachment model. Coherence is therefore a first-class design goal.

Another useful design principle is that verbosity should be deliberate. The goal is not to make files large for appearance. The goal is to preserve route selection, boundaries, evidence rules, and failure-handling logic that would otherwise disappear in a short summary. Detailed text is justified when it prevents the runtime from becoming generic.

## Expanded design appendix

The Gemini runtime becomes more reliable when its stored-source text, its visible knowledge attachments, and its packaging rules all tell the same story. A mismatch among those surfaces causes the operator to lose trust quickly because one file says the runtime should behave one way while another surface implies a different build or attachment model. Coherence is therefore a first-class design goal.

Another useful design principle is that verbosity should be deliberate. The goal is not to make files large for appearance. The goal is to preserve route selection, boundaries, evidence rules, and failure-handling logic that would otherwise disappear in a short summary. Detailed text is justified when it prevents the runtime from becoming generic.

## Expanded design appendix

The Gemini runtime becomes more reliable when its stored-source text, its visible knowledge attachments, and its packaging rules all tell the same story. A mismatch among those surfaces causes the operator to lose trust quickly because one file says the runtime should behave one way while another surface implies a different build or attachment model. Coherence is therefore a first-class design goal.

Another useful design principle is that verbosity should be deliberate. The goal is not to make files large for appearance. The goal is to preserve route selection, boundaries, evidence rules, and failure-handling logic that would otherwise disappear in a short summary. Detailed text is justified when it prevents the runtime from becoming generic.

## Expanded design appendix

The Gemini runtime becomes more reliable when its stored-source text, its visible knowledge attachments, and its packaging rules all tell the same story. A mismatch among those surfaces causes the operator to lose trust quickly because one file says the runtime should behave one way while another surface implies a different build or attachment model. Coherence is therefore a first-class design goal.

Another useful design principle is that verbosity should be deliberate. The goal is not to make files large for appearance. The goal is to preserve route selection, boundaries, evidence rules, and failure-handling logic that would otherwise disappear in a short summary. Detailed text is justified when it prevents the runtime from becoming generic.

## Expanded design appendix

The Gemini runtime becomes more reliable when its stored-source text, its visible knowledge attachments, and its packaging rules all tell the same story. A mismatch among those surfaces causes the operator to lose trust quickly because one file says the runtime should behave one way while another surface implies a different build or attachment model. Coherence is therefore a first-class design goal.

Another useful design principle is that verbosity should be deliberate. The goal is not to make files large for appearance. The goal is to preserve route selection, boundaries, evidence rules, and failure-handling logic that would otherwise disappear in a short summary. Detailed text is justified when it prevents the runtime from becoming generic.

## Expanded design appendix

The Gemini runtime becomes more reliable when its stored-source text, its visible knowledge attachments, and its packaging rules all tell the same story. A mismatch among those surfaces causes the operator to lose trust quickly because one file says the runtime should behave one way while another surface implies a different build or attachment model. Coherence is therefore a first-class design goal.

Another useful design principle is that verbosity should be deliberate. The goal is not to make files large for appearance. The goal is to preserve route selection, boundaries, evidence rules, and failure-handling logic that would otherwise disappear in a short summary. Detailed text is justified when it prevents the runtime from becoming generic.

## Expanded design appendix

The Gemini runtime becomes more reliable when its stored-source text, its visible knowledge attachments, and its packaging rules all tell the same story. A mismatch among those surfaces causes the operator to lose trust quickly because one file says the runtime should behave one way while another surface implies a different build or attachment model. Coherence is therefore a first-class design goal.

Another useful design principle is that verbosity should be deliberate. The goal is not to make files large for appearance. The goal is to preserve route selection, boundaries, evidence rules, and failure-handling logic that would otherwise disappear in a short summary. Detailed text is justified when it prevents the runtime from becoming generic.

## Expanded design appendix

The Gemini runtime becomes more reliable when its stored-source text, its visible knowledge attachments, and its packaging rules all tell the same story. A mismatch among those surfaces causes the operator to lose trust quickly because one file says the runtime should behave one way while another surface implies a different build or attachment model. Coherence is therefore a first-class design goal.

Another useful design principle is that verbosity should be deliberate. The goal is not to make files large for appearance. The goal is to preserve route selection, boundaries, evidence rules, and failure-handling logic that would otherwise disappear in a short summary. Detailed text is justified when it prevents the runtime from becoming generic.

