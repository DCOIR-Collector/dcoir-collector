#!/usr/bin/env python3
"""Offline smoke checks for the DCOIR Review package."""

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
assert config.post_progress_comment is False
assert config.debug is False
assert config.ignored_providers == []
assert mod.provider_slug("Venice") == "venice"
assert mod.command_matches("/or-review", config.commands)
assert mod.command_matches("/or-review security", config.commands)
assert mod.command_matches("  /or-review security", config.commands)
assert mod.command_matches("\n/dcoir-review\tplease", config.commands)
assert mod.command_matches("/dcoir-review", config.commands)
assert mod.matching_command("/dcoir-review please", config.commands) == "/dcoir-review"
assert mod.command_requests_debug("/dcoir-review debug", "/dcoir-review")
assert mod.command_requests_debug("/dcoir-review debug=true", "/dcoir-review")
assert mod.command_requests_debug("/dcoir-review --debug", "/dcoir-review")
assert mod.command_requests_debug("/dcoir-review debug: true", "/dcoir-review")
assert mod.command_requests_debug("/dcoir-review debug yes", "/dcoir-review")
assert not mod.command_requests_debug("/dcoir-review debug=false", "/dcoir-review")
assert not mod.command_requests_debug("/dcoir-review --debug=false", "/dcoir-review")
assert not mod.command_requests_debug("/dcoir-review debug: false", "/dcoir-review")
debug_config = replace(config)
mod.apply_debug_flag(debug_config, "/dcoir-review debug", "/dcoir-review")
assert debug_config.debug is True
assert debug_config.post_progress_comment is True
assert not mod.command_matches("looks good", config.commands)
assert not mod.command_matches("/or-reviewer", config.commands)
assert not mod.command_matches("/dcoir-review-anything", config.commands)
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
cookie_secret = "sessionid=cookie-secret-123456789; connect.sid=connect-secret-123456789; csrf=csrf-secret-123456789"
set_cookie_secret = "refresh=refresh-cookie-secret-123456789; Path=/; HttpOnly"
url_password = "url-password-123456789!"
curl_password = "curl-password-123456789!"
curl_proxy_password = "proxy-curl-password-123456789!"
curl_spaced_password = "curl password secret 12345!"
curl_fallback_expression = "${{ secrets.CURL_PASSWORD || 'fallback curl secret 12345' }}"
curl_proxy_fallback_expression = "${{ secrets.PROXY_PASSWORD || 'proxy fallback secret 12345' }}"
curl_inner_brace_expression = "${{ secrets.CURL_PASSWORD || 'fallback }} curl secret 12345' }}"
curl_unclosed_expression = "${{ secrets.CURL_PASSWORD || 'unclosed curl secret 12345"
curl_backtick_expression = "`printf backtick curl secret 12345`"
curl_multiline_backtick_expression = "`printf multiline backtick curl secret 12345\n`"
curl_multiline_backtick_tail_expression = "`printf benign\nmultiline backtick tail secret 12345`"
curl_unclosed_quoted_password = "top quoted secret 12345"
curl_proxy_unclosed_quoted_password = "proxy top quoted secret 12345"
curl_multiline_double_quote_password = "multiline double quoted tail secret 12345"
curl_multiline_single_quote_password = "multiline single quoted tail secret 12345"
curl_multiline_ansi_quote_password = "multiline ansi quoted tail secret 12345"
curl_multiline_locale_quote_password = "multiline locale quoted tail secret 12345"
curl_ansi_password = "ansi curl secret 12345"
curl_locale_password = "locale curl secret 12345"
curl_escaped_space_password = r"escaped\ curl\ secret\ 12345"
curl_concat_password = "concat curl secret 12345"
netrc_password = "netrc-password-123456789!"
signed_url_secret = "signed-url-secret-123456789abcdef"
sas_secret = "azure-sas-secret-123456789abcdef"
private_key_block = "\n".join(
    [
        "-----BEGIN OPENSSH PRIVATE KEY-----",
        "b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAlwAAAAdzc2gtcn",
        "NhAAAAAwEAAQAAAIEAprivate-key-secret-material-123456789",
        "-----END OPENSSH PRIVATE KEY-----",
    ]
)
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
aws_signed_url = f"https://bucket.s3.amazonaws.com/object?X-Amz-Credential={openrouter_key}&X-Amz-Signature={signed_url_secret}&X-Amz-Expires=3600"
azure_sas_url = f"https://account.blob.core.windows.net/container/blob?sv=2026-01-01&sp=r&sig={sas_secret}"
generic_signed_url = f"https://example.test/webhook?sig={signed_url_secret}&token={openrouter_key}"
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
        f'Authorization: Bearer "{bearer_secret}"',
        f"Proxy-Authorization: Basic '{basic_secret}'",
        f'Authorization: token "{github_secret_fallback}"',
        f"Proxy-Authorization: Basic {basic_secret}",
        f"Cookie: {cookie_secret}",
        f"Set-Cookie: {set_cookie_secret}",
        f"X-Api-Key: {single_quoted_api_key}",
        f'"Authorization": "Bearer {bearer_secret}"',
        f'Authorization: "Bearer {bearer_secret}"',
        f'Authorization: Bearer {bearer_secret}',
        f'headers = {{ Authorization: "Bearer {bearer_secret}" }}',
        f'headers = {{ Cookie: "{cookie_secret}" }}',
        f'Authorization: "Bearer {bearer_secret}"',
        f"'Proxy-Authorization': 'Basic {basic_secret}'",
        f'"Cookie": "{cookie_secret}"',
        f'"Set-Cookie": f"{set_cookie_secret}"',
        f'"X-Api-Key": "token {single_quoted_api_key}"',
        f"curl -H \"Authorization: Bearer {bearer_secret}\" https://example.test/",
        f"curl -udcoir:{curl_password} https://example.test/",
        f"curl -u dcoir:{curl_password} https://example.test/",
        f"curl --user dcoir:{curl_password} https://example.test/",
        f"curl --user=dcoir:{curl_password} https://example.test/",
        f"curl -u :{curl_password} https://example.test/",
        f"curl -u:{curl_password} https://example.test/",
        f"curl --user :{curl_password} https://example.test/",
        f"curl --user=:{curl_password} https://example.test/",
        f"curl --proxy-user dcoir:{curl_proxy_password} https://example.test/",
        f"curl --proxy-user=dcoir:{curl_proxy_password} https://example.test/",
        f"curl --proxy-user :{curl_proxy_password} https://example.test/",
        f"curl --proxy-user=:{curl_proxy_password} https://example.test/",
        f"curl -u ':{curl_spaced_password}' https://example.test/",
        f"curl -u':{curl_spaced_password}' https://example.test/",
        f'curl --user ":{curl_spaced_password}" https://example.test/',
        f'curl --user=":{curl_spaced_password}" https://example.test/',
        f"curl -u 'dcoir:{curl_spaced_password}' https://example.test/",
        f"curl -u'dcoir:{curl_spaced_password}' https://example.test/",
        f'curl --user "dcoir:{curl_spaced_password}" https://example.test/',
        f'curl --user="dcoir:{curl_spaced_password}" https://example.test/',
        f'curl --proxy-user "dcoir:{curl_spaced_password}" https://example.test/',
        f"curl -u :{curl_fallback_expression} https://example.test/",
        f"curl -u:{curl_fallback_expression} https://example.test/",
        f"curl --user :{curl_fallback_expression} https://example.test/",
        f"curl --user=:{curl_fallback_expression} https://example.test/",
        f"curl --proxy-user=:{curl_proxy_fallback_expression} https://example.test/",
        f"curl --user=:{curl_inner_brace_expression} https://example.test/",
        f"curl --user=:{curl_unclosed_expression} https://example.test/",
        f"curl -u :{curl_backtick_expression} https://example.test/",
        f"curl -u:{curl_backtick_expression} https://example.test/",
        f"curl --user :{curl_backtick_expression} https://example.test/",
        f"curl --user=:{curl_backtick_expression} https://example.test/",
        f"curl -u dcoir:{curl_backtick_expression} https://example.test/",
        f"curl -udcoir:{curl_backtick_expression} https://example.test/",
        f"curl --user dcoir:{curl_backtick_expression} https://example.test/",
        f"curl --user=dcoir:{curl_backtick_expression} https://example.test/",
        f"curl --proxy-user dcoir:{curl_backtick_expression} https://example.test/",
        f"curl --user=:{curl_multiline_backtick_expression} https://example.test/",
        f"curl --user=:{curl_multiline_backtick_tail_expression} https://example.test/",
        f'curl --user "dcoir:benign\n{curl_multiline_double_quote_password}" https://example.test/',
        f"curl --proxy-user 'proxy:benign\n{curl_multiline_single_quote_password}' https://example.test/",
        f"curl --user $'dcoir:benign\n{curl_multiline_ansi_quote_password}' https://example.test/",
        f'curl --proxy-user $"proxy:benign\n{curl_multiline_locale_quote_password}" https://example.test/',
        f"curl -u $':{curl_ansi_password}' https://example.test/",
        f"curl -u$':{curl_ansi_password}' https://example.test/",
        f"curl --user $':{curl_ansi_password}' https://example.test/",
        f"curl --user=$':{curl_ansi_password}' https://example.test/",
        f"curl --proxy-user $':{curl_ansi_password}' https://example.test/",
        f"curl -u $'dcoir:{curl_ansi_password}' https://example.test/",
        f"curl -u$'dcoir:{curl_ansi_password}' https://example.test/",
        f"curl --user $'dcoir:{curl_ansi_password}' https://example.test/",
        f"curl --user=$'dcoir:{curl_ansi_password}' https://example.test/",
        f'curl -u $":{curl_locale_password}" https://example.test/',
        f'curl -u$":{curl_locale_password}" https://example.test/',
        f'curl --user $":{curl_locale_password}" https://example.test/',
        f'curl --user=$":{curl_locale_password}" https://example.test/',
        f'curl -u $"dcoir:{curl_locale_password}" https://example.test/',
        f'curl -u$"dcoir:{curl_locale_password}" https://example.test/',
        f'curl --user $"dcoir:{curl_locale_password}" https://example.test/',
        f'curl --user=$"dcoir:{curl_locale_password}" https://example.test/',
        f"curl -u :{curl_escaped_space_password} https://example.test/",
        f"curl -u:{curl_escaped_space_password} https://example.test/",
        f"curl --user :{curl_escaped_space_password} https://example.test/",
        f"curl --user=:{curl_escaped_space_password} https://example.test/",
        f"curl -u dcoir:{curl_escaped_space_password} https://example.test/",
        f"curl -udcoir:{curl_escaped_space_password} https://example.test/",
        f"curl --user dcoir:{curl_escaped_space_password} https://example.test/",
        f"curl --user=dcoir:{curl_escaped_space_password} https://example.test/",
        f"curl --proxy-user=dcoir:{curl_escaped_space_password} https://example.test/",
        f"curl -u :concat' {curl_concat_password}' https://example.test/",
        f'curl -u:concat" {curl_concat_password}" https://example.test/',
        f"curl --user :concat$' {curl_concat_password}' https://example.test/",
        f'curl --user=:concat$" {curl_concat_password}" https://example.test/',
        f"curl -u dcoir:concat' {curl_concat_password}' https://example.test/",
        f'curl -udcoir:concat" {curl_concat_password}" https://example.test/',
        f"curl --user dcoir:concat$' {curl_concat_password}' https://example.test/",
        f'curl --user=dcoir:concat$" {curl_concat_password}" https://example.test/',
        f"curl --proxy-user=:concat' {curl_concat_password}' https://example.test/",
        f"machine example.test login dcoir password {netrc_password}",
        f"DATABASE_URL=postgres://dcoir:{url_password}@db.example.test/dcoir",
        f"PACKAGE_URL=https://{openrouter_key}@packages.example.test/simple",
        aws_signed_url,
        azure_sas_url,
        generic_signed_url,
        private_key_block,
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
        f'"Authorization": "Bearer {quoted_env_reference}"',
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
        f'curl --user="dcoir:{curl_unclosed_quoted_password} https://example.test/',
        f"curl --proxy-user='proxy:{curl_proxy_unclosed_quoted_password} https://example.test/",
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
    "cookie-secret",
    "connect-secret",
    "csrf-secret",
    "refresh-cookie-secret",
    url_password,
    curl_password,
    curl_proxy_password,
    curl_spaced_password,
    "fallback curl secret",
    "proxy fallback secret",
    "fallback }} curl secret",
    "unclosed curl secret",
    "backtick curl secret",
    "multiline backtick curl secret",
    "multiline backtick tail secret",
    curl_unclosed_quoted_password,
    curl_proxy_unclosed_quoted_password,
    curl_multiline_double_quote_password,
    curl_multiline_single_quote_password,
    curl_multiline_ansi_quote_password,
    curl_multiline_locale_quote_password,
    "ansi curl secret",
    "locale curl secret",
    r"escaped\ curl\ secret",
    "concat curl secret",
    netrc_password,
    signed_url_secret,
    sas_secret,
    "PRIVATE KEY",
    "private-key-secret-material",
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
assert assignment_redacted.count("[redacted-secret]") >= 35
for safe_header in [
    '"Authorization": "Bearer ${OPENROUTER_API_KEY}"',
    'Authorization: "Bearer ${OPENROUTER_API_KEY}"',
    'headers = { Authorization: "Bearer ${OPENROUTER_API_KEY}" }',
    'Authorization: Bearer "${OPENROUTER_API_KEY}"',
]:
    assert mod.sanitize_text(safe_header, config) == safe_header
