#!/usr/bin/env python3
"""Offline smoke checks for the OpenRouter PR review package."""

from __future__ import annotations

import importlib.util
import json
import os
from dataclasses import replace
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
assert "/dcoir-review" in config.commands
assert config.model == "openrouter/free"
assert config.model_stack == ["openrouter/free"]
assert config.allowed_authors == ["malwaredevil"]
assert config.post_summary_when_findings is False
assert config.include_confidence is False
assert config.redact_secret_literals is True
assert config.openrouter_max_attempts == 4
assert config.openrouter_retry_max_seconds == 45
assert config.script_timeout_seconds == 1500
assert config.post_progress_comment is True
assert config.ignored_providers == []
assert mod.provider_slug("Venice") == "venice"
assert mod.command_matches("/or-review", config.commands)
assert mod.command_matches("/or-review security", config.commands)
assert mod.command_matches("/dcoir-review", config.commands)
assert mod.matching_command("/dcoir-review please", config.commands) == "/dcoir-review"
assert not mod.command_matches("looks good", config.commands)
assert mod.model_stack_label(config) == "openrouter/free"

previous_openrouter_key = os.environ.pop("OPENROUTER_API_KEY", None)
try:
    try:
        mod.env_required("OPENROUTER_API_KEY")
    except RuntimeError as exc:
        assert "OPENROUTER_API_KEY" in str(exc)
    else:
        raise AssertionError("missing OPENROUTER_API_KEY should raise RuntimeError")
finally:
    if previous_openrouter_key is not None:
        os.environ["OPENROUTER_API_KEY"] = previous_openrouter_key

schema = json.loads((ROOT / "schemas" / "openrouter-pr-review.schema.json").read_text(encoding="utf-8"))
assert schema["properties"]["findings"]["type"] == "array"

secret_like = "sk_" + "live_demo_secret_value_123456"
redacted = mod.sanitize_text(f'token = "{secret_like}"', config)
assert "sk_live_demo" not in redacted
assert "[redacted-secret]" in redacted

