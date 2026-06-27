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

    $patchPath = Join-Path $env:TEMP 'dcoir_review_runtime_format_hook.py'
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
'@ | Set-Content -LiteralPath $patchPath -Encoding UTF8

    Invoke-Native -FilePath 'python' -ArgumentList @($patchPath)
    Invoke-Native -FilePath 'python' -ArgumentList @('-m', 'py_compile', 'scripts/openrouter_pr_review.py', 'scripts/openrouter_pr_review_pareto_context.py')
    Invoke-Native -FilePath 'git' -ArgumentList @('diff', '--check', '--', 'scripts/openrouter_pr_review.py', 'scripts/openrouter_pr_review_pareto_context.py')
    Invoke-Native -FilePath 'git' -ArgumentList @('diff', '--', 'scripts/openrouter_pr_review.py', 'scripts/openrouter_pr_review_pareto_context.py')
    Invoke-Native -FilePath 'git' -ArgumentList @('status', '--short')

    & git rm --quiet --ignore-unmatch -- 'chatgpt_staging/exec_requests/dcoir-review-format-eval-hook-20260627T131744Z.json'
    & git rm --quiet --ignore-unmatch -- 'chatgpt_staging/exec_requests/dcoir-review-format-eval-hook-20260627T132500Z.json'
    & git rm --quiet --ignore-unmatch -- 'chatgpt_staging/exec_scripts/dcoir-review-format-eval-hook-20260627T131744Z.ps1'
    & git rm --quiet --ignore-unmatch -- 'chatgpt_staging/exec_scripts/dcoir-review-format-eval-hook-20260627T132500Z.ps1'
    & git rm --quiet --ignore-unmatch -- 'chatgpt_staging/exec_scripts/dcoir-review-runtime-format-hook-20260627T133000Z.ps1'

    Invoke-Native -FilePath 'git' -ArgumentList @('add', 'scripts/openrouter_pr_review.py', 'scripts/openrouter_pr_review_pareto_context.py')
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
    Invoke-Native -FilePath 'git' -ArgumentList @('commit', '-m', 'Harden dcoir-review runtime formatting')
    Invoke-Native -FilePath 'git' -ArgumentList @('push', 'origin', 'HEAD:main')
    exit 0
}
catch {
    Write-Error ($_ | Out-String)
    exit 1
}
