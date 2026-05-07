#!/usr/bin/env python3
import datetime as dt,json,os,time,urllib.error,urllib.parse,urllib.request
from pathlib import Path
API='https://api.airtable.com/v0'; BASE=os.environ.get('DCOIR_AIRTABLE_BASE_ID') or 'appM4KSwnVf3G3OTK'; REQ='exec-20260507-wbs22-wave3-bulk-merge-safe-001'
T={'wbs':'tblRxTmpW0VunQlUK','ev':'tblrPFQH2uZEYBYE9','chk':'tblTe75HKZOJaPDGn','plan':'tblBcp5FyMIfOm7Xe'}
W={'state':'fld627GL9W2hnoDa5','validation':'fldBWgf90H3Ja8kQU','context':'fld3IwH6VYmFqnywU'}
E={'key':'fldua3G9lRVdiIpEO','case':'fld42VCNN0p0kbzVp','work':'fldD5IQJtuwW2GKXH','summary':'fld6PWvy2bMvqMpUt','source':'flddBu10OfbDkTxfj','created':'fldFHNOi3cWcrR1y2','updated':'fldU5SlBXT3vlRRLI','result':'fldh0cLWnWvHgzC5f','retention':'fld9xUZL00MIzHqf8'}
C={'id':'fld05CE02z75xTywV','session':'fld63FgvRtBDYjHw1','summary':'fldnl8krcTV95l0WT','focus':'fldG1EIERtFLlUOCO','open':'fldrQ15ciUon2vwsn','decisions':'fldeR0OJNC1tb2xxC','next':'fldI86NLTExK50Paw','resume':'fldCL16aBoQmpk7yg','at':'fldDmyw0j3EKlt5YF','created':'fldwzh5UZvQC6IGuv','updated':'fldAKs3Vd79AAZJ9Z','trigger':'fldTaxKPaShTfMFog','github':'fldNkO3A4aCeR83ty','status':'flduf5QvQRtf4' if False else 'flduf5QvQRtyMRfq4','retention':'fldb34YQQ976acIzJ'}
P={'active':'fldSqjWSLBN0sWFZz','title':'fldAZSPBZfjCynqEh','next':'fldcMUhjqIAOeAc7r','updated':'fldP3pUOzZ8y7GoWr'}
REC={'wbs06':'recxw7OJh28aLkG2y','wbs07':'recDJ0KWFG357NTIY','wbs08':'rec0jEYcxU4FDS8zf','plan':'recoLHyurY4OZx3K8'}
EKEY='VE-WBS22-WAVE3-BULK-EXEC-20260507-001'; CID='CHK-DCOIR-WBS22-WAVE3-BULK-EXEC-20260507-001'
def now(): return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def call(m,url,body=None):
 tok=os.environ.get('DCOIR_AIRTABLE_TOKEN') or os.environ.get('AIRTABLE_TOKEN')
 if not tok: raise SystemExit('missing token env')
 data=None if body is None else json.dumps(body).encode(); r=urllib.request.Request(url,data=data,method=m); r.add_header('Authorization','Bearer '+tok); r.add_header('Content-Type','application/json')
 for i in range(6):
  try:
   with urllib.request.urlopen(r,timeout=90) as resp:
    raw=resp.read().decode(); return {} if not raw else json.loads(raw)
  except urllib.error.HTTPError as e:
   raw=e.read().decode('utf-8','replace')
   if e.code==429 and i<5: time.sleep(2+i); continue
   raise RuntimeError(raw[:600])
def url(t,s=''): return f"{API}/{BASE}/{urllib.parse.quote(t,safe='')}{s}"
def get(t,rid): return call('GET',url(t,'/'+rid))
def find(t,f,v):
 rows=call('GET',url(t,'?'+urllib.parse.urlencode({'filterByFormula':'{'+f+"}='"+v+"'",'pageSize':'10'}))).get('records',[]); return rows[0] if rows else None
def create(t,rows):
 out=[]
 for i in range(0,len(rows),10): out+=call('POST',url(t),{'records':rows[i:i+10]}).get('records',[])
 return out
def patch(t,rows):
 out=[]
 for i in range(0,len(rows),10): out+=call('PATCH',url(t),{'records':rows[i:i+10]}).get('records',[])
 return out
def add(a,b):
 a=a or ''; return a if b in a else ((a.rstrip()+'\n\n'+b).strip() if a.strip() else b)
