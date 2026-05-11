$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$RequestId = 'applyin-20260511-gemini-usb-subagent-clean-001'
$PayloadPath = "chatgpt_staging/in/$RequestId/payload.zip.b64"
$WorkRoot = "chatgpt_staging/work/$RequestId-repair"
$ZipPath = Join-Path $WorkRoot 'payload.zip'
$ExtractRoot = Join-Path $WorkRoot 'extract'
$NewZipPath = Join-Path $WorkRoot 'payload.repaired.zip'

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
from pathlib import Path, PurePosixPath

request_id = 'applyin-20260511-gemini-usb-subagent-clean-001'
payload_path = Path('chatgpt_staging/in') / request_id / 'payload.zip.b64'
work_root = Path('chatgpt_staging/work') / f'{request_id}-repair'
zip_path = work_root / 'payload.zip'
extract_root = work_root / 'extract'
new_zip_path = work_root / 'payload.repaired.zip'

raw = payload_path.read_text(encoding='ascii')
clean = ''.join(raw.split())
blob = base64.b64decode(clean, validate=True)
if not blob.startswith(b'PK'):
    raise SystemExit('decoded payload is not a ZIP')
zip_path.write_bytes(blob)
shutil.unpack_archive(str(zip_path), str(extract_root), 'zip')
manifest_path = extract_root / 'apply_manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
if manifest.get('schema') != 'dcoir.chatgpt_staging.apply_manifest.v1':
    raise SystemExit('unexpected apply manifest schema')

updated = []
for item in manifest.get('files', []):
    target = item.get('path', '')
    if not target or target.startswith('/') or '..' in PurePosixPath(target).parts:
        raise SystemExit(f'unsafe target path in manifest: {target!r}')
    source = item.get('source', '')
    src_path = extract_root / source
    if not src_path.is_file():
        raise SystemExit(f'missing source file in payload: {source}')
    expected_new = item.get('expected_new_sha256')
    actual_new = hashlib.sha256(src_path.read_bytes()).hexdigest()
    if expected_new != actual_new:
        raise SystemExit(f'new sha mismatch for {target}: expected {expected_new}, got {actual_new}')
    if item.get('create_only'):
        continue
    current = subprocess.check_output(['git', 'show', f'HEAD:{target}'])
    item['expected_current_sha256'] = hashlib.sha256(current).hexdigest()
    updated.append(target)

manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8', newline='\n')
with zipfile.ZipFile(new_zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
    zf.write(manifest_path, 'apply_manifest.json')
    files_root = extract_root / 'files'
    for path in sorted(files_root.rglob('*')):
        if path.is_file():
            rel = path.relative_to(extract_root).as_posix()
            zf.write(path, rel)

with zipfile.ZipFile(new_zip_path, 'r') as zf:
    names = zf.namelist()
    if 'apply_manifest.json' not in names or not any(n.startswith('files/') for n in names):
        raise SystemExit('repaired ZIP shape invalid')

new_blob = new_zip_path.read_bytes()
payload_path.write_text(base64.b64encode(new_blob).decode('ascii') + '\n', encoding='ascii')
round_trip = base64.b64decode(''.join(payload_path.read_text(encoding='ascii').split()), validate=True)
if round_trip != new_blob:
    raise SystemExit('base64 round trip failed')

report = {
    'request_id': request_id,
    'payload_path': str(payload_path),
    'updated_expected_current_hashes': updated,
    'zip_size_bytes': len(new_blob),
    'payload_b64_size_bytes': payload_path.stat().st_size,
    'payload_b64_sha256': hashlib.sha256(payload_path.read_bytes()).hexdigest(),
}
report_path = work_root / 'repair_report.json'
report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2))
'@

$ScriptPath = Join-Path $WorkRoot 'repair_payload.py'
New-Item -ItemType Directory -Force -Path $WorkRoot | Out-Null
$python | Out-File -FilePath $ScriptPath -Encoding utf8
python $ScriptPath
if ($LASTEXITCODE -ne 0) { throw 'payload hash repair failed' }

$payloadText = Get-Content -LiteralPath $PayloadPath -Raw -Encoding ASCII
$compact = ($payloadText -split '\s+') -join ''
if (($compact.Length % 4) -ne 0) { throw 'repaired payload has invalid base64 length' }
[Convert]::FromBase64String($compact) | Out-Null

if ($env:DCOIR_DOWNLOADS_DIR) {
  New-Item -ItemType Directory -Force -Path $env:DCOIR_DOWNLOADS_DIR | Out-Null
  Copy-Item -LiteralPath (Join-Path $WorkRoot 'repair_report.json') -Destination (Join-Path $env:DCOIR_DOWNLOADS_DIR 'repair_report.json') -Force
}

git config user.name 'github-actions[bot]'
git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
git add -- $PayloadPath
$staged = git diff --cached --name-only
if (-not ($staged -contains $PayloadPath)) { throw 'repaired payload was not staged' }
git commit -m 'Repair USB Gemini apply-in payload current hashes'
git push
Write-Host "Repaired and pushed $PayloadPath"
