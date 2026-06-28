#!/usr/bin/env python3
"""Offline checks for Pareto routing and first-pass context wrapper."""

from __future__ import annotations

import base64
import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import urllib.error
from email.message import Message
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "openrouter_pr_review_pareto_context.py"

spec = importlib.util.spec_from_file_location("openrouter_pr_review_pareto_context", SCRIPT)
if spec is None or spec.loader is None:
    raise SystemExit("unable to load openrouter_pr_review_pareto_context.py")
mod = importlib.util.module_from_spec(spec)

sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

os.environ["GITHUB_REPOSITORY"] = "DCOIR-Collector/dcoir-collector"
os.environ["PR_NUMBER"] = "287"
os.environ["OPENROUTER_API_KEY"] = "test-openrouter-key"

config = mod.load_pareto_context_config(str(ROOT / ".github" / "openrouter-pr-review-pareto.yml"))
assert config.model == "openrouter/pareto-code"
assert config.model_stack == ["openrouter/pareto-code", "openrouter/auto"]
assert config.pareto_min_coding_score == 0.80
assert config.auto_cost_quality_tradeoff == 2
assert "google/gemini-*" not in config.auto_allowed_models
assert "google/gemini-3.1-pro-preview*" in config.auto_allowed_models
assert "google/gemini-3.1-pro*" not in config.auto_allowed_models
assert config.first_pass_deep_review is True
assert config.deep_review_max_files == 8
assert config.debug is False
assert config.post_progress_comment is False
assert config.per_file_first_pass_review is True
assert config.per_file_review_concurrency == 4
assert config.fix_synthesis_enabled is True
assert config.required_finding_reserved_budget == 9
assert config.required_finding_min_per_family == 2


fix_synthesis_verifier_marker = "single-line-pr-head-anchor"
fix_file_text = "def restore(raw_state):\n    state = decode_state(raw_state)\n    return state\n"
fix_replacement = "    state = json.loads(raw_state)"
assert mod.verified_suggested_replacement(
    {"suggested_replacement": fix_replacement},
    fix_file_text,
    2,
    config,
) == fix_replacement
assert mod.verified_suggested_replacement(
    {"suggested_replacement": "    state = decode_state(raw_state)"},
    fix_file_text,
    2,
    config,
) == ""
assert mod.verified_suggested_replacement(
    {"suggested_replacement": "    state = json.loads(raw_state)\n    return state"},
    fix_file_text,
    2,
    config,
) == ""
assert mod.verified_suggested_replacement(
    {"suggested_replacement": "```python\nstate = json.loads(raw_state)\n```"},
    fix_file_text,
    2,
    config,
) == ""
assert mod.verified_suggested_replacement(
    {"suggested_replacement": "    state = decode_state(raw_state) ~~~"},
    fix_file_text,
    2,
    config,
) == ""
assert mod.verified_suggested_replacement(
    {"suggested_replacement": "Use json.loads instead"},
    fix_file_text,
    2,
    config,
) == ""
assert mod.verified_suggested_replacement(
    {"suggested_replacement": fix_replacement},
    fix_file_text,
    99,
    config,
) == ""

native_fix_comment = mod.base.build_inline_comment(
    {
        "title": "Unsafe deserialization",
        "severity": "high",
        "confidence": 0.95,
        "body": "The changed line deserializes untrusted state.",
        "validation": "python3 -m py_compile scripts/openrouter_pr_review_pareto_context.py",
        "suggested_replacement": fix_replacement,
    },
    "test-model",
    config,
)
assert "```suggestion\n    state = json.loads(raw_state)\n```" in native_fix_comment

fallback_fix_comment = mod.base.build_inline_comment(
    {
        "title": "Unsafe deserialization",
        "severity": "high",
        "confidence": 0.95,
        "body": "The changed line needs a broader repair than one line.",
        "validation": "python3 -m py_compile scripts/openrouter_pr_review_pareto_context.py",
        "suggested_replacement": "",
        "fix_guidance": {
            "language": "python",
            "remove": "decode_state(raw_state)",
            "replace": "json.loads(raw_state)",
            "add": "Add a JSON schema validation test for the accepted state shape.",
            "notes": "Keep the repair limited to the deserialization path.",
        },
    },
    "test-model",
    config,
)
assert "**On line 0 remove:**" not in fallback_fix_comment
assert "**On line" not in fallback_fix_comment
assert "**Remove:**" in fallback_fix_comment
assert "**Replace with:**" in fallback_fix_comment
assert "**Add:**" in fallback_fix_comment
assert "Keep the repair limited" in fallback_fix_comment
assert "```suggestion" not in fallback_fix_comment
assert "**Notes:**" in fallback_fix_comment
assert "```text\nKeep the repair limited to the deserialization path.\n```" not in fallback_fix_comment

