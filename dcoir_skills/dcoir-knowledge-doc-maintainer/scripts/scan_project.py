#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, re, zipfile
from zipfile import BadZipFile
from pathlib import Path
from typing import Any, Dict, List

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
KNOWLEDGE_RE = re.compile(r"^Knowledge - \d{2} - .+\.md$", re.IGNORECASE)

def sha256(path: Path) -> str:
    h=hashlib.sha256();
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def parse_powershell_params(text: str) -> List[Dict[str, Any]]:
    out=[]; m=re.search(r'param\((.*?)\n\)', text, re.S)
    if not m: return out
    for raw in m.group(1).splitlines():
        line=raw.strip()
        pm=re.search(r"\[(?P<type>[^\]]+)\]\$(?P<name>[A-Za-z0-9_]+)(?:\s*=\s*(?P<default>.+?))?,?$", line)
        if pm:
            out.append({'name': pm.group('name'), 'type': pm.group('type'), 'default': (pm.group('default') or '').strip().rstrip(',')})
    return out

def inventory_collector_zip(path: Path | None) -> List[str]:
    if not path or not path.exists(): return []
    names=[]
    try:
        with zipfile.ZipFile(path) as zf:
            for name in zf.namelist():
                base=os.path.basename(name)
                if base.lower().endswith('.exe'): names.append(base)
    except BadZipFile:
        return []
    return sorted(set(names))

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('--source-dir', required=True); ap.add_argument('--output-json', required=True); ap.add_argument('--state-file'); ap.add_argument('--write-state'); args=ap.parse_args()
    source_dir=Path(args.source_dir)
    collector=source_dir / 'project_sources' / 'DCOIR_Collector.ps1'
    harness=source_dir / 'project_sources' / 'run_DCOIR_Tests.ps1'
    collector_zip=source_dir / 'supporting_assets' / 'DCOIR_Collector.zip'
    knowledge_dir=source_dir / 'knowledge'
    report={
      'control_plane': {'manifest':'project_sources/CP-01_DCOIR_Version_Manifest.txt','change_log':'project_sources/CP-02_DCOIR_Change_Log.txt'},
      'collector_source_path': str(collector.relative_to(source_dir)) if collector.exists() else None,
      'collector_runtime_filename': 'DCOIR_Collector.ps1',
      'harness_source_path': str(harness.relative_to(source_dir)) if harness.exists() else None,
      'harness_runtime_filename': 'run_DCOIR_Tests.ps1',
      'harness_wrapper_present': (source_dir / 'project_sources' / 'run_DCOIR_Tests.cmd').exists(),
      'collector_parameters': parse_powershell_params(collector.read_text(encoding='utf-8')) if collector.exists() else [],
      'harness_parameters': parse_powershell_params(harness.read_text(encoding='utf-8')) if harness.exists() else [],
      'collector_tool_inventory': inventory_collector_zip(collector_zip if collector_zip.exists() else None),
      'editable_knowledge_sources': sorted(p.name for p in knowledge_dir.glob('*.md')) if knowledge_dir.exists() else [],
      'knowledge_doc_target_format': '.md.txt',
      'suggested_doc_set': DOC_TITLES,
      'runtime_filename_guidance': 'Use current GitHub-readable provenance such as project_sources/DCOIR_Collector.ps1 and project_sources/run_DCOIR_Tests.ps1, and use the runtime filenames DCOIR_Collector.ps1 and run_DCOIR_Tests.ps1 in operator-facing execution docs. Do not document a CMD harness wrapper unless the current control plane restores one.',
      'source_hashes': {str(p.relative_to(source_dir)): sha256(p) for p in [collector, harness] if p.exists()},
    }
    out=Path(args.output_json); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(report, indent=2), encoding='utf-8')
    if args.write_state:
        Path(args.write_state).write_text(json.dumps({'source_hashes': report['source_hashes'], 'editable_knowledge_sources': report['editable_knowledge_sources']}, indent=2), encoding='utf-8')
    return 0
if __name__ == '__main__': raise SystemExit(main())
