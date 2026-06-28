#!/usr/bin/env python3
"""Offline checks for the hardened DCOIR Review runner."""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "openrouter_pr_review_hardened.py"

spec = importlib.util.spec_from_file_location("openrouter_pr_review_hardened", SCRIPT)
if spec is None or spec.loader is None:
    raise SystemExit("unable to load openrouter_pr_review_hardened.py")
mod = importlib.util.module_from_spec(spec)
import sys

sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

os.environ["GITHUB_REPOSITORY"] = "DCOIR-Collector/dcoir-collector"
os.environ["PR_NUMBER"] = "277"

config = mod.load_hardened_config(str(ROOT / ".github" / "openrouter-pr-review-governed.yml"))
assert "/or-review" in config.commands
assert "/dcoir-review" in config.commands
assert config.model == "openrouter/auto"
assert config.model_stack == ["openrouter/auto"]
assert config.smoke_test_free_model is False
assert config.auto_cost_quality_tradeoff == 2
assert "openai/gpt-5*" in config.auto_allowed_models
assert "google/gemini-2.5-pro*" in config.auto_allowed_models
assert "google/gemini-3.1-pro*" in config.auto_allowed_models
assert "google/gemini-*" not in config.auto_allowed_models
assert config.fallback_models == []
assert config.fail_on_unanchored_findings is True
assert config.fail_on_summary_only_problem is True
assert config.risk_sentinel_quality_gate is True
assert config.risk_sentinel_retry_on_empty is True
assert config.risk_sentinel_max_anchors == 12
assert config.debug is False
assert config.post_progress_comment is False

budgeted_findings = mod.select_findings_for_inline(
    [
        {
            "title": "Optional TypeScript issue",
            "severity": "critical",
            "confidence": 0.99,
            "path": "project_sources/validation/example.ts",
            "line": 10,
            "body": "Optional TypeScript issue.",
            "suggested_replacement": "",
            "validation": "",
        },
        {
            "title": "PowerShell issue",
            "severity": "high",
            "confidence": 0.90,
            "path": "collector/run.ps1",
            "line": 20,
            "body": "PowerShell issue.",
            "suggested_replacement": "",
            "validation": "",
        },
        {
            "title": "GitHub Actions issue",
            "severity": "medium",
            "confidence": 0.90,
            "path": ".github/workflows/validate.yml",
            "line": 5,
            "body": "GitHub Actions issue.",
            "suggested_replacement": "",
            "validation": "",
        },
    ],
    2,
)
assert [item["path"] for item in budgeted_findings] == ["collector/run.ps1", ".github/workflows/validate.yml"]

validation_hints = mod.validation_hint_block(
    [
        {"filename": "collector/example.py"},
        {"filename": "collector/example.ps1"},
        {"filename": ".github/workflows/openrouter-pr-review.yml"},
    ]
)
assert "python3 -m py_compile collector/example.py" in validation_hints
assert "PSParser" in validation_hints
assert "build_workflow_inventory.py --check" in validation_hints

short_prompt_config = copy.copy(config)
short_prompt_config.max_prompt_chars = 900
large_diff = """diff --git a/docs/review.md b/docs/review.md
index 1111111..2222222 100644
--- a/docs/review.md
+++ b/docs/review.md
@@ -1,2 +1,3 @@
 Review gates remain required.
+External review may be skipped after local checks.
 Keep issue receipts current.
""" + ("+filler line to force prompt truncation\n" * 200)
bounded_prompt = mod.build_prompt(
    {"number": 277, "title": "Prompt budget test", "body": "Ensure hardening survives truncation."},
    [{"filename": "docs/review.md", "status": "modified", "additions": 201, "deletions": 0, "changes": 201}],
    large_diff,
    short_prompt_config,
)
assert len(bounded_prompt) <= short_prompt_config.max_prompt_chars
assert bounded_prompt.startswith("Governed review hardening requirements:")
assert "Every semantic, Markdown, governance, validation, or review-gate concern" in bounded_prompt

schema = json.loads((ROOT / "schemas" / "openrouter-pr-review.schema.json").read_text(encoding="utf-8"))
payload = mod.build_openrouter_payload("review prompt", schema, config, ["venice"], "openrouter/auto")
assert payload["model"] == "openrouter/auto"
assert "models" not in payload
assert payload["provider"]["ignore"] == ["venice"]
assert payload["provider"]["allow_fallbacks"] is True
assert payload["provider"]["require_parameters"] is True
assert payload["response_format"]["type"] == "json_schema"
assert payload["response_format"]["json_schema"]["strict"] is True
assert payload["plugins"] == [
    {
        "id": "auto-router",
        "allowed_models": config.auto_allowed_models,
        "cost_quality_tradeoff": 2,
    }
]
assert payload["session_id"].startswith("dcoir-review:DCOIR-Collector-dcoir-collector:pr-277")
assert len(payload["session_id"]) <= 256

