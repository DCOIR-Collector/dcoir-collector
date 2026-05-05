$ErrorActionPreference='Stop'
[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12
$token=[Environment]::GetEnvironmentVariable('DCOIR_AIRTABLE_TOKEN','Machine')
$base=[Environment]::GetEnvironmentVariable('DCOIR_AIRTABLE_BASE_ID','Machine')
if([string]::IsNullOrWhiteSpace($token)){throw 'Missing DCOIR_AIRTABLE_TOKEN'}
if([string]::IsNullOrWhiteSpace($base)){throw 'Missing DCOIR_AIRTABLE_BASE_ID'}
$headers=@{Authorization="Bearer $token";'Content-Type'='application/json'}
function Upsert($TableId,$MergeFieldName,[array]$Records){$body=@{performUpsert=@{fieldsToMergeOn=@($MergeFieldName)};records=$Records;typecast=$false}|ConvertTo-Json -Depth 100 -Compress;Invoke-RestMethod -Method Patch -Uri "https://api.airtable.com/v0/$base/$TableId" -Headers $headers -Body $body|Out-Null}
$plan='PLAN-AIRTABLE-CLEANUP-RESTRUCTURE';$review='2026-08-05';$wbs='tblRxTmpW0VunQlUK';$scaf='tblvtcId7PiFKvfKO';$plans='tblBcp5FyMIfOm7Xe'
$csv=@'
P,T,S,G,A,D,C
02.01,Confirm table review inputs,airtable,planning_only,Discovery evidence,Inputs are available or evidence gaps are documented,Do not begin table review from chat memory
02.02,Create table review template,governance,planning_only,Review rubric,Rubric covers purpose authority retention dependencies risk searchability and enforcement,Standardizes every table review
02.03,Define table review order,airtable,planning_only,All tables,Tables are ordered by authority dependency risk and value,High authority tables come first
02.04,Assess table purpose and relevance,airtable,planning_only,Each table,Each table has purpose and current relevance notes,Prevents stale surfaces from being preserved by habit
02.05,Assess dependencies and cleanup risk,airtable,planning_only,Each table,Dependencies and risk are documented,Future action depends on dependency evidence
02.06,Close out table review methodology,validation,planning_only,WBS 02,All WBS 02 children are resolved and next handoff is clear,No table action occurs here
03.01,Classify authoritative structured fields,airtable,planning_only,Structured fields,Authoritative state fields are identified,ChatGPT should query these first
03.02,Classify explanatory free-text fields,airtable,planning_only,Text fields,Explanatory fields are identified,Free text is context not authority
03.03,Identify risky free-text authority,airtable,planning_only,Text fields,Risky text-as-state fields are flagged for redesign,Prevents prose from carrying decisions
03.04,Define standard note format,governance,planning_only,Notes fields,Standard note sections are defined,Improves consistency without over-structuring
03.05,Map text-to-structure candidates,airtable,planning_only,Text fields,Candidate fields for later structured replacement are listed,No field change occurs here
03.06,Close out field boundary model,validation,planning_only,WBS 03,Boundary rules are ready for table use,Future sessions can apply without chat context
04.01,List ID-related fields,airtable,planning_only,ID fields,ID-like fields are inventoried by table,Foundation for calculated IDs
04.02,Define table-specific ID components,airtable,planning_only,ID components,Each table has proposed controlled ID parts,Avoids universal formula mistakes
04.03,Define canonical slug sources,governance,planning_only,Slug parts,Slug values come from standardized fields,Prevents near-duplicate vocabulary drift
04.04,Define uniqueness suffix options,airtable,planning_only,Unique suffix,Each table has suffix strategy and collision note,Meaningful IDs remain unique
04.05,Define dedupe signatures,airtable,planning_only,Dedupe keys,Each table gets dedupe signature proposal,Supports pre-write duplicate checks
04.06,Close out ID standard,validation,planning_only,WBS 04,ID and dedupe recommendations are ready,No formula change occurs here
05.01,Inventory select fields,airtable,planning_only,Select fields,Select fields and options are listed,Supports taxonomy design
05.02,Classify authoritative single-selects,airtable,planning_only,Single-select fields,Decision fields are identified,Single-selects carry definitive state
05.03,Classify supplemental multi-select tags,airtable,planning_only,Multi-select fields,Tag fields are marked supplemental unless justified,Prevents tag sprawl as authority
05.04,Draft option interpretation rules,governance,planning_only,Select options,Important options have meaning and use boundaries,Reduces subjective option use
05.05,Define vocabulary change process,governance,operator_review,Select option governance,Future option changes require approval and validation,Prevents taxonomy drift
05.06,Close out taxonomy design,validation,planning_only,WBS 05,Vocabulary recommendations are ready,No option change occurs here
06.01,Define cleanup category criteria,governance,planning_only,Classification model,Every category has concrete criteria,Consistent classification matters
06.02,Define strict archive test,governance,planning_only,Archive criteria,Archive requires future use review date and removal condition,Prevents over-saving stale material
06.03,Define merge candidate evidence,airtable,operator_review,Merge candidates,Survivor rationale and dependency review are required,No merge is authorized here
06.04,Define removal candidate gate,governance,operator_review,Removal candidates,Dependency review and approval are required before later action,No removal is authorized here
06.05,Define operator-review triggers,governance,planning_only,Ambiguous items,Unclear authority conflict or survivor decisions route to review,Judgment calls stay visible
06.06,Close out classification model,validation,planning_only,WBS 06,Criteria are ready for application,No cleanup action occurs here
07.01,Map Airtable findings to skill impacts,skill,planning_only,DCOIR skills,Skill impact questions are part of every finding,Skills are downstream surfaces
07.02,Map findings to project instructions,project_config,planning_only,Project instructions,Instruction impacts are captured as candidates only,No configuration change occurs here
07.03,Map findings to sources,source,planning_only,Project sources,Source impacts are captured with role and freshness concerns,No source change occurs here
07.04,Map findings to GitHub surfaces,github,planning_only,Repo surfaces,Repo impact candidates are captured by path and role,No repo production change occurs here
07.05,Map findings to automation needs,automation,planning_only,Automation candidates,Monitoring or tool needs are captured,No automation is activated here
07.06,Close out cross-surface review model,validation,planning_only,WBS 07,Impact matrix is ready for table review,Prevents Airtable-only fixes
08.01,List enforcement rules,governance,planning_only,Rule set,Rules are enumerated with intended outcomes,Rules alone are not enforcement
08.02,Assign accountable mechanism per rule,governance,planning_only,Rule mechanisms,Each rule has a named control,Provides a thing to blame
08.03,Define pre-write checks,automation,planning_only,Pre-write validation,Write-related rules have concrete checks,Supports future Write Gate
08.04,Define post-write readback checks,validation,planning_only,Readback checks,Write-related rules have after-action checks,Prevents unverified completion
08.05,Define drift detection methods,automation,planning_only,Drift checks,Rules have detection methods for recurring degradation,Prevents repeat cleanup cycles
08.06,Close out enforcement assurance,validation,planning_only,WBS 08,Rule-to-mechanism matrix is ready,No enforcement tooling is installed here
09.01,Define Write Gate inputs,airtable,planning_only,Write payloads,Inputs include approval schema payload dedupe and readback plan,No PASS without inputs
09.02,Define PASS FAIL contract,governance,planning_only,Gate decision model,PASS and FAIL conditions are explicit,No PASS means no Airtable write
09.03,Define duplicate search contract,airtable,planning_only,Dedupe searches,Required pre-create searches are defined,Search failure blocks create
09.04,Define schema and select validation,airtable,planning_only,Live schema,Target fields and select values are validated,Prevents invented values
09.05,Define implementation candidate,skill,skill_change,Possible write gate skill,Candidate skill contract is scoped for later approval,No skill is created here
09.06,Close out Write Gate design,validation,planning_only,WBS 09,Gate design is ready for implementation decision,No operational gate is installed here
10.01,Identify monitored review fields,airtable,planning_only,Review fields,Fields feeding monitoring are listed,Review dates must not be inert
10.02,Define due-review workflow,automation,planning_only,Review workflow,Due records route to review process,No monitor is activated here
10.03,Define drift checks,automation,planning_only,Drift signals,Checks cover bad IDs invalid values duplicate signatures stale records and blanks,Drift is detected not silently tolerated
10.04,Define alert and decision path,workflow,planning_only,Review routing,Signals route to operator-assisted decisions,No gated action is automatic
10.05,Define monitoring evidence format,validation,planning_only,Monitoring reports,Output format supports evidence and readback,Signals become actionable
10.06,Close out monitoring design,validation,planning_only,WBS 10,Monitoring design is ready for tooling review,No monitor starts here
11.01,Define before-snapshot requirements,validation,planning_only,Pre-change evidence,Required before evidence is defined,Supports recovery and audit
11.02,Define action evidence requirements,validation,planning_only,Execution evidence,Lane command target and affected objects must be recorded,Supports traceability
11.03,Define after-readback requirements,validation,planning_only,Post-action state,Expected state must be read back and compared,Prevents unsupported readiness claims
11.04,Define searchability tests,validation,planning_only,Lookup evidence,Records must be findable by key alias source and purpose,Measures cleanup goal
11.05,Define dependency verification checks,validation,planning_only,Dependencies,Relationships must still resolve after later actions,Prevents broken links
11.06,Close out validation strategy,validation,planning_only,WBS 11,Validation plan is ready for future execution tasks,No evidence rows required yet
12.01,Define in-session Airtable lane,airtable,planning_only,Connector lane,Criteria define when direct Airtable connector is acceptable,Direct writes remain gated
12.02,Define chatgpt-exec lane,workflow,planning_only,GitHub Actions lane,Criteria define when workflow lane is preferred for evidence and repeatability,Matches autonomous execution preference
12.03,Define GitHub Desktop speed lane,github,planning_only,Local repo lane,Criteria define when operator local lane is best,Supports manual repo work safely
12.04,Define reusable tool lane,automation,planning_only,Reusable tools,Criteria define when durable tools are better than one-off scripts,Prevents ad hoc sprawl
12.05,Define manual review lane,governance,planning_only,Judgment-heavy decisions,Operator review is required for ambiguous irreversible or authority decisions,Human judgment stays explicit
12.06,Close out lane matrix,validation,planning_only,WBS 12,Lane decision matrix is ready,No execution lane switch occurs here
13.01,List explicit approval actions,governance,planning_only,Approval boundary,Actions requiring approval are listed,Planning language is not approval
13.02,Define approval phrase standard,governance,planning_only,Approval evidence,Approval must specify action target scope and lane,Prevents vague authorization
13.03,Define dependency review gate,airtable,planning_only,Dependency-sensitive actions,Dependency review requirements are listed,Review precedes action
13.04,Define never-automatic actions,governance,planning_only,Hard stops,Actions that must never be automatic are listed,Protects high-risk operations
13.05,Tie approvals to Write Gate,airtable,planning_only,Write Gate approval check,Write Gate cannot PASS without required approval evidence,Unifies safety gates
13.06,Close out safety gates,validation,planning_only,WBS 13,Safety rules are ready for future sessions,No new approval is implied
14.01,Draft starter prompt elements,project_config,planning_only,Future session prompts,Required prompt elements are listed,Supports safe resume
14.02,Define missing-block hard stop,project_config,planning_only,Expertise block,Missing block causes hard stop before planning or execution,Prevents context loss
14.03,Define session mode declarations,project_config,planning_only,Session modes,Mode declaration controls allowed actions,Prevents planning-execution confusion
14.04,Define prompt update surfaces,source,planning_only,Prompt carriers,Instructions sources checkpoints and WBS context are mapped,Changes require approval
14.05,Define closeout handoff format,project_config,planning_only,Resume handoff,Handoff includes WBS state next action gates and evidence links,Supports blind future sessions
14.06,Close out prompt enforcement,validation,planning_only,WBS 14,Prompt enforcement design is ready,No instruction edit occurs here
15.01,Inventory DCOIR skills in scope,skill,planning_only,Skills,Potentially affected skills are listed,No skill modification occurs here
15.02,Check table and field assumptions,skill,planning_only,Skill references,Skill references to table field values and routes are identified,Finds stale assumptions
15.03,Check write behavior assumptions,skill,planning_only,Write paths,Skills that write or validate rows are flagged for Write Gate alignment,Prevents bypass patterns
15.04,Check routing and memory assumptions,skill,planning_only,Routing surfaces,Routing dependencies and retired-route risks are identified,Keeps skills aligned
15.05,Define skill update package plan,skill,skill_change,Affected skills,Update validation package and readback requirements are defined,Skill changes require later approval
15.06,Close out skill impact review,validation,planning_only,WBS 15,Skill impact matrix is ready,No skill package is created here
16.01,Inventory current project instruction constraints,project_config,planning_only,Current instructions,Relevant current rules are summarized,Prevents conflicts
16.02,Map needed instruction updates,project_config,planning_only,Candidate rules,Instruction update candidates are listed only,No configuration change occurs here
16.03,Define instruction conflict checks,project_config,planning_only,Rule conflicts,Potential conflicts route to operator decision,No silent override
16.04,Define instruction update evidence,validation,planning_only,Instruction readback,Future changes require diff readback and behavior check,Prevents unverified updates
16.05,Define instruction-source split,source,planning_only,Authority placement,Rules are assigned to instructions sources Airtable or skills as appropriate,Prevents duplicated authority
16.06,Close out project instruction review,validation,planning_only,WBS 16,Instruction impact review is ready,No instruction change occurs here
17.01,Inventory retained source attachments,source,planning_only,Project sources,Sources are listed with role and relevance,No source change occurs here
17.02,Check source freshness and conflicts,source,planning_only,Source set,Stale or conflicting guidance is identified,Prevents stale source authority
17.03,Map sources to Airtable authority,source,planning_only,Source relationships,Sources are classified as pointer runbook evidence or candidate obsolete,Supports Airtable-first authority
17.04,Define source replacement criteria,source,operator_review,Source disposition,Criteria govern keep replace or retire decisions,Source changes require approval
17.05,Define source readback validation,validation,planning_only,Source validation,Future changes require readback and conflict checks,Prevents unsupported replacement claims
17.06,Close out sources review,validation,planning_only,WBS 17,Source impact matrix is ready,No source is changed here
18.01,Inventory GitHub repo surfaces,github,planning_only,Repo surfaces,Potentially affected repo files workflows and tools are listed,GitHub remains support/source lane
18.02,Map workflow impacts,workflow,planning_only,Workflows,Workflow assumptions about Airtable and env names are identified,Prevents workflow drift
18.03,Map operator tool impacts,github,planning_only,Operator tools,Tools reading or writing Airtable are flagged,Supports tool alignment
18.04,Map repo documentation impacts,github,planning_only,Repo docs,Docs needing alignment are listed by path and role,Repo edits require approval
18.05,Define GitHub update lane and validation,github,github_change,Future repo changes,Lane and readback validation are defined,No production repo logic changes here
18.06,Close out GitHub impact review,validation,planning_only,WBS 18,GitHub impact matrix is ready,No repo source update occurs here
19.01,List automation needs,automation,planning_only,Automation candidates,Write Gate monitoring evidence export and drift needs are listed,Only repeated enforcement justifies automation
19.02,Classify automation surfaces,automation,planning_only,Implementation surfaces,Candidates map to Airtable GitHub ChatGPT skills workflows or tools,Toolbox means full project toolbox
19.03,Define automation safety gates,governance,planning_only,Automation gates,Automation may detect and report but gated actions require approval,Prevents unsafe autonomy
19.04,Define monitoring alert flow,workflow,planning_only,Alerts,Signals route to WBS operator review or evidence records,Keeps alerts actionable
19.05,Define reusable tool registry impact,automation,planning_only,Tool registry,New or borrowed tools must be registered and tracked,Prevents untracked scripts
19.06,Close out automation review,validation,planning_only,WBS 19,Automation architecture is ready,No automation is activated here
20.01,Build cross-surface dependency graph,mixed,planning_only,Dependencies,Dependencies between Airtable skills instructions sources GitHub and automation are mapped,Prevents partial updates
20.02,Define change ordering rules,mixed,planning_only,Sequencing rules,Order of changes across surfaces is defined,Keeps execution exact
20.03,Define batch boundaries,governance,planning_only,Execution waves,Work is divided into bounded waves,Supports session-bounded discipline
20.04,Define rollback and recovery checkpoints,validation,planning_only,Recovery planning,Each wave needs evidence and recovery notes,Prevents irreversible drift
20.05,Define approval bundles per wave,governance,operator_review,Approval waves,Operator approval scopes are grouped by surface and risk,Approval stays precise
20.06,Close out sequencing model,validation,planning_only,WBS 20,Execution sequencing model is ready,No execution wave starts here
21.01,Define WBS hierarchy rules,governance,planning_only,Hierarchy rules,Plan workstream task subtask and atomic levels are defined,Prevents flat completion errors
21.02,Define required WBS metadata,airtable,planning_only,WBS fields,Required metadata is specified,Future sessions can resume without chat memory
21.03,Define parent completion rule,governance,planning_only,Parent state,Parent cannot complete until children are resolved with evidence,Prevents missed subtasks
21.04,Define iterative decomposition rule,governance,planning_only,Further breakdown,Any child may be decomposed further before execution,Supports arbitrary depth
21.05,Define WBS readback checks,validation,planning_only,WBS records,Readback confirms rows order linkage and gates,Validates scaffold integrity
21.06,Close out WBS traceability model,validation,planning_only,WBS 21,Traceability model is ready and applied,No cleanup execution occurs here
22.05,Prevent scaffold sprawl during plan,governance,planning_only,New scaffold candidates,Every future scaffold object requires registry row purpose review date and pending disposition,Prevents temporary object bloat
22.06,Close out scaffold lifecycle model,validation,planning_only,WBS 22,Scaffold objects have disposition or approved extension,No scaffold closure without evidence
'@
$records=@();$parents=New-Object System.Collections.Generic.HashSet[string]
foreach($r in ($csv|ConvertFrom-Csv)){[void]$parents.Add($r.P.Split('.')[0]);$key='CLEANUP-WBS-'+($r.P -replace '\.','-');$parent='CLEANUP-WBS-'+$r.P.Split('.')[0];$rank=[int]$r.P.Split('.')[1];$records+=@{fields=[ordered]@{wbs_key=$key;plan_key=$plan;wbs_path=$r.P;parent_wbs_key=$parent;rank=$rank;title=$r.T;level='task';surface=$r.S;state='planned';gate=$r.G;target=$r.A;done_criteria=$r.D;validation_notes='Readback of this WBS row and later task evidence required. Planning scaffold only.';context=$r.C;review_after=$review}}}
for($i=0;$i -lt $records.Count;$i+=10){$chunk=@($records[$i..([Math]::Min($i+9,$records.Count-1))]);Upsert $wbs 'wbs_key' $chunk}
$parentRecords=@();foreach($p in $parents){$parentRecords+=@{fields=[ordered]@{wbs_key=('CLEANUP-WBS-'+$p);plan_key=$plan;wbs_path=$p;state='planned';done_criteria="Complete only when all ordered child tasks under WBS $p are complete skipped with reason or blocked/operator-review with evidence and readback.";validation_notes="Read back child rows under WBS $p before parent completion.";review_after=$review}}}
for($i=0;$i -lt $parentRecords.Count;$i+=10){$chunk=@($parentRecords[$i..([Math]::Min($i+9,$parentRecords.Count-1))]);Upsert $wbs 'wbs_key' $chunk}
$planUpdate=@{fields=[ordered]@{plan_id=$plan;active_task_id='CLEANUP-WBS-01-01';active_task_title='Confirm discovery scope and authority boundary';next_recommended_action='Begin WBS 01.01 and proceed through WBS hierarchy in order. Keep discovery and planning read-only until explicit execution approvals are issued.';last_updated_text='2026-05-05T14:45:00Z';review_after=$review}}
Upsert $plans 'plan_id' @($planUpdate)
$scafRec=@{fields=[ordered]@{scaffold_key='SCAFFOLD-GITHUB-WORKFLOW-CHATGPT-EXEC-ALL-WBS-DECOMPOSITION';plan_key=$plan;scaffold_name='chatgpt-exec full WBS decomposition request';scaffold_type='workflow';status='active_scaffold';purpose='Uses GitHub Actions chatgpt-exec to seed child WBS planning tasks across the remaining top-level workstreams.';created_surface='GitHub Actions';created_locator='chatgpt_staging/exec_requests/exec-20260505-cleanup-wbs-all-decompose-001.json and chatgpt_staging/exec_scripts/cleanup_wbs_all_decompose_001.ps1';final_disposition='pending';review_after=$review;notes='Track and disposition this workflow/script scaffold under WBS 22 at plan conclusion.'}}
Upsert $scaf 'scaffold_key' @($scafRec)
$downloads=[Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR','Machine');if(-not [string]::IsNullOrWhiteSpace($downloads)){New-Item -ItemType Directory -Path $downloads -Force|Out-Null;[ordered]@{request_id='exec-20260505-cleanup-wbs-all-decompose-001';child_rows_seeded=$records.Count;parent_rows_touched=$parentRecords.Count;cleanup_execution=$false;table_changes='WBS planning rows and scaffold registry tracking row only';finished_utc=(Get-Date).ToUniversalTime().ToString('o')}|ConvertTo-Json -Depth 10|Set-Content -Path (Join-Path $downloads 'cleanup_wbs_all_decomposition_summary.json') -Encoding UTF8}
Write-Host "Seeded full remaining WBS decomposition: $($records.Count) child tasks and $($parentRecords.Count) parent updates."