def main():
 ts=now(); out=Path(os.environ.get('DCOIR_DOWNLOADS_DIR') or os.getcwd())/REQ; out.mkdir(parents=True,exist_ok=True)
 before={k:get(T['wbs'],REC[k]) for k in ['wbs06','wbs07','wbs08']}; before['plan']=get(T['plan'],REC['plan']); actions=[]
 if not find(T['ev'],'evidence_key',EKEY):
  create(T['ev'],[{'fields':{E['key']:EKEY,E['case']:'WBS22-WAVE3-BULK',E['work']:'CLEANUP-WBS-22-07',E['summary']:'Wave 3 merge-safe review batch completed by chatgpt-exec. WBS22-06 and WBS22-07 complete, WBS22-08 active, plan pointer advanced. No queue row creation, queue processing, schema, source, skill, workflow, scaffold, or Wave 6 work was performed.',E['source']:f'chatgpt_staging/status_reports/chatgpt-exec/{REQ}/workflow_report.md',E['created']:ts,E['updated']:ts,E['result']:'passed',E['retention']:'operational'}}]); actions.append('evidence')
 patch(T['wbs'],[
  {'id':REC['wbs06'],'fields':{W['state']:'complete',W['validation']:add(before['wbs06']['fields'].get('validation_notes',''),f'Wave 3 preparation completed by {REQ} at {ts}. Evidence {EKEY}.'),W['context']:add(before['wbs06']['fields'].get('context',''),f'Wave 3 preparation completed by {REQ}.')}},
  {'id':REC['wbs07'],'fields':{W['state']:'complete',W['validation']:add(before['wbs07']['fields'].get('validation_notes',''),f'Wave 3 execution completed by {REQ} at {ts}. Evidence {EKEY}.'),W['context']:add(before['wbs07']['fields'].get('context',''),f'Wave 3 execution completed by {REQ}.')}},
  {'id':REC['wbs08'],'fields':{W['state']:'active',W['validation']:add(before['wbs08']['fields'].get('validation_notes',''),f'Activated for Wave 4 by {REQ} at {ts}.'),W['context']:add(before['wbs08']['fields'].get('context',''),f'Activated for Wave 4 by {REQ}.')}}]); actions.append('wbs')
 patch(T['plan'],[{'id':REC['plan'],'fields':{P['active']:'CLEANUP-WBS-22-08',P['title']:'Prepare Wave 4 Delete Queue candidates',P['next']:'Continue with Wave 4 candidate preparation using compatible bulk batches. Stop before Wave 6 review.',P['updated']:ts}}]); actions.append('plan')
 if not find(T['chk'],'checkpoint_id',CID):
  create(T['chk'],[{'fields':{C['id']:CID,C['session']:'DCOIR-WBS22-WAVE3-BULK',C['summary']:'Wave 3 batch complete. WBS22-08 is now active.',C['focus']:'Resume at CLEANUP-WBS-22-08 for Wave 4.',C['open']:'Waves 4-5 continue sequentially. Stop before Wave 6.',C['decisions']:'Bulk inside each wave only.',C['next']:'Prepare Wave 4 batch.',C['resume']:'Resume at WBS22 Wave 4; verify active task CLEANUP-WBS-22-08.',C['at']:ts,C['created']:ts,C['updated']:ts,C['trigger']:'milestone',C['github']:'airtable_only',C['status']:'active',C['retention']:'operational'}}]); actions.append('checkpoint')
 after={k:get(T['wbs'],REC[k]) for k in ['wbs06','wbs07','wbs08']}; after['plan']=get(T['plan'],REC['plan']); after['evidence']=find(T['ev'],'evidence_key',EKEY); after['checkpoint']=find(T['chk'],'checkpoint_id',CID)
 errors=[]
 if after['wbs06']['fields'].get('state')!='complete': errors.append('wbs06')
 if after['wbs07']['fields'].get('state')!='complete': errors.append('wbs07')
 if after['wbs08']['fields'].get('state')!='active': errors.append('wbs08')
 if after['plan']['fields'].get('active_task_id')!='CLEANUP-WBS-22-08': errors.append('plan')
 if not after['evidence']: errors.append('evidence')
 if not after['checkpoint']: errors.append('checkpoint')
 rep={'request_id':REQ,'result':'failed' if errors else 'passed','actions':actions,'errors':errors,'evidence_key':EKEY,'checkpoint_id':CID,'finished_at_utc':now()}
 (out/(REQ+'_report.json')).write_text(json.dumps(rep,indent=2),encoding='utf-8'); print(json.dumps(rep,indent=2))
 if errors: raise SystemExit(','.join(errors))
if __name__=='__main__': main()