malformed_guidance_comment = mod.base.build_inline_comment(
    {
        "path": "project_sources/collector/tools/dcoir_review_intentional_python_probe.py",
        "title": "Malformed fix guidance",
        "severity": "high",
        "confidence": 0.95,
        "body": "The repair formatter should not render nested fences or malformed validation commands.",
        "validation": "python3 -m py_compile project_sources/collector/tools/dcoir_review_intentional_python_probe.py && python3 -c \"\npython3 -m py_compile project_sources/collector/tools/dcoir_review_intentional_python_probe.py\nbandit -r project_sources/collector/tools/dcoir_review_intentional_python_probe.py",
        "suggested_replacement": "",
        "fix_guidance": {
            "language": "powershell",
            "add": "```powershell\nWrite-Output \"safe\"\n```",
        },
    },
    "test-model",
    config,
)
assert "```powershell\n```powershell" not in malformed_guidance_comment
assert "Write-Output \"safe\"" in malformed_guidance_comment
assert 'python3 -m py_compile project_sources/collector/tools/dcoir_review_intentional_python_probe.py && python3 -c "' not in malformed_guidance_comment
assert "bandit -r project_sources/collector/tools/dcoir_review_intentional_python_probe.py" in malformed_guidance_comment

heading_notes_comment = mod.base.build_inline_comment(
    {
        "title": "Global state write",
        "severity": "high",
        "confidence": 0.95,
        "body": "Fallback notes must not escape into markdown headings.",
        "validation": "pwsh -NoProfile -Command Invoke-ScriptAnalyzer -Path probe.ps1",
        "suggested_replacement": "",
        "fix_guidance": {
            "language": "powershell",
            "remove": "Remove the global write.",
            "notes": "# The function should record state through governed storage, not global scope.",
        },
    },
    "test-model",
    config,
)
assert "**Notes:**" in heading_notes_comment
assert "```text\n# The function should record state through governed storage, not global scope.\n```" not in heading_notes_comment
assert "# The function should record state through governed storage, not global scope." in heading_notes_comment

eval_hardened_fix = mod.harden_python_dynamic_exec_fix_result(
    {
        "suggested_replacement": "return eval(expression, {'__builtins__': {}})",
        "replace": "Replace with `return eval(expression, {'__builtins__': {}}, {})`.",
        "notes": "Restricted globals make this safe.",
    },
    {
        "title": "Arbitrary Python code execution via eval on caller-controlled expression",
        "body": "eval runs caller-controlled Python code.",
        "validation": "python3 -m py_compile probe.py",
    },
    "project_sources/collector/tools/dcoir_review_intentional_python_probe.py",
    "    return eval(expression, {'__builtins__': __builtins__, 'os': os, 'Path': Path})",
)
assert eval_hardened_fix["suggested_replacement"] == ""
assert "eval(" not in eval_hardened_fix["replace"]
assert "exec(" not in eval_hardened_fix["replace"]
assert "ast.literal_eval" in eval_hardened_fix["replace"]
assert "Restricted globals make this safe" not in eval_hardened_fix["notes"]

try:
    mod.optional_float({"pareto_min_coding_score": "high"}, "pareto_min_coding_score")
except ValueError as exc:
    assert "pareto_min_coding_score" in str(exc)
else:
    raise AssertionError("malformed optional float should fail with a clear config error")

schema = json.loads((ROOT / "schemas" / "openrouter-pr-review.schema.json").read_text(encoding="utf-8"))
pareto_payload = mod.build_openrouter_payload("review prompt", schema, config, [], "openrouter/pareto-code")
assert pareto_payload["model"] == "openrouter/pareto-code"
assert pareto_payload["provider"]["require_parameters"] is True
assert pareto_payload["response_format"]["json_schema"]["strict"] is True
assert pareto_payload["plugins"] == [{"id": "pareto-router", "min_coding_score": 0.80}]