header_cases = {
    f'"Authorization": "Bearer {bearer_secret}"': '"Authorization": "Bearer [redacted-secret]"',
    f'Authorization: "Bearer {bearer_secret}"': 'Authorization: "Bearer [redacted-secret]"',
    f'Authorization: Bearer {bearer_secret}': 'Authorization: Bearer [redacted-secret]',
    f'Authorization: Bearer "{bearer_secret}"': 'Authorization: Bearer [redacted-secret]',
    f"Proxy-Authorization: Basic '{basic_secret}'": 'Proxy-Authorization: Basic [redacted-secret]',
    f'Authorization: token "{github_secret_fallback}"': 'Authorization: token [redacted-secret]',
    'Authorization: Bearer "${OPENROUTER_API_KEY}"': 'Authorization: Bearer "${OPENROUTER_API_KEY}"',
    f'headers = {{ Authorization: "Bearer {bearer_secret}" }}': 'headers = { Authorization: "Bearer [redacted-secret]" }',
    f'headers = {{ Cookie: "{cookie_secret}" }}': 'headers = { Cookie: "[redacted-secret]" }',
    "headers = { Cookie: sessionid=cookie-secret-123456789, X-Trace: \"keep-me\" }": "headers = { Cookie: [redacted-secret], X-Trace: \"keep-me\" }",
    "headers = { \"Set-Cookie\": sessionid=cookie-secret-123456789, X-Trace: \"keep-me\" }": "headers = { \"Set-Cookie\": [redacted-secret], X-Trace: \"keep-me\" }",
    "Cookie: sessionid=cookie-secret-123456789; connect.sid=connect-secret-123456789": "Cookie: [redacted-secret]",
    "headers = { Cookie: session=secret-123456, sid=second-secret-7890 }": "headers = { Cookie: [redacted-secret]}",
    "headers = { Set-Cookie: session=secret-123456, sid=second-secret-7890 }": "headers = { Set-Cookie: [redacted-secret]}",
    "headers = { Cookie: session=secret-123456, sid=second-secret-7890, X-Trace: \"keep-me\" }": "headers = { Cookie: [redacted-secret], X-Trace: \"keep-me\" }",
    "headers = { Set-Cookie: session=secret-123456, sid=second-secret-7890, X-Trace: \"keep-me\" }": "headers = { Set-Cookie: [redacted-secret], X-Trace: \"keep-me\" }",
    "headers = { Cookie: ${COOKIE_HEADER}:actual-secret-123 }": "headers = { Cookie: [redacted-secret]}",
    "headers = { Cookie: ${COOKIE_HEADER}:actual-secret-123 } trailing_text": "headers = { Cookie: [redacted-secret]} trailing_text",
    "headers = { Cookie: ${COOKIE_HEADER} }": "headers = { Cookie: ${COOKIE_HEADER} }",
    "headers = { Set-Cookie: ${COOKIE_HEADER}:actual-secret-123 }": "headers = { Set-Cookie: [redacted-secret]}",
    "headers = { Set-Cookie: ${COOKIE_HEADER} }": "headers = { Set-Cookie: ${COOKIE_HEADER} }",
    "headers = { Cookie: ${{ secrets.COOKIE_HEADER }} }": "headers = { Cookie: ${{ secrets.COOKIE_HEADER }} }",
    "Cookie: session=secret-123456, sid=second-secret-7890": "Cookie: [redacted-secret]",
    "Set-Cookie: session=secret-123456, sid=second-secret-7890": "Set-Cookie: [redacted-secret]",
    "headers = { Cookie: ${COOKIE_HEADER}, X-Trace: \"keep-me\" }": "headers = { Cookie: ${COOKIE_HEADER}, X-Trace: \"keep-me\" }",
    f'headers = {{ Authorization: Bearer {bearer_secret}, X-Trace: "keep-me" }}': 'headers = { Authorization: Bearer [redacted-secret], X-Trace: "keep-me" }',
    f'headers = {{ Authorization: Bearer {bearer_secret} }}': 'headers = { Authorization: Bearer [redacted-secret] }',
    f'Authorization: Bearer {bearer_secret}\nnext: field': 'Authorization: Bearer [redacted-secret]\nnext: field',
}
for unsafe_header, expected_header in header_cases.items():
    assert mod.sanitize_text(unsafe_header, config) == expected_header
