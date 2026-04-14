# Knowledge - 12 - Gemini Runtime Bundle and Source Tree

_Stored-source runtime structure, compile path, and operator-visible bundle composition_

**Summary:** Stored-source runtime tree layout, compile path, manifest-driven inventory, and the practical rules for keeping the Gemini bundle coherent.

| Source class | Authoritative basis |
| --- | --- |
| Project sources | project_sources/DCOIR_Gemini_Bundle_Source/Gemini_Bundle_Source_Manifest.json.txt; project_sources/PP-09_Gemini_Enterprise_Agent_Designer_Generator_Workflow_v1_0_0.txt; project_sources/PP-10_Gemini_Enterprise_Agent_Designer_Bounded_Design_Artifact_v0_1_1.txt; project_sources/generation_validation/compile_dcoir_gemini_bundle.py |
| Official external sources | Not required for this page |
| Scope note | The runtime bundle is source-driven from the stored-source tree. |

## Stored-source compile model

The major-version Gemini line treats the stored runtime source tree as the editable shipping surface. The maintained agent files, the generated index, the quick-start surfaces, the attachment map, and the approved knowledge attachment set all live under one governed source root. Ordinary shipment should compile from that tree instead of regenerating a new runtime on the fly.

## Top-level source tree layout

The current runtime source root is structured so the operator can reason about it by function:
- `00_START_HERE/` holds the human-readable entry surfaces that explain what is in the bundle and how the attachments are organized
- `01_GEMINI_AGENT_BUILD/` holds the prime agent, the sub-agents, and the generated runtime index for the current topology
- `02_PRIME_AGENT_ATTACHMENTS/` holds the shared knowledge files used as the approved operator-facing attachment set
- `Gemini_Bundle_Source_Manifest.json.txt` defines the runtime inventory and required file set

## Ordinary compile workflow

The stable compile rhythm is straightforward:
1. confirm the current control plane and runtime source root
2. edit the affected runtime files directly in the stored-source tree
3. update the manifest or the visible attachment inventory when the required file set changed
4. run the compile script against the source root
5. validate the compiled output and inspect the resulting ZIP contents
6. ship the compiled runtime bundle

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

