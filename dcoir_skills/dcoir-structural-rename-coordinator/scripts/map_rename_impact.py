#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

def map_impact(data):
    old=data.get('old_name','')
    new=data.get('new_name','')
    areas=['manifest','change_log','docs','skills','packaging_rules','tests']
    if old.startswith('Knowledge -') or new.endswith('.zip'):
        areas.append('supporting_assets')
    return {'old_name':old,'new_name':new,'impacted_areas':areas,'default_release_posture':'full_refresh_bundle','deeper_regression_required':True}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input-json',required=True); ap.add_argument('--output-json',required=True); args=ap.parse_args()
    out=map_impact(json.loads(Path(args.input_json).read_text())); p=Path(args.output_json); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(out, indent=2)); print(json.dumps(out, indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