curl_cases = {
    f"curl -uuser:{curl_password} https://example.test/": "curl -uuser:[redacted-secret] https://example.test/",
    f"curl -u user:{curl_password} https://example.test/": "curl -u user:[redacted-secret] https://example.test/",
    f"curl --user user:{curl_password} https://example.test/": "curl --user user:[redacted-secret] https://example.test/",
    f"curl --user=user:{curl_password} https://example.test/": "curl --user=user:[redacted-secret] https://example.test/",
    f"curl -u :{curl_password} https://example.test/": "curl -u :[redacted-secret] https://example.test/",
    f"curl -u:{curl_password} https://example.test/": "curl -u:[redacted-secret] https://example.test/",
    f"curl --user :{curl_password} https://example.test/": "curl --user :[redacted-secret] https://example.test/",
    f"curl --user=:{curl_password} https://example.test/": "curl --user=:[redacted-secret] https://example.test/",
    f"curl --proxy-user proxy:{curl_proxy_password} https://example.test/": "curl --proxy-user proxy:[redacted-secret] https://example.test/",
    f"curl --proxy-user=proxy:{curl_proxy_password} https://example.test/": "curl --proxy-user=proxy:[redacted-secret] https://example.test/",
    f"curl --proxy-user :{curl_proxy_password} https://example.test/": "curl --proxy-user :[redacted-secret] https://example.test/",
    f"curl --proxy-user=:{curl_proxy_password} https://example.test/": "curl --proxy-user=:[redacted-secret] https://example.test/",
    f"curl -u ':{curl_spaced_password}' https://example.test/": "curl -u ':[redacted-secret]' https://example.test/",
    f"curl -u':{curl_spaced_password}' https://example.test/": "curl -u':[redacted-secret]' https://example.test/",
    f'curl --user ":{curl_spaced_password}" https://example.test/': 'curl --user ":[redacted-secret]" https://example.test/',
    f'curl --user=":{curl_spaced_password}" https://example.test/': 'curl --user=":[redacted-secret]" https://example.test/',
    f"curl -u 'dcoir:{curl_spaced_password}' https://example.test/": "curl -u 'dcoir:[redacted-secret]' https://example.test/",
    f"curl -u'dcoir:{curl_spaced_password}' https://example.test/": "curl -u'dcoir:[redacted-secret]' https://example.test/",
    f'curl --user "dcoir:{curl_spaced_password}" https://example.test/': 'curl --user "dcoir:[redacted-secret]" https://example.test/',
    f'curl --user="dcoir:{curl_spaced_password}" https://example.test/': 'curl --user="dcoir:[redacted-secret]" https://example.test/',
    f'curl --proxy-user "dcoir:{curl_spaced_password}" https://example.test/': 'curl --proxy-user "dcoir:[redacted-secret]" https://example.test/',
    f"curl -u :{curl_fallback_expression} https://example.test/": "curl -u :[redacted-secret] https://example.test/",
    f"curl -u:{curl_fallback_expression} https://example.test/": "curl -u:[redacted-secret] https://example.test/",
    f"curl --user :{curl_fallback_expression} https://example.test/": "curl --user :[redacted-secret] https://example.test/",
    f"curl --user=:{curl_fallback_expression} https://example.test/": "curl --user=:[redacted-secret] https://example.test/",
    f"curl --proxy-user=:{curl_proxy_fallback_expression} https://example.test/": "curl --proxy-user=:[redacted-secret] https://example.test/",
    f"curl --user=:{curl_inner_brace_expression} https://example.test/": "curl --user=:[redacted-secret] https://example.test/",
    f"curl --user=:{curl_unclosed_expression} https://example.test/": "curl --user=:[redacted-secret]",
    f"curl -u :{curl_backtick_expression} https://example.test/": "curl -u :[redacted-secret] https://example.test/",
    f"curl -u:{curl_backtick_expression} https://example.test/": "curl -u:[redacted-secret] https://example.test/",
    f"curl --user :{curl_backtick_expression} https://example.test/": "curl --user :[redacted-secret] https://example.test/",
    f"curl --user=:{curl_backtick_expression} https://example.test/": "curl --user=:[redacted-secret] https://example.test/",
    f"curl -u dcoir:{curl_backtick_expression} https://example.test/": "curl -u dcoir:[redacted-secret] https://example.test/",
    f"curl -udcoir:{curl_backtick_expression} https://example.test/": "curl -udcoir:[redacted-secret] https://example.test/",
    f"curl --user dcoir:{curl_backtick_expression} https://example.test/": "curl --user dcoir:[redacted-secret] https://example.test/",
    f"curl --user=dcoir:{curl_backtick_expression} https://example.test/": "curl --user=dcoir:[redacted-secret] https://example.test/",
    f"curl --proxy-user dcoir:{curl_backtick_expression} https://example.test/": "curl --proxy-user dcoir:[redacted-secret] https://example.test/",
    f"curl --user=:{curl_multiline_backtick_expression} https://example.test/": "curl --user=:[redacted-secret] https://example.test/",
    f"curl --user=:{curl_multiline_backtick_tail_expression} https://example.test/": "curl --user=:[redacted-secret] https://example.test/",
    f'curl --user="dcoir:{curl_unclosed_quoted_password} https://example.test/': 'curl --user="dcoir:[redacted-secret]',
    f"curl --proxy-user='proxy:{curl_proxy_unclosed_quoted_password} https://example.test/": "curl --proxy-user='proxy:[redacted-secret]",
    f'curl --user "dcoir:benign\n{curl_multiline_double_quote_password}" https://example.test/': 'curl --user "dcoir:[redacted-secret]" https://example.test/',
    f"curl --proxy-user 'proxy:benign\n{curl_multiline_single_quote_password}' https://example.test/": "curl --proxy-user 'proxy:[redacted-secret]' https://example.test/",
    f"curl --user $'dcoir:benign\n{curl_multiline_ansi_quote_password}' https://example.test/": "curl --user $'dcoir:[redacted-secret]' https://example.test/",
    f'curl --proxy-user $"proxy:benign\n{curl_multiline_locale_quote_password}" https://example.test/': 'curl --proxy-user $"proxy:[redacted-secret]" https://example.test/',
    f"curl -u $':{curl_ansi_password}' https://example.test/": "curl -u $':[redacted-secret]' https://example.test/",
    f"curl -u$':{curl_ansi_password}' https://example.test/": "curl -u$':[redacted-secret]' https://example.test/",
    f"curl --user $':{curl_ansi_password}' https://example.test/": "curl --user $':[redacted-secret]' https://example.test/",
    f"curl --user=$':{curl_ansi_password}' https://example.test/": "curl --user=$':[redacted-secret]' https://example.test/",
    f"curl --proxy-user $':{curl_ansi_password}' https://example.test/": "curl --proxy-user $':[redacted-secret]' https://example.test/",
    f"curl -u $'dcoir:{curl_ansi_password}' https://example.test/": "curl -u $'dcoir:[redacted-secret]' https://example.test/",
    f"curl -u$'dcoir:{curl_ansi_password}' https://example.test/": "curl -u$'dcoir:[redacted-secret]' https://example.test/",
    f"curl --user $'dcoir:{curl_ansi_password}' https://example.test/": "curl --user $'dcoir:[redacted-secret]' https://example.test/",
    f"curl --user=$'dcoir:{curl_ansi_password}' https://example.test/": "curl --user=$'dcoir:[redacted-secret]' https://example.test/",
    f'curl -u $":{curl_locale_password}" https://example.test/': 'curl -u $":[redacted-secret]" https://example.test/',
    f'curl -u$":{curl_locale_password}" https://example.test/': 'curl -u$":[redacted-secret]" https://example.test/',
    f'curl --user $":{curl_locale_password}" https://example.test/': 'curl --user $":[redacted-secret]" https://example.test/',
    f'curl --user=$":{curl_locale_password}" https://example.test/': 'curl --user=$":[redacted-secret]" https://example.test/',
    f'curl -u $"dcoir:{curl_locale_password}" https://example.test/': 'curl -u $"dcoir:[redacted-secret]" https://example.test/',
    f'curl -u$"dcoir:{curl_locale_password}" https://example.test/': 'curl -u$"dcoir:[redacted-secret]" https://example.test/',
    f'curl --user $"dcoir:{curl_locale_password}" https://example.test/': 'curl --user $"dcoir:[redacted-secret]" https://example.test/',
    f'curl --user=$"dcoir:{curl_locale_password}" https://example.test/': 'curl --user=$"dcoir:[redacted-secret]" https://example.test/',
    f"curl -u :{curl_escaped_space_password} https://example.test/": "curl -u :[redacted-secret] https://example.test/",
    f"curl -u:{curl_escaped_space_password} https://example.test/": "curl -u:[redacted-secret] https://example.test/",
    f"curl --user :{curl_escaped_space_password} https://example.test/": "curl --user :[redacted-secret] https://example.test/",
    f"curl --user=:{curl_escaped_space_password} https://example.test/": "curl --user=:[redacted-secret] https://example.test/",
    f"curl -u dcoir:{curl_escaped_space_password} https://example.test/": "curl -u dcoir:[redacted-secret] https://example.test/",
    f"curl -udcoir:{curl_escaped_space_password} https://example.test/": "curl -udcoir:[redacted-secret] https://example.test/",
    f"curl --user dcoir:{curl_escaped_space_password} https://example.test/": "curl --user dcoir:[redacted-secret] https://example.test/",
    f"curl --user=dcoir:{curl_escaped_space_password} https://example.test/": "curl --user=dcoir:[redacted-secret] https://example.test/",
    f"curl --proxy-user=dcoir:{curl_escaped_space_password} https://example.test/": "curl --proxy-user=dcoir:[redacted-secret] https://example.test/",
    f"curl -u :concat' {curl_concat_password}' https://example.test/": "curl -u :[redacted-secret] https://example.test/",
    f'curl -u:concat" {curl_concat_password}" https://example.test/': "curl -u:[redacted-secret] https://example.test/",
    f"curl --user :concat$' {curl_concat_password}' https://example.test/": "curl --user :[redacted-secret] https://example.test/",
    f'curl --user=:concat$" {curl_concat_password}" https://example.test/': "curl --user=:[redacted-secret] https://example.test/",
    f"curl -u dcoir:concat' {curl_concat_password}' https://example.test/": "curl -u dcoir:[redacted-secret] https://example.test/",
    f'curl -udcoir:concat" {curl_concat_password}" https://example.test/': "curl -udcoir:[redacted-secret] https://example.test/",
    f"curl --user dcoir:concat$' {curl_concat_password}' https://example.test/": "curl --user dcoir:[redacted-secret] https://example.test/",
    f'curl --user=dcoir:concat$" {curl_concat_password}" https://example.test/': "curl --user=dcoir:[redacted-secret] https://example.test/",
    f"curl --proxy-user=:concat' {curl_concat_password}' https://example.test/": "curl --proxy-user=:[redacted-secret] https://example.test/",
}
for curl_form, expected_curl in curl_cases.items():
    assert mod.sanitize_text(curl_form, config) == expected_curl
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
                f"Guidance object header \"Authorization\": \"Bearer {bearer_secret}\"",
                f"Guidance cookie Cookie: {cookie_secret}",
                f"Guidance URL postgres://dcoir:{url_password}@db.example.test/dcoir",
                f"Guidance signed {aws_signed_url}",
                f"Guidance token={unsafe_getenv_suffix}",
                f"Guidance safe token: {github_secret_reference}",
                private_key_block,
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
                    f'"Authorization": "Bearer {bearer_secret}"',
                    f'"Cookie": "{cookie_secret}"',
                    f"Authorization: Bearer {bearer_secret}",
                    f'Authorization: Bearer "{bearer_secret}"',
                    f'Authorization: Bearer \\"{bearer_secret}\\"',
                    f"Cookie: {cookie_secret}",
                    f"DATABASE_URL=postgres://dcoir:{url_password}@db.example.test/dcoir",
                    f'curl --user "dcoir:benign\n{curl_multiline_double_quote_password}" https://example.test/',
                    aws_signed_url,
                    private_key_block,
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
                        f'+Authorization: Bearer "{bearer_secret}"',
                        f'+Authorization: Bearer \\"{bearer_secret}\\"',
                        f"+Cookie: {cookie_secret}",
                        f'+headers = {{"Authorization": "Bearer {bearer_secret}", "Cookie": "{cookie_secret}"}}',
                        f"+DATABASE_URL=postgres://dcoir:{url_password}@db.example.test/dcoir",
                        f'+curl --proxy-user "proxy:benign\n{curl_multiline_single_quote_password}" https://example.test/',
                        f"+SIGNED={generic_signed_url}",
                        "+" + private_key_block.replace("\n", "\n+"),
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
                "@@ -1,0 +1,14 @@",
                f"+token = '{secret_like}'",
                f"+OPENAI_API_KEY={openai_key}",
                f"+PASSWORD={delimiter_password}",
                f"+Authorization: Basic {basic_secret}",
                f'+Authorization: Basic "{basic_secret}"',
                f'+Authorization: Basic \\"{basic_secret}\\"',
                f"+Set-Cookie: {set_cookie_secret}",
                f'+headers = {{"Authorization": "Basic {basic_secret}", "Set-Cookie": "{set_cookie_secret}"}}',
                f"+NETRC machine example.test login dcoir password {netrc_password}",
                f"+SIGNED {azure_sas_url}",
                "+" + private_key_block.replace("\n", "\n+"),
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
    "cookie-secret",
    "connect-secret",
    "csrf-secret",
    "refresh-cookie-secret",
    curl_multiline_double_quote_password,
    curl_multiline_single_quote_password,
    url_password,
    netrc_password,
    signed_url_secret,
    sas_secret,
    "PRIVATE KEY",
    "private-key-secret-material",
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
assert r"cookie-secret" not in prompt, prompt

