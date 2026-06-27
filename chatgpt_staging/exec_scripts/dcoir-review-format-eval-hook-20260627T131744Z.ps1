$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

try {
    function Invoke-Native {
        param(
            [Parameter(Mandatory = $true)][string]$FilePath,
            [string[]]$ArgumentList = @()
        )
        & $FilePath @ArgumentList
        if ($LASTEXITCODE -ne 0) {
            throw ('Command failed with exit code {0}: {1} {2}' -f $LASTEXITCODE, $FilePath, ($ArgumentList -join ' '))
        }
    }

    $patchPath = Join-Path $env:TEMP 'dcoir_review_format_eval_hook.py'
@'
from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"Expected patch anchor not found in {path}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


base_path = "scripts/openrouter_pr_review.py"
replace_once(
    base_path,
    '''def fix_guidance_value_text(value: Any, config: Config, *, neutralize_mentions: bool = False) -> str:
    return strip_markdown_fence_lines(
        sanitize_github_output(str(value or "").strip(), config, neutralize_mentions=neutralize_mentions)
    )


def build_inline_comment(finding: dict[str, Any], model_used: str, config: Config) -> str:
''',
    '''def fix_guidance_value_text(value: Any, config: Config, *, neutralize_mentions: bool = False) -> str:
    return strip_markdown_fence_lines(
        sanitize_github_output(str(value or "").strip(), config, neutralize_mentions=neutralize_mentions)
    )


def markdown_emphasis_safe_text(value: str) -> str:
    text = " ".join(str(value or "").strip().splitlines())
    return re.sub(r"([*_`])", r"\\\1", text)


def build_inline_comment(finding: dict[str, Any], model_used: str, config: Config) -> str:
''',
)
replace_once(
    base_path,
    '''    title = sanitize_github_output(str(finding.get("title", "Finding")).strip(), config)
    severity = str(finding.get("severity", "medium")).upper()
    confidence = float(finding.get("confidence", 0))
    body = sanitize_github_output(str(finding.get("body", "")).strip(), config)
''',
    '''    title = markdown_emphasis_safe_text(sanitize_github_output(str(finding.get("title", "Finding")).strip(), config))
    severity = markdown_emphasis_safe_text(str(finding.get("severity", "medium")).upper())
    confidence = float(finding.get("confidence", 0))
    body = sanitize_github_output(str(finding.get("body", "")).strip(), config)
''',
)

pareto_path = "scripts/openrouter_pr_review_pareto_context.py"
replace_once(
    pareto_path,
    '''    result, model_used, service_tier = hardened.openrouter_review(prompt, schema, config, reporter=None)
    hardened.write_debug_json_artifact_safely(
''',
    '''    result, model_used, service_tier = hardened.openrouter_review(prompt, schema, config, reporter=None)
    result = harden_python_dynamic_exec_fix_result(result, finding, path, line_text)
    hardened.write_debug_json_artifact_safely(
''',
)

selftest_path = "scripts/openrouter_pr_review_pareto_context_selftest.py"
replace_once(
    selftest_path,
    '''assert "```suggestion\\n    state = json.loads(raw_state)\\n```" in native_fix_comment

fallback_fix_comment = mod.base.build_inline_comment(
''',
    '''assert "```suggestion\\n    state = json.loads(raw_state)\\n```" in native_fix_comment

markdown_title_comment = mod.base.build_inline_comment(
    {
        "title": "Unsafe **bold** title with `code`",
        "severity": "high",
        "confidence": 0.95,
        "body": "The heading should keep model Markdown inert.",
        "validation": "python3 -m py_compile scripts/openrouter_pr_review.py",
        "suggested_replacement": "",
    },
    "test-model",
    config,
)
assert "**HIGH: Unsafe \\*\\*bold\\*\\* title with \\`code\\`**" in markdown_title_comment
assert "**HIGH: Unsafe **bold** title" not in markdown_title_comment

fallback_fix_comment = mod.base.build_inline_comment(
''',
)
replace_once(
    selftest_path,
    '''assert "ast.literal_eval" in eval_hardened_fix["replace"]
assert "Restricted globals make this safe" not in eval_hardened_fix["notes"]

try:
''',
    '''assert "ast.literal_eval" in eval_hardened_fix["replace"]
assert "Restricted globals make this safe" not in eval_hardened_fix["notes"]

original_openrouter_review = mod.hardened.openrouter_review
original_write_debug_text = mod.hardened.write_debug_text_artifact_safely
original_write_debug_json = mod.hardened.write_debug_json_artifact_safely
try:
    mod.hardened.openrouter_review = lambda *_args, **_kwargs: (
        {
            "suggested_replacement": "    return eval(expression, {'__builtins__': {}}, {})",
            "replace": "Replace with restricted eval.",
            "notes": "Restricted globals make this safe.",
        },
        "test-model",
        "test-tier",
    )
    mod.hardened.write_debug_text_artifact_safely = lambda *_args, **_kwargs: None
    mod.hardened.write_debug_json_artifact_safely = lambda *_args, **_kwargs: None
    synthesized_eval = mod.synthesize_fix_for_finding(
        1,
        {
            "title": "Arbitrary Python code execution via eval on caller-controlled expression",
            "severity": "critical",
            "confidence": 0.99,
            "path": "probe.py",
            "line": 2,
            "body": "eval runs caller-controlled code.",
            "validation": "python3 -m py_compile probe.py",
        },
        "def evaluate_operator_expression(expression):\\n    return eval(expression, {'__builtins__': __builtins__, 'os': os})\\n",
        {},
        config,
    )
finally:
    mod.hardened.openrouter_review = original_openrouter_review
    mod.hardened.write_debug_text_artifact_safely = original_write_debug_text
    mod.hardened.write_debug_json_artifact_safely = original_write_debug_json
assert synthesized_eval.get("suggested_replacement", "") == ""
assert "fix_guidance" in synthesized_eval
assert "eval(" not in synthesized_eval["fix_guidance"]["replace"]
assert "exec(" not in synthesized_eval["fix_guidance"]["replace"]
assert "Restricted globals make this safe" not in synthesized_eval["fix_guidance"].get("notes", "")

try:
''',
)
'@ | Set-Content -LiteralPath $patchPath -Encoding UTF8

    Invoke-Native -FilePath 'python' -ArgumentList @($patchPath)
    Invoke-Native -FilePath 'python' -ArgumentList @('-m', 'py_compile', 'scripts/openrouter_pr_review.py', 'scripts/openrouter_pr_review_pareto_context.py', 'scripts/openrouter_pr_review_pareto_context_selftest.py')
    Invoke-Native -FilePath 'python' -ArgumentList @('scripts/openrouter_pr_review_pareto_context_selftest.py')
    Invoke-Native -FilePath 'git' -ArgumentList @('diff', '--check', '--', 'scripts/openrouter_pr_review.py', 'scripts/openrouter_pr_review_pareto_context.py', 'scripts/openrouter_pr_review_pareto_context_selftest.py')
    Invoke-Native -FilePath 'git' -ArgumentList @('diff', '--', 'scripts/openrouter_pr_review.py', 'scripts/openrouter_pr_review_pareto_context.py', 'scripts/openrouter_pr_review_pareto_context_selftest.py')
    Invoke-Native -FilePath 'git' -ArgumentList @('status', '--short')

    & git rm --quiet -- 'chatgpt_staging/exec_scripts/dcoir-review-format-eval-hook-20260627T131744Z.ps1'
    if ($LASTEXITCODE -ne 0) { throw ('git rm failed for current script with exit code {0}' -f $LASTEXITCODE) }

    & git diff --cached --quiet
    $stagedBeforeAdd = $LASTEXITCODE
    Invoke-Native -FilePath 'git' -ArgumentList @('add', 'scripts/openrouter_pr_review.py', 'scripts/openrouter_pr_review_pareto_context.py', 'scripts/openrouter_pr_review_pareto_context_selftest.py')
    & git diff --cached --quiet
    $diffExit = $LASTEXITCODE
    if ($diffExit -eq 0) {
        Write-Host 'No source or cleanup changes detected after patch; nothing to commit.'
        exit 0
    }
    if ($diffExit -ne 1) {
        throw ('git diff --cached --quiet failed with exit code {0}' -f $diffExit)
    }

    Invoke-Native -FilePath 'git' -ArgumentList @('config', 'user.name', 'dcoir-chatgpt-exec')
    Invoke-Native -FilePath 'git' -ArgumentList @('config', 'user.email', 'dcoir-chatgpt-exec@users.noreply.github.com')
    Invoke-Native -FilePath 'git' -ArgumentList @('commit', '-m', 'Harden dcoir-review fix comments')
    Invoke-Native -FilePath 'git' -ArgumentList @('push', 'origin', 'HEAD:main')
    exit 0
}
catch {
    Write-Error ($_ | Out-String)
    exit 1
}
