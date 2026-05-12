$ErrorActionPreference = 'Stop'
$repo = $env:DCOIR_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repo)) { throw 'DCOIR_REPO_ROOT is not set' }
Set-Location $repo

git config user.name 'chatgpt-exec'
git config user.email 'chatgpt-exec@users.noreply.github.com'
git pull --ff-only origin main

# Reuse v001 for patching and validation, then stage repo-relative paths explicitly.
& .\chatgpt_staging\exec_scripts\gemini_generated_prime_migration_001.ps1

$paths = @(
  'project_sources/gemini/bundle_source/Gemini_Bundle_Source_Manifest.json',
  'project_sources/gemini/tools/build_dcoir_gemini_release.py',
  'project_sources/gemini/tools/compile_dcoir_gemini_bundle.py',
  'project_sources/gemini/tools/validate_dcoir_gemini_bundle.py',
  'project_sources/gemini/docs/DOC-10_DCOIR_Gemini_Stored_Source_And_Compile_Strategy_v1_0_0.txt',
  'project_sources/gemini/docs/DOC-11_DCOIR_Gemini_Creation_Pipeline_v1_0_0.txt',
  'project_sources/gemini/bundle_source/01_GEMINI_AGENT_BUILD/Prime_Agent_DCOIR_Gemini_Orchestrator.md.txt'
)

git add -- $paths

if (git diff --cached --quiet) {
  Write-Host 'No Gemini generated-prime migration changes to commit.'
} else {
  git commit -m 'Make Gemini prime agent generated from chunk source'
  git push origin HEAD:main
}
