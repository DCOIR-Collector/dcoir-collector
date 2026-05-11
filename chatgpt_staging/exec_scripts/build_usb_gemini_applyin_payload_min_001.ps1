$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$RequestId = 'applyin-20260511-gemini-usb-subagent-clean-001'
$Branch = 'chatgpt/usb-violations-gemini-subagent-current-main-20260511'
$Repo = (Get-Location).Path
$Work = Join-Path $Repo "chatgpt_staging\work\$RequestId"
$Src = Join-Path $Work 'source'
$Py = Join-Path $Work 'patch.py'
$Payload = Join-Path $Repo "chatgpt_staging\in\$RequestId\payload.zip.b64"
Remove-Item -Recurse -Force $Work -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $Src | Out-Null

git fetch origin $Branch --depth=1
if ($LASTEXITCODE -ne 0) { throw 'fetch failed' }
$fromBranch = @(
 'project_sources/gemini/bundle_source/01_GEMINI_AGENT_BUILD/Sub_Agent_11_USB_Violations_Report_Composer.md.txt',
 'project_sources/gemini/bundle_source/Gemini_Bundle_Source_Manifest.json',
 'project_sources/gemini/bundle_source/01_GEMINI_AGENT_BUILD/Generated_DCOIR_Gemini_Agent_Index.md.txt',
 'project_sources/gemini/bundle_source/00_START_HERE/Gemini_Build_Quick_Start.md.txt'
)
foreach ($p in $fromBranch) {
  $out = Join-Path $Src $p
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $out) | Out-Null
  git show "FETCH_HEAD:$p" | Out-File -FilePath $out -Encoding utf8
  if ($LASTEXITCODE -ne 0) { throw "git show failed: $p" }
}

$python = @'
from pathlib import Path
REPO=Path.cwd(); RID='applyin-20260511-gemini-usb-subagent-clean-001'; SRC=REPO/'chatgpt_staging'/'work'/RID/'source'
def r(p): return (REPO/p).read_text(encoding='utf-8')
def w(p,t):
    q=SRC/p; q.parent.mkdir(parents=True, exist_ok=True); q.write_text(t, encoding='utf-8', newline='\n')
def one(t,a,b,n):
    if t.count(a)!=1: raise SystemExit(f'{n} matches {t.count(a)}')
    return t.replace(a,b,1)
# Prime minimal routing
p='project_sources/gemini/bundle_source/01_GEMINI_AGENT_BUILD/Prime_Agent_DCOIR_Gemini_Orchestrator.md.txt'
t=r(p)
t=one(t,'10. Output Contract Consistency Guard and Report Composer\n\nParent-agent orchestration rules:','10. Output Contract Consistency Guard and Report Composer\n11. USB Violations Report Composer\n\nParent-agent orchestration rules:','prime list')
t=one(t,'10. Output Contract Consistency Guard and Report Composer must render only the allowed analyst-facing final format and must include benign tuning guidance when a benign disposition is reached.\n11. No sub-agent may produce user-visible workflow narration, transfer language, or meta commentary.','10. Output Contract Consistency Guard and Report Composer must render only the allowed analyst-facing final format and must include benign tuning guidance when a benign disposition is reached.\n11. USB Violations Report Composer must activate only when the operator explicitly asks to prepare, validate, draft, or convert weekly USB violations report material.\n12. No sub-agent may produce user-visible workflow narration, transfer language, or meta commentary.','prime rules')
for old,new in [('12. If Query Planner','13. If Query Planner'),('13. If Query Planner','14. If Query Planner'),('14. If Query Planner','15. If Query Planner'),('15. If a narrow','16. If a narrow')]:
    t=t.replace(old,new,1)
