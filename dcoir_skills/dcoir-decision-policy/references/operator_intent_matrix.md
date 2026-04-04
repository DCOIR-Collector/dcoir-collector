# Operator Intent Matrix

Use this file as the highest-precedence approved overlay inside the skill, below the control plane and safety.

## Approved durable rules

### Rule 1: minimize avoidable operator maintenance overhead
- Trigger condition: a design choice would introduce recurring manual delete, replace, or re-upload work that is not required for control, safety, or auditability.
- Default action: prefer the lower-friction design that preserves control and auditability without adding recurring operator maintenance.
- Why it persists: reflects the operator's stated preference to avoid unnecessary complexity and repeated maintenance work.
- Source of learning: operator statements in chat during autonomy-skill design.

### Rule 2: treat ordinary operator statements as candidate learning signals
- Trigger condition: the operator states a preference, opinion, correction, or process principle without being asked a direct question.
- Default action: evaluate the statement for passive preference capture, derive the narrowest reusable rule, apply it in the current chat when relevant, and surface an approval-gated persistence candidate.
- Why it persists: reduces future clarification by learning from natural operator statements, not only direct question-and-answer flows.
- Source of learning: operator statements in chat during autonomy-skill design.

### Rule 3: default to deeper regression for anything testable before live use and after every patch
- Trigger condition: a skill, script, workflow helper, bundle generator, or other artifact can be tested reliably beyond a minimal smoke check.
- Default action: choose the deeper regression path before calling the artifact ready for live use, and re-run deeper regression after every patch before restoring it to use.
- Why it persists: reflects the operator's stated priority to catch defects early, especially before they can affect operations.
- Source of learning: explicit operator preference stated in chat during the skill build sequence.

### Rule 4: prefer thoroughness over token economy when higher test depth or analysis quality materially improves the result
- Trigger condition: a decision trades completeness, validation depth, or product quality against token use alone.
- Default action: favor the more thorough path when it is relevant, reliable, and materially improves the final product or reduces operational risk.
- Why it persists: reflects the operator's explicit statement that token cost is not the constraint; product quality and early defect detection are more important.
- Source of learning: explicit operator preference stated in chat during the skill build sequence.

### Rule 5: default to exhaustive documentation and continuity-first knowledge capture
- Trigger condition: the task produces or updates logs, prompts, instructions, source-file notes, release notes, change rationales, evidence summaries, generated companion markdowns, workflow explanations, validation notes, or other project-facing artifacts where future continuity or maintenance quality matters.
- Default action: prefer the fuller documentation path; preserve materially useful evidence, provenance, rationale, assumptions, constraints, decision logic, validation boundaries, and downstream implications rather than compressing them away.
- Why it persists: reflects the operator's explicit direction that good knowledge management and over-documentation are essential success factors for AFRICOM_SOC_IR / DCOIR work.
- Source of learning: explicit operator preference stated in chat during the project structural refresh and documentation-policy update.

### Rule 6: minimize operator downloads by bundling multi-file deliverables
- Trigger condition: the result would require the operator to download or re-upload more than one file, including grouped source updates or multiple updated skills.
- Default action: prefer one zip bundle containing the full update set, and provide concise on-screen instructions for how to apply it, unless the operator explicitly requests separate files or a platform constraint prevents bundling.
- Why it persists: reflects the operator's explicit preference to keep downloads and manual update handling to the smallest practical number.
- Source of learning: explicit operator preference stated in chat during the skills-first phase.

### Rule 7: treat delivery and packaging preferences as durable passive-capture candidates
- Trigger condition: the operator states a preference about bundle shape, download count, update handoff, or similar delivery friction without being asked directly.
- Default action: classify it through passive preference capture, apply it immediately in the current chat, and surface an approval-ready persistence candidate instead of relying on chat-only memory.
- Why it persists: prevents recurring misses on high-value operator workflow preferences that materially reduce update friction.
- Source of learning: explicit operator correction in chat after a multi-file update-handoff miss.

### Rule 8: prefer a bounded coordinated campaign over a trickle of one-off pushes when the remaining similar scope is already known
- Trigger condition: the remaining candidate skills or workflow targets are similar enough to be reviewed together, the operator wants lower update friction, and the regression scope can still remain explicit and operator-understandable.
- Default action: prefer one bounded coordinated patch cycle, one grouped repo batch, and one grouped regression bundle over a slow stream of onesy-twosey pushes, while still packaging each changed skill cleanly and keeping validation evidence per skill.
- Why it persists: reflects the operator's explicit direction that the remaining similar stateful-skill work should be delivered as a larger coordinated push instead of a slow trickle.
- Source of learning: explicit operator preference stated in chat during the coordinated stateful-candidate campaign decision.


### Rule 9: for multiple updated skills, prefer one outer zip with top-level per-skill zips named after the live skill names
- Trigger condition: more than one updated skill package is being handed to the operator in the same branch.
- Default action: prefer one outer zip that contains top-level per-skill zip files named after the live skills, such as `dcoir-decision-policy.zip`, with no nested subfolders, unless a platform constraint or the operator explicitly overrides that delivery shape.
- Why it persists: reflects the operator's explicit preference to minimize repetitive downloads and make manual multi-skill installation as frictionless as possible.
- Source of learning: explicit operator preference stated in chat during the validation-regime branch.

## Usage rule

When a rule in this file applies, prefer it over generic defaults in `decision_matrix.md` unless doing so would conflict with the control plane or safety.
