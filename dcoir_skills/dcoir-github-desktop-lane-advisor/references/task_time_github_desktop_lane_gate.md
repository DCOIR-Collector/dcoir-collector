# Task-time GitHub Desktop Lane Gate

Use this reference when DCOIR work may require local Git, GitHub Desktop, manual bundles, operator_tools, reusable PowerShell helpers, repo snapshots, patch/apply packages, GitHub Actions launchers, or local execution guidance.

## Trigger checklist
Run a compact gate before final instructions when any of these appear:
- local git or GitHub Desktop status, conflict, pull, commit, push, branch, or bundle guidance;
- speed-lane or manual repo-update bundle selection;
- targeted/text-only repo snapshot or operator upload request;
- reusable PowerShell helper recommendation or new tool candidate;
- GitHub Actions orchestrator or local launcher guidance;
- repo patch/apply, ChatGPT-friendly ZIP, validation/log capture, or failed lane recovery;
- repeated local-tool friction that should become a durable operator tool.

## Compact output
Return:
1. lane classification;
2. Operator Tools Registry/catalog surfaces consulted or required;
3. existing tool selected, new tool candidate, or no-tool decision;
4. safety preconditions and destructive-command restrictions;
5. exact launcher/output/log/ZIP only when safe;
6. companion skills to invoke;
7. verification/readback path;
8. checkpoint need;
9. best next move.

## Safety rules
Prefer existing active tools and module patterns over one-off scripts. Never recommend destructive git cleanup, forced overwrite, stash pop, reset hard, git clean, or deletion without explicit operator intent, safety rationale, and a verified recovery path. Keep local config names secret-safe and route config variables through dcoir-local-config-registry-maintainer.
