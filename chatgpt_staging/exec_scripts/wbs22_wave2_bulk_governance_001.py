#!/usr/bin/env python3
from __future__ import annotations
import datetime as dt, json, os, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path
API='https://api.airtable.com/v0'; BASE=os.environ.get('DCOIR_AIRTABLE_BASE_ID') or 'appM4KSwnVf3G3OTK'; REQ='exec-20260507-wbs22-wave2-bulk-governance-001'
T={'wbs':'tblRxTmpW0VunQlUK','ev':'tblrPFQH2uZEYBYE9','chk':'tblTe75HKZOJaPDGn','plan':'tblBcp5FyMIfOm7Xe','queue':'tblf13aCslg6rJBah'}
W={'state':'fld627GL9W2hnoDa5','validation':'fldBWgf90H3Ja8kQU','context':'fld3IwH6VYmFqnywU'}
E={'key':'fldua3G9lRVdiIpEO','case':'fld42VCNN0p0kbzVp','work':'fldD5IQJtuwW2GKXH','summary':'fld6PWvy2bMvqMpUt','source':'flddBu10OfbDkTxfj','created':'fldFHNOi3cWcrR1y2','updated':'fldU5SlBXT3vlRRLI','result':'fldh0cLWnWvHgzC5f','retention':'fld9xUZL00MIzHqf8'}
C={'id':'fld05CE02z75xTywV','session':'fld63FgvRtBDYjHw1','summary':'fldnl8krcTV95l0WT','focus':'fldG1EIERtFLlUOCO','open':'fldrQ15ciUon2vwsn','decisions':'fldeR0OJNC1tb2xxC','next':'fldI86NLTExK50Paw','resume':'fldCL16aBoQmpk7yg','at':'fldDmyw0j3EKlt5YF','created':'fldwzh5UZvQC6IGuv','updated':'fldAKs3Vd79AAZJ9Z','trigger':'fldTaxKPaShTfMFog','github':'fldNkO3A4aCeR83ty','status':'flduf5QvQRtyMRfq4','retention':'fldb34YQQ976acIzJ'}
P={'active':'fldSqjWSLBN0sWFZz','title':'fldAZSPBZfjCynqEh','next':'fldcMUhjqIAOeAc7r','updated':'fldP3pUOzZ8y7GoWr'}
Q={'summary':'fld93kyr3N268jC2L','decision':'fld426HqFdGNRfe9w','resume':'fldwfYuyQqR9ipkip','last':'fldTqHQAnOI8vaWXw'}
REC={'wbs04':'recSJWdke5hsh9E4H','wbs05':'recPiAsI0H1F7JF2s','wbs06':'recxw7OJh28aLkG2y','plan':'recoLHyurY4OZx3K8','queue':'recj3CPhowuJGYoze'}
EKEY='VE-WBS22-WAVE2-BULK-EXEC-20260507-001'; CID='CHK-DCOIR-WBS22-WAVE2-BULK-EXEC-20260507-001'
def now(): return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def req(m,u,b=None):
 token=os.environ.get('DCOIR_AIRTABLE_TOKEN') or os.environ.get('AIRTABLE_TOKEN')
 if not token: raise SystemExit('missing airtable token env')
 data=None if b is None else json.dumps(b).encode('utf-8'); r=urllib.request.Request(u,data=data,method=m); r.add_header('Authorization','Bearer '+token); r.add_header('Content-Type','application/json')
 for i in range(6):
  try:
   with urllib.request.urlopen(r,timeout=90) as resp:
    raw=resp.read().decode('utf-8','replace'); return {} if not raw else json.loads(raw)
  except urllib.error.HTTPError as e:
   raw=e.read().decode('utf-8','replace')
   if e.code==429 and i<5: time.sleep(2+i); continue
   raise RuntimeError(f'{m} failed HTTP {e.code}: {raw[:800]}')
def u(t,s=''): return f"{API}/{BASE}/{urllib.parse.quote(t,safe='')}{s}"
def get(t,rid): return req('GET',u(t,'/'+urllib.parse.quote(rid,safe='')))
def find(t,f,v):
 formula='{'+f+"}='"+v.replace("'","\\'")+"'"; rows=req('GET',u(t,'?'+urllib.parse.urlencode({'filterByFormula':formula,'pageSize':'10'}))).get('records',[]); return rows[0] if rows else None
def create(t,rows):
 out=[]
 for i in range(0,len(rows),10): out+=req('POST',u(t),{'records':rows[i:i+10]}).get('records',[])
 return out
def patch(t,rows):
 out=[]
 for i in range(0,len(rows),10): out+=req('PATCH',u(t),{'records':rows[i:i+10]}).get('records',[])
 return out
def note(a,b):
 a=a or ''; return a if b in a else ((a.rstrip()+'\n\n'+b).strip() if a.strip() else b)
