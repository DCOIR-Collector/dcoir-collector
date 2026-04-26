# Release Notes

Purpose
- This folder holds retained DCOIR release notes, transition notes, and promoted delivery history.
- Release notes preserve what was true at the time of the note. They are not the live work queue unless Airtable or the retained control plane explicitly reauthorizes them.

How to use this folder
- Use release notes as historical context for decisions, validation results, and transition state.
- Use Airtable `Queue Control`, `Work Items`, `Plans`, and `Plan Tasks` for current work order and active execution state.
- Use Airtable `Retained Repo Manifest` and `Repo Surface Registry` to confirm whether a release-note file remains part of the retained repo after final cleanup.
- If a release note mentions a next active branch, treat that as historical branch state from the note date unless a current Airtable plan or queue row confirms it remains active.

Current retained surfaces
- `20260401_connector_first_transition_note.txt` — historical connector-first transition note from 2026-04-01.

Retention posture
- Keep release notes that preserve promoted project history or explain durable workflow decisions.
- Do not delete release notes during ordinary work. T99 final cleanup may review them only after retained-manifest, Airtable coverage, and no-missing-reference gates pass.
