#!/usr/bin/env python3
"""Offline checks for Pareto routing and first-pass context wrapper."""

from __future__ import annotations

import base64
import contextlib
import importlib.util
import io
import json
import os
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
import sys

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
    with mock.patch.dict(os.environ, unauthorized_env, clear=True), contextlib.redirect_stdout(unauthorized_stdout):
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

multi_arg_path_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/path_writer.py
@@ -0,0 +1,5 @@
+from pathlib import Path
+def write_triage_note(case_id, note, output_dir):
+    destination = Path(output_dir, f"{case_id}.txt")
+    destination.write_text(note, encoding="utf-8")
"""
)
assert any(
    item.path == "tools/path_writer.py"
    and item.line == 3
    and item.label == mod.FILE_WRITE_PATH_LABEL
    for item in multi_arg_path_sentinels
)

variable_segment_path_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/path_writer.py
@@ -0,0 +1,6 @@
+from pathlib import Path
+def write_triage_note(filename, note, output_dir):
+    destination = Path(output_dir) / filename
+    destination.write_text(note, encoding="utf-8")
"""
)
assert any(
    item.path == "tools/path_writer.py"
    and item.line == 3
    and item.label == mod.FILE_WRITE_PATH_LABEL
    for item in variable_segment_path_sentinels
)

join_variable_segment_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/path_writer.py
@@ -0,0 +1,6 @@
+import os
+def write_triage_note(filename, note, output_dir):
+    destination = os.path.join(output_dir, filename)
+    destination.write_text(note, encoding="utf-8")
"""
)
assert any(
    item.path == "tools/path_writer.py"
    and item.line == 3
    and item.label == mod.FILE_WRITE_PATH_LABEL
    for item in join_variable_segment_sentinels
)

path_wrapped_join_write_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/path_writer.py
@@ -0,0 +1,7 @@
+import os
+from pathlib import Path
+def write_triage_note(filename, note, output_dir):
+    destination = os.path.join(output_dir, filename)
+    Path(destination).write_text(note, encoding="utf-8")
"""
)
assert any(
    item.path == "tools/path_writer.py"
    and item.line == 4
    and item.label == mod.FILE_WRITE_PATH_LABEL
    for item in path_wrapped_join_write_sentinels
)

qualified_path_wrapped_join_write_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/path_writer.py
@@ -0,0 +1,7 @@
+import os
+import pathlib
+def write_triage_note(filename, note, output_dir):
+    destination = os.path.join(output_dir, filename)
+    pathlib.Path(destination).write_bytes(note)
"""
)
assert any(
    item.path == "tools/path_writer.py"
    and item.line == 4
    and item.label == mod.FILE_WRITE_PATH_LABEL
    for item in qualified_path_wrapped_join_write_sentinels
)

multiline_path_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/path_writer.py
@@ -0,0 +1,8 @@
+from pathlib import Path
+def write_triage_note(filename, note, output_dir):
+    destination = Path(
+        output_dir,
+        filename,
+    )
+    destination.write_text(note, encoding="utf-8")
"""
)
assert mod.python_dynamic_path_target("destination = Path(\n    output_dir,\n    filename,\n)") == "destination"
assert any(
    item.path == "tools/path_writer.py"
    and item.line == 3
    and item.label == mod.FILE_WRITE_PATH_LABEL
    for item in multiline_path_sentinels
)

qualified_multiline_path_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/path_writer.py
@@ -0,0 +1,7 @@
+import pathlib
+def write_triage_note(filename, note, output_dir):
+    destination = pathlib.Path(
+        output_dir,
+        filename,
+    )
+    destination.write_text(note, encoding="utf-8")
"""
)
assert mod.python_dynamic_path_target("destination = pathlib.Path(\n    output_dir,\n    filename,\n)") == "destination"
assert any(
    item.path == "tools/path_writer.py"
    and item.line == 3
    and item.label == mod.FILE_WRITE_PATH_LABEL
    for item in qualified_multiline_path_sentinels
)
aliased_path_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/path_writer.py
@@ -0,0 +1,6 @@
+from pathlib import Path as P
+def write_triage_note(filename, note, output_dir):
+    destination = P(output_dir, filename)
+    destination.write_text(note, encoding="utf-8")
"""
)
assert any(
    item.path == "tools/path_writer.py"
    and item.line == 3
    and item.label == mod.FILE_WRITE_PATH_LABEL
    for item in aliased_path_sentinels
)
aliased_wrapped_path_write_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/path_writer.py
@@ -0,0 +1,7 @@
+import pathlib as pl
+def write_triage_note(filename, note, output_dir):
+    destination = pl.Path(output_dir, filename)
+    pl.Path(destination).write_text(note, encoding="utf-8")
"""
)
assert any(
    item.path == "tools/path_writer.py"
    and item.line == 3
    and item.label == mod.FILE_WRITE_PATH_LABEL
    for item in aliased_wrapped_path_write_sentinels
)
mod.set_python_path_alias_context({"tools/path_writer.py": {"P", "pl.Path"}})
try:
    existing_alias_path_sentinels = mod.detect_risk_sentinels(
        """diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- a/tools/path_writer.py
