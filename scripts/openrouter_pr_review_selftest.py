#!/usr/bin/env python3
"""Offline smoke checks for the OpenRouter PR review package."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "openrouter_pr_review.py"

spec = importlib.util.spec_from_file_location("openrouter_pr_review", SCRIPT)
if spec is None or spec.loader is None:
    raise SystemExit("unable to load openrouter_pr_review.py")
mod = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

sample_diff = """diff --git a/calculator.js b/calculator.js
index 1111111..2222222 100644
--- a/calculator.js
+++ b/calculator.js
@@ -1,3 +1,4 @@
 function calculateTotal(price) {
+  const tax = 0.05;
   return price;
 }
"""

line_index = mod.build_diff_line_index(sample_diff)
assert ("calculator.js", 2) in line_index, line_index

config = mod.load_yaml_like_config(str(ROOT / ".github" / "openrouter-pr-review.yml"))
assert "/or-review" in config.commands
assert config.model == "openrouter/free"
assert config.allowed_authors == ["malwaredevil"]
assert config.post_summary_when_findings is False
assert config.include_confidence is False
assert config.redact_secret_literals is True
assert config.openrouter_max_attempts == 4
assert config.openrouter_retry_max_seconds == 45
assert config.ignored_providers == []
assert mod.provider_slug("Venice") == "venice"
assert mod.command_matches("/or-review", config.commands)
assert mod.command_matches("/or-review security", config.commands)
assert not mod.command_matches("looks good", config.commands)

schema = json.loads((ROOT / "schemas" / "openrouter-pr-review.schema.json").read_text(encoding="utf-8"))
assert schema["properties"]["findings"]["type"] == "array"

redacted = mod.sanitize_text('token = "sk_live_demo_secret_value_123456"', config)
assert "sk_live_demo" not in redacted
assert "[redacted-secret]" in redacted

comment = mod.build_inline_comment(
    {
        "title": "Hardcoded token",
        "severity": "critical",
        "confidence": 1.0,
        "body": 'The changed line assigns token = "sk_live_demo_secret_value_123456".',
        "suggested_replacement": 'token = os.getenv("OPENROUTER_TOKEN")',
        "validation": "bash scripts/validate-codex-local.sh",
    },
    "openrouter/free",
    config,
)
assert "Confidence:" not in comment
assert "sk_live_demo" not in comment
assert "Model: `openrouter/free`" in comment

err = mod.parse_openrouter_error('{"error":{"message":"Provider returned error","metadata":{"provider_name":"Venice","retry_after_seconds":21}}}')
assert err["provider"] == "Venice"
assert err["retry_after"] == 21

assert mod.is_safe_suggestion('token = os.getenv("OPENROUTER_TOKEN")')
assert not mod.is_safe_suggestion('Use environment variables for secrets.')

print("offline selftest passed")
