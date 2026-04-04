#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import zipfile
from zipfile import BadZipFile
from pathlib import Path
from typing import Any, Dict, List

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
PACKAGED_CONTRACT_PATH = SKILL_ROOT / "references" / "project_discovery_contract.json"
REPO_CONTRACT_PATH = Path("dcoir_skills/project_discovery_contract.json")

def load_project_contract(source_dir: Path) -> dict[str, Any]:
    repo_contract = source_dir / REPO_CONTRACT_PATH
    candidate = repo_contract if repo_contract.exists() else PACKAGED_CONTRACT_PATH
    return json.loads(candidate.read_text(encoding="utf-8"))

CONTRACT = json.loads(PACKAGED_CONTRACT_PATH.read_text(encoding="utf-8"))
MANIFEST_SECTION_KEYS = CONTRACT.get("manifest_sections", {})
CURRENT_MANIFEST_HEADINGS = CONTRACT.get("current_prose_headings", {})

MANIFEST_SECTION_KEYS = {
    "CURRENT GOVERNED GITHUB READABLE SOURCES": "governed_github_readable_sources",
    "CURRENT GOVERNED KNOWLEDGE SOURCES IN GITHUB": "governed_knowledge_sources",
    "CURRENT GOVERNED SETTINGS MIRRORS IN GITHUB": "governed_settings_mirrors",
    "CURRENT SUPPORTING ASSETS IN GITHUB": "supporting_assets",
}

CURRENT_MANIFEST_HEADINGS = CONTRACT.get("current_prose_headings", CURRENT_MANIFEST_HEADINGS)

DOC_TITLES = [
    "Knowledge - 01 - Overview and About.md.txt",
    "Knowledge - 02 - Elastic Quick Start.md.txt",
    "Knowledge - 03 - Local Test and Regression.md.txt",
    "Knowledge - 04 - Tier 1 Collect Runbook.md.txt",
    "Knowledge - 05 - Tier 2 Collect Runbook.md.txt",
    "Knowledge - 06 - Enrichment Actions.md.txt",
    "Knowledge - 07 - Artifact Review Guide.md.txt",
    "Knowledge - 08 - Troubleshooting.md.txt",
    "Knowledge - 09 - FAQ.md.txt",
    "Knowledge - 10 - AI Prompt and Agent Design.md.txt",
]

KNOWLEDGE_RE = re.compile(r"^Knowledge - \d{2} - .+\.(?:docx|md\.txt)$", re.IGNORECASE)
TOOL_DOC_MAP = {
    "accesschk": {"family": "AccessChk", "doc_hint": "accesschk"},
    "autorunsc": {"family": "Autoruns/Autorunsc", "doc_hint": "autoruns"},
    "handle": {"family": "Handle", "doc_hint": "handle"},
    "listdlls": {"family": "ListDLLs", "doc_hint": "listdlls"},
    "pipelist": {"family": "PipeList", "doc_hint": "pipelist"},
    "pslist": {"family": "PsList", "doc_hint": "pslist"},
    "sigcheck": {"family": "Sigcheck", "doc_hint": "sigcheck"},
    "streams": {"family": "Streams", "doc_hint": "streams"},
    "strings": {"family": "Strings", "doc_hint": "strings"},
    "tcpvcon": {"family": "TCPView/Tcpvcon", "doc_hint": "tcpview"},
}

CONTROL_FILE_CANDIDATES = {k: v for k, v in CONTRACT.get("control_file_roles", {}).items() if k in {"manifest", "change_log"}}


def runtime_download_name(filename: str) -> str | None:
    if filename.endswith(('.ps1', '.cmd', '.json', '.xml')):
        return filename
    if filename.endswith(('.ps1.txt', '.cmd.txt', '.json.txt', '.xml.txt')):
        return filename[:-4]
    return None



def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()



def resolve_existing_file(source_dir: Path, candidates: List[str]) -> Path:
    for name in candidates:
        path = source_dir / name
        if path.exists():
            return path
    raise FileNotFoundError(', '.join(candidates))