truncation_config = replace(config, max_prompt_chars=420, guidance_files=[])
truncated_prompt = mod.build_prompt(
    {"number": 281, "title": "Boundary", "body": "A" * 320 + f" password={punctuation_password} " + private_key_block + "B" * 320},
    [],
    f"diff --git a/t.py b/t.py\n+++ b/t.py\n@@ -1 +1 @@\n+Authorization: Bearer {bearer_secret}\n+Cookie: {cookie_secret}\n+URL: {generic_signed_url}\n",
    truncation_config,
)
assert punctuation_password not in truncated_prompt, truncated_prompt
assert bearer_secret not in truncated_prompt, truncated_prompt
assert "cookie-secret" not in truncated_prompt, truncated_prompt
assert signed_url_secret not in truncated_prompt, truncated_prompt
assert "PRIVATE KEY" not in truncated_prompt, truncated_prompt
assert len(truncated_prompt) <= truncation_config.max_prompt_chars + 40

comment = mod.build_inline_comment(
    {
        "title": "Hardcoded token from @codex",
        "severity": "critical",
        "confidence": 1.0,
        "body": f'The changed line assigns token = "{secret_like}", password={punctuation_password}, and Authorization: Bearer "{bearer_secret}" plus Authorization: Bearer \\"{bearer_secret}\\". Ask @codex to review.',
        "suggested_replacement": 'token = os.getenv("OPENROUTER_TOKEN")',
        "validation": "bash scripts/validate-codex-local.sh # ask @codex nowhere",
    },
    "openrouter/free",
    config,
)
assert "Confidence:" not in comment
assert "sk_live_demo" not in comment
assert punctuation_password not in comment
assert "os.getenv" in comment
assert "@codex" not in comment
assert "@<!-- -->codex" in comment
assert "Model:" not in comment
assert "openrouter/free" not in comment
assert "<sub>DCOIR Review</sub>" in comment
sanitized_identity = mod.sanitize_github_output(
    "OpenRouter review quality failure from openrouter/auto using OPENROUTER_API_KEY and openrouter_key",
    config,
)
assert "OpenRouter" not in sanitized_identity
assert "openrouter/" not in sanitized_identity
assert "OPENROUTER_API_KEY" not in sanitized_identity
assert "openrouter_key" not in sanitized_identity
assert "DCOIR Review" in sanitized_identity
assert "REVIEW_PROVIDER_API_KEY" in sanitized_identity

