#!/usr/bin/env python3
from __future__ import annotations
import datetime as dt, json, os, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

API = 'https://api.airtable.com/v0'
BASE = os.environ.get('DCOIR_AIRTABLE_BASE_ID') or 'appM4KSwnVf3G3OTK'
REQ = 'exec-20260507-wbs22-wave1-bulk-evidence-001'
T = {
  'wbs':'tblRxTmpW0VunQlUK', 'ev':'tblrPFQH2uZEYBYE9',
  'chk':'tblTe75HKZOJaPDGn', 'plan':'tblBcp5FyMIfOm7Xe'
}
W = {'state':'fld627GL9W2hnoDa5','validation':'fldBWgf90H3Ja8kQU','context':'fld3IwH6VYmFqnywU'}
E = {'key':'fldua3G9lRVdiIpEO','case':'fld42VCNN0p0kbzVp','work':'fldD5IQJtuwW2GKXH','summary':'fld6PWvy2bMvqMpUt','source':'flddBu10OfbDkTxfj','created':'fldFHNOi3cWcrR1y2','updated':'fldU5SlBXT3vlRRLI','result':'fldh0cLWnWvHgzC5f','retention':'fld9xUZL00MIzHqf8'}
C = {'id':'fld05CE02z75xTywV','session':'fld63FgvRtBDYjHw1','summary':'fldnl8krcTV95l0WT','focus':'fldG1EIERtFLlUOCO','open':'fldrQ15ciUon2vwsn','decisions':'fldeR0OJNC1tb2xxC','next':'fldI86NLTExK50Paw','resume':'fldCL16aBoQmpk7yg','at':'fldDmyw0j3EKlt5YF','created':'fldwzh5UZvQC6IGuv','updated':'fldAKs3Vd79AAZJ9Z','trigger':'fldTaxKPaShTfMFog','github':'fldNkO3A4aCeR83ty','status':'flduf5QvQRtyMRfq4','retention':'fldb34YQQ976acIzJ'}
P = {'active':'fldSqjWSLBN0sWFZz','title':'fldAZSPBZfjCynqEh','next':'fldcMUhjqIAOeAc7r','updated':'fldP3pUOzZ8y7GoWr'}
REC = {'wbs03':'recpMq2l7OjE5YfoK','wbs04':'recSJWdke5hsh9E4H','plan':'recoLHyurY4OZx3K8'}
EKEY = 'VE-WBS22-WAVE1-BULK-EXEC-20260507-001'
CID = 'CHK-DCOIR-WBS22-WAVE1-BULK-EXEC-20260507-001'

def now(): return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')

def req(method, url, body=None):
    token = os.environ.get('DCOIR_AIRTABLE_TOKEN') or os.environ.get('AIRTABLE_TOKEN')
    if not token: raise SystemExit('missing airtable token env')
    data = None if body is None else json.dumps(body).encode('utf-8')
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header('Authorization', 'Bearer '+token); r.add_header('Content-Type','application/json')
    for i in range(6):
        try:
            with urllib.request.urlopen(r, timeout=90) as resp:
                raw = resp.read().decode('utf-8','replace')
                return {} if not raw else json.loads(raw)
        except urllib.error.HTTPError as e:
            raw = e.read().decode('utf-8','replace')
            if e.code == 429 and i < 5: time.sleep(2+i); continue
            raise RuntimeError(f'{method} failed HTTP {e.code}: {raw[:800]}')

def u(table, suffix=''):
    return f"{API}/{BASE}/{urllib.parse.quote(table, safe='')}{suffix}"

def get(table, rid): return req('GET', u(table, '/'+urllib.parse.quote(rid, safe='')))

def find(table, field_name, value):
    formula = "{"+field_name+"}='"+value.replace("'","\\'")+"'"
    data = req('GET', u(table, '?' + urllib.parse.urlencode({'filterByFormula':formula,'pageSize':'10'})))
    rows = data.get('records', [])
    return rows[0] if rows else None

def create(table, rows):
    out=[]
    for i in range(0,len(rows),10): out += req('POST', u(table), {'records':rows[i:i+10]}).get('records', [])
    return out

def patch(table, rows):
    out=[]
    for i in range(0,len(rows),10): out += req('PATCH', u(table), {'records':rows[i:i+10]}).get('records', [])
    return out

def note(existing, add):
    existing = existing or ''
    return existing if add in existing else ((existing.rstrip()+'\n\n'+add).strip() if existing.strip() else add)

