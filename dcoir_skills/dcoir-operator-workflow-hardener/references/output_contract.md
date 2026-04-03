# Output Contract

## Exact next-step answer
Use this compact structure when the operator wants the next move only:

- Current assessment: <one sentence>
- Best next action: <one command or one action>
- Why: <one short sentence>

## Pasted collector-output interpretation
Use this structure when the user pastes raw collector output:

- Workflow phase: <one phase label>
- Current assessment: <one sentence>
- Best next action: <one action>
- Why: <one short sentence>
- Immediate follow-on: <optional, only if strongly implied>

## Lane-selection rule
- Endpoint-side steps: Elastic syntax only
- Local review steps: PowerShell 5.1 or analyst-tool action only
- If both are needed, order them as separate numbered steps, never a blended command

## High-priority cues
Prioritize these explicit markers when present:
1. `NEXT_GET_FILE`
2. `CLEANUP_COMMAND`
3. `DELETE_SCRIPT_COMMAND`
4. `CLEANUP_STATUS`
5. interpretation-guide text
