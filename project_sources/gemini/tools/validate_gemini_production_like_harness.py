#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys, zipfile
from pathlib import Path
REQ=['project_sources/validation/out_*/','project_sources/TestResults/','project_sources/gemini/fixtures/behavioral_replay/blind_artifacts/**','project_sources/collector/fixtures/blind_artifacts/**','chatgpt_workflow_report_section/']
COUNTS={'prime_chunks':21,'sub_agents':11,'knowledge_sources':28}
BANNED=['expected_behavior','forbidden_behavior','expected_verdict','artifact_expectations','must_find','must_not_find','answer key','rubric','grader']
def j(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def rel(p,r):
    try: return Path(p).relative_to(r).as_posix()
    except ValueError: return Path(p).as_posix()
def add(ms,l,m,p=''): ms.append({'level':l,'message':m,**({'path':p} if p else {})})
def sha_text(t): return hashlib.sha256(t.encode('utf-8')).hexdigest()
def sha_file(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()
def gitignore(root,ms):
    txt=(root/'.gitignore').read_text(encoding='utf-8') if (root/'.gitignore').is_file() else ''
    miss=[x for x in REQ if x not in txt]
    for x in miss: add(ms,'error',f'.gitignore missing {x}','.gitignore')
    return {'present':bool(txt),'missing_patterns':miss}
def build_prompt(idx,sc,sdir,root,ms):
    tmpl=idx.get('prompt_template',{}); v=sc.get('visible',{})
    lines=[tmpl.get('header','Governed DCOIR Gemini blind replay. Return operator-facing text only.'),tmpl.get('evidence_boundary','Use only listed evidence; name gaps and the smallest safe next move.'),'','Operator turn:',str(v.get('turn','')).strip(),'','Evidence attachments:']; at=[]
    for n,txt in enumerate(v.get('evidence_inline',[]),1):
        label=f'inline_evidence_{n}.txt'; lines += ['',f'--- BEGIN ATTACHMENT: {label} ---',str(txt).rstrip(),f'--- END ATTACHMENT: {label} ---']; at.append({'path':label,'size_bytes':len(str(txt).encode('utf-8')),'sha256':sha_text(str(txt))})
    for item in v.get('evidence_files',[]):
        p=(sdir/item).resolve(); txt=''
        if not p.is_file(): add(ms,'error',f"{sc.get('id')} attachment missing",rel(p,root))
        else: txt=p.read_text(encoding='utf-8-sig'); at.append({'path':rel(p,root),'size_bytes':p.stat().st_size,'sha256':sha_file(p)})
        lines += ['',f'--- BEGIN ATTACHMENT: {item} ---',txt.rstrip(),f'--- END ATTACHMENT: {item} ---']
    no=list(tmpl.get('no',[]))+list(v.get('disallowed',[]))
    if no: lines += ['','Disallowed behavior:']+[f'- {x}' for x in no]
    return '\n'.join(lines).rstrip()+'\n',at
def check_prompt(idx,sc,spath,prompt,ms,root):
    low=prompt.lower()
    for term in BANNED:
        if term in low: add(ms,'error',f"{sc.get('id')} prompt leaks grading vocabulary: {term}",rel(spath,root))
    for field in ('expected_behavior','forbidden_behavior'):
        for item in sc.get('hidden',{}).get(field,[]):
            t=str(item).strip().lower()
            if len(t)>=80 and t in low: add(ms,'error',f"{sc.get('id')} prompt leaks long hidden {field} text",rel(spath,root))
    for term in idx.get('redaction_prohibited_terms',[]):
        if str(term).lower() in low: add(ms,'error',f"{sc.get('id')} prompt leaks prohibited redaction term",rel(spath,root))
    for pat in idx.get('redaction_prohibited_patterns',[]):
        if str(pat).lower() in low: add(ms,'error',f"{sc.get('id')} prompt leaks prohibited redaction pattern",rel(spath,root))
def check_signals(sc,spath,prompt,ms,root):
    exp=sc.get('artifact_expectations',{})
    miss=[x for x in exp.get('must_find',[]) if x not in prompt]
    unexpected=[x for x in exp.get('must_not_find',[]) if x in prompt]
    for x in miss: add(ms,'error',f"{sc.get('id')} missing expected fixture signal: {x}",rel(spath,root))
    for x in unexpected: add(ms,'error',f"{sc.get('id')} contains prohibited fixture signal: {x}",rel(spath,root))
    return {'missing_required_signals':miss,'unexpected_prohibited_signals':unexpected}
def blind(root,fixtures,out,ms,require):
    broot=fixtures/'blind'; idx=j(broot/'index.json'); pdir=out/'model_visible_prompts'; pdir.mkdir(parents=True,exist_ok=True)
    rows=[]; tags=set()
    for legacy in idx.get('matrix',[]):
        if len(legacy)>=3: tags.update(str(x) for x in legacy[:3] if x)
    for ref in idx.get('scenarios',[]):
        sp=(broot/ref['path']).resolve()
        if not sp.is_file(): add(ms,'error',f"listed scenario is missing: {ref.get('id')}",rel(sp,root)); continue
        sc=j(sp); sid=sc.get('id',ref.get('id')); sdir=sp.parent
        for need in ('id','owner','family','visible','hidden','artifact_expectations'):
            if need not in sc: add(ms,'error',f'{sid} missing required field {need}',rel(sp,root))
        prompt,atts=build_prompt(idx,sc,sdir,root,ms); check_prompt(idx,sc,sp,prompt,ms,root); sig=check_signals(sc,sp,prompt,ms,root)
        pp=pdir/f'{sid}.prompt.txt'; pp.write_text(prompt,encoding='utf-8')
        owner=str(sc.get('owner',ref.get('owner',''))); fam=str(sc.get('family',ref.get('family',''))); tier=str(sc.get('tier',ref.get('tier','medium'))); tags.update([owner,fam,tier])
        rows.append({'scenario_id':sid,'owner':owner,'family':fam,'tier':tier,'prompt_path':rel(pp,root),'prompt_sha256':sha_text(prompt),'attachment_count':len(atts),'attachments':atts,'expected_verdict':sc.get('hidden',{}).get('expected_verdict',''),'artifact_expectations':sig})
    gap=None; collector_bundle=idx.get('collector_bundle',{}); bundle=collector_bundle.get('path')
    if bundle:
        bp=root/bundle
        if not bp.exists():
            gap=f'stored artifact not present at {bundle}; full artifact replay remains manual/operator-supplied'; add(ms,'error' if require else 'warning',gap,'blind/index.json')
        elif bp.is_dir():
            sm=collector_bundle.get('sanitized_manifest')
            if sm and not (root/sm).is_file():
                gap=f'sanitized stored artifact tree present at {bundle}, but sanitized manifest is missing at {sm}'; add(ms,'error',gap,'blind/index.json')
    return {'schema':idx.get('schema'),'legacy_matrix_count':len(idx.get('matrix',[])),'scenario_count':len(rows),'coverage_tags':sorted(x for x in tags if x),'prompts':rows,'stored_artifact_gap':gap}
def collector(root,ms):
    ip=root/'project_sources/collector/fixtures/blind/index.json'
    if not ip.is_file(): add(ms,'error','collector blind index missing',rel(ip,root)); return {'present':False}
    idx=j(ip); rows=[]
    for fx in idx.get('fixtures',[]):
        mp=root/fx.get('manifest',fx.get('manifest_path',''))
        if not mp.is_file(): add(ms,'error',f"collector fixture manifest missing for {fx.get('id',fx.get('fixture_id'))}",rel(mp,root)); continue
        m=j(mp); rows.append({'fixture_id':fx.get('id',fx.get('fixture_id')),'manifest_path':rel(mp,root),'artifact_count':len(m.get('artifacts',[])),'derived_scenarios':m.get('derived_scenarios',[])})
    return {'present':True,'fixture_count':len(idx.get('fixtures',[])),'manifests':rows}
def construct(root,out,ms,mode):
    src=root/'project_sources/gemini/bundle_source'; man=j(src/'Gemini_Bundle_Source_Manifest.json'); top=man['topology']; chunks=j(src/man['prime_agent_chunk_manifest'])
    counts={'prime_chunks':len(chunks['chunks']),'sub_agents':len(top['sub_agent_files']),'knowledge_sources':len(man['knowledge_attachment_sources'])}
    for k,v in COUNTS.items():
        if counts[k]!=v: add(ms,'error',f'{k} {counts[k]} != {v}',rel(src,root))
    build={'attempted':False}
    if mode in ('medium','full'):
        bout=out/'construct_load'; cmd=[sys.executable,str(root/'project_sources/gemini/tools/build_dcoir_gemini_release.py'),'--source-root',str(src),'--output-dir',str(bout)]
        pr=subprocess.run(cmd,text=True,capture_output=True); build={'attempted':True,'returncode':pr.returncode}
        if pr.returncode: add(ms,'error','construct build failed',rel(src,root)); build['stderr']=pr.stderr[-2000:]
        zips=sorted(bout.glob('*.zip'))
        if zips:
            names=zipfile.ZipFile(zips[-1]).namelist(); rels=[n.split('/',1)[1] if '/' in n else n for n in names]
            leaks=[x for x in rels if x in set(man.get('source_only_files',[])) or any(x.startswith(d.rstrip('/')+'/') for d in man.get('source_only_dirs',[]))]
            build.update({'zip_path':rel(zips[-1],root),'zip_entry_count':len(names),'prime_present':top['prime_agent_file'] in rels,'source_only_leaks':leaks})
            if not build['prime_present'] or leaks: add(ms,'error','construct zip contract failed',rel(zips[-1],root))
    return {'manifest_path':rel(src/'Gemini_Bundle_Source_Manifest.json',root),'counts':counts,'build':build}
def write_reports(out,rep):
    out.mkdir(parents=True,exist_ok=True); (out/'gemini_production_like_harness_report.json').write_text(json.dumps(rep,indent=2),encoding='utf-8')
    (out/'gemini_production_like_scenario_matrix.json').write_text(json.dumps({'summary':rep['summary'],'scenarios':rep['blind_scenarios'].get('prompts',[]),'collector_fixtures':rep.get('collector_fixtures',{})},indent=2),encoding='utf-8')
    md=['# Gemini Production-Like Behavioral Harness Report','','## Summary']+[f"- {k}: `{v}`" for k,v in rep['summary'].items()]+['','## Scenario Matrix','','| Scenario | Owner | Family | Tier | Attachments | Expected verdict |','|---|---|---|---|---:|---|']
    for r in rep['blind_scenarios'].get('prompts',[]): md.append(f"| {r['scenario_id']} | {r['owner']} | {r['family']} | {r['tier']} | {r['attachment_count']} | {r['expected_verdict']} |")
    md += ['','## Messages']+[f"- {m['level']}: {m['message']}"+(f" (`{m['path']}`)" if m.get('path') else '') for m in rep['messages']]+['','## Verdict Semantics','','- Workflow success means the harness ran and produced trustworthy evidence artifacts.','- Harness success means schemas, prompt separation, artifact signals, redaction checks, and construct loading passed.','- Behavior success remains `not_scored_static_harness` unless a deterministic or live model response lane is executed.','- Raw collector bundles remain operator-supplied and ignored; committed sanitized fixture trees may be used for static/full-artifact harness coverage.']
    text='\n'.join(md)+'\n'; (out/'gemini_production_like_harness_report.md').write_text(text,encoding='utf-8'); (out/'chatgpt_workflow_report_section.md').write_text(text,encoding='utf-8')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',default='.'); ap.add_argument('--fixtures-root',default='project_sources/gemini/fixtures/behavioral_replay'); ap.add_argument('--output-dir',default='project_sources/validation/out_gemini_production_like_harness'); ap.add_argument('--mode',choices=['light','medium','full'],default='light'); ap.add_argument('--require-stored-artifacts',action='store_true'); a=ap.parse_args()
    root=Path(a.repo_root).resolve(); out=(root/a.output_dir).resolve(); out.mkdir(parents=True,exist_ok=True); ms=[]
    gi=gitignore(root,ms); bl=blind(root,(root/a.fixtures_root).resolve(),out,ms,a.require_stored_artifacts); cf=collector(root,ms); co=construct(root,out,ms,a.mode); err=[m for m in ms if m['level']=='error']; warn=[m for m in ms if m['level']=='warning']
    summary={'workflow_verdict':'success' if not err else 'failure','harness_success':str(not err).lower(),'behavior_success':'not_scored_static_harness','evidence_fidelity':'static' if a.mode=='light' else 'static_plus_construct_build','mode':a.mode,'error_count':len(err),'warning_count':len(warn),'legacy_matrix_count':bl.get('legacy_matrix_count',0),'scenario_count':bl.get('scenario_count',0),'collector_fixture_count':cf.get('fixture_count',0)}
    rep={'summary':summary,'messages':ms,'gitignore':gi,'construct':co,'blind_scenarios':bl,'collector_fixtures':cf}; write_reports(out,rep); print(json.dumps(summary,indent=2)); return 1 if err else 0
if __name__=='__main__': raise SystemExit(main())
