---
name: dcoir-attention-signaler
description: emit conspicuous dcoir attention banners for chat responses when chatgpt needs to draw the operator's eye to the screen. use in every africom_soc_ir or dcoir project chat session on the first substantive project response, again at major mid-conversation milestones or important review points, whenever a direct operator answer or approval is needed, and for major completions or blocked states. supports session-start, milestone, review, complete, action-required, and blocked banner classes with header, footer, and dual placements. use only when working inside the africom_soc_ir / dcoir project context; if that project context is not present, do not use this skill. follow the airtable-first startup/control-plane model and use github only for governed source, promoted history, packaging, or explicit repo readback when required.
---

<!-- skill-marker: updated-skill|20260427T180000Z|T4.0.5.9-airtable-first-startup-cutover|source-update|dcoir-attention-signaler|SKILL.md -->

# DCOIR Attention Signaler

## Airtable-first startup authority
- For normal AFRICOM_SOC_IR / DCOIR startup, resume, current-state reporting, administrative control, queue selection, active-plan recovery, helper-memory lookup, or operator-preference recovery, use Airtable-first authority.
- Required order: Project Instructions; CP-00 only as a bootstrap pointer when present; Airtable `Governance Control Plane` row `CONTROL-STARTUP-AIRTABLE-FIRST`; Airtable `Session Checkpoints`; Airtable `Queue Control`; Airtable `Work Items`; active Airtable `Plans` and `Plan Tasks`; Airtable `Operator Preferences`; then skill-specific Airtable memory tables when relevant.
- Do not fetch GitHub `CP-01` or `CP-02` during normal startup when the Airtable startup-control row is available and current.
- Read GitHub CP files only for repository-source tasks: source-file role resolution, packaging or release bundles, prompt/collector source inspection, promoted-history comparison, final T99 keep/delete review, or explicit operator request.
- Treat any older instruction that says to read `CP-01` and `CP-02` first as superseded for startup, resume, queue, administrative-control, helper-memory, and operator-preference branches. If a source task still requires those files and they are absent, use Airtable `Governance Control Plane`, `Repo Surface Registry`, `Repo File Coverage Detail`, `Retained Repo Manifest`, and active plan state before stopping.


## Required project gate
This skill is for the AFRICOM_SOC_IR / DCOIR project only.
Before proceeding, verify that the current task is actually inside the AFRICOM_SOC_IR / DCOIR project context and grounded in the current Airtable-first authority model or current governed GitHub source working line.
If the current AFRICOM_SOC_IR / DCOIR project context is not present, do not proceed.

Use this skill to add conspicuous visual attention cues to important DCOIR responses.

## Core workflow
1. Classify the attention state as one of these: `session-start`, `milestone`, `review`, `complete`, `action-required`, or `blocked`.
2. Choose placement:
   - `header` for the first substantive reply in a DCOIR project chat or for immediate attention before the main response
   - `footer` for completion or lower-urgency review signaling after the main response
   - `dual` for major milestones, direct operator-answer prompts, approval requests, or blocked states
3. Choose a short message.
4. Run `scripts/render_attention_signal.py` when a deterministic banner is useful.
5. Insert the rendered banner into the response.

## Session-start default
- In every AFRICOM_SOC_IR or DCOIR project chat session, emit a `session-start` banner on the first substantive project response.
- Use `header` placement for the session-start banner.
- Keep the message short and action-oriented, such as `dcoir architecture review in progress` or `important dcoir review in progress`.
- Do not wait for completion or a blocked state before signaling in a project session.

## Mid-conversation signaling defaults
- Emit a `milestone` banner at major mid-conversation review points when the operator should look at the screen now even though the task is not finished.
- Prefer `dual` placement for major architecture decisions, important branch resolutions, substantial interim findings, or any point where the operator would likely want to read immediately.
- Emit an `action-required` banner whenever the response contains a direct operator question, approval request, or decision that materially gates the next branch.
- For `action-required`, prefer `dual` placement and place the question or required decision immediately after the header banner.
- Use `review` for important but lower-urgency inspection points that do not block the next branch.

## Default placement rules
- Use `header` for `session-start`.
- Use `dual` for `milestone` when the result is important enough that the operator should notice mid-stream.
- Use `footer` or `dual` for `review` depending on importance.
- Use `footer` for important completions.
- Use `dual` for approval requests, direct operator-answer prompts, or blocked states.
- Use `header` only when the operator needs to notice the issue before reading the body.

## Styling rules
- Do not claim to create a true browser popup or guaranteed audio alert from this environment.
- Do not claim reliable red text, arbitrary text color, or client-side styling support. Chat rendering may ignore HTML, ANSI, or CSS color attempts.
- Prefer stronger borders, uppercase labels, short high-signal wording, and `dual` placement over unreliable color tricks.
- If a client happens to render inline color markup, treat that as incidental rather than guaranteed behavior.

## Hard rules
- Do not omit the first substantive banner in a DCOIR project chat session.
- Do not omit banners for direct operator-answer or approval-needed turns.
- Do not spam banners on every low-importance turn after the session-start banner.
- Keep the message short, high-signal, and specific.
- Prefer banner classes from `references/banner_message_templates.md`.

## Command
```bash
python scripts/render_attention_signal.py --signal-class milestone --placement dual --message "important architecture decision ready for review"
```

## Output handling
- For any DCOIR project chat session, prefer a `session-start` header banner on the first substantive response.
- For major mid-conversation findings, architecture decisions, or interim review points, prefer a `milestone` dual banner.
- For direct operator questions or approvals, prefer an `action-required` dual banner.
- For completion after substantial work, prefer a footer banner.
- Keep the main response readable; the banner should draw attention, not replace the content.

## References
- `references/banner_message_templates.md`
- `references/attention_modes.md`