with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
    handle.write(
        "\n".join(
            [
                "commands:",
                "  - /or-review",
                "model: openrouter/free",
                "model_stack:",
                "  - openrouter/free",
                "smoke_test_free_model: false",
            ]
        )
    )
    free_config_path = handle.name
try:
    try:
        mod.load_hardened_config(free_config_path)
    except RuntimeError as exc:
        assert "smoke-test only" in str(exc)
    else:
        raise AssertionError("free-router config without smoke opt-in should fail")
finally:
    Path(free_config_path).unlink(missing_ok=True)

sample_diff = """diff --git a/docs/review.md b/docs/review.md
index 1111111..2222222 100644
--- a/docs/review.md
+++ b/docs/review.md
@@ -1,2 +1,3 @@
 Review gates remain required.
+External review may be skipped after local checks.
 Keep issue receipts current.
"""
line_index = mod.base.build_diff_line_index(sample_diff)
accepted = mod.normalize_findings(
    {
        "summary": "One actionable review-gate regression.",
        "findings": [
            {
                "title": "Review gate bypass",
                "severity": "high",
                "confidence": 0.95,
                "path": "docs/review.md",
                "line": 2,
                "body": "The changed line weakens governed review ordering.",
                "suggested_replacement": "",
                "validation": "Read back issue and PR review gates.",
            }
        ],
    },
    config,
    line_index,
)
assert len(accepted) == 1

inline_findings, review_body_findings = mod.split_findings(
    {
        "summary": "The only high-signal finding is a review-gate regression.",
        "findings": [
            {
                "title": "Review gate bypass",
                "severity": "high",
                "confidence": 0.95,
                "path": "docs/review.md",
                "line": 99,
                "body": "The changed wording weakens governed review ordering.",
                "suggested_replacement": "",
                "validation": "Read back issue and PR review gates.",
            }
        ],
    },
    config,
    line_index,
)
assert inline_findings == []
assert len(review_body_findings) == 1
assert "not an added changed line" in review_body_findings[0]["_unanchored_reason"]


def assert_clean(summary: str) -> None:
    assert mod.normalize_findings({"summary": summary, "findings": []}, config, line_index) == []


def assert_problem(summary: str) -> None:
    try:
        mod.normalize_findings({"summary": summary, "findings": []}, config, line_index)
    except mod.ReviewQualityError as exc:
        assert "summary indicated a possible issue" in str(exc)
    else:
        raise AssertionError(f"summary should fail review quality: {summary}")


for clean_summary in [
    "No high-confidence inline findings were found.",
    "No high-confidence issues.",
    "No actionable issues remain.",
    "No high-confidence regressions.",
    "No issues, regressions, or risks were identified.",
    "No findings, issues, regressions, or failures remain.",
    "No security issues, workflow regressions, or operational risks remain.",
    "No security issues, workflow regressions or operational risks remain.",
    "No security issues and workflow regressions remain.",
    "No security issues and regressions remain.",
    "No findings and issues were identified.",
    "No findings.",
    "No workflow security risks were identified.",
    "No regressions found.",
    "No regressions found and no security risks remain.",
    "No regressions found. No security risks remain.",
    "No high-confidence actionable findings. The PR hardens native GitHub suggestion verification by anchoring replacements to the actual file text, reducing the maximum length, blocking multi-line and marker-containing suggestions, and rejecting suggestions when the changed-line count is not exactly one. Both the verifier and the selftest new coverage look correct. The changed code does not introduce any correctness, security, governance, Windows PowerShell 5.1 compatibility, or validation-gap risk.",
]:
    assert_clean(clean_summary)

for problem_summary in [
    "The only high-signal finding is a governance regression.",
    "No high-confidence inline findings were found, but the only high-signal finding is a governance regression.",
    "No findings and security risks remain.",
    "No issues and security risks remain.",
    "No workflow security risks were identified, but validation should reject unanchored findings.",
    "No regressions found, but security risks remain.",
    "No regressions found and security risks remain.",
    "No findings and this security risk remains.",
    "No findings and the workflow regression remains.",
    "No regressions found. Security risks remain.",
    "No regressions found, security risks remain.",
    "The changed code does not introduce compatibility problems. Security risks remain.",
    "No issues, regressions, or risks were identified, security risks remain.",
    "No issues, security risks remain.",
    "No issues, regressions, security risks remain.",
    "No security issues, workflow regressions, operational risks remain.",
]:
    assert_problem(problem_summary)


multiline_subprocess_diff = """diff --git a/tools/run_probe.py b/tools/run_probe.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/run_probe.py
@@ -0,0 +1,6 @@
+import subprocess
+def run_probe(command):
+    subprocess.run(
+        command,
+        shell=True,
+    )
+"""
multiline_sentinels = mod.detect_risk_sentinels(multiline_subprocess_diff)
assert any(
    item.path == "tools/run_probe.py"
    and item.line == 5
    and item.label == "shell=True subprocess invocation"
    for item in multiline_sentinels
)
assert len({(item.path, item.line, item.label) for item in multiline_sentinels}) == len(multiline_sentinels)