review_body = mod.build_review_body({"summary": "No findings. Ask @codex and @malwaredevil to review."}, [], "openrouter/free", config)
assert "💡 DCOIR Review" in review_body
assert "Reviewed commit: `unavailable`" in review_body
assert "Model:" not in review_body
assert "OpenRouter" not in review_body
assert "@codex" not in review_body
assert "@malwaredevil" not in review_body
assert "@<!-- -->codex" in review_body
assert "@<!-- -->malwaredevil" in review_body

class FakeGitHub:
    def __init__(self) -> None:
        self.comments: list[str] = []
        self.updates: list[str] = []

    def create_issue_comment(self, _number: int, body: str) -> dict[str, int]:
        self.comments.append(body)
        return {"id": 123}

    def update_issue_comment(self, _comment_id: int, body: str) -> dict[str, str]:
        self.updates.append(body)
        return {}

fake_gh = FakeGitHub()
failure_reporter = mod.ProgressReporter(fake_gh, 281, "/or-review", config)
failure_message = "\n".join(
    [
        f"Authorization: Bearer {bearer_secret}",
        f'Authorization: Bearer "{bearer_secret}"',
        f'Authorization: Bearer \\"{bearer_secret}\\"',
        f"Cookie: {cookie_secret}",
        f"DATABASE_URL=postgres://dcoir:{url_password}@db.example.test/dcoir",
        f"curl --user=:{curl_fallback_expression} https://example.test/",
        f"curl --proxy-user=:{curl_proxy_fallback_expression} https://example.test/",
        f"curl --user=:{curl_inner_brace_expression} https://example.test/",
        f"curl --user=:{curl_unclosed_expression} https://example.test/",
        f"curl --user=:{curl_backtick_expression} https://example.test/",
        f"curl --user=:{curl_multiline_backtick_expression} https://example.test/",
        f"curl --user=:{curl_multiline_backtick_tail_expression} https://example.test/",
        f'curl --user "dcoir:benign\n{curl_multiline_double_quote_password}" https://example.test/',
        f"curl --proxy-user 'proxy:benign\n{curl_multiline_single_quote_password}' https://example.test/",
        f"curl --user $'dcoir:benign\n{curl_multiline_ansi_quote_password}' https://example.test/",
        f'curl --proxy-user $"proxy:benign\n{curl_multiline_locale_quote_password}" https://example.test/',
        f"curl --user=$':{curl_ansi_password}' https://example.test/",
        f'curl --user=$":{curl_locale_password}" https://example.test/',
        f"curl --user=:{curl_escaped_space_password} https://example.test/",
        f"curl --user=:concat' {curl_concat_password}' https://example.test/",
        generic_signed_url,
        private_key_block,
        "Ask @codex to review this failure.",
        f'curl --user="dcoir:{curl_unclosed_quoted_password} https://example.test/',
        f"curl --proxy-user='proxy:{curl_proxy_unclosed_quoted_password} https://example.test/",
    ]
)
failure_reporter.fail(failure_message)
assert fake_gh.comments == []

