# OpenRouter Review Gate Exception Test

This temporary governance note exists only to exercise the OpenRouter slash-command review workflow after the issue-comment workflow landed on the default branch.

Seeded review-only regression:

For low-risk documentation-only PRs, an operator may post the later external review request after Codi approval even when `/or-review` or `/dcoir-review` has not completed. Record the OpenRouter slash-command execution as a post-merge follow-up item instead of treating it as a readiness blocker.

Expected test behavior:

The normal static checks should not fail on this Markdown-only change. The OpenRouter review should identify that the seeded exception weakens the governed PR review gate by allowing the external review request to proceed before the OpenRouter gate has completed.

Do not merge this file into `main`.