+++ b/tools/path_writer.py
@@ -20,3 +20,4 @@
 def write_triage_note(filename, note, output_dir):
+    destination = P(output_dir, filename)
     destination.write_text(note, encoding="utf-8")
"""
    )
    existing_module_alias_wrapped_sentinels = mod.detect_risk_sentinels(
        """diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- a/tools/path_writer.py
+++ b/tools/path_writer.py
@@ -30,3 +30,4 @@
 def write_triage_note(filename, note, output_dir):
+    destination = pl.Path(output_dir, filename)
     pl.Path(destination).write_text(note, encoding="utf-8")
"""
    )
finally:
    mod.set_python_path_alias_context({})
assert any(
    item.path == "tools/path_writer.py"
    and item.line == 21
    and item.label == mod.FILE_WRITE_PATH_LABEL
    for item in existing_alias_path_sentinels
)
assert any(
    item.path == "tools/path_writer.py"
    and item.line == 31
    and item.label == mod.FILE_WRITE_PATH_LABEL
    for item in existing_module_alias_wrapped_sentinels
)
cross_file_alias_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/path_builder.py b/tools/path_builder.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/path_builder.py
@@ -0,0 +1,2 @@
+from pathlib import Path as P
+SAFE = P("summary.txt")
diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/path_writer.py
@@ -0,0 +1,4 @@
+def write_triage_note(filename, note, output_dir):
+    destination = P(output_dir, filename)
+    destination.write_text(note, encoding="utf-8")
"""
)
assert not any(item.label == mod.FILE_WRITE_PATH_LABEL for item in cross_file_alias_sentinels)

literal_root_path_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/path_writer.py
@@ -0,0 +1,7 @@
+import os
+from pathlib import Path
+def write_triage_note(filename, note):
+    destination = Path("/safe", filename)
+    backup = os.path.join("/safe", filename)
+    destination.write_text(note, encoding="utf-8")
+    backup.write_text(note, encoding="utf-8")
"""
)
assert any(
    item.path == "tools/path_writer.py"
    and item.line == 4
    and item.label == mod.FILE_WRITE_PATH_LABEL
    for item in literal_root_path_sentinels
)
assert any(
    item.path == "tools/path_writer.py"
    and item.line == 5
    and item.label == mod.FILE_WRITE_PATH_LABEL
    for item in literal_root_path_sentinels
)

multi_variable_fstring_path_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/path_writer.py
@@ -0,0 +1,5 @@
+from pathlib import Path
+def write_triage_note(base, filename, note):
+    destination = Path(f"{base}/{filename}")
+    destination.write_text(note, encoding="utf-8")
"""
)
assert any(
    item.path == "tools/path_writer.py"
    and item.line == 3
    and item.label == mod.FILE_WRITE_PATH_LABEL
    for item in multi_variable_fstring_path_sentinels
)

single_dynamic_path_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/path_writer.py
@@ -0,0 +1,6 @@
+from pathlib import Path
+def write_triage_note(filename, note):
+    destination = Path(filename)
+    destination.write_text(note, encoding="utf-8")
"""
)
assert any(
    item.path == "tools/path_writer.py"
    and item.line == 3
    and item.label == mod.FILE_WRITE_PATH_LABEL
    for item in single_dynamic_path_sentinels
)

chained_literal_then_variable_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/path_writer.py
@@ -0,0 +1,6 @@
+from pathlib import Path
+def write_triage_note(filename, note, output_dir):
+    destination = Path(output_dir) / "cases" / filename
+    destination.write_text(note, encoding="utf-8")
"""
)
assert any(
    item.path == "tools/path_writer.py"
    and item.line == 3
    and item.label == mod.FILE_WRITE_PATH_LABEL
    for item in chained_literal_then_variable_sentinels
)

