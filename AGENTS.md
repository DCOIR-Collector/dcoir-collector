# AGENTS.md

## Project purpose
This repository supports the AFRICOM SOC IR / DCOIR workflow. Preserve evidence-first reasoning, exact command-lane separation, and conservative claims.

## General rules
- Prefer small, reviewable changes.
- Do not remove project guidance unless explicitly asked.
- Preserve existing workflow rules unless a task specifically changes them.
- When editing code, run the closest available validation or test command.
- When changing documentation, check nearby files for naming and authority consistency.

## GitHub issue intake rules
When creating, recommending, triaging, or linking GitHub issues for this repository, use the closest available issue template.

Use:
- Bug report for code defects, broken behavior, or reproducible product/repo problems.
- Feature request for new capabilities or enhancements.
- Validation finding for live-test, regression-test, acceptance-test, or workflow validation findings.
- Collector test failure for DCOIR collector execution, harness, command, output, or packaging failures.
- Gemini / prompt-pack issue for Gemini prime-agent instructions, sub-agent instructions, combined prompt, modular prompt-pack, routing, or output-format problems.
- Documentation / workflow correction for stale, unclear, conflicting, missing, or misleading documentation and operator workflow guidance.

Do not recommend opening a blank GitHub issue unless no template fits.
If no template fits, recommend creating a new issue template first.

## Review guidelines
- Treat security regressions as high priority.
- Treat broken test instructions as high priority.
- Treat collector execution-lane confusion as high priority.
- Treat accidental credential, token, or sensitive-path exposure as high priority.
- Treat misleading documentation as review-worthy, not cosmetic.
- Check whether changes preserve Windows PowerShell 5.1 compatibility where collector instructions are involved.
