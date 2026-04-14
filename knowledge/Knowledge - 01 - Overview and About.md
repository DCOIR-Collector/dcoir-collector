# Knowledge - 01 - Overview and About

_AFRICOM_SOC_IR / DCOIR project context and supporting knowledge-doc charter_

**Summary:** Current DCOIR posture, governing surfaces, source classes, and the role of the maintained Knowledge-doc set without granting it control-plane authority.

| Source class | Authoritative basis |
| --- | --- |
| Project sources | project_sources/CP-01_DCOIR_Version_Manifest.txt; project_sources/CP-02_DCOIR_Change_Log.txt; project_sources/DOC-01_AFRICOM_SOC_IR_Project_Setup_and_Workflow.txt; project_sources/DOC-03_DCOIR_Repository_Layout_Spec_v1_0_0.txt; project_sources/LOG-01_DCOIR_Todo_Log.txt |
| Official external sources | Not required for this page |
| Scope note | Generated from the current GitHub-primary control plane and maintained supporting knowledge lane. |

## Current project posture

- The GitHub repository `malwaredevil/dcoir-collector` is the sole working source for governed readable text files.
- Project Instructions, `project_sources/CP-01_DCOIR_Version_Manifest.txt`, and `project_sources/CP-02_DCOIR_Change_Log.txt` form the default control plane for current-state work.
- The current collector runtime is `project_sources/DCOIR_Collector.ps1` and the current local regression harness is `project_sources/run_DCOIR_Tests.ps1`.
- The governed helper-skill source lives under `dcoir_skills/` and now supports grouped GitHub Desktop repo-update bundles, batched skill-install waves, and bounded current-state resume behavior.
- The maintained Knowledge-doc set under `knowledge/` is supporting human-readable documentation only. It helps explain the current workflow but never overrides the control plane.

## Source classes that matter

| Class | Examples | How to treat it |
| --- | --- | --- |
| Control plane | Project Instructions; `project_sources/CP-01_DCOIR_Version_Manifest.txt`; `project_sources/CP-02_DCOIR_Change_Log.txt` | Authoritative for current status, governance, and what is current |
| Governed GitHub-readable sources | `project_sources/DCOIR_Collector.ps1`; `project_sources/run_DCOIR_Tests.ps1`; current prompt-pack and workflow files | Authoritative when marked current in the manifest |
| Supporting assets | `supporting_assets/DCOIR_Collector.zip`; `supporting_assets/supporting_knowledge_docs.zip` | Important for delivery or local execution, but not control-plane authority |
| Knowledge docs | `knowledge/Knowledge - ## - *.md` | Supporting human-readable docs only; never override the control plane |

## What this Knowledge-doc set is for

- Give the operator readable explanations of the current collector, harness, workflow, enrichment, artifact-review, and AI-design posture.
- Stay grounded in current approved sources and official vendor references where external truth is required.
- Keep stable filenames so the docs can be refreshed as a current maintained set without changing authority rules.
- Support GitHub-primary maintenance while still allowing a retained `supporting_knowledge_docs.zip` delivery asset when the workflow still wants that convenience bundle.
- Reduce stale guidance drift by refreshing affected doc clusters together when the same outdated source-name or delivery-model assumption appears on multiple current pages.

## Current planned Knowledge-doc pages

- Overview and About
- Elastic Quick Start
- Local Test and Regression
- Tier 1 Collect Runbook
- Tier 2 Collect Runbook
- Enrichment Actions
- Artifact Review Guide
- Troubleshooting
- FAQ
- AI Prompt and Agent Design
> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.

## Governance and current working posture

The governed DCOIR working line is GitHub-primary. Current readable source files live in the repository and remain the engineering truth for the collector runtime, the local regression harness, the Gemini stored-source tree, and the prompt-pack design line. The maintained knowledge set exists to make those working parts easier to understand, easier to use correctly, and harder to misuse when an operator is moving quickly during incident work.

