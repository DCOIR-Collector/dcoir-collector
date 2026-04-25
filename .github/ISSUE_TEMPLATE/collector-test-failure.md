---
name: Collector test failure
about: Report a DCOIR collector execution, harness, command, output, or packaging failure
title: '[Collector test failure]: '
labels: ['collector', 'test-failure', 'needs-triage']
assignees: ''

---

## Collector test failure

### Test lane
- [ ] Local workstation test - Windows PowerShell 5.1
- [ ] Elastic Defend response action
- [ ] GitHub Actions workflow
- [ ] Gemini-guided workflow
- [ ] Runtime package / delivery bundle
- [ ] Other

### Exact command or instruction used
Paste the exact local command, Elastic response-action command, workflow dispatch input, or Gemini instruction.

### Actual result
Paste the error, output, failed assertion, missing file, or observed behavior.

### Expected result
Describe what should have happened.

### Environment
- OS / endpoint:
- PowerShell version:
- Elastic context, if relevant:
- Package or collector version, if known:

### Evidence
Attach screenshots, logs, output files, retrieved bundles, workflow run links, or relevant issue links.

### Blocking level
- [ ] Blocks all collector testing
- [ ] Blocks one collector path
- [ ] Blocks packaging or retrieval only
- [ ] Non-blocking but confusing
- [ ] Documentation-only issue

### Command-lane check
- [ ] Local PowerShell syntax was kept separate from Elastic response-action syntax
- [ ] This issue may involve command-lane confusion

### Recommended next action
Describe the likely fix, retest, or deeper triage step.
