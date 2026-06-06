#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$repo_root"

status=0
files_file="$(mktemp)"
trap 'rm -f "$files_file"' EXIT

if [ "$#" -gt 0 ]; then
  printf '%s\n' "$@" > "$files_file"
elif git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git ls-files > "$files_file"
else
  find . -type f \
    -not -path './.git/*' \
    -not -path './node_modules/*' \
    -not -path './dist/*' \
    -not -path './build/*' \
    | sed 's#^./##' > "$files_file"
fi

echo '[validate-codex-local] changed or selected files:'
sed -n '1,200p' "$files_file"

if command -v rg >/dev/null 2>&1; then
  echo '[validate-codex-local] secret-pattern scan'
  if rg -n --hidden \
    -g '!.git' \
    -g '!node_modules' \
    -g '!dist' \
    -g '!build' \
    -g '!vendor' \
    -e 'github_pat_[A-Za-z0-9_]{20,}' \
    -e 'ghp_[A-Za-z0-9_]{20,}' \
    -e 'gho_[A-Za-z0-9_]{20,}' \
    -e 'AKIA[0-9A-Z]{16}' \
    -e '-----BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY-----' \
    -e '(?i)(api[_-]?key|secret|token|password)[[:space:]]*[:=][[:space:]]*["'"'"']?[A-Za-z0-9_./+=-]{16,}' \
    .; then
    echo '[validate-codex-local] potential secret patterns found'
    status=1
  else
    echo '[validate-codex-local] no obvious secret patterns found'
  fi
else
  echo '[validate-codex-local] WARN: rg not available; skipping secret scan'
fi

if grep -Eq '\.sh$' "$files_file"; then
  echo '[validate-codex-local] shell checks'
  while IFS= read -r file; do
    [ -f "$file" ] || continue
    case "$file" in
      *.sh)
        if command -v shellcheck >/dev/null 2>&1; then shellcheck "$file" || status=1; fi
        if command -v shfmt >/dev/null 2>&1; then shfmt -d "$file" || status=1; fi
        ;;
    esac
  done < "$files_file"
fi

if grep -Eq '\.(yml|yaml)$' "$files_file"; then
  echo '[validate-codex-local] yaml checks'
  if command -v yamllint >/dev/null 2>&1; then
    while IFS= read -r file; do
      [ -f "$file" ] || continue
      case "$file" in
        *.yml|*.yaml) yamllint "$file" || status=1 ;;
      esac
    done < "$files_file"
  else
    echo '[validate-codex-local] WARN: yamllint not available'
  fi
fi

if grep -Eq '\.py$' "$files_file"; then
  echo '[validate-codex-local] python checks'
  if command -v ruff >/dev/null 2>&1; then ruff check . || status=1; else echo '[validate-codex-local] WARN: ruff not available'; fi
  if command -v bandit >/dev/null 2>&1; then bandit -q -r . -x ./.git,./.venv,./venv,./node_modules || status=1; else echo '[validate-codex-local] WARN: bandit not available'; fi
fi

if [ "${CODEX_RUN_SEMGREP:-0}" = "1" ] && command -v semgrep >/dev/null 2>&1; then
  echo '[validate-codex-local] semgrep checks'
  if [ -f .semgrep.yml ]; then
    semgrep --config .semgrep.yml . || status=1
  else
    echo '[validate-codex-local] WARN: CODEX_RUN_SEMGREP=1 but no .semgrep.yml exists; skipping semgrep to avoid remote rule dependency'
  fi
fi

if grep -Eq '\.(ps1|psm1|psd1)$' "$files_file"; then
  echo '[validate-codex-local] PowerShell parser checks'
  if command -v pwsh >/dev/null 2>&1; then
    pwsh -NoProfile -File scripts/validate-windows-powershell-51.ps1 -AllowPowerShell7 -AllowEmpty || status=1
  elif command -v powershell >/dev/null 2>&1; then
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-windows-powershell-51.ps1 -AllowEmpty || status=1
  else
    echo '[validate-codex-local] WARN: no PowerShell executable available'
  fi
fi

if [ -f scripts/validate-codeql-security-workflow.py ]; then
  echo '[validate-codex-local] CodeQL workflow config check'
  python3 scripts/validate-codeql-security-workflow.py || status=1
fi

git status --short || true
exit "$status"