The practical consequence is simple. When a statement affects what is current, what is allowed, what is compiled, what is packaged, or what is treated as a supported runtime behavior, the control plane and the current GitHub-readable project sources win. Knowledge docs help the operator move faster, but they do not get to silently redefine the system.

Several distinctions matter every time work starts:
- project instructions and the current control-plane files establish what is current
- the collector runtime and harness sources define executable behavior
- the Gemini stored-source tree defines the editable operator-facing runtime attachment and agent source set
- retained ZIP assets are delivery conveniences, not engineering authority
- knowledge docs are human-readable operational guidance, not replacement source files

## DCOIR operational scope

DCOIR sits in the narrow lane between alert triage and host-based evidence development. A DCOIR action is not the same thing as a generic incident-response script run, and it is not the same thing as an unconstrained remote shell. The collector line exists to answer bounded investigative questions by staging or retrieving host-side evidence in a disciplined way. The prompt-pack and Gemini lines exist to help analysts choose the next evidence-producing step without losing source discipline, command-lane discipline, or output consistency.

In practice, DCOIR work frequently moves through these stages:
1. startup and readiness checks
2. baseline triage of existing alert or host evidence
3. decision on whether telemetry, live response, or collection is the best next move
4. bounded collection or enrichment when the host question cannot be answered from current evidence
5. artifact review and evidence-grounded interpretation
6. final synthesis, continued triage, benign disposition, malicious disposition, or unresolved closure only after real evidence paths were used

That rhythm matters because misuse usually comes from skipping stages. The most common failures are broad collection without a clear question, treating workflow metadata as proof, mixing endpoint syntax with local syntax, or reading prompt-pack design artifacts as if they were the runtime itself.

## Source classes and how to reason about them

Different source classes answer different questions.

### Control plane
Control-plane files decide what is current, what role each durable file serves, and what the active working line is. They are the first place to check when a repo contains both current material and historical material.

### Governed project sources
Governed source files answer behavior questions. They are where the collector runtime, the harness, the Gemini bundle source, and the prompt-pack line actually live. If a quick alias, parameter, bundle rule, topology rule, or stored-source compile behavior matters, governed source is where the durable answer should come from.

### Supporting assets
Supporting assets are useful, sometimes essential, but they are not automatically source of truth. A ZIP can be a valid delivery vehicle while still being secondary to the readable GitHub source that produced it.

### Knowledge docs
Knowledge docs sit in the operator-readability lane. Their job is to preserve a good explanation of current behavior, current guardrails, and current workflows in language that an operator can act on without having to reconstruct the entire repo every time.

## Collector line, harness line, and Gemini line

Three parallel surfaces are easy to confuse.

### Collector line
The collector line is the host-evidence engine. It is responsible for baseline collection, deeper collection, enrich-session actions, retrieval-oriented actions, and cleanup-oriented actions. It operates with explicit command lanes and should not be treated as a free-form shell framework.

### Harness line
The harness line exists to exercise the stable collector line from a local repo-style layout. It is intentionally separate from normal operator endpoint execution because regression and runtime use different command contexts even when they ultimately exercise the same collector behavior.

### Gemini line
The Gemini line is the stored-source, prompt-pack-grounded, operator-facing AI bundle. It is built from the stored runtime source tree, not from improvisational generation during ordinary packaging. It depends on detailed agent fields and a maintained attachment set so the runtime remains predictable and explicit instead of thin and vague.

## Knowledge-doc expectations

The maintained knowledge set is most useful when it is opinionated about the exact mistakes the operator should not make. Good knowledge docs on this line do not merely list filenames or repeat one command example. They should help someone who has never used the collector before understand:
- which lane they are in
- what the command will actually do
- what outputs matter first
- what a result does and does not prove
- when to stop and use a narrower step instead of a broader one
- how the Gemini design line relates to the collector line without becoming magic hidden behavior

That means useful knowledge content should preserve:
- exact runtime names when execution matters
- command-lane separation every time endpoint and local work can be confused
- evidence-first phrasing when an artifact is reviewed
- explicit statements about what is workflow state versus what is case evidence
- explicit statements about what the bundle and its attachments are for without treating them as authority

