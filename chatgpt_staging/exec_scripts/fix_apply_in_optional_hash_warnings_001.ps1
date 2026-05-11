$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$path = '.github/workflows/chatgpt-apply-in.yml'
$text = Get-Content -LiteralPath $path -Raw -Encoding UTF8
$old = @'
          pwsh -NoProfile -File .github/scripts/Invoke-ChatGptReportPush.ps1 \
            -CommitMessage "Apply ChatGPT staging bundle and report [skip ci]" \
            -Paths "chatgpt_staging/apply_reports" "$REPORT_DIR" "$PAYLOAD" "chatgpt_staging/work/applied_paths.txt" "chatgpt_staging/work/deleted_paths.txt" "chatgpt_staging/work/hash_warnings.txt"
'@
$new = @'
          report_paths=(
            "chatgpt_staging/apply_reports"
            "$REPORT_DIR"
            "$PAYLOAD"
            "chatgpt_staging/work/applied_paths.txt"
            "chatgpt_staging/work/deleted_paths.txt"
          )
          if [[ -f chatgpt_staging/work/hash_warnings.txt ]]; then
            report_paths+=("chatgpt_staging/work/hash_warnings.txt")
          fi
          pwsh -NoProfile -File .github/scripts/Invoke-ChatGptReportPush.ps1 \
            -CommitMessage "Apply ChatGPT staging bundle and report [skip ci]" \
            -Paths "${report_paths[@]}"
'@
if (-not $text.Contains($old)) { throw 'Expected apply-in commit helper block not found.' }
$text = $text.Replace($old, $new)
Set-Content -LiteralPath $path -Value $text -Encoding UTF8

if (-not ((Get-Content -LiteralPath $path -Raw -Encoding UTF8).Contains('report_paths=('))) { throw 'Patch verification failed.' }

git config user.name 'github-actions[bot]'
git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
git add -- $path
git commit -m 'Make apply-in hash warnings path optional'
git push
Write-Host 'Updated chatgpt-apply-in optional hash_warnings path handling.'
