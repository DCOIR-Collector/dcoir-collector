# Decision Matrix

Use this matrix when the operator's likely preference must be inferred.

## A. Authority and source selection

| Situation | Default action |
| --- | --- |
| Airtable startup/control-plane row and live Airtable state are present | Proceed using Airtable-first startup/admin authority; read GitHub CP/source files only when repository-source work requires them |
| Current and historical files coexist | Prefer the current manifest role and ignore historical files unless explicitly requested |
| A needed file exists but is not current in the manifest | Do not treat it as authoritative |
| GitHub manifest and change log disagree outside repository-source scope | Report promoted-history drift and proceed from Airtable live authority for startup/admin/queue work |
| Control-plane role cannot be resolved | Stop and report the missing role |

## B. Packaging and release scope

| Situation | Default action |
| --- | --- |
| Structural, renamed, or broad multi-file change | Build a full-refresh bundle |
| Local testing or local execution request | Build a strict repo-layout bundle |
| Skill-only maintenance outside the Project bundle | Package the updated skill only |
| Request is ambiguous between repo and update but mentions upload/refresh | Choose update mode |
| Request is ambiguous between repo and update but mentions local test/run | Choose repo mode |

## C. Validation depth

| Situation | Default action |
| --- | --- |
| Real runtime or real workspace flow can be exercised | Run the real flow |
| Real runtime is unavailable but artifacts can be generated | Perform artifact-level validation and state the limit |
| A repair is made to a skill or script | Re-run the same failing path after the patch |
| Multiple downstream artifacts could be tested | Test the operator-facing artifact first |
| Anything testable can be exercised reliably | Default to deeper regression before live use, not smoke-only validation |
| A skill, script, or other testable artifact is patched | Re-run deeper regression before treating it as ready again |
| Testing depth competes with time or token cost | Prefer the deeper reliable test set when it meaningfully reduces production risk |

## D. Evidence handling

| Situation | Default action |
| --- | --- |
| Partial evidence only | Give best current assessment from reviewed scope only |
| One next validation step is clearly strongest | Recommend only that step |
| Several equivalent follow-ups exist | Choose the narrowest one that best reduces uncertainty |
| Evidence does not support a stronger conclusion | Keep the conclusion bounded |

## E. Execution syntax selection

| Situation | Default action |
| --- | --- |
| Endpoint-side action | Use Elastic Defend response-action syntax |
| Local analyst workstation action | Use Windows PowerShell 5.1 syntax |
| Current GitHub-readable script source is used for execution guidance | Reason from the repo path, document operator steps with the canonical runtime name |
| Request mixes incompatible execution lanes | Normalize to one lane instead of blending both |

## F. Skill-building behavior

| Situation | Default action |
| --- | --- |
| New repeated workflow appears | Prefer a dedicated skill over repeated chat-only handling |
| Infrequent but high-risk workflow appears | Prefer a governance/enforcement skill |
| A skill can enforce best practice with minimal complexity | Build it |
| A skill is stale after project changes | Reproduce, patch, re-test, and repackage |

## G. Question threshold

Ask only when the missing answer would change:
1. authority
2. safety
3. final release scope
4. verification status
5. an explicitly reserved operator choice

Otherwise proceed.


## H. Campaign execution cadence

| Situation | Default action |
| --- | --- |
| Operator approved a bounded coordinated campaign and did not ask for intermediate status-only pauses | Continue executing until there is a real operator action, blocker, materially changed evidence state, or decision requirement |
| A mid-campaign milestone produces no operator action and no branching decision | Keep working instead of stopping to summarize progress only |
| A repo-update zip, installable skill zip, blocker, or true decision point is ready | Surface it immediately with the smallest complete operator-facing handoff |

## I. Blocked repo-update recovery ladder

Use this ladder when a GitHub/API/connector repo update is blocked, partially blocked, or unverified.

| Situation | Default action |
| --- | --- |
| Direct GitHub connector write is available and safe | Use the direct connector write first because it minimizes operator burden and gives immediate readback |
| Direct write fails due to stale SHA, path mismatch, transient API behavior, or a simple argument mistake | Retry once with corrected bounded inputs or use the nearest equivalent connector operation; do not loop indefinitely |
| Direct write is blocked by connector safety, write shape limits, unsupported multi-file operation, or unreliable verification | Switch to the staged ChatGPT apply-in/GitHub Actions lane when the repo workflow supports the requested path and validation/report readback can verify the result |
| Staged apply-in is unavailable, unsafe for the target path, blocked, or unverified | Produce a GitHub Desktop/manual repo-update bundle with only affected repo-relative files and no wrapper/meta files, plus the suggested commit summary in chat/Airtable only |
| Any automation lane succeeds | Verify by GitHub readback, workflow report, logs, or file fetch before closing the Work Item |
| Any lane fails after bounded recovery | Preserve the returned log/report/error evidence, update Airtable, and surface the next smallest operator action rather than accepting the block as final |

