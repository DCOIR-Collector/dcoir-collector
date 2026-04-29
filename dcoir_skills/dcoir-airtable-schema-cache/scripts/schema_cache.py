#!/usr/bin/env python3
"""Build and inspect a local DCOIR Airtable schema cache.

The script expects JSON from an Airtable schema readback such as list_tables_for_base.
It never calls external APIs and never stores secrets.
"""
from __future__ import annotations
import argparse, json, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

REQ = ["Governance Control Plane","Queue Control","Work Items","Plans","Session Checkpoints","Idea Inbox","Operator Preferences","Validation Test Cases","Validation Evidence","Repo Surface Registry","Admin Registry","Delete Queue","DCOIR Lifecycle Ledger","Local Configuration Registry"]
RET = ["Plan Tasks","Plan Checkpoints","Skill State Registry","Schema Registry","Tracking Registry","Repo File Coverage Detail","Retained Repo Manifest"]

def load_json(path: str) -> Any:
    with open(path, 'r', encoding='utf-8') as f: return json.load(f)

def write_json(path: str, obj: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f: json.dump(obj, f, indent=2, sort_keys=True)
        
def get_tables(raw: Any) -> List[Dict[str, Any]]:
    if isinstance(raw, dict) and isinstance(raw.get('tables'), list): return raw['tables']
    if isinstance(raw, dict) and isinstance(raw.get('result'), dict) and isinstance(raw['result'].get('tables'), list): return raw['result']['tables']
    if isinstance(raw, list): return raw
    raise SystemExit('No Airtable tables list found. Save the list_tables_for_base JSON response and try again.')

def norm_field(f: Dict[str, Any]) -> Dict[str, Any]:
    out = {'id': f.get('id'), 'name': f.get('name'), 'type': f.get('type'), 'description': f.get('description') or ''}
    opts = f.get('options') or f.get('typeOptions') or {}
    choices = opts.get('choices') if isinstance(opts, dict) else None
    if isinstance(choices, list): out['choices'] = [c.get('name') for c in choices if isinstance(c, dict) and c.get('name')]
    elif isinstance(choices, dict): out['choices'] = [v.get('name') for v in choices.values() if isinstance(v, dict) and v.get('name')]
    if isinstance(opts, dict):
        for key in ['linkedTableId','inverseLinkFieldId','recordLinkFieldId']:
            if key in opts: out[key] = opts[key]
    return out

def build(args):
    raw = load_json(args.schema_json)
    tables = get_tables(raw)
    cache = {'generated_at': datetime.now(timezone.utc).isoformat(), 'source': args.source, 'base_id': args.base_id, 'tables': {}, 'tables_by_id': {}, 'operational_expectations': {'required_tables': REQ, 'do_not_assume_without_live_readback': RET}, 'warnings': []}
    for t in tables:
        name = t.get('name')
        if not name: continue
        fields = {fld.get('name'): norm_field(fld) for fld in t.get('fields', []) if isinstance(fld, dict) and fld.get('name')}
        cache['tables'][name] = {'id': t.get('id'), 'name': name, 'description': t.get('description') or '', 'primaryFieldId': t.get('primaryFieldId') or t.get('primaryColumnId'), 'fields': fields, 'fields_by_id': {v['id']: k for k,v in fields.items() if v.get('id')}}
        if t.get('id'): cache['tables_by_id'][t['id']] = name
    missing = [x for x in REQ if x not in cache['tables']]
    present_retired = [x for x in RET if x in cache['tables']]
    if missing: cache['warnings'].append({'type':'missing_required_operational_tables','tables':missing})
    if present_retired: cache['warnings'].append({'type':'retired_by_default_tables_present_verify_before_use','tables':present_retired})
    write_json(args.output, cache)
    print(json.dumps({'cache': args.output, 'table_count': len(cache['tables']), 'warnings': cache['warnings']}, indent=2))

def summary(args):
    c = load_json(args.cache)
    print(json.dumps({'cache': args.cache, 'generated_at': c.get('generated_at'), 'base_id': c.get('base_id'), 'table_count': len(c.get('tables',{})), 'tables': sorted(c.get('tables',{}).keys()), 'warnings': c.get('warnings',[])}, indent=2))

def lookup(args):
    c = load_json(args.cache); t = c.get('tables',{}).get(args.table)
    if not t: raise SystemExit(f'table not found in cache: {args.table}')
    if args.field:
        f = t.get('fields',{}).get(args.field)
        if not f: raise SystemExit(f'field not found in cache: {args.table}.{args.field}')
        print(json.dumps({'table': {'name': t['name'], 'id': t.get('id')}, 'field': f}, indent=2)); return
    print(json.dumps(t, indent=2))

def validate_required(args):
    c = load_json(args.cache); names = set(c.get('tables',{}))
    out = {'required_present': sorted([x for x in REQ if x in names]), 'required_missing': sorted([x for x in REQ if x not in names]), 'retired_by_default_present': sorted([x for x in RET if x in names]), 'retired_by_default_absent': sorted([x for x in RET if x not in names])}
    print(json.dumps(out, indent=2))
    if out['required_missing']: sys.exit(2)

def diff(args):
    a,b = load_json(args.old), load_json(args.new)
    at,bt = set(a.get('tables',{})), set(b.get('tables',{}))
    changed = []
    for t in sorted(at & bt):
        af,bf = set(a['tables'][t].get('fields',{})), set(b['tables'][t].get('fields',{}))
        if af != bf: changed.append({'table':t,'fields_added':sorted(bf-af),'fields_removed':sorted(af-bf)})
    print(json.dumps({'tables_added': sorted(bt-at), 'tables_removed': sorted(at-bt), 'field_changes': changed}, indent=2))

def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd', required=True)
    b=sub.add_parser('build'); b.add_argument('--schema-json', required=True); b.add_argument('--output', required=True); b.add_argument('--base-id', default='appM4KSwnVf3G3OTK'); b.add_argument('--source', default='airtable list_tables_for_base live readback'); b.set_defaults(func=build)
    s=sub.add_parser('summary'); s.add_argument('--cache', required=True); s.set_defaults(func=summary)
    l=sub.add_parser('lookup'); l.add_argument('--cache', required=True); l.add_argument('--table', required=True); l.add_argument('--field'); l.set_defaults(func=lookup)
    v=sub.add_parser('validate-required'); v.add_argument('--cache', required=True); v.set_defaults(func=validate_required)
    d=sub.add_parser('diff'); d.add_argument('--old', required=True); d.add_argument('--new', required=True); d.set_defaults(func=diff)
    args=p.parse_args(); args.func(args)
if __name__ == '__main__': main()
