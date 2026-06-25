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

diverse_risk_diff = """diff --git a/probes/kubernetes.yml b/probes/kubernetes.yml
index 0000000..1111111 100644
--- /dev/null
+++ b/probes/kubernetes.yml
@@ -0,0 +1,14 @@
+apiVersion: v1
+kind: Pod
+spec:
+  hostNetwork: true
+  containers:
+    - securityContext:
+        privileged: true
+        allowPrivilegeEscalation: true
+        runAsUser: 0
+  volumes:
+    - name: host-root
+      hostPath:
+        path: /
diff --git a/probes/operator.ps1 b/probes/operator.ps1
index 0000000..2222222 100644
--- /dev/null
+++ b/probes/operator.ps1
@@ -0,0 +1,8 @@
+Expand-Archive -Path $Request.Archive -DestinationPath $Request.ExtractTo -Force
+Start-Process -FilePath $Request.Tool -ArgumentList $Request.Arguments -Wait
+Invoke-WebRequest -Uri $Request.CallbackUrl -Headers @{ Authorization = "Bearer $($Request.Token)" } -OutFile (Join-Path $env:TEMP $Request.OutputName)
+$acl = Get-Acl -LiteralPath $Request.TargetPath
+$rule = New-Object System.Security.AccessControl.FileSystemAccessRule("Everyone", "FullControl", "Allow")
+$acl.SetAccessRule($rule)
+Set-Acl -LiteralPath $Request.TargetPath -AclObject $acl
diff --git a/probes/pipeline.ts b/probes/pipeline.ts
index 0000000..3333333 100644
--- /dev/null
+++ b/probes/pipeline.ts
@@ -0,0 +1,12 @@
+const destination = path.join(workspace, request.destination);
+writeFileSync(destination, request.body, "utf8");
+exec(`powershell -NoProfile ${request.command}`);
+const mapper = new Function("record", request.expression);
+const query = `select * from alerts where owner = '${request.userId}' and ${request.sqlFilter}`;
+await fetch(request.url, { headers: { Authorization: process.env.PROVIDER_TOKEN } });
diff --git a/probes/workflow.yml b/probes/workflow.yml
index 0000000..4444444 100644
--- /dev/null
+++ b/probes/workflow.yml
@@ -0,0 +1,10 @@
+on:
+  pull_request_target:
+jobs:
+  unsafe:
+    steps:
+      - uses: actions/checkout@v7
+        with:
+          ref: ${{ github.event.pull_request.head.ref }}
+      - run: bash -c "${{ github.event.pull_request.title }}"
+      - run: curl -H "Authorization: Bearer ${{ secrets.GITHUB_TOKEN }}" "${{ github.event.pull_request.body }}"
"""
diverse_sentinels = mod.detect_risk_sentinels(diverse_risk_diff, 12)
diverse_labels = {item.label for item in diverse_sentinels}
assert "TypeScript/JavaScript unsafe path construction" in diverse_labels
assert "TypeScript/JavaScript unsafe file write" in diverse_labels
assert "Node.js command execution" in diverse_labels
assert "PowerShell process launch" in diverse_labels
assert "PowerShell unsafe archive extraction" in diverse_labels
assert "PowerShell outbound request or download" in diverse_labels
assert "CI token exfiltration primitive" in diverse_labels
assert "GitHub Actions privileged PR context" in diverse_labels
assert "Kubernetes privileged container setting" in diverse_labels
assert "Kubernetes host filesystem exposure" in diverse_labels
assert len({item.path for item in diverse_sentinels}) >= 4

calls: list[str] = []
original_openrouter_review = mod.openrouter_review


def fake_openrouter_review(prompt: str, _schema: dict, _config: object, _reporter: object | None = None):
    calls.append(prompt)
    if len(calls) == 1:
        return {"summary": "No high-confidence inline findings were found.", "findings": []}, "weak-model", ""
    return {
        "summary": "Found unsafe shell execution.",
        "findings": [
            {
                "title": "Avoid shell execution",
                "severity": "high",
                "confidence": 0.95,
                "path": "validation-review-probes/intentional_flawed_review_baseline.py",
                "line": 4,
                "body": "shell=True executes constructed text.",
                "suggested_replacement": "",
                "validation": "python3 scripts/openrouter_pr_review_hardened_selftest.py",
            }
        ],
    }, "strong-model", ""


