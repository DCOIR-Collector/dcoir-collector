# Workflow Phases

Use this reference to map DCOIR operator state to the best next action.

## Phase 1: collector staged or ready to run
Signals:
- operator asks how to launch collection
- request is for exact endpoint-side execution

Default next move:
- give the exact Elastic Defend `execute --command` syntax for the requested collector mode
- use the runtime filename `DCOIR_Collector.ps1`

## Phase 2: collect completed and bundle is ready
Signals:
- collector output includes `COLLECT_BUNDLE_PATH=`
- collector output includes `NEXT_GET_FILE=get-file --path ... collect bundle`

Default next move:
- retrieval is usually the best next operator action
- mention cleanup only as the immediate follow-on when the output also provides a cleanup cue

## Phase 3: enrich session started
Signals:
- output indicates an enrich session was created
- output gives a next action to add more targets or finalize later

Default next move:
- respect the enrich session state
- if the operator wants more data, choose the narrowest `enrich-add-*` path that matches the reviewed need
- do not finalize early unless the requested scope is complete

## Phase 4: enrich session finalized and enrich bundle is ready
Signals:
- output includes `ENRICH_BUNDLE_PATH=`
- output includes `NEXT_GET_FILE=get-file --path ... enrich bundle`

Default next move:
- retrieve the enrich bundle first
- cleanup can follow if the output explicitly provides it

## Phase 5: cleanup ready but not yet run
Signals:
- output includes `CLEANUP_COMMAND=`
- output or quick steps say to keep the current run until cleanup is explicitly run

Default next move:
- do not imply cleanup is complete
- if retrieval is still pending, retrieval usually comes before cleanup

## Phase 6: cleanup complete
Signals:
- output includes `CLEANUP_STATUS=COMPLETE`

Default next move:
- collection or enrichment can restart cleanly if the operator needs a new run
- do not recommend retrieving a bundle that the operator already discarded unless the output still shows a retained path

## Analyst interpretation cues
Some output includes interpretation guidance such as signer review, ACL review, EVTX review, or file retrieval guidance.

Defaults:
- prefer the single strongest next step tied to that interpretation block
- when the guidance says to retrieve the file and review locally, keep endpoint retrieval and local review as separate lanes