t=one(t,'10. a request to answer version/build provenance for the Gemini agent\n','10. a request to answer version/build provenance for the Gemini agent\n11. a request to prepare, validate, draft, or convert a weekly USB violations report\n','prime trigger')
w(p,t)
# Attachment map
p='project_sources/gemini/bundle_source/00_START_HERE/Agent_Attachment_Map.md.txt'; t=r(p).replace('one-prime-plus-ten-sub-agent runtime topology','one-prime-plus-eleven-sub-agent runtime topology'); w(p,t)
# Knowledge 13 full small rewrite
p='knowledge/Knowledge - 13 - Gemini Agent Topology and Routing.md'
w(p,'''# Knowledge - 13 - Gemini Agent Topology and Routing\n\n_Gemini prime-agent and sub-agent routing model_\n\n**Summary:** The current Gemini topology is one prime agent plus eleven specialist sub-agents. The prime routes work; specialists own bounded lanes.\n\n---\n\n## Prime-agent role\n\nThe prime agent owns startup and intake posture, branch selection, specialist routing, evidence-first discipline, and final response coordination. The prime should not duplicate every specialist's job.\n\n---\n\n## Sub-agent ownership\n\n| Agent | Owns |\n| --- | --- |\n| 01 Session Readiness and Intake | startup, intake boundaries, readiness |\n| 02 Environment and Coverage Mapper | visibility, evidence surfaces, coverage assumptions |\n| 03 Alert Family Classifier | alert-family classification and benign-technology differentiation |\n| 04 Evidence and Provenance Analyst | source labels, proof boundaries, provenance |\n| 05 Query Planner and Syntax Guard | one best query/command and syntax correctness |\n| 06 Collector Execution and Bundle Workflow Orchestrator | collector justification, execution lane, bundle workflow |\n| 07 Collector Artifact Interpreter | collector output meaning and artifact priority |\n| 08 IOC Parsing and Public Enrichment Planner | indicator parsing and bounded public enrichment |\n| 09 Targeted Collection Designer | narrow evidence-gap reduction and targeted collection design |\n| 10 Output Contract Guard | final structure, decision state, and output consistency |\n| 11 USB Violations Report Composer | weekly USB violations report validation, ticket-prefix classification, split-output handling, and exact plaintext email block drafting |\n\n---\n\n## Routing rules\n\n- Stay in triage when current evidence can answer the question.\n- Use collector-aware agents only when collection, enrichment, retrieval, or artifact interpretation is actually in scope.\n- Use IOC enrichment only for evidence-grounded indicators.\n- Use targeted collection when a narrow evidence gap exists.\n- Use final-output enforcement only after the evidence path is clear.\n- Use the USB Violations Report Composer only when the operator explicitly asks to prepare, validate, draft, or convert weekly USB violations report material.\n\n---\n\n## Validation surfaces\n\nTopology changes should be checked against manifest topology inventory, generated agent index, prime-agent routing text, sub-agent descriptions/instructions, behavior scenario validation, and scenario validation rows in Airtable.\n\n---\n\n> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.\n''')
# Knowledge 15 and DOC11
p='knowledge/Knowledge - 15 - Gemini Attachment Set, Validation, and Maintenance.md'; t=r(p); t=t.replace('5. Update GitHub Actions required-surface checks.','5. Update GitHub Actions required-surface checks when non-manifest-governed surfaces change; Gemini topology required-file enforcement should remain manifest-driven.'); t=t.replace('- workflow checks enforce the current count and required files;','- workflow checks derive Gemini required files from the manifest and enforce required files without duplicating sub-agent counts;'); w(p,t)
p='project_sources/gemini/docs/DOC-11_DCOIR_Gemini_Creation_Pipeline_v1_0_0.txt'; t=r(p).replace('`Gemini_Bundle_Source_Manifest.json.txt`','`Gemini_Bundle_Source_Manifest.json`').replace('new ten-sub-agent topology','current manifest-listed sub-agent topology'); t=one(t,'- Validation must compare the manifest topology against the actual source-tree contents and fail on drift.\n','- Validation must compare the manifest topology against the actual source-tree contents and fail on drift.\n- Workflow required-surface validation must read Gemini bundle required files from the manifest rather than duplicating hardcoded sub-agent file lists.\n','doc11'); w(p,t)
# validate-on-push manifest-driven Gemini required files
p='.github/workflows/validate-on-push.yml'; t=r(p); lines=[]
for line in t.splitlines():
    if "'project_sources/gemini/bundle_source/" in line and 'Gemini_Bundle_Source_Manifest.json' not in line: continue
    lines.append(line)
