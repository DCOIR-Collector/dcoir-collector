# Knowledge - 09 - FAQ

_Short answers to recurring operator and project questions_

**Summary:** Fast-reference answers to recurring DCOIR workflow, packaging, authority, command-lane, and maintenance questions.

| Source class | Authoritative basis |
| --- | --- |
| Project sources | project_sources/CP-01_DCOIR_Version_Manifest.txt; project_sources/CP-02_DCOIR_Change_Log.txt; project_sources/DOC-01_AFRICOM_SOC_IR_Project_Setup_and_Workflow.txt; project_sources/DOC-03_DCOIR_Repository_Layout_Spec_v1_0_0.txt |
| Official external sources | Not required for this page |
| Scope note | Answers here summarize current project rules; they do not replace the control plane. |

## Questions and answers

| Question | Answer |
| --- | --- |
| Why do some historical references still mention `.ps1.txt` or `.cmd.txt` files? | Older Project-space or bundle-oriented workflow references used readable text suffixes more heavily. The current GitHub-primary governed working line keeps current readable sources at native repo paths such as `project_sources/DCOIR_Collector.ps1` and `project_sources/run_DCOIR_Tests.ps1`. |
| Why is `DCOIR_Collector.zip` treated differently from the script sources? | It is a retained supporting asset used for packaging and local execution support, but it is not part of the control plane. |
| Why are Knowledge docs non-authoritative? | They are supporting human-readable docs meant to help the operator. They must not override the control plane or other authoritative project sources. |
| Why is there no default `.cmd` harness wrapper in current guidance? | The current governed line does not carry a default `run_DCOIR_Tests.cmd` wrapper. Local regression should use `run_DCOIR_Tests.ps1` directly unless the control plane later restores a wrapper source. |
| When do I use local PowerShell syntax instead of `execute --command`? | Use local PowerShell syntax for local test and workstation tasks. Use `execute --command` only for endpoint response-console actions. |
| Why do GitHub Desktop manual repo-update bundles include a suggested commit summary? | The current operator workflow uses GitHub Desktop as the easiest approved path for grouped repo-relative file placement, and the suggested commit summary reduces manual friction during those waves. |

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.

## Expanded questions and answers

**Q: What is the fastest way to think about DCOIR?**

Think of DCOIR as a bounded host-evidence workflow that exists to answer real investigative questions without turning every case into an unconstrained shell session or a monolithic collect-everything event.

**Q: What is the difference between the collector line and the Gemini line?**

The collector line gathers or stages host-side evidence. The Gemini line helps route, interpret, and structure the next analyst-facing move using the stored-source runtime tree and its attachment set.

**Q: Why are knowledge docs not authoritative?**

They preserve readable operational guidance. They must help the operator use the system correctly without redefining current behavior independently of the governed source line.

**Q: When should I use Tier 1?**

Use Tier 1 when you need the normal first-pass baseline host package before choosing a narrower enrichment, retrieval, or deeper collection branch.

**Q: When should I use Tier 2?**

Use Tier 2 after baseline review established a real need for deeper persistence or configuration context, not just because more data feels safer.

**Q: Why is one-action-at-a-time enrichment important?**

It keeps the causal link between the blocked question and the chosen follow-up action clear. That makes later review and decision-making much cleaner.

**Q: When is retrieval better than more collection?**

Retrieval is better when the existing output already points to a known artifact that is more likely to answer the next question than another wide collection step.

**Q: Why keep endpoint and local syntax separate?**

Because the same collector invocation means different things in an endpoint response-action lane and a local PowerShell lane. Mixing them creates confusion faster than almost any other operator mistake.

**Q: What should I read first after a Tier 1 run?**

Start with the merged baseline report when available, then metadata, then flat final_artifacts output, then any artifacts those surfaces clearly elevate as high signal.

**Q: Are metadata reports evidence?**

Metadata reports are useful workflow-state artifacts. They explain what ran and what was produced, but they are not automatically proof of suspicious activity.

**Q: What is the public-source IOC rule in one sentence?**

Public enrichment supports context and corroboration for evidence-grounded indicators, but it never replaces case evidence or becomes case truth by itself.

**Q: Why does the Gemini workflow favor a long Description field?**

Because Description is treated as routing-critical. A strong runtime Description tells the system what the agent owns, what inputs it expects, what outputs it controls, and when it should be selected.

**Q: Why compile from the stored-source tree?**

Because ordinary shipment should come from the governed editable runtime source tree rather than improvised generation during packaging.

**Q: Do new Gemini attachment files require other updates?**

Often yes. If the required attachment set or operator-visible knowledge inventory changes, the attachment map and sometimes the manifest should be refreshed so the bundle remains coherent.

**Q: Where does current manual testing state belong?**

Airtable Validation Test Cases is the dynamic manual-testing surface. GitHub remains the engineering and packaging authority for durable source changes.

## Practical heuristics worth memorizing

- Narrow question first, then narrow branch.
- Wrapper artifact first only if it helps choose the real evidence carrier.
- Baseline before deeper context unless a narrower follow-up is already clearly justified.
- Retrieval before rerun when the artifact already exists.
- Stored-source compile before ad hoc generation for ordinary Gemini shipment.
- Attachment coherence matters; new files should not become orphaned extras.

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

