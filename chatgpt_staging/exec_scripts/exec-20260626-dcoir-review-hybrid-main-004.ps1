$ErrorActionPreference = 'Stop'
$innerScript = 'chatgpt_staging/exec_scripts/exec-20260626-dcoir-review-hybrid-main-003.ps1'
$trackedPaths = @(
  'scripts/openrouter_pr_review_pareto_context.py',
  '.github/openrouter-pr-review-pareto.yml',
  'scripts/openrouter_pr_review_pareto_context_selftest.py',
  'ops/requests/apply_patch/README.md',
  'ops/requests/apply_patch/20260626-dcoir-review-script-budget-001'
)

try {
  & $innerScript
  if ($LASTEXITCODE -ne 0) {
    throw "inner script exited with code $LASTEXITCODE"
  }
} catch {
  Write-Error "DCOIR review hybrid direct update failed: $($_.Exception.Message)"
  Write-Host '--- git status before cleanup ---'
  git status --short
  Write-Host '--- restoring tracked source/staging paths so chatgpt-exec can publish artifacts ---'
  git restore --staged --worktree -- $trackedPaths
  Write-Host '--- git status after cleanup ---'
  git status --short
  exit 1
}
