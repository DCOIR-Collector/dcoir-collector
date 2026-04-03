# Knowledge - 09 - FAQ

_Short answers to recurring operator and project questions_

**Summary:** This page answers the most common workflow and packaging questions using the current project rules.

| Source class | Authoritative basis |
| --- | --- |
| Project sources | CP-01_DCOIR_Version_Manifest.txt; DOC-01_AFRICOM_SOC_IR_Project_Setup_and_Workflow.txt; DOC-03_DCOIR_Repository_Layout_Spec_v1_0_0.txt; LOG-02_DCOIR_Lessons_Learned_Log.txt |
| Official external sources | Not required for this page |
| Scope note | Answers here summarize current project rules; they do not replace the control plane. |

## Questions and answers

| Question | Answer |
| --- | --- |
| Why do script files sometimes end in .ps1.txt or .cmd.txt? | The .txt suffix keeps the file readable inside the Project workspace. Repo or bundle generation strips only the final .txt to emit the native runtime file. |
| Why is DCOIR_Collector.zip treated differently from the .txt sources? | It is a supporting uploaded package asset for packaging, repo, and harness workflows, but it is not part of the control plane. |
| Why are Knowledge docs non-authoritative? | They are supporting human-readable docs meant to help the operator. They must not override the control plane or other authoritative project sources. |
| Why does the .cmd wrapper exist if the PowerShell harness already exists? | It gives the operator a one-command entry point for local full regression while keeping the uploaded PowerShell harness source readable inside the Project workspace. |
| When do I use local PowerShell syntax instead of execute --command? | Use local PowerShell syntax for local test and workstation tasks; use execute --command only for endpoint response-console actions. |

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