openrouter_key = "sk-or-v1-" + "a" * 32
openai_key = "sk-proj-" + "b" * 32
password_value = "supersecretvalue12345"
punctuation_password = "p@ssw0rd123!"
dotted_password = "correct.horse.battery.staple"
delimiter_password = "abc12345;moresecret"
yaml_password = "yaml:style:password!"
quoted_json_password = "quoted-json-password!"
single_quoted_api_key = "single-quoted-api-key!"
apostrophe_password = "p@ss'word123!"
double_quote_password = 'p@ss"word123!'
escaped_quote_password = r'aaaaaaaa\"tail-secret'
bearer_secret = "bearer-secret-123456789"
basic_secret = "QmFzaWMtc2VjcmV0LTEyMzQ1Njc4OQ=="
url_password = "url-password-123456789!"
curl_password = "curl-password-123456789!"
netrc_password = "netrc-password-123456789!"
quoted_env_reference = "${OPENROUTER_API_KEY}"
dollar_env_reference = "$DB_PASSWORD"
process_env_reference = "process.env.TOKEN"
github_secret_reference = "${{ secrets.OPENROUTER_TOKEN }}"
exact_os_getenv_reference = 'os.getenv("OPENROUTER_TOKEN")'
exact_secrets_reference = 'secrets.get("OPENROUTER_TOKEN")'
unsafe_process_reference = "process.env.TOKEN p@ss'word123!"
unsafe_getenv_reference = 'os.getenv("OPENROUTER_TOKEN") p@ssw0rd123!'
unsafe_secrets_reference = 'secrets.get("OPENROUTER_TOKEN") secret-tail-123!'
unsafe_process_suffix = "process.env.DB_PASSWORD;actual-secret-123"
unsafe_getenv_suffix = 'os.getenv("OPENROUTER_TOKEN")tail-secret'
unsafe_getenv_default = 'os.getenv("OPENROUTER_TOKEN", "fallback-secret-123")'
unsafe_process_concat = 'process.env.DB_PASSWORD + "actual-secret-456"'
unsafe_method_concat = 'os.getenv("OPENROUTER_TOKEN").strip() + "actual-secret-789"'
unsafe_shell_suffix = "${DB_PASSWORD}:actual-secret-000"
unsafe_f_string = "f\"{os.getenv('OPENROUTER_TOKEN')}:actual-secret-abc\""
github_secret_fallback = "${{ secrets.OPENROUTER_TOKEN || 'fallback-secret-456' }}"
assignment_text = "\n".join(
    [
        f"OPENROUTER_API_KEY={openrouter_key}",
        f"OPENAI_API_KEY={openai_key}",
        f"password={password_value}",
        f"password={punctuation_password}",
        f"password={dotted_password}",
        f"PASSWORD={delimiter_password}",
        f"api-key: {yaml_password}",
        f"Authorization: Bearer {bearer_secret}",
        f"Proxy-Authorization: Basic {basic_secret}",
        f"X-Api-Key: {single_quoted_api_key}",
        f"curl -H \"Authorization: Bearer {bearer_secret}\" https://example.test/",
        f"curl -u dcoir:{curl_password} https://example.test/",
        f"machine example.test login dcoir password {netrc_password}",
        f"DATABASE_URL=postgres://dcoir:{url_password}@db.example.test/dcoir",
        f"PACKAGE_URL=https://{openrouter_key}@packages.example.test/simple",
        f'"password": "{quoted_json_password}"',
        f"'apiKey': '{single_quoted_api_key}'",
        f'"password": "{apostrophe_password}"',
        f"'password': '{double_quote_password}'",
        f'"password": "{escaped_quote_password}"',
        f'"apiKey": "{quoted_env_reference}"',
        f'"password": "{dollar_env_reference}"',
        f'"token": "{process_env_reference}"',
        f'"token": "{github_secret_reference}"',
        f'"token": \'{exact_os_getenv_reference}\'',
        f'"secret": \'{exact_secrets_reference}\'',
        f'"password": "{unsafe_process_reference}"',
        f'"token": \'{unsafe_getenv_reference}\'',
        f'"secret": \'{unsafe_secrets_reference}\'',
        f"password={unsafe_process_suffix}",
        f"token={unsafe_getenv_suffix}",
        f"token={unsafe_getenv_default}",
        f"password={unsafe_process_concat}",
        f"token={unsafe_method_concat}",
        f"password={unsafe_shell_suffix}",
        f"token={unsafe_f_string}",
        f"token: {github_secret_fallback}",
    ]
)
assignment_redacted = mod.sanitize_text(assignment_text, config)
for leaked in [
    "sk-or-v1",
    "sk-proj",
    password_value,
    punctuation_password,
    dotted_password,
    delimiter_password,
    yaml_password,
    quoted_json_password,
    single_quoted_api_key,
    apostrophe_password,
    double_quote_password,
    escaped_quote_password,
    bearer_secret,
    basic_secret,
    url_password,
    curl_password,
    netrc_password,
    "tail-secret",
    unsafe_process_reference,
    unsafe_getenv_reference,
    unsafe_secrets_reference,
    unsafe_process_suffix,
    unsafe_getenv_suffix,
    unsafe_getenv_default,
    "fallback-secret",
    "actual-secret",
    "secret-tail-123!",
]:
    assert leaked not in assignment_redacted, assignment_redacted
for preserved in [quoted_env_reference, dollar_env_reference, process_env_reference, github_secret_reference, exact_os_getenv_reference, exact_secrets_reference]:
    assert preserved in assignment_redacted, assignment_redacted
assert assignment_redacted.count("[redacted-secret]") >= 24

safe_reference = mod.sanitize_text(
    'token = os.getenv("OPENROUTER_TOKEN")\npassword = process.env.DB_PASSWORD\napi_key=${OPENROUTER_API_KEY}\nsecret: ${{ secrets.OPENROUTER_TOKEN }}',
    config,
)
assert 'os.getenv("OPENROUTER_TOKEN")' in safe_reference
assert "process.env.DB_PASSWORD" in safe_reference
assert "${OPENROUTER_API_KEY}" in safe_reference
assert "${{ secrets.OPENROUTER_TOKEN }}" in safe_reference

original_read_text = mod.read_text

def fake_read_text(path: str, default: str = "") -> str:
    if path == "guidance-secret.md":
        return "\n".join(
            [
                f"Guidance bearer Authorization: Bearer {bearer_secret}",
                f"Guidance URL postgres://dcoir:{url_password}@db.example.test/dcoir",
                f"Guidance token={unsafe_getenv_suffix}",
                f"Guidance safe token: {github_secret_reference}",
            ]
        )
    return original_read_text(path, default)

