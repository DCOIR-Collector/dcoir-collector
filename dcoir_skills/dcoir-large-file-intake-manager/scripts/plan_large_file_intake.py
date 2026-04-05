#!/usr/bin/env python3
from __future__ import annotations
import argparse
PLAYBOOK = {'too-large': ('use metadata-first triage and request the highest-value narrow excerpt next', 'bounded confidence until the requested excerpt is reviewed'),'missing': ('pivot to the next best adjacent artifact or metadata source', 'bounded confidence because the intended artifact is absent'),'partial': ('analyze the present slice, state bounded confidence, then request the most decision-relevant missing slice', 'bounded confidence because only part of the artifact set is present')}
NEXT = {'merged_baseline_report':'request the findings summary plus the single most suspicious category block','metadata_report':'request the process, persistence, or network section tied to the current lead','final_artifacts':'request the one most suspicious file or the narrowest decisive excerpt','enrichment_report':'request the enrichment block tied to the lead under review','retrieved_artifact':'request the smallest behavior-defining excerpt such as the task action, script function, config key, or registry branch','raw_event_export':'request the event id, timestamp window, and the narrowest decisive event excerpt','generic':'request the single most decision-relevant next slice of evidence'}
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--artifact-type', required=True, choices=sorted(NEXT)); ap.add_argument('--file-status', required=True, choices=sorted(PLAYBOOK)); args = ap.parse_args()
    play, conf = PLAYBOOK[args.file_status]
    print(f'artifact_type: {args.artifact_type}')
    print(f'playbook: {play}')
    print(f'next_requested_excerpt: {NEXT[args.artifact_type]}')
    print(f'confidence_limit: {conf}')
if __name__ == '__main__':
    main()
