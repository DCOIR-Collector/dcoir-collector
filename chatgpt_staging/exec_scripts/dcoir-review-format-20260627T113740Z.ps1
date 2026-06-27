$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$RequestId = 'dcoir-review-format-20260627T113740Z'
$ReviewPath = 'scripts/openrouter_pr_review.py'
$SelftestPath = 'scripts/openrouter_pr_review_pareto_context_selftest.py'
$ScriptPath = "chatgpt_staging/exec_scripts/$RequestId.ps1"

function Replace-Once {
    param(
        [Parameter(Mandatory=$true)][string]$Text,
        [Parameter(Mandatory=$true)][string]$Old,
        [Parameter(Mandatory=$true)][string]$New,
        [Parameter(Mandatory=$true)][string]$Label
    )

    $candidates = @(
        @{ Old = $Old; New = $New },
        @{ Old = ($Old -replace "`r`n", "`n"); New = ($New -replace "`r`n", "`n") },
        @{ Old = ($Old -replace "`n", "`r`n"); New = ($New -replace "`n", "`r`n") }
    )

    foreach ($candidate in $candidates) {
        if ($Text.Contains([string]$candidate.Old)) {
            return $Text.Replace([string]$candidate.Old, [string]$candidate.New)
        }
    }

    throw "Missing patch anchor: $Label"
}

function Write-Utf8NoBom {
    param(
        [Parameter(Mandatory=$true)][string]$Path,
        [Parameter(Mandatory=$true)][string]$Text
    )
    $resolved = (Resolve-Path -LiteralPath $Path).Path
    [System.IO.File]::WriteAllText($resolved, $Text, [System.Text.UTF8Encoding]::new($false))
}

git config user.name 'github-actions[bot]'
git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
git pull --ff-only origin main

$review = Get-Content -Raw -LiteralPath $ReviewPath -Encoding UTF8
$oldValidation = @'
def is_validation_command(text: str) -> bool:
    stripped = text.strip()
    return any(stripped.startswith(prefix) for prefix in VALIDATION_COMMAND_PREFIXES)
'@
$newValidation = @'
def has_balanced_command_quotes(text: str) -> bool:
    quote = ""
    escaped = False
    for char in text:
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if quote:
            if char == quote:
                quote = ""
            continue
        if char in {"\"", "'"}:
            quote = char
    return not quote


def is_validation_command(text: str) -> bool:
    stripped = text.strip()
    return has_balanced_command_quotes(stripped) and any(stripped.startswith(prefix) for prefix in VALIDATION_COMMAND_PREFIXES)
'@
$review = Replace-Once -Text $review -Old $oldValidation -New $newValidation -Label 'validation quote guard'

$buildInlineMarker = @'
def build_inline_comment(finding: dict[str, Any], model_used: str, config: Config) -> str:
'@
$fixGuidanceHelpers = @'
def strip_markdown_fence_lines(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        if line.strip().startswith(("```", "~~~")):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def fix_guidance_value_text(value: Any, config: Config, *, neutralize_mentions: bool = False) -> str:
    return strip_markdown_fence_lines(
        sanitize_github_output(str(value or "").strip(), config, neutralize_mentions=neutralize_mentions)
    )


'@ + $buildInlineMarker
$review = Replace-Once -Text $review -Old $buildInlineMarker -New $fixGuidanceHelpers -Label 'fix guidance helper insertion'

$oldLanguage = '        language = sanitize_github_output(str(fix_guidance.get("language", "text") or "text").strip(), config)'
$newLanguage = @'
        language = sanitize_github_output(str(fix_guidance.get("language", "text") or "text").strip(), config)
        if not re.fullmatch(r"[A-Za-z0-9_+.-]{1,32}", language):
            language = "text"
'@
$review = Replace-Once -Text $review -Old $oldLanguage -New $newLanguage -Label 'fix guidance language guard'

$oldValueBlock = @'
            value = sanitize_github_output(
                str(fix_guidance.get(key, "") or "").strip(),
                config,
                neutralize_mentions=False,
            )
'@
$newValueBlock = @'
            value = fix_guidance_value_text(fix_guidance.get(key, ""), config, neutralize_mentions=False)
'@
$review = Replace-Once -Text $review -Old $oldValueBlock -New $newValueBlock -Label 'fix guidance value sanitizer'

$oldNotes = '        notes = sanitize_github_output(str(fix_guidance.get("notes", "") or "").strip(), config)'
$newNotes = '        notes = fix_guidance_value_text(fix_guidance.get("notes", ""), config)'
$review = Replace-Once -Text $review -Old $oldNotes -New $newNotes -Label 'fix guidance notes sanitizer'
Write-Utf8NoBom -Path $ReviewPath -Text $review

$selftest = Get-Content -Raw -LiteralPath $SelftestPath -Encoding UTF8
$oldSelftestAnchor = @'
assert "```suggestion" not in fallback_fix_comment

try:
'@
$newSelftestBlock = @'
assert "```suggestion" not in fallback_fix_comment

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

try:
'@
$selftest = Replace-Once -Text $selftest -Old $oldSelftestAnchor -New $newSelftestBlock -Label 'selftest malformed guidance guard'
Write-Utf8NoBom -Path $SelftestPath -Text $selftest

if (Test-Path -LiteralPath $ScriptPath -PathType Leaf) {
    Remove-Item -LiteralPath $ScriptPath -Force -ErrorAction Stop
}

python -m py_compile scripts/openrouter_pr_review.py scripts/openrouter_pr_review_pareto_context.py scripts/openrouter_pr_review_pareto_context_selftest.py
python scripts/openrouter_pr_review_pareto_context_selftest.py
git diff --check

git add $ReviewPath $SelftestPath $ScriptPath
git diff --cached --check
git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
    throw 'No staged source changes were produced.'
}

git commit -m 'Harden dcoir-review repair formatting'
git push origin HEAD:main

git status --short