t='\n'.join(lines)+'\n'
anchor='''          if ($missing.Count -gt 0) {\n            throw "Missing required governed surfaces: $($missing -join ', ')"\n          }\n          $knowledgeFiles = Get-ChildItem -LiteralPath knowledge -File -Filter 'Knowledge - *.md'\n'''
block='''          if ($missing.Count -gt 0) {\n            throw "Missing required governed surfaces: $($missing -join ', ')"\n          }\n          $geminiBundleRoot = 'project_sources/gemini/bundle_source'\n          $geminiManifestPath = Join-Path $geminiBundleRoot 'Gemini_Bundle_Source_Manifest.json'\n          $geminiManifest = Get-Content -LiteralPath $geminiManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json\n          $manifestRequired = @($geminiManifest.required_files | ForEach-Object { Join-Path $geminiBundleRoot ([string]$_) })\n          $manifestMissing = @($manifestRequired | Where-Object { -not (Test-Path -LiteralPath $_) })\n          if ($manifestMissing.Count -gt 0) { throw "Missing Gemini manifest-required surfaces: $($manifestMissing -join ', ')" }\n          $manifestSubAgents = @($geminiManifest.topology.sub_agent_files | ForEach-Object { [string]$_ })\n          $agentBuildRoot = Join-Path $geminiBundleRoot '01_GEMINI_AGENT_BUILD'\n          $bundleRootResolved = (Resolve-Path -LiteralPath $geminiBundleRoot).Path\n          $discoveredSubAgents = @(Get-ChildItem -LiteralPath $agentBuildRoot -File -Filter 'Sub_Agent_*.md.txt' | ForEach-Object { ($_.FullName.Substring($bundleRootResolved.Length + 1)).Replace('\\','/') })\n          $unlistedSubAgents = @($discoveredSubAgents | Where-Object { $_ -notin $manifestSubAgents })\n          if ($unlistedSubAgents.Count -gt 0) { throw "Discovered Gemini sub-agent files not listed in manifest topology: $($unlistedSubAgents -join ', ')" }\n          Write-Host "Gemini manifest-required surfaces validated: $($manifestRequired.Count) files; sub-agents: $($manifestSubAgents.Count)."\n          $knowledgeFiles = Get-ChildItem -LiteralPath knowledge -File -Filter 'Knowledge - *.md'\n'''
t=one(t,anchor,block,'validate block'); w(p,t)
# Behavior scenario marker
p='project_sources/gemini/tools/validate_dcoir_gemini_behavior_scenarios.py'; t=r(p)
if 'GeminiUSBViolationsReportComposer' not in t:
    scen="""    'GeminiUSBViolationsReportComposer': {\n        'description': 'The stored Gemini source should preserve the weekly USB violations report workflow and conservative parsing rules.',\n        'all_markers': ['usb violations', 'stuttgart', 'last friday', 'this friday', 'ticket', 'plaintext'],\n        'any_marker_groups': [\n            ['last week', \"last week's\"],\n            ['recipient', 'message draft'],\n        ],\n    },\n"""
    t=one(t,'\n}\n\n\ndef load_manifest','\n'+scen+'}\n\n\ndef load_manifest','scenario')
w(p,t)
print('payload sources prepared')
'@
New-Item -ItemType Directory -Force -Path $Work | Out-Null
$python | Out-File -FilePath $Py -Encoding utf8
python $Py
if ($LASTEXITCODE -ne 0) { throw 'source prep failed' }

