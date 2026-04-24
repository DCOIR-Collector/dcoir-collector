# GitHub Memory Query Map

## Default canonical records to check
- existing-file update -> `GH-PROC-001`
- new-file create -> `GH-PROC-002`
- large-file or structural refactor -> `GH-PROC-003`
- safety-block fallback -> `GH-PROC-004`
- post-write verification -> `GH-PROC-005`
- grouped multi-file transaction -> `GH-PROC-006`
- github preflight routing -> `GH-PROC-007`
- connector reference assisted lane selection -> `GH-PROC-008`

## Notes
- prefer the compiled lookup first, then open only the selected canonical records
- for grouped changes, pair the transaction procedure with post-write verification
- for connector-function choice or lane-shape ambiguity, pair `GH-PROC-007` with `GH-PROC-008`
- after blocker recovery, reuse the same canonical record family first before proposing any new promotion candidate

## Coordinated campaign and GitHub Desktop delivery notes
- coordinated multi-skill patch campaign -> start with `GH-PROC-007`, then add the specific record family for the expected repo action
- GitHub Desktop manual repo-update delivery or grouped governed push -> pair `GH-PROC-006` with `GH-PROC-005`, and include `GH-PROC-008` when connector-lane or delivery-shape selection is still in doubt

## Additional governed-delivery pairings
- coordinated multi-skill patch campaign -> `GH-PROC-007` + `GH-PROC-008`, then pair grouped existing-file delivery with `GH-PROC-006` + `GH-PROC-005` when the change set is already known
- GitHub Desktop manual repo-update delivery or grouped governed-push bundle -> `GH-PROC-006` + `GH-PROC-005`; include `GH-PROC-008` when connector-lane or function-shape choice is still ambiguous