debug_failure_config = replace(config, debug=True, post_progress_comment=True)
debug_fake_gh = FakeGitHub()
debug_failure_reporter = mod.ProgressReporter(debug_fake_gh, 281, "/or-review", debug_failure_config)
debug_failure_reporter.fail(failure_message)
failure_body = debug_fake_gh.comments[-1]
for leaked in [
    bearer_secret,
    "cookie-secret",
    url_password,
    signed_url_secret,
    "fallback curl secret",
    "proxy fallback secret",
    "fallback }} curl secret",
    "unclosed curl secret",
    "backtick curl secret",
    "multiline backtick curl secret",
    "multiline backtick tail secret",
    curl_unclosed_quoted_password,
    curl_proxy_unclosed_quoted_password,
    curl_multiline_double_quote_password,
    curl_multiline_single_quote_password,
    curl_multiline_ansi_quote_password,
    curl_multiline_locale_quote_password,
    "ansi curl secret",
    "locale curl secret",
    r"escaped\ curl\ secret",
    "concat curl secret",
    "PRIVATE KEY",
    "private-key-secret-material",
    "@codex",
]:
    assert leaked not in failure_body, failure_body
assert "@<!-- -->codex" in failure_body
assert "[redacted-secret]" in failure_body

err = mod.parse_openrouter_error('{"error":{"message":"Provider returned error","metadata":{"provider_name":"Venice","retry_after_seconds":21}}}')
assert err["provider"] == "Venice"
assert err["retry_after"] == 21

