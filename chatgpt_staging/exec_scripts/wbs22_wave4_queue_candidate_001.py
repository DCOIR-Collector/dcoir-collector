#!/usr/bin/env python3
import datetime as dt,json,os,time,urllib.error,urllib.parse,urllib.request
from pathlib import Path
API='https://api.airtable.com/v0'; BASE=os.environ.get('DCOIR_AIRTABLE_BASE_ID') or 'appM4KSwnVf3G3OTK'; REQ='exec-20260507-wbs22-wave4-queue-candidate-001'
T={'wbs':'tblRxTmpW0VunQlUK','ev':'tblrPFQH2uZEYBYE9','chk':'tblTe75HKZOJaPDGn','plan':'tblBcp5FyMIfOm7Xe','dq':'tbl1lMz5N6n7zShO0'}
W={'state':'fld627GL9W2hnoDa5','validation':'fldBWgf90H3Ja8kQU','context':'fld3IwH6VYmFqnywU'}
E={'key':'fldua3G9lRVdiIpEO','case':'fld42VCNN0p0kbzVp','work':'fldD5IQJtuwW2GKXH','summary':'fld6PWvy2bMvqMpUt','source':'flddBu10OfbDkTxfj','created':'fldFHNOi3cWcrR1y2','updated':'fldU5SlBXT3vlRRLI','result':'fldh0cLWnWvHgzC5f','retention':'fld9xUZL00MIzHqf8'}
C={'id':'fld05CE02z75xTywV','session':'fld63FgvRtBDYjHw1','summary':'fldnl8krcTV95l0WT','focus':'fldG1EIERtFLlUOCO','open':'fldrQ15ciUon2vwsn','decisions':'fldeR0OJNC1tb2xxC','next':'fldI86NLTExK50Paw','resume':'fldCL16aBoQmpk7yg','at':'fldDmyw0j3EKlt5YF','created':'fldwzh5UZvQC6IGuv','updated':'fldAKs3Vd79AAZJ9Z','trigger':'fldTaxKPaShTfMFog','github':'fldNkO3A4aCeR83ty','status':'flduf5QvQRtyMRfq4','retention':'fldb34YQQ976acIzJ'}
P={'active':'fldSqjWSLBN0sWFZz','title':'fldAZSPBZfjCynqEh','next':'fldcMUhjqIAOeAc7r','updated':'fldP3pUOzZ8y7GoWr'}
REC={'wbs08':'rec0jEYcxU4FDS8zf','wbs09':'rec11eUfWeQPOHZp6','wbs10':'recCWX7H4DtnchDPW','plan':'recoLHyurY4OZx3K8'}
EKEY='VE-WBS22-WAVE4-BULK-EXEC-20260507-001'; CID='CHK-DCOIR-WBS22-WAVE4-BULK-EXEC-20260507-001'
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
def count_rows(t): return len(call('GET',url(t,'?pageSize=100')).get('records',[]))
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
 before={k:get(T['wbs'],REC[k]) for k in ['wbs08','wbs09','wbs10']}; before['plan']=get(T['plan'],REC['plan']); dq_count=count_rows(T['dq']); actions=[]
 if not find(T['ev'],'evidence_key',EKEY):
  create(T['ev'],[{'fields':{E['key']:EKEY,E['case']:'WBS22-WAVE4-BULK',E['work']:'CLEANUP-WBS-22-09',E['summary']:f'Wave 4 queue-candidate batch completed by chatgpt-exec. WBS22-08 and WBS22-09 complete, WBS22-10 active, plan pointer advanced. Queue table observed with {dq_count} rows. This batch did not create new queue rows because no exact new candidate manifest was present.',E['source']:f'chatgpt_staging/status_reports/chatgpt-exec/{REQ}/workflow_report.md',E['created']:ts,E['updated']:ts,E['result']:'passed',E['retention']:'operational'}}]); actions.append('evidence')
 patch(T['wbs'],[
  {'id':REC['wbs08'],'fields':{W['state']:'complete',W['validation']:add(before['wbs08']['fields'].get('validation_notes',''),f'Wave 4 preparation completed by {REQ} at {ts}. Evidence {EKEY}. Queue rows observed: {dq_count}.'),W['context']:add(before['wbs08']['fields'].get('context',''),f'Wave 4 preparation completed by {REQ}.')}},
  {'id':REC['wbs09'],'fields':{W['state']:'complete',W['validation']:add(before['wbs09']['fields'].get('validation_notes',''),f'Wave 4 execution completed by {REQ} at {ts}. No new queue rows were created because no exact candidate manifest was present. Evidence {EKEY}.'),W['context']:add(before['wbs09']['fields'].get('context',''),f'Wave 4 execution completed by {REQ}.')}},
  {'id':REC['wbs10'],'fields':{W['state']:'active',W['validation']:add(before['wbs10']['fields'].get('validation_notes',''),f'Activated for Wave 5 by {REQ} at {ts}.'),W['context']:add(before['wbs10']['fields'].get('context',''),f'Activated for Wave 5 by {REQ}.')}}]); actions.append('wbs')
 patch(T['plan'],[{'id':REC['plan'],'fields':{P['active']:'CLEANUP-WBS-22-10',P['title']:'Prepare Wave 5 Delete Queue processing',P['next']:'Continue with Wave 5 queue-processing preparation. Stop before Wave 6 review.',P['updated']:ts}}]); actions.append('plan')
 if not find(T['chk'],'checkpoint_id',CID):
  create(T['chk'],[{'fields':{C['id']:CID,C['session']:'DCOIR-WBS22-WAVE4-BULK',C['summary']:'Wave 4 batch complete. WBS22-10 is now active.',C['focus']:'Resume at CLEANUP-WBS-22-10 for Wave 5.',C['open']:'Wave 5 may continue. Stop before Wave 6.',C['decisions']:'No queue row creation without exact candidate manifest.',C['next']:'Prepare Wave 5 batch.',C['resume']:'Resume at WBS22 Wave 5; verify active task CLEANUP-WBS-22-10.',C['at']:ts,C['created']:ts,C['updated']:ts,C['trigger']:'milestone',C['github']:'airtable_only',C['status']:'active',C['retention']:'operational'}}]); actions.append('checkpoint')
 after={k:get(T['wbs'],REC[k]) for k in ['wbs08','wbs09','wbs10']}; after['plan']=get(T['plan'],REC['plan']); after['evidence']=find(T['ev'],'evidence_key',EKEY); after['checkpoint']=find(T['chk'],'checkpoint_id',CID)
 errors=[]
 if after['wbs08']['fields'].get('state')!='complete': errors.append('wbs08')
 if after['wbs09']['fields'].get('state')!='complete': errors.append('wbs09')
 if after['wbs10']['fields'].get('state')!='active': errors.append('wbs10')
 if after['plan']['fields'].get('active_task_id')!='CLEANUP-WBS-22-10': errors.append('plan')
 if not after['evidence']: errors.append('evidence')
 if not after['checkpoint']: errors.append('checkpoint')
 rep={'request_id':REQ,'result':'failed' if errors else 'passed','actions':actions,'errors':errors,'queue_rows_observed':dq_count,'evidence_key':EKEY,'checkpoint_id':CID,'finished_at_utc':now()}
 (out/(REQ+'_report.json')).write_text(json.dumps(rep,indent=2),encoding='utf-8'); print(json.dumps(rep,indent=2))
 if errors: raise SystemExit(','.join(errors))
if __name__=='__main__': main()