## Common misunderstandings that the operator should avoid

- A retained ZIP is not automatically the canonical source.
- A knowledge page is not allowed to silently override a governed runtime file.
- A collector action is not justified merely because the collector is available.
- A retrieval or metadata artifact is not the same thing as host-behavior evidence.
- A Gemini design note is not the same thing as the runtime field set that the operator will actually ship.
- A local PowerShell example is not an endpoint response-console command until it is deliberately wrapped in the response-action lane.
- A question that can still be answered by telemetry or live response does not automatically justify collection.
- More text is only useful when it preserves operational meaning, branch conditions, and error prevention.

## Working glossary

**Baseline collect** means the broad first-pass host collection used to establish a starting evidence set.

**Tier 2 collect** means a deeper host collection lane focused on additional persistence and configuration context when Tier 1 did not answer the question.

**Enrichment session** means a one-action-at-a-time follow-up lane used to add bounded evidence or retrieval context after baseline review.

**Retrieval-ready output** means workflow state showing that the next useful move may be getting a file or artifact that already exists rather than re-running a collector phase.

**Stored-source compile** means the ordinary Gemini shipment model in which the runtime bundle is compiled from the editable source tree already checked into the repository.

**Attachment set** means the shared knowledge files and related operator-readable support files that the Gemini runtime carries alongside the agent definitions.

## Operator habits that scale well

- Check the lane first. Decide whether the task is endpoint execution, local regression, artifact review, prompt design, or bundle maintenance.
- Prefer the narrowest step that can answer the next real question.
- Read workflow-state outputs as workflow-state outputs, not as verdicts.
- Keep local examples and endpoint examples visibly different every time.
- Update stored-source runtime text directly when the behavior or attachment set changes.
- Refresh related explanation clusters together when a naming model or packaging rule changes, so stale guidance does not survive in neighboring pages.
- Treat the Airtable Validation Test Cases table as the dynamic manual-testing surface for current validation work, while keeping GitHub as the engineering and packaging authority for the actual source line.

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
## Expanded practical appendix

A good operational document earns its length by making future mistakes less likely. The most useful additional detail usually lives in branch conditions, review order, common misunderstandings, and the statements about what a result does not prove. Those are the parts that operators forget under pressure, and they are the parts that improve runtime behavior when the knowledge set is used as an attachment family.

## Expanded practical appendix

A good operational document earns its length by making future mistakes less likely. The most useful additional detail usually lives in branch conditions, review order, common misunderstandings, and the statements about what a result does not prove. Those are the parts that operators forget under pressure, and they are the parts that improve runtime behavior when the knowledge set is used as an attachment family.

## Expanded practical appendix

A good operational document earns its length by making future mistakes less likely. The most useful additional detail usually lives in branch conditions, review order, common misunderstandings, and the statements about what a result does not prove. Those are the parts that operators forget under pressure, and they are the parts that improve runtime behavior when the knowledge set is used as an attachment family.

## Expanded practical appendix

A good operational document earns its length by making future mistakes less likely. The most useful additional detail usually lives in branch conditions, review order, common misunderstandings, and the statements about what a result does not prove. Those are the parts that operators forget under pressure, and they are the parts that improve runtime behavior when the knowledge set is used as an attachment family.

## Expanded practical appendix

A good operational document earns its length by making future mistakes less likely. The most useful additional detail usually lives in branch conditions, review order, common misunderstandings, and the statements about what a result does not prove. Those are the parts that operators forget under pressure, and they are the parts that improve runtime behavior when the knowledge set is used as an attachment family.

## Expanded practical appendix

A good operational document earns its length by making future mistakes less likely. The most useful additional detail usually lives in branch conditions, review order, common misunderstandings, and the statements about what a result does not prove. Those are the parts that operators forget under pressure, and they are the parts that improve runtime behavior when the knowledge set is used as an attachment family.

## Expanded practical appendix