mod.read_text = fake_read_text
try:
    prompt_config = replace(config, guidance_files=["guidance-secret.md"])
    prompt = mod.build_prompt(
        {
            "number": 281,
            "title": f"Prompt redaction {openrouter_key}",
            "body": "\n".join(
                [
                    f"body token {secret_like}",
                    f"OPENROUTER_API_KEY={openrouter_key}",
                    f'"password": "{quoted_json_password}"',
                    f"Authorization: Bearer {bearer_secret}",
                    f"DATABASE_URL=postgres://dcoir:{url_password}@db.example.test/dcoir",
                    f'"token": "{process_env_reference}"',
                    f'"password": "{unsafe_process_reference}"',
                    f"token={unsafe_getenv_default}",
                ]
            ),
        },
        [
            {
                "filename": f"example-{openai_key}.py",
                "status": "modified",
                "additions": 1,
                "deletions": 0,
                "changes": 1,
                "patch": "\n".join(
                    [
                        f"+token = '{secret_like}'",
                        f"+password={punctuation_password}",
                        f"+Authorization: Bearer {bearer_secret}",
                        f"+DATABASE_URL=postgres://dcoir:{url_password}@db.example.test/dcoir",
                        f'+\"password\": \"{quoted_json_password}\"',
                        f'+\"password\": \"{apostrophe_password}\"',
                        f'+\"password\": \"{escaped_quote_password}\"',
                        f'+\"token\": \"{process_env_reference}\"',
                        f'+\"token\": \"{github_secret_reference}\"',
                        f'+\"password\": \"{unsafe_process_reference}\"',
                        f"+token={unsafe_getenv_suffix}",
                        f"+token={unsafe_f_string}",
                    ]
                ),
            }
        ],
        "\n".join(
            [
                "diff --git a/example.py b/example.py",
                "+++ b/example.py",
                "@@ -1,0 +1,11 @@",
                f"+token = '{secret_like}'",
                f"+OPENAI_API_KEY={openai_key}",
                f"+PASSWORD={delimiter_password}",
                f"+Authorization: Basic {basic_secret}",
                f"+NETRC machine example.test login dcoir password {netrc_password}",
                f'+\"password\": \"{quoted_json_password}\"',
                f'+\"password\": \"{escaped_quote_password}\"',
                f'+\"token\": \"{process_env_reference}\"',
                f'+\"password\": \"{unsafe_process_reference}\"',
                f"+password={unsafe_shell_suffix}",
                "",
            ]
        ),
        prompt_config,
    )
finally:
    mod.read_text = original_read_text

for leaked in [
    "sk_live_demo",
    "sk-or-v1",
    "sk-proj",
    punctuation_password,
    delimiter_password,
    quoted_json_password,
    apostrophe_password,
    escaped_quote_password,
    bearer_secret,
    basic_secret,
    url_password,
    netrc_password,
    unsafe_process_reference,
    unsafe_getenv_suffix,
    unsafe_getenv_default,
    unsafe_shell_suffix,
    "tail-secret",
    "fallback-secret",
    "actual-secret",
]:
    assert leaked not in prompt, prompt
assert process_env_reference in prompt, prompt
assert github_secret_reference in prompt, prompt
assert "[redacted-secret]" in prompt
assert r"\"quoted-json-password" not in prompt, prompt
assert r"bearer-secret" not in prompt, prompt

truncation_config = replace(config, max_prompt_chars=420, guidance_files=[])
truncated_prompt = mod.build_prompt(
    {"number": 281, "title": "Boundary", "body": "A" * 320 + f" password={punctuation_password} " + "B" * 320},
    [],
    f"diff --git a/t.py b/t.py\n+++ b/t.py\n@@ -1 +1 @@\n+Authorization: Bearer {bearer_secret}\n",
    truncation_config,
)
assert punctuation_password not in truncated_prompt, truncated_prompt
assert bearer_secret not in truncated_prompt, truncated_prompt
assert len(truncated_prompt) <= truncation_config.max_prompt_chars + 40

comment = mod.build_inline_comment(
    {
        "title": "Hardcoded token",
        "severity": "critical",
        "confidence": 1.0,
        "body": f'The changed line assigns token = "{secret_like}" and password={punctuation_password}.',
        "suggested_replacement": 'token = os.getenv("OPENROUTER_TOKEN")',
        "validation": "bash scripts/validate-codex-local.sh",
    },
    "openrouter/free",
    config,
)
assert "Confidence:" not in comment
assert "sk_live_demo" not in comment
assert punctuation_password not in comment
assert "os.getenv" in comment
assert "Model: `openrouter/free`" in comment

err = mod.parse_openrouter_error('{"error":{"message":"Provider returned error","metadata":{"provider_name":"Venice","retry_after_seconds":21}}}')
assert err["provider"] == "Venice"
assert err["retry_after"] == 21

assert mod.is_safe_suggestion('token = os.getenv("OPENROUTER_TOKEN")')
assert not mod.is_safe_suggestion("Use environment variables for secrets.")

print("offline selftest passed")