def parse_manifest(path: Path) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        'governed_github_readable_sources': [],
        'governed_knowledge_sources': [],
        'governed_settings_mirrors': [],
        'supporting_assets': [],
        'section_maps': {value: {} for value in MANIFEST_SECTION_KEYS.values()},
    }
    current_section = None
    lines = path.read_text(encoding='utf-8').splitlines()

    def record(section: str, key: str, filename: str) -> None:
        filename = filename.strip()
        if not filename or filename.endswith('/'):
            return
        bucket = data[section]
        if filename not in bucket:
            bucket.append(filename)
        data['section_maps'][section][key] = filename
        key_lower = key.strip().lower()
        if section == 'governed_github_readable_sources':
            if key_lower == 'runtime wrapper':
                data['section_maps'][section]['Collector_Current'] = filename
            elif key_lower == 'harness':
                data['section_maps'][section]['Harness_PS1_Current'] = filename
                data['section_maps'][section]['Harness_PS1_Project_Readable_Current'] = filename

    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line in MANIFEST_SECTION_KEYS:
            current_section = MANIFEST_SECTION_KEYS[line]
            continue
        lower = line.lower()
        if lower in CURRENT_MANIFEST_HEADINGS:
            current_section = CURRENT_MANIFEST_HEADINGS[lower]
            continue
        if line.endswith(':') and lower[:-1] in CURRENT_MANIFEST_HEADINGS:
            current_section = CURRENT_MANIFEST_HEADINGS[lower[:-1]]
            continue
        if line.isupper() and line not in MANIFEST_SECTION_KEYS:
            current_section = None
            continue
        if current_section and line.startswith('- '):
            payload = line[2:].strip()
            if ':' in payload:
                key, value = payload.split(':', 1)
                record(current_section, key.strip(), value.strip())
            else:
                record(current_section, payload, payload)
    return data



def resolve_current_source(source_dir: Path, manifest_data: Dict[str, Any], key_candidates: List[str], fallback_candidates: List[str]) -> Path:
    section_map = manifest_data.get('section_maps', {}).get('governed_github_readable_sources', {})
    for key in key_candidates:
        filename = section_map.get(key)
        if filename and (source_dir / filename).exists():
            return source_dir / filename
    return resolve_existing_file(source_dir, fallback_candidates)