comment_only_diff = """diff --git a/tools/comment_examples.py b/tools/comment_examples.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/comment_examples.py
@@ -0,0 +1,4 @@
+# avoid subprocess.run("echo hi", shell=True) in production
+# Invoke-Expression is intentionally mentioned in this comment-only example
+# Remove-Item -Recurse also appears only as documentation
+
+"""
assert mod.detect_risk_sentinels(comment_only_diff) == []

probe_diff = """diff --git a/validation-review-probes/Invoke-IntentionalFlawedReviewBaseline.ps1 b/validation-review-probes/Invoke-IntentionalFlawedReviewBaseline.ps1
index 0000000..1111111 100644
--- /dev/null
+++ b/validation-review-probes/Invoke-IntentionalFlawedReviewBaseline.ps1
@@ -0,0 +1,61 @@
+function New-OsqueryStatement {
+    param([string]$Filter)
+    return "SELECT pid, name, path FROM processes WHERE name LIKE '%$Filter%';"
+}
+function Invoke-CollectorProbe {
+    param([string]$Path, [string]$CommandText)
+    Invoke-Expression "Get-ChildItem $Path | Where-Object Name -like '$CommandText'"
+}
+function Test-ShouldEscalate {
+    if ($Severity -eq "High" -or "Critical") {
+        return $true
+    }
+}
+function Remove-ProbeWorkspace {
+    Remove-Item $Path -Recurse -Force
+}
+function Write-RequestedFile {
+    param([pscustomobject]$Request)
+    $targetPath = Join-Path -Path (Get-Location).Path -ChildPath $Request.RelativePath
+    Set-Content -Path $targetPath -Value $Request.Content -Encoding utf8
+}
+function Send-CaseContext {
+    $payload = @{ env = Get-ChildItem Env: | ForEach-Object { "$($_.Name)=$($_.Value)" } }
+}
diff --git a/validation-review-probes/intentional_flawed_review_baseline.py b/validation-review-probes/intentional_flawed_review_baseline.py
index 0000000..2222222 100644
--- /dev/null
+++ b/validation-review-probes/intentional_flawed_review_baseline.py
@@ -0,0 +1,52 @@
+def build_process_query(hostname, operator_filter):
+    return f"WHERE hostname = '{hostname}' AND name LIKE '%{operator_filter}%';"
+def write_triage_note(case_id, note, output_dir):
+    subprocess.run(f"git add {destination}", shell=True, check=False)
+def should_escalate(severity, confidence):
+    if severity == "critical" or "high":
+        return True
+def cleanup_collector_workspace(path_from_comment):
+    shutil.rmtree(path_from_comment, ignore_errors=True)
+def export_env_to_report(report_path):
+    Path(report_path).write_text("\\n".join(f"{key}={value}" for key, value in os.environ.items()))
"""
sentinels = mod.detect_risk_sentinels(probe_diff)
assert len(sentinels) >= 10
assert any(item.path.endswith(".py") and item.label == "shell=True subprocess invocation" for item in sentinels)
assert any(item.path.endswith(".py") and item.label == "truthy literal branch condition" for item in sentinels)
assert any(item.path.endswith(".ps1") and item.label == "PowerShell Invoke-Expression" for item in sentinels)
assert any(item.path.endswith(".ps1") and item.label == "PowerShell unsafe file-write path" for item in sentinels)
assert any(item.path.endswith(".ps1") and item.label == "environment dump or exfiltration primitive" for item in sentinels)
assert mod.detect_risk_sentinels(
    """diff --git a/docs/examples.md b/docs/examples.md
index 0000000..1111111 100644
--- /dev/null
+++ b/docs/examples.md
@@ -0,0 +1,2 @@
+Example text mentions subprocess.run("echo hi", shell=True) for reviewer education.
""",
) == []

risk_prompt = mod.build_prompt(
    {"number": 287, "title": "Validation probe", "body": "Disposable validation baseline."},
    [
        {"filename": "validation-review-probes/intentional_flawed_review_baseline.py", "status": "added"},
        {"filename": "validation-review-probes/Invoke-IntentionalFlawedReviewBaseline.ps1", "status": "added"},
    ],
    probe_diff,
    config,
    sentinels,
)
assert "Changed-code risk signals detected before model review" in risk_prompt
assert "command/process execution" in risk_prompt
assert "container/orchestration privilege escalation" in risk_prompt
assert "Project emphasis" in risk_prompt
assert "PowerShell collectors" in risk_prompt
assert "GitHub Actions/YAML" in risk_prompt
assert "shell=True subprocess invocation" in risk_prompt
assert "PowerShell Invoke-Expression" in risk_prompt
assert "PowerShell unsafe file-write path" in risk_prompt
