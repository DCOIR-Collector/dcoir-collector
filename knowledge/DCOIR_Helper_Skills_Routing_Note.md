# DCOIR Helper Skills Routing Note

This note is a governed descriptive routing aid for the current `dcoir-*` helper skills.

## Fast routing matrix

| Task family | Preferred helper skill | Typical routing cues | Notes |
| --- | --- | --- | --- |
| Resume current project state | dcoir-session-resume | resume, where are we, what is current | Start here for continuity-focused restarts |
| GitHub repo write or grouped update work | dcoir-memory-preflight | update GitHub, grouped repo edit, control-plane change | Consult task memory before execution |
| Validation plan or test sequencing | dcoir-validation-orchestrator | validation plan, test order | Default for explicit validation planning |
| Collector QA or repair | dcoir-collector-qa | collector error, harness failure | Collector maintenance aid |
| Rank what to fix first after live testing | dcoir-live-test-remediation-planner | live-test findings, remediation order, what to fix first | Use current delivery classes, not the retired coarse split |
| Session-local continuity and grouped-push cleanup | dcoir-session-tracker | what is left, staged write set, handoff | Local JSON working-state skill |
| Root or folder README maintenance | dcoir-readme-maintainer | improve README, navigation links | Focused README upkeep |
| Knowledge and supporting docs maintenance | dcoir-knowledge-doc-maintainer | regenerate docs, inventory doc changes | Knowledge-doc generation and refresh |

## Testing workflow note
The standard dynamic manual-testing surface for collector and Gemini sessions is Airtable table `Validation Test Cases`.

Use that table to:
- start future collector/Gemini testing sessions
- pick the relevant active test IDs
- update observed status and evidence during the run
- add, split, retire, or narrow rows as the product changes

GitHub remains the engineering, source, packaging, workflow, and issue-tracking surface.
