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
        "path": "collector/token_probe.py",
        "body": f'The changed line assigns token = "{secret_like}", password={punctuation_password}, and Authorization: Bearer "{bearer_secret}" plus Authorization: Bearer \\"{bearer_secret}\\". Ask @codex to review.',
        "suggested_replacement": 'token = os.getenv("OPENROUTER_TOKEN")',
        "validation": "python3 -m py_compile collector/token_probe.py",
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
assert "python3 -m py_compile collector/token_probe.py" in comment
assert "bandit -r collector/token_probe.py" in comment
ps_comment = mod.build_inline_comment(
    {
        "title": "Unsafe PowerShell path write",
        "severity": "high",
        "confidence": 0.95,
        "path": "tools/probe.ps1",
        "body": "Set-Content writes to a request-controlled path.",
        "suggested_replacement": "",
        "validation": "",
    },
    "openrouter/free",
    config,
)
assert 'PSParser]::Tokenize((Get-Content -Raw -LiteralPath "tools/probe.ps1")' in ps_comment
assert 'Invoke-ScriptAnalyzer -Path "tools/probe.ps1"' in ps_comment
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
sanitized_progress_identity = mod.sanitize_github_output(
    "openrouter openrouter-attempt openrouter-result openrouter-retry openrouter/pareto-code",
    config,
)
assert sanitized_progress_identity == "provider provider-attempt provider-result provider-retry provider/pareto-code"
with tempfile.TemporaryDirectory() as tmp:
    previous_debug_artifact_dir = os.environ.get("DCOIR_REVIEW_DEBUG_ARTIFACT_DIR")
    os.environ["DCOIR_REVIEW_DEBUG_ARTIFACT_DIR"] = tmp
    try:
        quiet_path = mod.write_debug_text_artifact(config, "quiet.txt", "quiet output")
        assert quiet_path is None
        assert not (Path(tmp) / "quiet.txt").exists()

        debug_path = mod.write_debug_text_artifact(
            debug_config,
            "prompts/01-initial-prompt.txt",
            f"OpenRouter prompt with OPENROUTER_API_KEY={openrouter_key}; ask @codex to inspect",
        )
        assert debug_path == (Path(tmp) / "prompts/01-initial-prompt.txt").resolve(strict=False)
        debug_text = debug_path.read_text(encoding="utf-8")
        assert "OpenRouter" not in debug_text
        assert openrouter_key not in debug_text
        assert "REVIEW_PROVIDER_API_KEY" in debug_text
        assert "@<!-- -->codex" in debug_text

        json_path = mod.write_debug_json_artifact(
            debug_config,
            "metadata/review-context.json",
            {"provider": "OpenRouter", "secret": openrouter_key, "items": ["openrouter", "@codex"]},
        )
        debug_json = json.loads(json_path.read_text(encoding="utf-8"))
        assert debug_json["provider"] == "review provider"
        assert debug_json["secret"] == "[redacted-secret]"
        assert debug_json["items"] == ["provider", "@<!-- -->codex"]

        try:
            mod.write_debug_text_artifact(debug_config, "../escape.txt", "escape")
        except ValueError as exc:
            assert "unsafe debug artifact name" in str(exc)
        else:
            raise AssertionError("debug artifact path traversal should be rejected")
    finally:
        if previous_debug_artifact_dir is None:
            os.environ.pop("DCOIR_REVIEW_DEBUG_ARTIFACT_DIR", None)
        else:
            os.environ["DCOIR_REVIEW_DEBUG_ARTIFACT_DIR"] = previous_debug_artifact_dir

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