assert mod.is_safe_suggestion('token = os.getenv("OPENROUTER_TOKEN")')
assert not mod.is_safe_suggestion("Use environment variables for secrets.")


header_fallback_secret = "fallback header secret 12345"
header_command_secret = "command header secret 12345"
header_ansi_secret = "ansi header secret 12345"
header_line_continuation_secret = "header continuation secret 12345"
header_quoted_secret = "quoted header secret 12345"
escaped_quoted_header_secret = "escaped quoted header secret 12345"
header_fallback_expression = "${{ secrets.AUTH_TOKEN || '" + header_fallback_secret + "' }}"
header_command_expression = "$(printf '" + header_command_secret + "')"
header_ansi_expression = "$'" + header_ansi_secret + "'"
header_line_continuation = "\\" + "\n  " + header_line_continuation_secret
header_regression_cases = [
    (f"Authorization: Bearer {header_fallback_expression}", header_fallback_secret),
    (f"Proxy-Authorization: Basic {header_command_expression}", header_command_secret),
    (f"Authorization: Bearer {header_ansi_expression}", header_ansi_secret),
    (f"Authorization: Bearer {header_line_continuation}", header_line_continuation_secret),
    (f'Authorization: Bearer "{header_quoted_secret}"', header_quoted_secret),
    (f"Proxy-Authorization: Basic '{header_quoted_secret}'", header_quoted_secret),
    (f'Authorization: Bearer \\"{escaped_quoted_header_secret}\\"', escaped_quoted_header_secret),
    (f'Proxy-Authorization: Basic \\"{escaped_quoted_header_secret}\\"', escaped_quoted_header_secret),
]
for safe_quoted_header in [
    'Authorization: Bearer "${OPENROUTER_API_KEY}"',
    "Proxy-Authorization: Basic '${OPENROUTER_API_KEY}'",
    'Authorization: Bearer \\"${OPENROUTER_API_KEY}\\"',
]:
    assert mod.sanitize_text(safe_quoted_header, config) == safe_quoted_header