def main():
    ts = now(); outdir = Path(os.environ.get('DCOIR_DOWNLOADS_DIR') or os.getcwd()) / REQ; outdir.mkdir(parents=True, exist_ok=True)
    before = {'wbs03':get(T['wbs'],REC['wbs03']), 'wbs04':get(T['wbs'],REC['wbs04']), 'plan':get(T['plan'],REC['plan'])}
    actions=[]
    if not find(T['ev'], 'evidence_key', EKEY):
        create(T['ev'], [{'fields':{E['key']:EKEY,E['case']:'WBS22-WAVE1-BULK-EXECUTION',E['work']:'CLEANUP-WBS-22-03',E['summary']:'Wave 1 evidence/backfill bulk execution via chatgpt-exec. WBS22-03 completed, WBS22-04 activated, plan pointer advanced. No schema, queue-processing, duplicate/merge, source, skill, workflow, scaffold, or Wave 6 work was performed.',E['source']:f'chatgpt_staging/status_reports/chatgpt-exec/{REQ}/workflow_report.md',E['created']:ts,E['updated']:ts,E['result']:'passed',E['retention']:'operational'}}]); actions.append('created evidence')
    add03 = f'Wave 1 bulk execution completed by {REQ} at {ts}. Evidence {EKEY}. Scope: evidence/backfill and progression only.'
    add04 = f'Activated for Wave 2 preparation by {REQ} at {ts}. Run Wave 2 sequentially with compatible bulk batches.'
    patch(T['wbs'], [
      {'id':REC['wbs03'], 'fields':{W['state']:'complete', W['validation']:note(before['wbs03'].get('fields',{}).get('validation_notes',''), add03), W['context']:note(before['wbs03'].get('fields',{}).get('context',''), add03)}},
      {'id':REC['wbs04'], 'fields':{W['state']:'active', W['validation']:note(before['wbs04'].get('fields',{}).get('validation_notes',''), add04), W['context']:note(before['wbs04'].get('fields',{}).get('context',''), add04)}}
    ]); actions.append('updated WBS batch')
    patch(T['plan'], [{'id':REC['plan'], 'fields':{P['active']:'CLEANUP-WBS-22-04',P['title']:'Prepare Wave 2 status review retention and pointer cleanup',P['next']:'Continue WBS22 with Wave 2 preparation. Use compatible bulk Airtable batches via chatgpt-exec where practical. Stop before Wave 6 review.',P['updated']:ts}}]); actions.append('advanced plan pointer')
    if not find(T['chk'], 'checkpoint_id', CID):
        create(T['chk'], [{'fields':{C['id']:CID,C['session']:'DCOIR-WBS22-WAVE1-BULK',C['summary']:'Wave 1 bulk evidence/backfill completed via chatgpt-exec. WBS22-03 complete, WBS22-04 active, plan pointer advanced.',C['focus']:'Resume at CLEANUP-WBS-22-04 for Wave 2 preparation.',C['open']:'Waves 2-5 proceed sequentially with compatible bulk batches. Stop before Wave 6 review.',C['decisions']:'Use compact reports and avoid large Airtable display grids. Use chatgpt-exec/operator-tool patterns where practical.',C['next']:'Prepare and execute Wave 2 compatible bulk updates from live Airtable readback.',C['resume']:'Resume AFRICOM_SOC_IR / DCOIR at WBS22 Wave 2. Verify plan active task CLEANUP-WBS-22-04.',C['at']:ts,C['created']:ts,C['updated']:ts,C['trigger']:'milestone',C['github']:'airtable_only',C['status']:'active',C['retention']:'operational'}}]); actions.append('created checkpoint')
    after = {'wbs03':get(T['wbs'],REC['wbs03']), 'wbs04':get(T['wbs'],REC['wbs04']), 'plan':get(T['plan'],REC['plan']), 'evidence':find(T['ev'],'evidence_key',EKEY), 'checkpoint':find(T['chk'],'checkpoint_id',CID)}
    errors=[]
    if after['wbs03'].get('fields',{}).get('state') != 'complete': errors.append('WBS22-03 not complete')
    if after['wbs04'].get('fields',{}).get('state') != 'active': errors.append('WBS22-04 not active')
    if after['plan'].get('fields',{}).get('active_task_id') != 'CLEANUP-WBS-22-04': errors.append('plan pointer not advanced')
    if not after['evidence']: errors.append('evidence missing')
    if not after['checkpoint']: errors.append('checkpoint missing')
    report={'request_id':REQ,'result':'failed' if errors else 'passed','actions':actions,'errors':errors,'evidence_key':EKEY,'checkpoint_id':CID,'before_compact':{k:v.get('id') for k,v in before.items()},'after_compact':{k:(v.get('id') if v else None) for k,v in after.items()},'finished_at_utc':now()}
    (outdir/(REQ+'_report.json')).write_text(json.dumps(report, indent=2), encoding='utf-8')
    (outdir/(REQ+'_report.md')).write_text('# '+REQ+'\n\nResult: **'+report['result']+'**\n\nEvidence: `'+EKEY+'`\n\nCheckpoint: `'+CID+'`\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    if errors: raise SystemExit('; '.join(errors))

if __name__ == '__main__': main()