def parse_powershell_params(text: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    start = text.find('param(')
    if start < 0:
        return out
    i = start + len('param(')
    depth = 1
    buf: List[str] = []
    while i < len(text) and depth > 0:
        ch = text[i]
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth == 0:
                break
        buf.append(ch)
        i += 1
    block = ''.join(buf)
    attr_lines: List[str] = []
    for raw in block.splitlines():
        line = raw.strip()
        if not line:
            continue
        pm = re.search(r"\[(?P<type>[^\]]+)\]\$(?P<name>[A-Za-z0-9_]+)(?:\s*=\s*(?P<default>.+?))?,?$", line)
        if not pm and line.startswith('['):
            attr_lines.append(line.rstrip(','))
            continue
        if pm:
            validates: List[str] = []
            attrs = ' '.join(attr_lines)
            vm = re.search(r"ValidateSet\((.*?)\)", attrs)
            if vm:
                validates = [x.strip().strip('"') for x in vm.group(1).split(',') if x.strip()]
            out.append({
                'name': pm.group('name'),
                'type': pm.group('type'),
                'default': (pm.group('default') or '').strip().rstrip(','),
                'attributes': attr_lines[:],
                'validate_set': validates,
            })
            attr_lines = []
    return out



def parse_quick_examples(text: str) -> List[str]:
    return [m.group(1).strip() for m in re.finditer(r'"\s+(powershell\.exe .*?)"', text)]



def parse_endpoint_examples(text: str) -> List[str]:
    return [m.group(1).strip() for m in re.finditer(r"Write-Output '([^']+execute --command [^']+)'", text)]



def inventory_collector_zip(path: Path | None) -> List[Dict[str, Any]]:
    if not path or not path.exists():
        return []
    tools: Dict[str, Dict[str, Any]] = {}
    try:
        with zipfile.ZipFile(path) as zf:
            for name in zf.namelist():
                base = os.path.basename(name)
                if not base.lower().endswith('.exe'):
                    continue
                stem = base[:-4].lower()
                normalized = re.sub(r'64$', '', stem)
                info = TOOL_DOC_MAP.get(normalized, {'family': normalized, 'doc_hint': normalized})
                row = tools.setdefault(normalized, {
                    'tool_key': normalized,
                    'tool_family': info['family'],
                    'doc_hint': info['doc_hint'],
                    'variants': [],
                })
                row['variants'].append(base)
    except BadZipFile:
        return []
    return [tools[k] for k in sorted(tools)]



def load_state(path: Path | None) -> Dict[str, Any]:
    if not path or not path.exists():
        return {}
    return json.loads(path.read_text(encoding='utf-8'))



def inventory_manifest_files(source_dir: Path, filenames: List[str]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for filename in filenames:
        if '*' in filename:
            rows.append({'filename': filename, 'exists': True, 'runtime_download_name': None})
            continue
        p = source_dir / filename
        row = {
            'filename': filename,
            'exists': p.exists(),
            'runtime_download_name': runtime_download_name(Path(filename).name),
        }
        if p.exists():
            row['size'] = p.stat().st_size
            row['sha256'] = sha256(p)
        rows.append(row)
    return rows



def inventory_knowledge_dir(path: Path) -> List[str]:
    if not path.exists():
        return []
    return sorted(p.name for p in path.glob('*.md'))



def inventory_knowledge_docs_zip(path: Path | None) -> List[str]:
    if not path or not path.exists():
        return []
    names: List[str] = []
    try:
        with zipfile.ZipFile(path) as zf:
            for name in zf.namelist():
                base = Path(name).name
                if KNOWLEDGE_RE.match(base):
                    names.append(base)
    except BadZipFile:
        return []
    return sorted(set(names))



def main() -> int:
    global MANIFEST_SECTION_KEYS, CURRENT_MANIFEST_HEADINGS, CONTROL_FILE_CANDIDATES
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-dir', required=True)
    ap.add_argument('--state-file')
    ap.add_argument('--output-json', required=True)
    ap.add_argument('--write-state')
    args = ap.parse_args()

    source_dir = Path(args.source_dir)
    contract = load_project_contract(source_dir)
    MANIFEST_SECTION_KEYS = contract.get('manifest_sections', MANIFEST_SECTION_KEYS)
    CURRENT_MANIFEST_HEADINGS = contract.get('current_prose_headings', CURRENT_MANIFEST_HEADINGS)
    CONTROL_FILE_CANDIDATES = {k: v for k, v in contract.get('control_file_roles', {}).items() if k in {'manifest', 'change_log'}}
    manifest = resolve_existing_file(source_dir, CONTROL_FILE_CANDIDATES['manifest'])
    change_log = resolve_existing_file(source_dir, CONTROL_FILE_CANDIDATES['change_log'])
    manifest_data = parse_manifest(manifest)
    prev_state = load_state(Path(args.state_file) if args.state_file else None)

    collector = resolve_current_source(source_dir, manifest_data, ['Collector_Current'], ['project_sources/DCOIR_Collector.ps1', 'DCOIR_Collector.ps1'])
    harness = resolve_current_source(source_dir, manifest_data, ['Harness_PS1_Current', 'Harness_PS1_Project_Readable_Current'], ['project_sources/run_DCOIR_Tests.ps1', 'run_DCOIR_Tests.ps1'])
    collector_zip = source_dir / 'supporting_assets' / 'DCOIR_Collector.zip'
    if not collector_zip.exists():
        collector_zip = None

    recognized_sources = inventory_manifest_files(source_dir, manifest_data['governed_github_readable_sources'])
    governed_knowledge_sources = inventory_manifest_files(source_dir, manifest_data['governed_knowledge_sources'])
    supporting_assets = inventory_manifest_files(source_dir, manifest_data['supporting_assets'])
    settings_references = inventory_manifest_files(source_dir, manifest_data['governed_settings_mirrors'])

    source_hashes = {row['filename']: row['sha256'] for row in recognized_sources if row.get('exists') and row.get('sha256')}
    asset_hashes = {row['filename']: row['sha256'] for row in supporting_assets if row.get('exists') and row.get('sha256')}

    knowledge_dir = source_dir / 'knowledge'
    editable_knowledge_sources = inventory_knowledge_dir(knowledge_dir)
    retained_knowledge_zip_docs = inventory_knowledge_docs_zip(source_dir / 'supporting_assets' / 'supporting_knowledge_docs.zip')

    prev_source_hashes = prev_state.get('source_hashes', {})
    prev_asset_hashes = prev_state.get('asset_hashes', {})
    prev_editable_knowledge = sorted(prev_state.get('editable_knowledge_sources', []))

    changed_sources = sorted([name for name, dig in source_hashes.items() if prev_source_hashes.get(name) != dig])
    changed_assets = sorted([name for name, dig in asset_hashes.items() if prev_asset_hashes.get(name) != dig])
    knowledge_source_set_changed = editable_knowledge_sources != prev_editable_knowledge

    report: Dict[str, Any] = {
        'control_plane': {
            'manifest': str(manifest.relative_to(source_dir)),
            'change_log': str(change_log.relative_to(source_dir)),
        },
        'recognized_governed_github_readable_sources': recognized_sources,
        'current_repo_guide': 'README.md' if (source_dir / 'README.md').exists() else None,
        'current_split_todo_structure': sorted([
            str(p.relative_to(source_dir))
            for p in ([source_dir / 'project_sources' / 'LOG-01_DCOIR_Todo_Log.txt', source_dir / 'project_sources' / 'LOG-01_DCOIR_Todo_Index.txt'] + sorted((source_dir / 'project_sources' / 'todo').glob('*.txt')) if (source_dir / 'project_sources' / 'todo').exists() else [source_dir / 'project_sources' / 'LOG-01_DCOIR_Todo_Log.txt', source_dir / 'project_sources' / 'LOG-01_DCOIR_Todo_Index.txt'])
            if p.exists()
        ]),
        'recognized_governed_knowledge_sources': governed_knowledge_sources,
        'supporting_assets': supporting_assets,
        'settings_references': settings_references,
        'editable_knowledge_sources': editable_knowledge_sources,
        'retained_knowledge_docs_from_supporting_zip': retained_knowledge_zip_docs,
        'knowledge_source_set_changed': knowledge_source_set_changed,
        'changed_source_files': changed_sources,
        'changed_supporting_assets': changed_assets,
        'knowledge_doc_target_format': '.md.txt',
        'suggested_doc_set': DOC_TITLES,
        'collector_source_filename': collector.name,
        'collector_source_path': str(collector.relative_to(source_dir)),
        'collector_runtime_filename': runtime_download_name(collector.name),
        'collector_parameters': parse_powershell_params(collector.read_text(encoding='utf-8')),
        'harness_source_filename': harness.name,
        'harness_source_path': str(harness.relative_to(source_dir)),
        'harness_runtime_filename': runtime_download_name(harness.name),
        'harness_parameters': parse_powershell_params(harness.read_text(encoding='utf-8')),
        'collector_quick_examples': parse_quick_examples(collector.read_text(encoding='utf-8')),
        'collector_endpoint_examples': parse_endpoint_examples(collector.read_text(encoding='utf-8')),
        'collector_tool_inventory': inventory_collector_zip(collector_zip),
        'runtime_filename_guidance': 'Use current GitHub-native runtime filenames such as DCOIR_Collector.ps1 and run_DCOIR_Tests.ps1 in operator-facing execution docs.',
        'authoritative_external_sources': [
            'Microsoft Learn / Sysinternals official documentation',
            'Microsoft Learn / PowerShell official documentation',
            'Elastic official documentation',
        ],
        'ambiguities': [],
    }

    out_path = Path(args.output_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding='utf-8')

    if args.write_state:
        state = {
            'source_hashes': source_hashes,
            'asset_hashes': asset_hashes,
            'editable_knowledge_sources': editable_knowledge_sources,
        }
        Path(args.write_state).write_text(json.dumps(state, indent=2), encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
