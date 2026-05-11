$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$RequestId = 'applyin-20260511-gemini-usb-subagent-clean-001'
$PayloadPath = "chatgpt_staging/in/$RequestId/payload.zip.b64"
$WorkRoot = "chatgpt_staging/work/$RequestId-strip-workflow"
$ExtractRoot = Join-Path $WorkRoot 'extract'
$ZipPath = Join-Path $WorkRoot 'payload.zip'
$NewZipPath = Join-Path $WorkRoot 'payload.no-workflow.zip'

Remove-Item -LiteralPath $WorkRoot -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $ExtractRoot | Out-Null

$python = @'
from __future__ import annotations

import base64
import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

request_id = 'applyin-20260511-gemini-usb-subagent-clean-001'
payload_path = Path('chatgpt_staging/in') / request_id / 'payload.zip.b64'
work_root = Path('chatgpt_staging/work') / f'{request_id}-strip-workflow'
extract_root = work_root / 'extract'
zip_path = work_root / 'payload.zip'
new_zip_path = work_root / 'payload.no-workflow.zip'
workflow_target = '.github/workflows/validate-on-push.yml'
workflow_source = 'files/.github/workflows/validate-on-push.yml'

clean = ''.join(payload_path.read_text(encoding='ascii').split())
blob = base64.b64decode(clean, validate=True)
if not blob.startswith(b'PK'):
    raise SystemExit('decoded payload is not a ZIP')
zip_path.write_bytes(blob)
shutil.unpack_archive(str(zip_path), str(extract_root), 'zip')
manifest_path = extract_root / 'apply_manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
files = manifest.get('files', [])
kept = [item for item in files if item.get('path') != workflow_target]
removed = [item.get('path') for item in files if item.get('path') == workflow_target]
if not removed:
    raise SystemExit('workflow target was not present in payload manifest')
manifest['files'] = kept
allowed = [root for root in manifest.get('allowed_roots', []) if root != '.github/workflows']
manifest['allowed_roots'] = allowed
manifest['allow_workflow_changes'] = False
manifest.pop('workflow_change_reason', None)

# Refresh current hashes from the current repo checkout for all remaining existing targets.
for item in manifest.get('files', []):
    target = item['path']
    src_path = extract_root / item['source']
    if not src_path.is_file():
        raise SystemExit(f'missing payload source: {item["source"]}')
    new_sha = hashlib.sha256(src_path.read_bytes()).hexdigest()
    if item.get('expected_new_sha256') != new_sha:
        raise SystemExit(f'new sha mismatch for {target}')
    if not item.get('create_only'):
        current = subprocess.check_output(['git', 'show', f'HEAD:{target}'])
        item['expected_current_sha256'] = hashlib.sha256(current).hexdigest()

manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8', newline='\n')
workflow_payload_file = extract_root / workflow_source
if workflow_payload_file.exists():
    workflow_payload_file.unlink()

with zipfile.ZipFile(new_zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
    zf.write(manifest_path, 'apply_manifest.json')
    files_root = extract_root / 'files'
    for path in sorted(files_root.rglob('*')):
        if path.is_file():
            rel = path.relative_to(extract_root).as_posix()
            zf.write(path, rel)

with zipfile.ZipFile(new_zip_path, 'r') as zf:
    names = set(zf.namelist())
    if 'apply_manifest.json' not in names:
        raise SystemExit('missing apply_manifest.json in repaired zip')
    if workflow_source in names:
        raise SystemExit('workflow source still present in repaired zip')

new_blob = new_zip_path.read_bytes()
payload_path.write_text(base64.b64encode(new_blob).decode('ascii') + '\n', encoding='ascii')
round_trip = base64.b64decode(''.join(payload_path.read_text(encoding='ascii').split()), validate=True)
if round_trip != new_blob:
    raise SystemExit('payload base64 round-trip failed')
report = {
    'request_id': request_id,
    'payload_path': str(payload_path),
    'removed_targets': removed,
    'remaining_file_count': len(kept),
    'allowed_roots': manifest.get('allowed_roots', []),
    'payload_b64_sha256': hashlib.sha256(payload_path.read_bytes()).hexdigest(),
}
(work_root / 'strip_workflow_report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2))
'@

$ScriptPath = Join-Path $WorkRoot 'strip_workflow.py'
New-Item -ItemType Directory -Force -Path $WorkRoot | Out-Null
$python | Out-File -FilePath $ScriptPath -Encoding utf8
python $ScriptPath
if ($LASTEXITCODE -ne 0) { throw 'strip workflow payload repair failed' }

$payloadText = Get-Content -LiteralPath $PayloadPath -Raw -Encoding ASCII
$compact = ($payloadText -split '\s+') -join ''
if (($compact.Length % 4) -ne 0) { throw 'payload base64 length invalid after workflow strip' }
[Convert]::FromBase64String($compact) | Out-Null

if ($env:DCOIR_DOWNLOADS_DIR) {
  New-Item -ItemType Directory -Force -Path $env:DCOIR_DOWNLOADS_DIR | Out-Null
  Copy-Item -LiteralPath (Join-Path $WorkRoot 'strip_workflow_report.json') -Destination (Join-Path $env:DCOIR_DOWNLOADS_DIR 'strip_workflow_report.json') -Force
}

git config user.name 'github-actions[bot]'
git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
git add -- $PayloadPath
git commit -m 'Remove workflow file from USB Gemini apply-in payload'
git push
Write-Host 'Repaired payload by removing workflow-file target.'