def main():
 ts=now(); out=Path(os.environ.get('DCOIR_DOWNLOADS_DIR') or os.getcwd())/REQ; out.mkdir(parents=True,exist_ok=True)
 before={k:get(T['wbs'],REC[k]) for k in ['wbs04','wbs05','wbs06']}; before['plan']=get(T['plan'],REC['plan']); before['queue']=get(T['queue'],REC['queue'])
 actions=[]
 if not find(T['ev'],'evidence_key',EKEY):
  create(T['ev'],[{'fields':{E['key']:EKEY,E['case']:'WBS22-WAVE2-BULK-EXECUTION',E['work']:'CLEANUP-WBS-22-05',E['summary']:'Wave 2 resume/governance consistency bulk execution via chatgpt-exec. WBS22-04 and WBS22-05 completed, WBS22-06 activated, plan pointer advanced. Queue/plan/WBS consistency was refreshed. No duplicate/merge, queue-row creation or processing, schema, source, skill, workflow, scaffold, or Wave 6 work was performed.',E['source']:f'chatgpt_staging/status_reports/chatgpt-exec/{REQ}/workflow_report.md',E['created']:ts,E['updated']:ts,E['result']:'passed',E['retention']:'operational'}}]); actions.append('created evidence')
 add04=f'Wave 2 preparation completed by {REQ} at {ts}. Evidence {EKEY}.'; add05=f'Wave 2 execution completed by {REQ} at {ts}. Resume/governance consistency only.'; add06=f'Activated for Wave 3 duplicate/merge candidate preparation by {REQ} at {ts}.'
 patch(T['wbs'],[
  {'id':REC['wbs04'],'fields':{W['state']:'complete',W['validation']:note(before['wbs04'].get('fields',{}).get('validation_notes',''),add04),W['context']:note(before['wbs04'].get('fields',{}).get('context',''),add04)}},
  {'id':REC['wbs05'],'fields':{W['state']:'complete',W['validation']:note(before['wbs05'].get('fields',{}).get('validation_notes',''),add05),W['context']:note(before['wbs05'].get('fields',{}).get('context',''),add05)}},
  {'id':REC['wbs06'],'fields':{W['state']:'active',W['validation']:note(before['wbs06'].get('fields',{}).get('validation_notes',''),add06),W['context']:note(before['wbs06'].get('fields',{}).get('context',''),add06)}}]); actions.append('updated WBS batch')
 patch(T['plan'],[{'id':REC['plan'],'fields':{P['active']:'CLEANUP-WBS-22-06',P['title':'Prepare Wave 3 duplicate and merge candidates' if False else 'title'] if False else P['title']:'Prepare Wave 3 duplicate and merge candidates',P['next']:'Continue WBS22 with Wave 3 duplicate/merge candidate preparation. Use compatible bulk batches. Stop before Wave 6 review.',P['updated']:ts}}]); actions.append('advanced plan pointer')
 q=before['queue'].get('fields',{}); qnote=f'Wave 2 consistency readback refreshed by {REQ} at {ts}; active plan now advances to CLEANUP-WBS-22-06 after Wave 2 completion.'
 patch(T['queue'],[{'id':REC['queue'],'fields':{Q['summary']:note(q.get('branch_summary',''),qnote),Q['resume']:note(q.get('resume_rule',''),qnote),Q['last']:ts}}]); actions.append('refreshed queue clarity')
 if not find(T['chk'],'checkpoint_id',CID):
  create(T['chk'],[{'fields':{C['id']:CID,C['session']:'DCOIR-WBS22-WAVE2-BULK',C['summary']:'Wave 2 bulk resume/governance consistency completed via chatgpt-exec. WBS22-04 and WBS22-05 complete; WBS22-06 active; plan pointer advanced.',C['focus']:'Resume at CLEANUP-WBS-22-06 for Wave 3 preparation.',C['open']:'Waves 3-5 proceed sequentially with compatible bulk batches. Stop before Wave 6 review.',C['decisions']:'Bulk within each wave; do not combine all waves into one run. Keep reports compact.',C['next']:'Prepare and execute Wave 3 compatible duplicate/merge-safe updates without record deletion or queue processing.',C['resume']:'Resume AFRICOM_SOC_IR / DCOIR at WBS22 Wave 3. Verify plan active task CLEANUP-WBS-22-06.',C['at']:ts,C['created']:ts,C['updated']:ts,C['trigger']:'milestone',C['github']:'airtable_only',C['status']:'active',C['retention']:'operational'}}]); actions.append('created checkpoint')
 after={k:get(T['wbs'],REC[k]) for k in ['wbs04','wbs05','wbs06']}; after['plan']=get(T['plan'],REC['plan']); after['evidence']=find(T['ev'],'evidence_key',EKEY); after['checkpoint']=find(T['chk'],'checkpoint_id',CID)
 err=[]
 if after['wbs04'].get('fields',{}).get('state')!='complete': err.append('wbs04 not complete')
 if after['wbs05'].get('fields',{}).get('state')!='complete': err.append('wbs05 not complete')
 if after['wbs06'].get('fields',{}).get('state')!='active': err.append('wbs06 not active')
 if after['plan'].get('fields',{}).get('active_task_id')!='CLEANUP-WBS-22-06': err.append('plan not advanced')
 if not after['evidence']: err.append('evidence missing')
 if not after['checkpoint']: err.append('checkpoint missing')
 rep={'request_id':REQ,'result':'failed' if err else 'passed','actions':actions,'errors':err,'evidence_key':EKEY,'checkpoint_id':CID,'after_compact':{k:(v.get('id') if v else None) for k,v in after.items()},'finished_at_utc':now()}
 (out/(REQ+'_report.json')).write_text(json.dumps(rep,indent=2),encoding='utf-8'); (out/(REQ+'_report.md')).write_text('# '+REQ+'\n\nResult: **'+rep['result']+'**\n',encoding='utf-8'); print(json.dumps(rep,indent=2))
 if err: raise SystemExit('; '.join(err))
if __name__=='__main__': main()