mod.openrouter_review = fake_openrouter_review
try:
    retry_result, retry_model, _retry_tier = mod.openrouter_review_with_quality_retry(
        "initial prompt",
        schema,
        config,
        None,
        sentinels,
    )
finally:
    mod.openrouter_review = original_openrouter_review
assert len(calls) == 2
assert retry_model == "strong-model"
assert retry_result["findings"]
assert "Review quality retry" in calls[1]
assert "validation-review-probes/intentional_flawed_review_baseline.py" in calls[1]

tiny_retry_config = copy.copy(config)
tiny_retry_config.max_prompt_chars = 240
tiny_retry_prompt = mod.build_quality_retry_prompt("x" * 1000, {"summary": "No findings."}, sentinels, tiny_retry_config)
assert len(tiny_retry_prompt) <= tiny_retry_config.max_prompt_chars

try:
    mod.enforce_risk_sentinel_findings([], sentinels, config)
except mod.ReviewQualityError as exc:
    assert "high-risk changed-line signals" in str(exc)
else:
    raise AssertionError("empty findings after risk-sentinel retry should fail review quality")

try:
    mod.enforce_risk_sentinel_findings(
        [
            {
                "title": "Unrelated accepted finding",
                "severity": "high",
                "confidence": 0.95,
                "path": sentinels[0].path,
                "line": sentinels[0].line,
                "body": "This finding is actionable but does not mention the sentinel risk class.",
                "suggested_replacement": "",
                "validation": "python3 scripts/openrouter_pr_review_hardened_selftest.py",
            }
        ],
        sentinels,
        config,
    )
except mod.ReviewQualityError as exc:
    assert "did not produce actionable findings covering those signals" in str(exc)
else:
    raise AssertionError("unrelated findings must not satisfy risk-sentinel coverage")

fallback_findings = mod.add_risk_sentinel_fallback_findings([], sentinels, config)
assert fallback_findings
assert all(finding["title"].startswith("Deterministic risk sentinel:") for finding in fallback_findings)
mod.enforce_risk_sentinel_findings(fallback_findings, sentinels, config)
mod.enforce_risk_sentinel_findings([], [], config)

full_budget_config = copy.copy(config)
full_budget_config.max_inline_comments = 2
covered_sentinel, uncovered_sentinel = sentinels[0], sentinels[1]
full_budget_findings = [
    {
        "title": f"Covered deterministic risk: {covered_sentinel.label}",
        "severity": "critical",
        "confidence": 0.99,
        "path": covered_sentinel.path,
        "line": covered_sentinel.line,
        "body": f"{covered_sentinel.detail}. {covered_sentinel.label}.",
        "suggested_replacement": "",
        "validation": "python3 scripts/openrouter_pr_review_hardened_selftest.py",
    },
    {
        "title": "Lower-priority model finding",
        "severity": "low",
        "confidence": 0.70,
        "path": covered_sentinel.path,
        "line": covered_sentinel.line,
        "body": "Useful but lower-priority context that does not cover the uncovered sentinel.",
        "suggested_replacement": "",
        "validation": "python3 scripts/openrouter_pr_review_hardened_selftest.py",
    },
]
augmented_full_budget = mod.add_risk_sentinel_fallback_findings(
    full_budget_findings,
    [covered_sentinel, uncovered_sentinel],
    full_budget_config,
)
assert len(augmented_full_budget) == 2
assert any(finding["title"] == f"Covered deterministic risk: {covered_sentinel.label}" for finding in augmented_full_budget)
assert any(
    finding["title"] == f"Deterministic risk sentinel: {uncovered_sentinel.label}" for finding in augmented_full_budget
)
assert not any(finding["title"] == "Lower-priority model finding" for finding in augmented_full_budget)
mod.enforce_risk_sentinel_findings(
    augmented_full_budget,
    [covered_sentinel, uncovered_sentinel],
    full_budget_config,
)

print("hardened DCOIR Review selftest passed")
