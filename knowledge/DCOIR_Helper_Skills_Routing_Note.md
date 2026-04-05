# DCOIR Helper Skills Routing Note

This note is a governed descriptive routing aid for the current `dcoir-*` helper skills.

## Fast routing matrix

| Task family | Preferred helper skill | Typical routing cues | Notes |
| --- | --- | --- | --- |
| Resume current project state | dcoir-session-resume | resume, where are we, what is current | Start here for continuity-focused restarts |
| GitHub repo write or grouped update work | dcoir-memory-preflight | update GitHub, grouped repo edit, control-plane change | Consult task memory before execution |
| Decide default branch or operator-preference path | dcoir-decision-policy | choose path, operator preference, batch updates | Prefer fewer manual waves when compatible fixes exist |
| What else must change after a repo update | dcoir-change-impact-analyzer | downstream impact, refresh set | Use after a proposed or completed change |
| Review release or packaging class | dcoir-release-scope-builder | what delivery class, targeted or manual repo bundle | Use after the changed set is known |
| Review readiness before treating a change as ready | dcoir-promotion-readiness-reviewer | is this ready, blocking gaps, regression evidence | Use after packaging posture is settled |
| Collector QA or repair | dcoir-collector-qa | collector error, harness failure | Collector maintenance aid |
| Operator execution or collector-follow-through guidance | dcoir-operator-workflow-hardener | next endpoint step, cleanup guidance, NEXT_GET_FILE | Keep runtime filename and lane separation explicit |
| Validation plan or test sequencing | dcoir-validation-orchestrator | validation plan, test order | Default for explicit validation planning |
| Deep regression for helper skills | dcoir-skill-regression-auditor | regression plan, fixture coverage | Use before or after skill changes |
| Verify package/source parity or install drift | dcoir-parity-verifier | parity drift, package cleanliness, installed mismatch | Use for governed source vs delivered-skill checks |
| Session-local continuity and grouped-push cleanup | dcoir-session-tracker | what is left, staged write set, handoff | Local JSON working-state skill |
| Task decomposition and resume-state guidance | dcoir-plan-tracker | plan work, blocker capture, resume plan | Local JSON plan-state skill |
| Root or folder README maintenance | dcoir-readme-maintainer | improve README, navigation links | Focused README upkeep |
| Knowledge and supporting docs maintenance | dcoir-knowledge-doc-maintainer | regenerate docs, inventory doc changes | Knowledge-doc generation and refresh |
| Reassemble the combined analyst-facing prompt draft | dcoir-prompt-pack-assembler | rebuild prompt pack, combined master draft, reassemble pp-01 through pp-07 | Uses the live GitHub-primary `project_sources/` prompt-pack line |
| Define the triage-to-DCOIR handoff contract | dcoir-triage-to-collector-escalation-designer | escalation contract, triage handoff, expected next evidence | Keep the next DCOIR step and next expected artifact explicit |
| Keep working when evidence is too large, partial, or missing | dcoir-large-file-intake-manager | too large to upload, partial artifact, missing file | Prefer one high-value next requested slice over a broad dump |
| Rank what to fix first after live testing | dcoir-live-test-remediation-planner | live-test findings, remediation order, what to fix first | Use current delivery classes, not the retired coarse split |
| Coordinate renames and naming-model changes | dcoir-structural-rename-coordinator | rename file, re-home source, rename skill, structural rename | Map current repo and skill delivery posture before patching |
| Emit conspicuous attention banners | dcoir-attention-signaler | milestone, blocked, action required, session start | Use in DCOIR chats when the operator should look now |

## Inventory note
The current governed helper-skill source set lives under `dcoir_skills/` and the project control plane remains the authority for what is current.