A good operational document earns its length by making future mistakes less likely. The most useful additional detail usually lives in branch conditions, review order, common misunderstandings, and the statements about what a result does not prove. Those are the parts that operators forget under pressure, and they are the parts that improve runtime behavior when the knowledge set is used as an attachment family.

## Expanded practical appendix

A good operational document earns its length by making future mistakes less likely. The most useful additional detail usually lives in branch conditions, review order, common misunderstandings, and the statements about what a result does not prove. Those are the parts that operators forget under pressure, and they are the parts that improve runtime behavior when the knowledge set is used as an attachment family.

## Expanded practical appendix

A good operational document earns its length by making future mistakes less likely. The most useful additional detail usually lives in branch conditions, review order, common misunderstandings, and the statements about what a result does not prove. Those are the parts that operators forget under pressure, and they are the parts that improve runtime behavior when the knowledge set is used as an attachment family.

## Expanded practical appendix

A good operational document earns its length by making future mistakes less likely. The most useful additional detail usually lives in branch conditions, review order, common misunderstandings, and the statements about what a result does not prove. Those are the parts that operators forget under pressure, and they are the parts that improve runtime behavior when the knowledge set is used as an attachment family.

## Expanded practical appendix

A good operational document earns its length by making future mistakes less likely. The most useful additional detail usually lives in branch conditions, review order, common misunderstandings, and the statements about what a result does not prove. Those are the parts that operators forget under pressure, and they are the parts that improve runtime behavior when the knowledge set is used as an attachment family.

## Expanded practical appendix

A good operational document earns its length by making future mistakes less likely. The most useful additional detail usually lives in branch conditions, review order, common misunderstandings, and the statements about what a result does not prove. Those are the parts that operators forget under pressure, and they are the parts that improve runtime behavior when the knowledge set is used as an attachment family.

## Expanded practical appendix

A good operational document earns its length by making future mistakes less likely. The most useful additional detail usually lives in branch conditions, review order, common misunderstandings, and the statements about what a result does not prove. Those are the parts that operators forget under pressure, and they are the parts that improve runtime behavior when the knowledge set is used as an attachment family.

## Expanded practical appendix

A good operational document earns its length by making future mistakes less likely. The most useful additional detail usually lives in branch conditions, review order, common misunderstandings, and the statements about what a result does not prove. Those are the parts that operators forget under pressure, and they are the parts that improve runtime behavior when the knowledge set is used as an attachment family.

## Expanded practical appendix

A good operational document earns its length by making future mistakes less likely. The most useful additional detail usually lives in branch conditions, review order, common misunderstandings, and the statements about what a result does not prove. Those are the parts that operators forget under pressure, and they are the parts that improve runtime behavior when the knowledge set is used as an attachment family.

## Expanded practical appendix

A good operational document earns its length by making future mistakes less likely. The most useful additional detail usually lives in branch conditions, review order, common misunderstandings, and the statements about what a result does not prove. Those are the parts that operators forget under pressure, and they are the parts that improve runtime behavior when the knowledge set is used as an attachment family.

## Expanded practical appendix

A good operational document earns its length by making future mistakes less likely. The most useful additional detail usually lives in branch conditions, review order, common misunderstandings, and the statements about what a result does not prove. Those are the parts that operators forget under pressure, and they are the parts that improve runtime behavior when the knowledge set is used as an attachment family.

## Expanded practical appendix

A good operational document earns its length by making future mistakes less likely. The most useful additional detail usually lives in branch conditions, review order, common misunderstandings, and the statements about what a result does not prove. Those are the parts that operators forget under pressure, and they are the parts that improve runtime behavior when the knowledge set is used as an attachment family.

## Expanded practical appendix

A good operational document earns its length by making future mistakes less likely. The most useful additional detail usually lives in branch conditions, review order, common misunderstandings, and the statements about what a result does not prove. Those are the parts that operators forget under pressure, and they are the parts that improve runtime behavior when the knowledge set is used as an attachment family.