chained_variable_then_literal_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/path_writer.py
@@ -0,0 +1,6 @@
+from pathlib import Path
+def write_triage_note(filename, note, output_dir):
+    destination = Path(output_dir) / filename / "note.txt"
+    destination.write_text(note, encoding="utf-8")
"""
)
assert any(
    item.path == "tools/path_writer.py"
    and item.line == 3
    and item.label == mod.FILE_WRITE_PATH_LABEL
    for item in chained_variable_then_literal_sentinels
)

fixture_string_sentinels = mod.detect_risk_sentinels(
    '''diff --git a/scripts/openrouter_pr_review_pareto_context_selftest.py b/scripts/openrouter_pr_review_pareto_context_selftest.py
index 0000000..1111111 100644
--- /dev/null
+++ b/scripts/openrouter_pr_review_pareto_context_selftest.py
@@ -0,0 +1,6 @@
+# Intentionally unsafe sentinel fixture string; never executed by this selftest.
+fixture = """diff --git a/probe.py b/probe.py
++    subprocess.run(f"git add {destination}", shell=True, check=False)
+"""
'''
)
assert not any(item.label == "shell=True subprocess invocation" for item in fixture_string_sentinels)

split_fixture_marker_sentinels = mod.detect_risk_sentinels(
    '''diff --git a/scripts/openrouter_pr_review_pareto_context_selftest.py b/scripts/openrouter_pr_review_pareto_context_selftest.py
index 0000000..1111111 100644
--- /dev/null
+++ b/scripts/openrouter_pr_review_pareto_context_selftest.py
@@ -0,0 +1,7 @@
+# Intentionally unsafe sentinel fixture string; never executed by this selftest.
+fixture = """
+diff --git a/probe.py b/probe.py
++    subprocess.run(f"git add {destination}", shell=True, check=False)
+"""
'''
)
assert not any(item.label == "shell=True subprocess invocation" for item in split_fixture_marker_sentinels)

real_multiline_sql_sentinels = mod.detect_risk_sentinels(
    '''diff --git a/tools/query_builder.py b/tools/query_builder.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/query_builder.py
@@ -0,0 +1,5 @@
+def load_case(case_id):
+    query = f"""
+SELECT * FROM cases WHERE id = {case_id}  -- intentionally unsafe for sentinel testing only
+"""
'''
)
assert any(
    item.path == "tools/query_builder.py"
    and item.line == 3
    and item.label == "raw SQL/query string interpolation"
    for item in real_multiline_sql_sentinels
)

comment_like_string_close_sentinels = mod.detect_risk_sentinels(
    '''diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/path_writer.py
@@ -0,0 +1,6 @@
+def write_triage_note(case_id, note, output_dir):
+    doc = """open text
+    # """
+    destination = Path(output_dir) / f"{case_id}.txt"
+    destination.write_text(note, encoding="utf-8")
'''
)
assert any(
    item.path == "tools/path_writer.py"
    and item.line == 4
    and item.label == mod.FILE_WRITE_PATH_LABEL
    for item in comment_like_string_close_sentinels
)

assert mod.detect_risk_sentinels(
    """diff --git a/tools/comment_examples.py b/tools/comment_examples.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/comment_examples.py
@@ -0,0 +1,3 @@
+# destination = Path(output_dir) / f"{case_id}.txt"
+# destination.write_text(note, encoding="utf-8")
"""
) == []
literal_path_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/safe_writer.py b/tools/safe_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/safe_writer.py
@@ -0,0 +1,5 @@
+from pathlib import Path
+def write_summary(output_dir, note):
+    destination = Path(output_dir) / "summary.txt"
+    destination.write_text(note, encoding="utf-8")
"""
)
assert not any(item.label == mod.FILE_WRITE_PATH_LABEL for item in literal_path_sentinels)
literal_single_path_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/safe_writer.py b/tools/safe_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/safe_writer.py
@@ -0,0 +1,5 @@
+from pathlib import Path
+def write_summary(note):
+    destination = Path("summary.txt")
+    destination.write_text(note, encoding="utf-8")
"""
)
assert not any(item.label == mod.FILE_WRITE_PATH_LABEL for item in literal_single_path_sentinels)
safe_reassign_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/safe_writer.py b/tools/safe_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/safe_writer.py
@@ -0,0 +1,6 @@
+from pathlib import Path
+def write_summary(output_dir, note, case_id):
+    destination = Path(output_dir) / f"{case_id}.txt"
+    destination = Path(output_dir) / "summary.txt"
+    destination.write_text(note, encoding="utf-8")
"""
)
assert not any(item.label == mod.FILE_WRITE_PATH_LABEL for item in safe_reassign_sentinels)
self_derived_reassign_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/path_writer.py
@@ -0,0 +1,7 @@
+from pathlib import Path
+def write_triage_note(filename, note, output_dir):
+    destination = Path(output_dir) / filename
+    destination = destination.resolve()
+    destination.write_text(note, encoding="utf-8")
"""
)
assert any(
    item.path == "tools/path_writer.py"
    and item.line == 3
    and item.label == mod.FILE_WRITE_PATH_LABEL
    for item in self_derived_reassign_sentinels
)
self_derived_context_reassign_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- a/tools/path_writer.py
+++ b/tools/path_writer.py
@@ -1,6 +1,7 @@
 from pathlib import Path
 def write_triage_note(filename, note, output_dir):
     destination = Path(output_dir) / filename
+    destination = destination.resolve()
     destination.write_text(note, encoding="utf-8")
"""
)
assert any(
    item.path == "tools/path_writer.py"
    and item.line == 4
    and item.text.strip() == "destination = destination.resolve()"
    and item.label == mod.FILE_WRITE_PATH_LABEL
    for item in self_derived_context_reassign_sentinels
)
value_less_annotation_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/path_writer.py
@@ -0,0 +1,7 @@
+from pathlib import Path
+def write_triage_note(filename, note, output_dir):
+    destination = Path(output_dir) / filename
+    destination: Path
+    destination.write_text(note, encoding="utf-8")
"""
)
assert mod.python_simple_assignment("destination: Path") is None
assert "destination" not in mod.python_assignment_target_names("destination: Path")
assert any(
    item.path == "tools/path_writer.py"
    and item.line == 3
    and item.label == mod.FILE_WRITE_PATH_LABEL
    for item in value_less_annotation_sentinels
)

augmented_dynamic_path_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/path_writer.py
@@ -0,0 +1,7 @@
+from pathlib import Path
+def write_triage_note(filename, note):
+    destination = Path("/safe")
+    destination /= filename
+    destination.write_text(note, encoding="utf-8")
"""
)
assert any(
    item.path == "tools/path_writer.py"
    and item.line == 4
    and item.text.strip() == "destination /= filename"
    and item.label == mod.FILE_WRITE_PATH_LABEL
    for item in augmented_dynamic_path_sentinels
)

augmented_context_dynamic_path_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- a/tools/path_writer.py
+++ b/tools/path_writer.py
@@ -1,5 +1,6 @@
 from pathlib import Path
 def write_triage_note(filename, note):
     destination = Path("/safe")
+    destination /= filename
     destination.write_text(note, encoding="utf-8")
"""
)
assert any(
    item.path == "tools/path_writer.py"
    and item.line == 4
    and item.text.strip() == "destination /= filename"
    and item.label == mod.FILE_WRITE_PATH_LABEL
    for item in augmented_context_dynamic_path_sentinels
)

augmented_literal_preserves_dynamic_path_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/path_writer.py
@@ -0,0 +1,7 @@
+from pathlib import Path
+def write_triage_note(filename, note, output_dir):
+    destination = Path(output_dir) / filename
+    destination /= "summary.txt"
+    destination.write_text(note, encoding="utf-8")
"""
)
assert any(
    item.path == "tools/path_writer.py"
    and item.line == 3
    and item.text.strip() == "destination = Path(output_dir) / filename"
    and item.label == mod.FILE_WRITE_PATH_LABEL
    for item in augmented_literal_preserves_dynamic_path_sentinels
)

augmented_literal_context_base_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- a/tools/path_writer.py
+++ b/tools/path_writer.py
@@ -1,5 +1,6 @@
 from pathlib import Path
 def write_triage_note(filename, note, output_dir):
     destination = Path(output_dir) / filename
+    destination /= "summary.txt"
     destination.write_text(note, encoding="utf-8")
"""
)
assert any(
    item.path == "tools/path_writer.py"
    and item.line == 4
    and item.text.strip() == 'destination /= "summary.txt"'
    and item.label == mod.FILE_WRITE_PATH_LABEL
    for item in augmented_literal_context_base_sentinels
)

paren_next_line_path_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/path_writer.py
@@ -0,0 +1,8 @@
+from pathlib import Path
+def write_triage_note(filename, note, output_dir):
+    destination = (
+        Path(output_dir) / filename
+    )
+    destination.write_text(note, encoding="utf-8")
"""
)
assert any(
    item.path == "tools/path_writer.py"
    and item.line == 3
    and item.text.strip() == "destination = ("
    and item.label == mod.FILE_WRITE_PATH_LABEL
    for item in paren_next_line_path_sentinels
)

backslash_next_line_path_diff = (
    "diff --git a/tools/path_writer.py b/tools/path_writer.py\n"
    "index 0000000..1111111 100644\n"
    "--- /dev/null\n"
    "+++ b/tools/path_writer.py\n"
    "@@ -0,0 +1,6 @@\n"
    "+from pathlib import Path\n"
    "+def write_triage_note(filename, note, output_dir):\n"
    "+    destination = \\\n"
    "+        Path(output_dir) / filename\n"
    "+    destination.write_text(note, encoding=\"utf-8\")\n"
)
backslash_next_line_path_sentinels = mod.detect_risk_sentinels(backslash_next_line_path_diff)
assert any(
    item.path == "tools/path_writer.py"
    and item.line == 3
    and item.text.strip() == "destination = \\"
    and item.label == mod.FILE_WRITE_PATH_LABEL
    for item in backslash_next_line_path_sentinels
)

paren_next_line_join_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/path_writer.py
@@ -0,0 +1,8 @@
+import os
+def write_triage_note(filename, note, output_dir):
+    destination = (
+        os.path.join(output_dir, filename)
+    )
+    destination.write_bytes(note)
"""
)
assert any(
    item.path == "tools/path_writer.py"
    and item.line == 3
    and item.text.strip() == "destination = ("
    and item.label == mod.FILE_WRITE_PATH_LABEL
    for item in paren_next_line_join_sentinels
)

cross_hunk_assignment_write_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/path_writer.py
@@ -0,0 +1,5 @@
+from pathlib import Path
+def write_triage_note(filename, note, output_dir):
+    destination = Path(output_dir) / filename
+    note = note.strip()
@@ -20,2 +20,3 @@ def write_triage_note(filename, note, output_dir):
+    destination.write_text(note, encoding="utf-8")
+    destination.write_bytes(note)
"""
)
assert any(
    item.path == "tools/path_writer.py"
    and item.line == 3
    and item.label == mod.FILE_WRITE_PATH_LABEL
    for item in cross_hunk_assignment_write_sentinels
)

disconnected_cross_hunk_multiline_assignment_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/path_writer.py
@@ -0,0 +1,3 @@
+from pathlib import Path
+def write_triage_note(filename, note, output_dir):
+    destination = (
@@ -20,2 +20,3 @@ def write_triage_note(filename, note, output_dir):
+        Path(output_dir) / filename
+    )
+    destination.write_text(note, encoding="utf-8")
"""
)
assert not any(
    item.label == mod.FILE_WRITE_PATH_LABEL
    for item in disconnected_cross_hunk_multiline_assignment_sentinels
)

cross_file_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/path_builder.py b/tools/path_builder.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/path_builder.py
@@ -0,0 +1,3 @@
+from pathlib import Path
+def build_path(output_dir, case_id):
+    destination = Path(output_dir) / f"{case_id}.txt"
diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/path_writer.py
@@ -0,0 +1,3 @@
+def write_path(destination, note):
+    destination.write_text(note, encoding="utf-8")
"""
)
assert not any(item.label == mod.FILE_WRITE_PATH_LABEL for item in cross_file_sentinels)
attribute_sibling_assignment_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/path_writer.py
@@ -0,0 +1,6 @@
+from pathlib import Path
+class Writer:
+    def write_triage_note(self, filename, note, output_dir):
+        self.destination = Path(output_dir) / filename
+        self.mode = "x"
+        self.destination.write_text(note, encoding="utf-8")
"""
)
assert any(
    item.path == "tools/path_writer.py"
    and item.line == 4
    and item.label == mod.FILE_WRITE_PATH_LABEL
    for item in attribute_sibling_assignment_sentinels
)
wrapped_literal_path_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/safe_writer.py b/tools/safe_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/safe_writer.py
@@ -0,0 +1,5 @@
+from pathlib import Path
+def write_summary(output_dir, note):
+    destination = Path(output_dir / "summary.txt")
+    destination.write_text(note, encoding="utf-8")
"""
)
assert not any(item.label == mod.FILE_WRITE_PATH_LABEL for item in wrapped_literal_path_sentinels)
long_path_assignment = "destination = " + ("a" * (mod.PYTHON_PATH_ASSIGNMENT_MAX_CHARS + 1)) + "Path(filename)"
assert mod.python_dynamic_path_target(long_path_assignment) is None

scope_reset_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/path_writer.py
@@ -0,0 +1,8 @@
+from pathlib import Path
+def build_path(filename, output_dir):
+    destination = Path(output_dir) / filename
+
+def write_supplied_path(destination, note):
+    destination.write_text(note, encoding="utf-8")
"""
)
assert not any(item.label == mod.FILE_WRITE_PATH_LABEL for item in scope_reset_sentinels)

outer_path_survives_nested_same_name_assignment_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/path_writer.py
@@ -0,0 +1,9 @@
+from pathlib import Path
+def write_triage_note(filename, note, output_dir):
+    destination = Path(output_dir) / filename
+    def helper(other_output_dir):
+        destination = Path(other_output_dir) / "helper.txt"
+        return destination
+    helper(output_dir)
+    destination.write_text(note, encoding="utf-8")
"""
)
assert any(
    item.path == "tools/path_writer.py"
    and item.line == 3
    and item.label == mod.FILE_WRITE_PATH_LABEL
    for item in outer_path_survives_nested_same_name_assignment_sentinels
)

comparison_path_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/path_writer.py
@@ -0,0 +1,5 @@
+from pathlib import Path
+def write_supplied_path(destination, filename, note):
+    if destination == Path(f"{filename}"):
+        destination.write_text(note, encoding="utf-8")
"""
)
assert mod.python_dynamic_path_target("if destination == Path(f'{filename}'):") is None
assert not any(item.label == mod.FILE_WRITE_PATH_LABEL for item in comparison_path_sentinels)

attribute_exact_reassign_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/path_writer.py
@@ -0,0 +1,7 @@
+from pathlib import Path
+class Writer:
+    def write_triage_note(self, filename, note, output_dir):
+        self.destination = Path(output_dir) / filename
+        self.destination = Path(output_dir) / "summary.txt"
+        self.destination.write_text(note, encoding="utf-8")
"""
)
assert not any(item.label == mod.FILE_WRITE_PATH_LABEL for item in attribute_exact_reassign_sentinels)

attribute_root_rebind_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/path_writer.py
@@ -0,0 +1,8 @@
+from pathlib import Path
+class Writer:
+    def write_triage_note(self, filename, note, output_dir, replacement):
+        self.destination = Path(output_dir) / filename
+        self = replacement
+        self.destination.write_text(note, encoding="utf-8")
"""
)
assert not any(item.label == mod.FILE_WRITE_PATH_LABEL for item in attribute_root_rebind_sentinels)

attribute_subscript_mutation_sentinels = mod.detect_risk_sentinels(
    """diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/path_writer.py
@@ -0,0 +1,8 @@
+from pathlib import Path
+class Writer:
+    def write_triage_note(self, filename, note, output_dir):
+        self.destination = Path(output_dir) / filename
+        self.destination[0] = "safe"
+        self.destination.write_text(note, encoding="utf-8")
"""
)
assert not any(item.label == mod.FILE_WRITE_PATH_LABEL for item in attribute_subscript_mutation_sentinels)

captured_max_anchors = []
original_detect_risk_sentinels = mod._original_detect_risk_sentinels


def fake_original_detect_risk_sentinels(_diff, max_anchors=None):
    captured_max_anchors.append(max_anchors)
    return [
        mod.hardened.RiskSentinel(
            path=f"tools/original_{index}.py",
            line=index,
            label=f"original sentinel {index}",
            detail="original sentinel detail",
            text="original sentinel text",
        )
        for index in range(1, 4)
    ]


mod._original_detect_risk_sentinels = fake_original_detect_risk_sentinels
try:
    bounded_path_sentinels = mod.detect_risk_sentinels(
        """diff --git a/tools/path_writer.py b/tools/path_writer.py
index 0000000..1111111 100644
--- /dev/null
+++ b/tools/path_writer.py
@@ -0,0 +1,5 @@
+from pathlib import Path
+def write_triage_note(filename, note, output_dir):
+    destination = Path(output_dir) / filename
+    destination.write_text(note, encoding="utf-8")
""",
        max_anchors=3,
    )
finally:
    mod._original_detect_risk_sentinels = original_detect_risk_sentinels
assert captured_max_anchors == [3]
assert len(bounded_path_sentinels) == 3
assert bounded_path_sentinels[0].label == mod.FILE_WRITE_PATH_LABEL


class FakeGitHubClient:
    repo = "DCOIR-Collector/dcoir-collector"

    def __init__(self, reviews: list[dict[str, str]] | None = None) -> None:
        self.reviews = reviews or []
        self.files = {
            "tools/review_probe.py": "def run_probe(command):\n    return subprocess.run(command, shell=True)\n",
            "docs/review.md": "# Review\n\nKeep governed review evidence visible.\n",
            "tools/later_probe.py": "import subprocess\n\nsubprocess.run('whoami', shell=True)\n",
            "tools/huge_probe.py": "print('large context line')\n" * 1000,
            "tools/aliased_writer.py": "from pathlib import Path as P\nimport pathlib as pl\n\ndef write_triage_note(filename, note, output_dir):\n    destination = P(output_dir, filename)\n    pl.Path(destination).write_text(note)\n",
        }

    def request(self, _method: str, path: str):
        if path.startswith("/repos/DCOIR-Collector/dcoir-collector/pulls/287/reviews"):
            params = mod.urllib.parse.parse_qs(mod.urllib.parse.urlparse(path).query)
            page = int(params.get("page", ["1"])[0])
            return self.reviews if page == 1 else []
        if "/contents/" not in path:
            raise AssertionError(f"unexpected GitHub path: {path}")
        encoded_path = path.split("/contents/", 1)[1].split("?", 1)[0]
        file_path = mod.urllib.parse.unquote(encoded_path)
        if file_path == "large/oversized.py":
            return {"type": "file", "encoding": "none", "content": ""}
        content = self.files[file_path].encode("utf-8")
        return {
            "type": "file",
            "encoding": "base64",
            "content": base64.b64encode(content).decode("ascii"),
        }


assert mod.has_prior_successful_context_review(FakeGitHubClient([{"body": mod.base.MARKER}]), 287) is False
assert (
    mod.has_prior_successful_context_review(
        FakeGitHubClient([{"body": f"{mod.base.MARKER}\n\n{mod.CONTEXT_REVIEW_MARKER} `first-pass-deep`"}]),
        287,
    )
    is True
)
assert mod.has_prior_successful_context_review(FakeGitHubClient([{"body": mod.base.MARKER}] * 100), 287) is False

alias_context = mod.build_python_path_alias_context(
    FakeGitHubClient(),
    {"head": {"sha": "abc123def4567890"}},
    [
        {"filename": "tools/aliased_writer.py", "status": "modified"},
        {"filename": "docs/review.md", "status": "modified"},
    ],
)
assert alias_context == {"tools/aliased_writer.py": {"P", "pl.Path"}}

deep_block, deep_summary = mod.build_deep_context_block(
    FakeGitHubClient(),
    {"head": {"sha": "abc123def4567890"}},
    [
        {"filename": "tools/review_probe.py", "status": "added"},
        {"filename": "docs/review.md", "status": "modified"},
        {"filename": "old/deleted.py", "status": "removed"},
    ],
    config,
    "first-pass-deep",
)
assert "Deep changed-file context" in deep_block
assert "tools/review_probe.py" in deep_block
assert "subprocess.run(command, shell=True)" in deep_block
assert "included 2 file context block" in deep_summary
assert "old/deleted.py (deleted)" in deep_summary

diff_block, diff_summary = mod.build_deep_context_block(FakeGitHubClient(), {}, [], config, "diff")
assert diff_block == ""
assert "diff-focused" in diff_summary

limited_config = mod.copy.copy(config)
limited_config.deep_review_max_files = 1
mixed_block, mixed_summary = mod.build_deep_context_block(
    FakeGitHubClient(),
    {"head": {"sha": "abc123def4567890"}},
    [
        {"filename": "old/deleted.py", "status": "removed"},
        {"filename": "missing/unavailable.py", "status": "modified"},
        {"filename": "tools/later_probe.py", "status": "modified"},
    ],
    limited_config,
    "first-pass-deep",
)
assert "tools/later_probe.py" in mixed_block
assert "included 1 file context block" in mixed_summary
assert "old/deleted.py (deleted)" in mixed_summary
assert "missing/unavailable.py" in mixed_summary

large_block, large_summary = mod.build_deep_context_block(
    FakeGitHubClient(),
    {"head": {"sha": "abc123def4567890"}},
    [
        {"filename": "large/oversized.py", "status": "modified"},
        {"filename": "tools/later_probe.py", "status": "modified"},
    ],
    limited_config,
    "first-pass-deep",
)
assert "tools/later_probe.py" in large_block
assert "large/oversized.py (file exceeds GitHub content API limit (>1 MB)" in large_summary

budget_config = mod.copy.copy(config)
budget_config.deep_review_max_files = 1
budget_config.deep_review_max_file_chars = 5000
budget_config.deep_review_max_total_chars = 520
budget_block, budget_summary = mod.build_deep_context_block(
    FakeGitHubClient(),
    {"head": {"sha": "abc123def4567890"}},
    [{"filename": "tools/huge_probe.py", "status": "modified"}],
    budget_config,
    "first-pass-deep",
)
assert "tools/huge_probe.py" in budget_summary
assert "[deep context budget exhausted]" in budget_block
assert budget_block.count("~~~") % 2 == 0

prompt_context = (
    "Deep changed-file context:\n\n"
    "### tools/huge_probe.py\n"
    "Status: modified; head ref: abc123def456\n"
    "~~~python\n"
    + ("print('large prompt context')\n" * 3000)
    + "\n~~~"
)
prompt_truncated = mod.build_prompt(
    {"number": 287, "title": "Prompt fence balance", "body": "Exercise prompt-level context truncation."},
    [{"filename": "tools/huge_probe.py", "status": "modified", "additions": 500, "deletions": 0, "changes": 500}],
    "diff --git a/tools/huge_probe.py b/tools/huge_probe.py\n",
    config,
    [],
    prompt_context,
    "first-pass-deep",
    "first-pass-deep; included 1 file context block(s): tools/huge_probe.py (truncated)",
)
assert mod.DEEP_CONTEXT_PROMPT_TRUNCATED_MARKER.strip() in prompt_truncated
assert prompt_truncated.count("~~~") % 2 == 0

prompt = mod.build_prompt(
    {"number": 287, "title": "Deep context probe", "body": "Test first-pass context."},
    [{"filename": "tools/review_probe.py", "status": "added", "additions": 2, "deletions": 0, "changes": 2}],
    "diff --git a/tools/review_probe.py b/tools/review_probe.py\n",
    config,
    [],
    deep_block,
    "first-pass-deep",
    deep_summary,
)
assert "Context mode: first-pass-deep" in prompt
assert "Deep changed-file context" in prompt
assert "subprocess.run(command, shell=True)" in prompt
assert "exact correction guidance" in prompt
assert "smallest safe patch direction" in prompt
assert "GitHub apply-ready suggestions" in prompt
assert "precise single-line replacement for the commented line" in prompt
assert "multiline, range, or speculative fixes" in prompt
assert "selected range" not in prompt

small_config = mod.copy.copy(config)
small_config.max_prompt_chars = 900
small_prompt = mod.build_prompt(
    {"number": 287, "title": "Small prompt", "body": "Ensure hardening survives."},
    [{"filename": "tools/review_probe.py", "status": "added", "additions": 2, "deletions": 0, "changes": 2}],
    "diff --git a/tools/review_probe.py b/tools/review_probe.py\n",
    small_config,
    [],
    deep_block + ("\nextra context" * 500),
    "first-pass-deep",
    deep_summary,
)
assert len(small_prompt) <= small_config.max_prompt_chars
assert small_prompt.startswith("Governed review hardening requirements:")
assert "Every semantic, Markdown, governance, validation, or review-gate concern" in small_prompt
assert mod.CONTEXT_REVIEW_MARKER not in small_prompt
assert mod.DEEP_CONTEXT_PROMPT_TRUNCATED_MARKER.strip() not in small_prompt


class FakeErrorBody:
    def read(self) -> bytes:
        return json.dumps({"error": {"message": "No endpoints found that can handle the requested parameters."}}).encode("utf-8")

    def close(self) -> None:
        return None


called_models: list[str] = []
original_request_once = mod.hardened.openrouter_request_once
empty_headers = Message()


def fake_request_once(_prompt: str, _schema: dict, _config: object, _ignored: list[str], model: str):
    called_models.append(model)
    if model == "openrouter/pareto-code":
        raise urllib.error.HTTPError(
            url="https://openrouter.ai/api/v1/chat/completions",
            code=404,
            msg="No endpoints found",
            hdrs=empty_headers,
            fp=FakeErrorBody(),
        )
    return {"summary": "No findings.", "findings": []}, "fallback-model", ""


mod.hardened.openrouter_request_once = fake_request_once
try:
    result, model_used, _tier = mod.hardened.openrouter_review("prompt", schema, config, None)
finally:
    mod.hardened.openrouter_request_once = original_request_once
assert called_models == ["openrouter/pareto-code", "openrouter/auto"]
assert model_used == "fallback-model"
assert result["findings"] == []

unsafe_context_summary = "included hostile/@codex.py and @malwaredevil-owned/file.py"
safe_context_summary = mod.sanitize_context_summary(unsafe_context_summary, config)
assert "@codex" not in safe_context_summary
assert "@malwaredevil" not in safe_context_summary
assert "@<!-- -->codex" in safe_context_summary

review_body = mod.append_context_to_review_body(mod.base.MARKER, "first-pass-deep", deep_summary, config)
assert "Context mode: `first-pass-deep`" in review_body
assert "Context readback:" in review_body
unsafe_review_body = mod.append_context_to_review_body(
    mod.base.MARKER,
    "first-pass-deep",
    unsafe_context_summary,
    config,
)
assert "@codex" not in unsafe_review_body
assert "@malwaredevil" not in unsafe_review_body
assert "@<!-- -->codex" in unsafe_review_body

print("Pareto context OpenRouter selftest passed")
