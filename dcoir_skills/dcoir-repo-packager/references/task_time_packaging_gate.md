# Task-time packaging gate

Use this reference when DCOIR work may produce or rely on a package, ZIP, bundle, affected-file artifact, installable skill package, GitHub Desktop manual update payload, or package validity claim.

## Trigger checklist
Run the gate before:
- creating repo-layout, bootstrap/update, GitHub Desktop manual update, skill, outer multi-skill, or affected-file packages;
- deciding wrapper-root/no-wrapper-root shape;
- deciding affected repo-relative paths;
- deciding whether commit summaries belong in chat/Airtable or inside an artifact;
- fallback from blocked connector/workflow update to manual bundle;
- claiming installability, marker/readback readiness, package hygiene, or validation evidence.

## Compact output
Return only:
1. package mode;
2. authority/source basis;
3. included paths/classes;
4. excluded paths/classes;
5. wrapper-root rule;
6. artifact filename(s);
7. validation/readback required;
8. companion skills;
9. safest next action.

## Hard rules
Do not package unapproved files, inferred files, missing files, wrapper roots for GitHub Desktop manual updates, `.git` directories, runtime residue, local caches unless explicitly approved as sanitized fixtures, or ChatGPT-only meta files. Keep suggested commit summaries out of GitHub Desktop manual update ZIPs unless explicitly requested as files.