class FakeOpenRouterResponse:
    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(
            {
                "model": "served-pareto-model",
                "choices": [{"message": {"content": json.dumps({"summary": "No findings.", "findings": []})}}],
            }
        ).encode("utf-8")


captured_payloads: list[dict] = []
original_urlopen = mod.hardened.urllib.request.urlopen


def fake_urlopen(request, timeout=0):
    captured_payloads.append(json.loads(request.data.decode("utf-8")))
    return FakeOpenRouterResponse()


mod.hardened.urllib.request.urlopen = fake_urlopen
try:
    parsed_response, served_model, service_tier = mod.hardened.openrouter_request_once("review prompt", schema, config, [], "openrouter/pareto-code")
finally:
    mod.hardened.urllib.request.urlopen = original_urlopen
assert parsed_response["findings"] == []
assert served_model == "served-pareto-model"
assert service_tier == ""
assert captured_payloads[0]["plugins"] == [{"id": "pareto-router", "min_coding_score": 0.80}]
assert captured_payloads[0]["response_format"]["json_schema"]["strict"] is True

auto_payload = mod.build_openrouter_payload("review prompt", schema, config, ["venice"], "openrouter/auto")
assert auto_payload["model"] == "openrouter/auto"
assert auto_payload["provider"]["ignore"] == ["venice"]
assert auto_payload["plugins"][0]["id"] == "auto-router"
assert auto_payload["plugins"][0]["cost_quality_tradeoff"] == 2

assert mod.review_mode_for_command("/dcoir-review", "/dcoir-review", config, False) == "first-pass-deep"
assert mod.review_mode_for_command("/dcoir-review", "/dcoir-review", config, True) == "diff"
assert mod.review_mode_for_command("/dcoir-review deep", "/dcoir-review", config, True) == "deep-forced"
assert mod.review_mode_for_command("/dcoir-review exhaustive", "/dcoir-review", config, True) == "deep-forced"
assert mod.review_mode_for_command("/dcoir-review diff", "/dcoir-review", config, False) == "diff"

anchor_diff = """diff --git a/probes/serialization_probe.py b/probes/serialization_probe.py
index 0000000..1111111 100644
--- /dev/null
+++ b/probes/serialization_probe.py
@@ -0,0 +1,5 @@
+import pickle
+def restore(raw_payload):
+    return pickle.loads(raw_payload)
+    return None
+# end
"""
anchor_line_index = mod.hardened.build_added_line_index(anchor_diff)
anchor_sentinels = mod.detect_risk_sentinels(anchor_diff)
anchored_findings, anchor_unanchored = mod.split_findings_with_review_body_fallback(
    {
        "summary": "Found unsafe deserialization.",
        "findings": [
            {
                "title": "Unsafe pickle deserialization",
                "severity": "high",
                "confidence": 0.95,
                "path": "probes/serialization_probe.py",
                "line": 4,
                "body": "The changed code deserializes untrusted bytes with pickle.loads.",
                "validation": "python3 -m py_compile probes/serialization_probe.py",
                "suggested_replacement": "",
            }
        ],
    },
    config,
    anchor_line_index,
    anchor_diff,
    anchor_sentinels,
)
assert anchor_unanchored == []
assert anchored_findings[0]["line"] == 3
assert anchored_findings[0]["_reanchored_from_line"] == 4

yaml_sentinels = mod.detect_risk_sentinels(
    """diff --git a/.github/workflows/probe.yml b/.github/workflows/probe.yml
index 0000000..1111111 100644
--- /dev/null
+++ b/.github/workflows/probe.yml
@@ -0,0 +1,13 @@
+name: probe
+on:
+  pull_request_target:
+permissions:
+  contents: write
+jobs:
+  test:
+    runs-on: ubuntu-latest
+    steps:
+      - uses: actions/checkout@v4
+        with:
+          ref: ${{ github.event.pull_request.head.sha }}
+      - run: curl https://example.test/install.sh | bash
"""
)
assert any(item.label == mod.GITHUB_ACTIONS_BROAD_WRITE_PERMISSION_LABEL and item.line == 5 for item in yaml_sentinels)
assert any(item.label == mod.GITHUB_ACTIONS_UNTRUSTED_CHECKOUT_REF_LABEL and item.line == 12 for item in yaml_sentinels)