$includes = @(
 'project_sources/gemini/bundle_source/01_GEMINI_AGENT_BUILD/Sub_Agent_11_USB_Violations_Report_Composer.md.txt=chatgpt_staging/work/applyin-20260511-gemini-usb-subagent-clean-001/source/project_sources/gemini/bundle_source/01_GEMINI_AGENT_BUILD/Sub_Agent_11_USB_Violations_Report_Composer.md.txt',
 'project_sources/gemini/bundle_source/Gemini_Bundle_Source_Manifest.json=chatgpt_staging/work/applyin-20260511-gemini-usb-subagent-clean-001/source/project_sources/gemini/bundle_source/Gemini_Bundle_Source_Manifest.json',
 'project_sources/gemini/bundle_source/01_GEMINI_AGENT_BUILD/Generated_DCOIR_Gemini_Agent_Index.md.txt=chatgpt_staging/work/applyin-20260511-gemini-usb-subagent-clean-001/source/project_sources/gemini/bundle_source/01_GEMINI_AGENT_BUILD/Generated_DCOIR_Gemini_Agent_Index.md.txt',
 'project_sources/gemini/bundle_source/01_GEMINI_AGENT_BUILD/Prime_Agent_DCOIR_Gemini_Orchestrator.md.txt=chatgpt_staging/work/applyin-20260511-gemini-usb-subagent-clean-001/source/project_sources/gemini/bundle_source/01_GEMINI_AGENT_BUILD/Prime_Agent_DCOIR_Gemini_Orchestrator.md.txt',
 'project_sources/gemini/bundle_source/00_START_HERE/Gemini_Build_Quick_Start.md.txt=chatgpt_staging/work/applyin-20260511-gemini-usb-subagent-clean-001/source/project_sources/gemini/bundle_source/00_START_HERE/Gemini_Build_Quick_Start.md.txt',
 'project_sources/gemini/bundle_source/00_START_HERE/Agent_Attachment_Map.md.txt=chatgpt_staging/work/applyin-20260511-gemini-usb-subagent-clean-001/source/project_sources/gemini/bundle_source/00_START_HERE/Agent_Attachment_Map.md.txt',
 'knowledge/Knowledge - 13 - Gemini Agent Topology and Routing.md=chatgpt_staging/work/applyin-20260511-gemini-usb-subagent-clean-001/source/knowledge/Knowledge - 13 - Gemini Agent Topology and Routing.md',
 'knowledge/Knowledge - 15 - Gemini Attachment Set, Validation, and Maintenance.md=chatgpt_staging/work/applyin-20260511-gemini-usb-subagent-clean-001/source/knowledge/Knowledge - 15 - Gemini Attachment Set, Validation, and Maintenance.md',
 'project_sources/gemini/docs/DOC-11_DCOIR_Gemini_Creation_Pipeline_v1_0_0.txt=chatgpt_staging/work/applyin-20260511-gemini-usb-subagent-clean-001/source/project_sources/gemini/docs/DOC-11_DCOIR_Gemini_Creation_Pipeline_v1_0_0.txt',
 '.github/workflows/validate-on-push.yml=chatgpt_staging/work/applyin-20260511-gemini-usb-subagent-clean-001/source/.github/workflows/validate-on-push.yml',
 'project_sources/gemini/tools/validate_dcoir_gemini_behavior_scenarios.py=chatgpt_staging/work/applyin-20260511-gemini-usb-subagent-clean-001/source/project_sources/gemini/tools/validate_dcoir_gemini_behavior_scenarios.py'
)
$argsList=@('tools/chatgpt_apply_in/build_payload_zip_b64.py','--repo-root','.','--request-id',$RequestId,'--allowed-root','project_sources/gemini/bundle_source','--allowed-root','project_sources/gemini/docs','--allowed-root','project_sources/gemini/tools','--allowed-root','knowledge','--allowed-root','.github/workflows','--output-dir','chatgpt_staging/in','--allow-workflow-changes','--workflow-change-reason','Make validate-on-push derive Gemini required bundle surfaces from the Gemini manifest while adding the USB report sub-agent.')
foreach($i in $includes){$argsList+=@('--include',$i)}
python @argsList
if ($LASTEXITCODE -ne 0) { throw 'payload build failed' }
if (-not (Test-Path -LiteralPath $Payload -PathType Leaf)) { throw 'payload missing' }
$txt=Get-Content -LiteralPath $Payload -Raw -Encoding ASCII
$compact=($txt -split '\s+') -join ''
if(($compact.Length % 4) -ne 0){throw 'invalid b64 length'}
[Convert]::FromBase64String($compact)|Out-Null

git config user.name 'github-actions[bot]'
git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
git add -- "chatgpt_staging/in/$RequestId/payload.zip.b64"
git commit -m 'Stage USB Gemini clean apply-in payload'
git push
Write-Host "payload staged"
