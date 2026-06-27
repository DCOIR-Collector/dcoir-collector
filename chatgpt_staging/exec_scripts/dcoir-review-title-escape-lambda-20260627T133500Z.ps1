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

    $patchPath = Join-Path $env:TEMP 'dcoir_review_title_escape_lambda.py'
@'
from pathlib import Path

path = Path("scripts/openrouter_pr_review.py")
lines = path.read_text(encoding="utf-8").splitlines()
old_count = 0
new_lines = []
replacement = '    return re.sub(r"([*_`])", lambda match: "\\\\" + match.group(1), text)'
for line in lines:
    if line.strip().startswith('return re.sub(r"([*_`])"'):
        new_lines.append(replacement)
        old_count += 1
    else:
        new_lines.append(line)
if old_count != 1:
    raise SystemExit(f"Expected exactly one markdown escape return line, found {old_count}")
path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
'@ | Set-Content -LiteralPath $patchPath -Encoding UTF8

    Invoke-Native -FilePath 'python' -ArgumentList @($patchPath)
    Invoke-Native -FilePath 'python' -ArgumentList @('-m', 'py_compile', 'scripts/openrouter_pr_review.py')
    Invoke-Native -FilePath 'git' -ArgumentList @('diff', '--check', '--', 'scripts/openrouter_pr_review.py')
    Invoke-Native -FilePath 'git' -ArgumentList @('diff', '--', 'scripts/openrouter_pr_review.py')
    Invoke-Native -FilePath 'git' -ArgumentList @('status', '--short')

    & git rm --quiet --ignore-unmatch -- 'chatgpt_staging/exec_scripts/dcoir-review-title-escape-lambda-20260627T133500Z.ps1'
    Invoke-Native -FilePath 'git' -ArgumentList @('add', 'scripts/openrouter_pr_review.py')
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
    Invoke-Native -FilePath 'git' -ArgumentList @('commit', '-m', 'Fix dcoir-review title escaping')
    Invoke-Native -FilePath 'git' -ArgumentList @('push', 'origin', 'HEAD:main')
    exit 0
}
catch {
    Write-Error ($_ | Out-String)
    exit 1
}
