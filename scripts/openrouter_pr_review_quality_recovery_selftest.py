#!/usr/bin/env python3
"""Offline checks for review-quality recovery retries."""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "openrouter_pr_review_hardened.py"

spec = importlib.util.spec_from_file_location("openrouter_pr_review_hardened", SCRIPT)
if spec is None or spec.loader is None:
    raise SystemExit("unable to load openrouter_pr_review_hardened.py")
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

os.environ["GITHUB_REPOSITORY"] = "DCOIR-Collector/dcoir-collector"
os.environ["PR_NUMBER"] = "296"

config = mod.load_hardened_config(str(ROOT / ".github" / "openrouter-pr-review-governed.yml"))
assert config.review_quality_retry_on_rejected_output is True

schema = json.loads((ROOT / "schemas" / "openrouter-pr-review.schema.json").read_text(encoding="utf-8"))
sample_diff = """diff --git a/docs/review.md b/docs/review.md
index 1111111..2222222 100644
--- a/docs/review.md
+++ b/docs/review.md
@@ -1,2 +1,3 @@
 Review gates remain required.
+External review may be skipped after local checks.
 Keep issue receipts current.
"""
line_index = mod.build_added_line_index(sample_diff)
assert ("docs/review.md", 2) in line_index
assert ("docs/review.md", 1) not in line_index
assert ("docs/review.md", 3) not in line_index


def accepted_result(confidence: float = 0.94) -> dict:
    return {
        "summary": "One actionable review-gate regression.",
        "findings": [
            {
                "title": "Review gate bypass",
                "severity": "high",
                "confidence": confidence,
                "path": "docs/review.md",
                "line": 2,
                "body": "The changed line weakens governed review ordering.",
                "suggested_replacement": "",
                "validation": "Read back issue and PR review gates.",
            }
        ],
    }


def run_recovery_case(first_result: dict, expected_reason: str) -> None:
    calls: list[str] = []
    original_openrouter_review = mod.openrouter_review

    def fake_openrouter_review(prompt: str, _schema: dict, _config: object, _reporter: object | None = None):
        calls.append(prompt)
        if len(calls) == 1:
            return first_result, "first-model", ""
        return accepted_result(), "recovery-model", ""

    mod.openrouter_review = fake_openrouter_review
    try:
        retry_result, retry_model, _retry_tier = mod.openrouter_review_with_quality_retry(
            "initial prompt",
            schema,
            config,
            None,
            [],
            line_index,
        )
    finally:
        mod.openrouter_review = original_openrouter_review

    assert len(calls) == 2
    assert retry_model == "recovery-model"
    assert len(mod.normalize_findings(retry_result, config, line_index)) == 1
    assert "Review quality retry" in calls[1]
    assert expected_reason in calls[1]


run_recovery_case(
    {"summary": "A governance regression remains in the review gate.", "findings": []},
    "summary indicated a possible issue",
)

run_recovery_case(
    {
        "summary": "Possible review gate bypass.",
        "findings": [
            {
                "title": "Review gate bypass",
                "severity": "high",
                "confidence": 0.20,
                "path": "docs/review.md",
                "line": 2,
                "body": "The changed line may weaken governed review ordering.",
                "suggested_replacement": "",
                "validation": "Read back issue and PR review gates.",
            }
        ],
    },
    "none met the configured minimum confidence",
)


run_recovery_case(
    {
        "summary": "One actionable review-gate regression, but the anchor is wrong.",
        "findings": [
            {
                "title": "Review gate bypass",
                "severity": "high",
                "confidence": 0.95,
                "path": "docs/review.md",
                "line": 99,
                "body": "The changed line weakens governed review ordering.",
                "suggested_replacement": "",
                "validation": "Read back issue and PR review gates.",
            }
        ],
    },
    "none were anchored to changed diff lines",
)

run_recovery_case(
    {
        "summary": "One actionable review-gate regression, but the anchor is on context.",
        "findings": [
            {
                "title": "Review gate bypass",
                "severity": "high",
                "confidence": 0.95,
                "path": "docs/review.md",
                "line": 1,
                "body": "The changed line weakens governed review ordering, but this anchor is unchanged context.",
                "suggested_replacement": "",
                "validation": "Read back issue and PR review gates.",
            }
        ],
    },
    "none were anchored to changed diff lines",
)

retry_disabled = copy.copy(config)
retry_disabled.review_quality_retry_on_rejected_output = False
calls: list[str] = []
original_openrouter_review = mod.openrouter_review


def fake_disabled_review(prompt: str, _schema: dict, _config: object, _reporter: object | None = None):
    calls.append(prompt)
    return {"summary": "A governance regression remains in the review gate.", "findings": []}, "first-model", ""


mod.openrouter_review = fake_disabled_review
try:
    disabled_result, _disabled_model, _disabled_tier = mod.openrouter_review_with_quality_retry(
        "initial prompt",
        schema,
        retry_disabled,
        None,
        [],
        line_index,
    )
finally:
    mod.openrouter_review = original_openrouter_review

assert len(calls) == 1
try:
    mod.normalize_findings(disabled_result, retry_disabled, line_index)
except mod.ReviewQualityError as exc:
    assert "summary indicated a possible issue" in str(exc)
else:
    raise AssertionError("summary-only quality failure should still fail closed when recovery is disabled")

print("review quality recovery selftest passed")
