#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys, zipfile
from pathlib import Path
REQ=['project_sources/validation/out_*/','project_sources/TestResults/','project_sources/gemini/fixtures/behavioral_replay/blind_artifacts/**','project_sources/collector/fixtures/blind_artifacts/**','chatgpt_workflow_report_section/']
COUNTS={'prime_chunks':21,'sub_agents':11,'knowledge_sources':28}
def j(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def rel(p,r):
    try: return Path(p).relative_to(r).as_posix()
    except ValueError: return str(p)
def add(ms,l,m,p=''): ms.append({'level':l,'message':m,**({'path':p} if p else {})})
def prompt(f):
    v=f['visible']; lines=['Governed DCOIR Gemini blind replay. Return operator-facing text only.','Use only listed evidence; name gaps and the smallest safe next move.','Operator turn:',v['turn'],'Evidence:']+[f'- {x}' for x in v.get('evidence',[])]+['Disallowed:']+[f'- {x}' for x in v.get('no',[])]
    return '\n'.join(lines)+'\n'
def gitignore(root,ms):
    text=(root/'.gitignore').read_text(encoding='utf-8') if (root/'.gitignore').is_file() else ''
    miss=[x for x in REQ if x not in text]
    for x in miss: add(ms,'error',f'.gitignore missing {x}','.gitignore')
    return {'present':bool(text),'missing_patterns':miss}
def blind(root,fixtures,out,ms,require):
    idx=j(fixtures/'blind/index.json'); rows=[]; tags=set(); pdir=out/'model_visible_prompts'; pdir.mkdir(parents=True,exist_ok=True)
    ev=idx.get('prompt_template',{}).get('evidence',[]); no=idx.get('prompt_template',{}).get('no',[]); hidden=idx.get('hidden_template',{}); bundle=idx.get('collector_bundle',{})
    for sid,owner,fam in idx.get('matrix',[]):
        f={'id':sid,'owner':owner,'family':fam,'visible':{'turn':f'Operator-like {fam} scenario. Use only provided evidence and name gaps.','evidence':ev,'no':no},'hidden':hidden,'artifact':{'bundle_path':bundle.get('path',''),'required_full':sid==bundle.get('required_for')}}
        tags.update([owner,fam]); txt=prompt(f); pp=pdir/f'{sid}.prompt.txt'; pp.write_text(txt,encoding='utf-8')
        if any(str(x) in txt for x in hidden.get('expect',[])+hidden.get('forbid',[])): add(ms,'error',f'{sid} leaks hidden grading','blind/index.json')
        art=f['artifact']
        if art.get('required_full') and not (root/art.get('bundle_path','')).is_file():
            add(ms,'error' if require else 'warning',f'stored artifact not present for {sid}; full artifact replay remains a gap','blind/index.json')
        rows.append({'scenario_id':sid,'scenario_family':fam,'coverage_tags':[owner,fam],'prompt_path':rel(pp,root),'prompt_sha256':hashlib.sha256(txt.encode()).hexdigest()})
    return {'scenario_count':len(rows),'coverage_tags':sorted(x for x in tags if x),'prompts':rows}

def construct(root,out,ms,mode):
    src=root/'project_sources/gemini/bundle_source'; m=j(src/'Gemini_Bundle_Source_Manifest.json'); top=m['topology']; chunks=j(src/m['prime_agent_chunk_manifest'])
    counts={'prime_chunks':len(chunks['chunks']),'sub_agents':len(top['sub_agent_files']),'knowledge_sources':len(m['knowledge_attachment_sources'])}
    for k,v in COUNTS.items():
        if counts[k]!=v: add(ms,'error',f'{k} {counts[k]} != {v}',rel(src,root))
    build={'attempted':False}
    if mode in ['medium','full']:
        bout=out/'construct_load'; cmd=[sys.executable,str(root/'project_sources/gemini/tools/build_dcoir_gemini_release.py'),'--source-root',str(src),'--output-dir',str(bout)]
        pr=subprocess.run(cmd,text=True,capture_output=True); build={'attempted':True,'returncode':pr.returncode}
        if pr.returncode: add(ms,'error','construct build failed',rel(src,root))
        zips=sorted(bout.glob('*.zip'))
        if zips:
            names=zipfile.ZipFile(zips[-1]).namelist(); rels=[n.split('/',1)[1] if '/' in n else n for n in names]; leaks=[x for x in rels if x in set(m.get('source_only_files',[])) or any(x.startswith(d.rstrip('/')+'/') for d in m.get('source_only_dirs',[]))]
            build.update({'zip_path':rel(zips[-1],root),'zip_entry_count':len(names),'prime_present':top['prime_agent_file'] in rels,'source_only_leaks':leaks})
            if not build['prime_present'] or leaks: add(ms,'error','construct zip contract failed',rel(zips[-1],root))
    return {'manifest_path':rel(src/'Gemini_Bundle_Source_Manifest.json',root),'counts':counts,'build':build}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',default='.'); ap.add_argument('--fixtures-root',default='project_sources/gemini/fixtures/behavioral_replay'); ap.add_argument('--output-dir',default='project_sources/validation/out_gemini_production_like_harness'); ap.add_argument('--mode',choices=['light','medium','full'],default='light'); ap.add_argument('--require-stored-artifacts',action='store_true'); a=ap.parse_args()
    root=Path(a.repo_root).resolve(); out=(root/a.output_dir).resolve(); out.mkdir(parents=True,exist_ok=True); ms=[]
    gi=gitignore(root,ms); bl=blind(root,(root/a.fixtures_root).resolve(),out,ms,a.require_stored_artifacts); co=construct(root,out,ms,a.mode); err=[m for m in ms if m['level']=='error']; warn=[m for m in ms if m['level']=='warning']
    summary={'workflow_verdict':'success' if not err else 'failure','harness_success':str(not err).lower(),'behavior_success':'not_scored_static_harness','evidence_fidelity':'static' if a.mode=='light' else 'static_plus_construct_build','mode':a.mode,'error_count':len(err),'warning_count':len(warn),'scenario_count':bl['scenario_count']}
    rep={'summary':summary,'messages':ms,'gitignore':gi,'construct':co,'blind_scenarios':bl}; (out/'gemini_production_like_harness_report.json').write_text(json.dumps(rep,indent=2),encoding='utf-8')
    md='# Gemini Production-Like Behavioral Harness Report\n\n## Summary\n'+'\n'.join(f'- {k}: `{v}`' for k,v in summary.items())+'\n\n## Messages\n'+'\n'.join(f"- {m['level']}: {m['message']}" for m in ms)+'\n'
    (out/'gemini_production_like_harness_report.md').write_text(md,encoding='utf-8'); (out/'chatgpt_workflow_report_section.md').write_text(md,encoding='utf-8'); print(json.dumps(summary,indent=2)); return 1 if err else 0
if __name__=='__main__': raise SystemExit(main())
