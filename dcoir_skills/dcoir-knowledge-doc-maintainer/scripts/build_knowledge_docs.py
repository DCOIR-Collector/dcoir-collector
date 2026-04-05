#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, zipfile
from pathlib import Path
from typing import Any, Iterable, List, Dict

def esc(v: Any) -> str:
    return str(v).replace('|', '\|').replace('
', '
').replace('', '
')

def table(headers: List[str], rows: Iterable[Iterable[Any]]) -> List[str]:
    out=["| " + " | ".join(esc(h) for h in headers) + " |", "| " + " | ".join('---' for _ in headers) + " |"]
    for row in rows:
        out.append("| " + " | ".join(esc(v) for v in row) + " |")
    return out

def build_doc_text(doc_data: Dict[str, Any]) -> str:
    lines=[f"# {doc_data['title']}", '', f"_{doc_data.get('subtitle','AFRICOM_SOC_IR / DCOIR supporting knowledge document')}_", '']
    if doc_data.get('summary'):
        lines += [f"**Summary:** {doc_data['summary']}", '']
    lines += ['## Source basis', '']
    rows=[["Project sources", '; '.join(doc_data.get('project_sources', [])) or 'None listed'], ["Official external sources", '; '.join(doc_data.get('external_sources', [])) or 'Not required for this page']]
    if doc_data.get('notes'):
        rows.append(['Scope note', doc_data['notes']])
    lines += table(['Source class','Authoritative basis'], rows) + ['']
    for section in doc_data.get('sections', []):
        lines += [f"## {section['heading']}", '']
        for para in section.get('paragraphs', []):
            lines += [para.rstrip(), '']
        for bullet in section.get('bullets', []):
            lines.append(f"- {bullet.rstrip()}")
        if section.get('bullets'):
            lines.append('')
        if section.get('table'):
            lines += table(section['table']['headers'], section['table']['rows']) + ['']
    lines += ['> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.', '']
    return '
'.join(lines)

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('--spec-json', required=True); ap.add_argument('--output-dir', required=True); ap.add_argument('--zip-path', required=True); args=ap.parse_args()
    spec=json.loads(Path(args.spec_json).read_text(encoding='utf-8'))
    outdir=Path(args.output_dir); outdir.mkdir(parents=True, exist_ok=True)
    produced=[]
    for doc in spec['documents']:
        path=outdir / doc['filename']; path.write_text(build_doc_text(doc), encoding='utf-8'); produced.append(path)
    zpath=Path(args.zip_path); zpath.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zpath, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for p in produced:
            zf.write(p, arcname=p.name)
    return 0
if __name__ == '__main__': raise SystemExit(main())
