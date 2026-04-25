#!/usr/bin/env python3
# skill-marker: updated-skill|20260425T071800Z|T2.3-airtable-first-skill-repair|source-update|dcoir-prompt-pack-assembler|assemble_dcoir_prompt_pack.py
import argparse, datetime as dt, json
from pathlib import Path

CONTROL_FILE_ALIASES = {
    'manifest': ['project_sources/CP-01_DCOIR_Version_Manifest.txt','CP-01_DCOIR_Version_Manifest.txt','project_sources/DCOIR_Version_Manifest.txt','DCOIR_Version_Manifest.txt'],
    'change_log': ['project_sources/CP-02_DCOIR_Change_Log.txt','CP-02_DCOIR_Change_Log.txt','project_sources/DCOIR_Change_Log.txt','DCOIR_Change_Log.txt'],
    'setup': ['project_sources/CP-01_DCOIR_Version_Manifest.txt','project_sources/CP-02_DCOIR_Change_Log.txt'],
}
PATTERNS = {
    'system': ['project_sources/PP-01_*.txt','PP-01_*.txt'],
    'output_schema': ['project_sources/PP-02_*.txt','PP-02_*.txt'],
    'baseline_triage': ['project_sources/PP-03_*.txt','PP-03_*.txt'],
    'enrichment_review': ['project_sources/PP-04_*.txt','PP-04_*.txt'],
    'retrieved_artifact_review': ['project_sources/PP-05_*.txt','PP-05_*.txt'],
    'final_case_synthesis': ['project_sources/PP-06_*.txt','PP-06_*.txt'],
    'guardrails': ['project_sources/PP-07_*.txt','PP-07_*.txt'],
}
ORDER = ['system','output_schema','baseline_triage','enrichment_review','retrieved_artifact_review','final_case_synthesis','guardrails']

class AssemblyError(RuntimeError):
    pass

def resolve_control_files(src: Path):
    out = {}
    for role, aliases in CONTROL_FILE_ALIASES.items():
        for alias in aliases:
            p = src / alias
            if p.exists():
                out[role] = p
                break
        if role not in out:
            raise AssemblyError(f'assembly refused: no {role} file found in workspace')
    return out

def discover(src: Path):
    out = {}
    for role, patterns in PATTERNS.items():
        hits = []
        for pattern in patterns:
            hits.extend(sorted(src.glob(pattern)))
        uniq = []
        seen = set()
        for hit in hits:
            r = hit.resolve()
            if r not in seen:
                uniq.append(hit)
                seen.add(r)
        if not uniq:
            raise AssemblyError(f'assembly refused: missing current prompt-pack module for {role}')
        if len(uniq) > 1:
            raise AssemblyError(f"assembly refused: multiple current files matched {role}: {', '.join(x.as_posix() for x in uniq)}")
        out[role] = uniq[0]
    return out

def build_draft(files, manifest_name):
    now = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')
    lines = ['DCOIR COMBINED MASTER PROMPT DRAFT','','Generated artifact: do not treat this file as control-plane authority.',f'Source of truth: the current modular prompt-pack files discovered from the GitHub-primary project_sources line after validating {manifest_name}.',f'Generated at: {now}','','Included source files in canonical order:']
    for i, (_, p) in enumerate(files, start=1):
        lines.append(f'{i}. {p.as_posix()}')
    lines.append('')
    lines.append('='*80)
    for i,(role,p) in enumerate(files, start=1):
        lines.extend(['',f'BEGIN MODULE {i}: {role.upper()}',f'Source file: {p.as_posix()}', '-'*80, p.read_text(encoding='utf-8').rstrip(), '', f'END MODULE {i}: {role.upper()}', '='*80])
    lines.append('')
    return '\n'.join(lines)

def build_report(success, reason, discovered, output_dir, resolved):
    lines = ['DCOIR Prompt Pack Assembly Report','',f"Status: {'success' if success else 'failure'}"]
    if reason:
        lines.append(f'Reason: {reason}')
    lines.extend(['','Resolved control files:'])
    for role in ('manifest','change_log','setup'):
        if role in resolved:
            lines.append(f'- {role}: {resolved[role].as_posix()}')
    lines.extend(['','Discovered current modular prompt-pack files:'])
    for role in ORDER:
        if role in discovered:
            lines.append(f'- {role}: {discovered[role].as_posix()}')
    lines.extend(['','Ignored non-modular prompt-pack files:','- PP-08 combined master runtime prompt','- PP-09 Gemini generator workflow','- PP-10 Gemini bounded design artifact','','Output files:'])
    if success:
        lines.append(f'- {(output_dir / "dcoir_combined_master_prompt_draft.txt").as_posix()}')
    lines.append(f'- {(output_dir / "dcoir_prompt_pack_assembly_report.txt").as_posix()}')
    lines.append('')
    return '\n'.join(lines)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-dir', required=True)
    ap.add_argument('--output-dir', required=True)
    args = ap.parse_args()
    src = Path(args.source_dir).resolve(); out = Path(args.output_dir).resolve(); out.mkdir(parents=True, exist_ok=True)
    discovered = {}; resolved = {}; success = False; reason = ''
    try:
        resolved = resolve_control_files(src)
        discovered = discover(src)
        files = [(role, discovered[role]) for role in ORDER]
        (out / 'dcoir_combined_master_prompt_draft.txt').write_text(build_draft(files, resolved['manifest'].name), encoding='utf-8')
        success = True
        reason = 'assembly completed from the current project_sources prompt-pack set'
    except Exception as exc:
        reason = str(exc)
    (out / 'dcoir_prompt_pack_assembly_report.txt').write_text(build_report(success, reason, discovered, out, resolved), encoding='utf-8')
    (out / 'dcoir_prompt_pack_assembly_report.json').write_text(json.dumps({'success': success, 'reason': reason, 'discovered': {k:str(v) for k,v in discovered.items()}, 'resolved_control_files': {k:str(v) for k,v in resolved.items()}}, indent=2), encoding='utf-8')
    print(build_report(success, reason, discovered, out, resolved))
    raise SystemExit(0 if success else 1)

if __name__ == '__main__':
    main()