unauthorized_config = mod.copy.copy(config)
unauthorized_config.allowed_authors = ["allowed-operator"]
original_load_pareto_context_config = mod.load_pareto_context_config
# Placeholder token only; this test never prints or validates a real secret.
unauthorized_env = {
    "GITHUB_REPOSITORY": "DCOIR-Collector/dcoir-collector",
    "PR_NUMBER": "287",
    "GITHUB_TOKEN": "test-token",
    "TRIGGER_COMMENT_ID": "123",
    "TRIGGER_COMMENT_BODY": "/dcoir-review",
    "TRIGGER_AUTHOR": "not-allowed",
    "OPENROUTER_REVIEW_CONFIG": "test-config.yml",
}
unauthorized_stdout = io.StringIO()
mod.load_pareto_context_config = lambda _path: unauthorized_config
try:
    with mock.patch.dict(getattr(os, "environ"), unauthorized_env, clear=True), contextlib.redirect_stdout(unauthorized_stdout):
        mod.main()
finally:
    mod.load_pareto_context_config = original_load_pareto_context_config
assert "Ignoring unauthorized author not-allowed" in unauthorized_stdout.getvalue()

path_write_sentinels = mod.detect_risk_sentinels(
    """diff --git a/validation-review-probes/intentional_flawed_review_baseline.py b/validation-review-probes/intentional_flawed_review_baseline.py
index 0000000..1111111 100644
--- /dev/null
+++ b/validation-review-probes/intentional_flawed_review_baseline.py
@@ -0,0 +1,6 @@
+from pathlib import Path
+def write_triage_note(case_id, note, output_dir):
+    destination = Path(output_dir) / f"{case_id}.txt"
+    destination.write_text(note, encoding="utf-8")
+    subprocess.run(["git", "add", str(destination)], check=True)
"""
)
assert any(
    item.path == "validation-review-probes/intentional_flawed_review_baseline.py"
    and item.line == 3
    and item.label == mod.FILE_WRITE_PATH_LABEL
    for item in path_write_sentinels
)

context_write_sentinels = mod.detect_risk_sentinels(
    """diff --git a/validation-review-probes/intentional_flawed_review_baseline.py b/validation-review-probes/intentional_flawed_review_baseline.py
index 0000000..1111111 100644
--- a/validation-review-probes/intentional_flawed_review_baseline.py
+++ b/validation-review-probes/intentional_flawed_review_baseline.py
@@ -1,5 +1,5 @@
 from pathlib import Path
 def write_triage_note(case_id, note, output_dir):
-    destination = Path(output_dir) / "summary.txt"
+    destination = Path(output_dir) / f"{case_id}.txt"
     destination.write_text(note, encoding="utf-8")
"""
)
assert any(
    item.path == "validation-review-probes/intentional_flawed_review_baseline.py"
    and item.line == 3
    and item.label == mod.FILE_WRITE_PATH_LABEL
    for item in context_write_sentinels
)

added_write_context_assignment_sentinels = mod.detect_risk_sentinels(
    """diff --git a/validation-review-probes/intentional_flawed_review_baseline.py b/validation-review-probes/intentional_flawed_review_baseline.py
index 0000000..1111111 100644
--- a/validation-review-probes/intentional_flawed_review_baseline.py
+++ b/validation-review-probes/intentional_flawed_review_baseline.py
@@ -1,4 +1,5 @@
 from pathlib import Path
 def write_triage_note(case_id, note, output_dir):
     destination = Path(output_dir) / f"{case_id}.txt"
+    destination.write_text(note, encoding="utf-8")
"""
)
assert any(
    item.path == "validation-review-probes/intentional_flawed_review_baseline.py"
    and item.line == 4
    and item.text.strip().startswith("destination.write_text")
    and item.label == mod.FILE_WRITE_PATH_LABEL
    for item in added_write_context_assignment_sentinels
)
