# Knowledge - 09 - FAQ

_Short answers to recurring operator and project questions_

**Summary:** This page answers common workflow, packaging, and documentation questions using the current project rules.

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
