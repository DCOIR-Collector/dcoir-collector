# Large-File Intake Playbooks

## too-large upload
- merged_baseline_report -> ask for the findings summary plus the single most suspicious category block
- metadata_report -> ask for the process, persistence, or network section tied to the current lead
- final_artifacts -> ask for the one most suspicious file or the narrowest decisive excerpt
- enrichment_report -> ask for the enrichment block tied to the lead under review
- retrieved_artifact -> ask for the smallest behavior-defining excerpt such as the task action, script function, config key, or registry branch
- raw_event_export -> ask for the event id, timestamp window, and the narrowest decisive event excerpt

## missing file
- ask for the next best adjacent artifact
- pivot to metadata, event excerpts, command output, screenshots, or the analyst summary if available
- prefer the upstream artifact in the DCOIR review order when the downstream artifact is missing

## partial upload
- state the bounded confidence limit
- analyze what is present
- request the most decision-relevant missing slice next
- prefer one next requested slice over a long shopping list