for header_form, header_secret in header_regression_cases:
    sanitized_header = mod.sanitize_text(header_form, config)
    assert header_secret not in sanitized_header, sanitized_header
    assert "[redacted-secret]" in sanitized_header, sanitized_header

curl_continuation_password = "continued curl secret 12345"
curl_proxy_continuation_password = "continued-proxy-curl-secret-12345"
curl_inline_continuation_password = "inline-continued-curl-secret-12345"
line_continuation = "\\" + "\n"
crlf_line_continuation = "\\" + "\r\n"
curl_continuation_cases = [
    (f'curl --user {line_continuation}  "dcoir:{curl_continuation_password}" https://example.test/', curl_continuation_password),
    (f"curl --proxy-user {crlf_line_continuation}  dcoir:{curl_proxy_continuation_password} https://example.test/", curl_proxy_continuation_password),
    (f"curl --user dcoir:{line_continuation}  {curl_inline_continuation_password} https://example.test/", curl_inline_continuation_password),
]
for curl_form, curl_secret in curl_continuation_cases:
    sanitized_curl = mod.sanitize_text(curl_form, config)
    assert curl_secret not in sanitized_curl, sanitized_curl
    assert "[redacted-secret]" in sanitized_curl, sanitized_curl

combined_regression_prompt = mod.build_prompt(
    {
        "number": 281,
        "title": "Continuation redaction",
        "body": "\n".join([
            f"Authorization: Bearer {header_fallback_expression}",
            f'Authorization: Bearer "{header_quoted_secret}"',
            f'Authorization: Bearer \\"{escaped_quoted_header_secret}\\"',
            f"Proxy-Authorization: Basic {header_command_expression}",
            f"curl --user dcoir:{line_continuation}  {curl_inline_continuation_password} https://example.test/",
        ]),
    },
    [],
    "",
    config,
)
for leaked in [
    header_fallback_secret,
    header_command_secret,
    header_ansi_secret,
    header_line_continuation_secret,
    header_quoted_secret,
    escaped_quoted_header_secret,
    curl_continuation_password,
    curl_proxy_continuation_password,
    curl_inline_continuation_password,
]:
    assert leaked not in combined_regression_prompt, combined_regression_prompt

print("offline selftest passed")
