#!/usr/bin/env python3
from __future__ import annotations
import argparse
MAP = {
    'suspicious-baseline': ('baseline triage', 'merged baseline report'),
    'single-enrichment-lead': ('enrichment review', 'enrichment report block tied to the lead'),
    'retrieved-artifact': ('retrieved artifact review', 'retrieved script, config, task XML, registry export, or raw event excerpt'),
    'case-synthesis': ('final case synthesis', 'reviewed baseline, enrichment, and retrieved-artifact evidence broad enough for closure'),
    'generic': ('baseline triage', 'best available DCOIR artifact text, preferring the merged baseline report'),
}
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--source-context', required=True); ap.add_argument('--trigger', default='generic', choices=sorted(MAP)); ap.add_argument('--summary', default='triage lead requires DCOIR follow-through'); ap.add_argument('--confidence-note', default='bounded confidence until the next expected evidence artifact is reviewed'); args = ap.parse_args()
    step, evidence = MAP[args.trigger]
    print('# DCOIR Escalation Contract\n')
    print(f'- source_context: {args.source_context}')
    print(f'- trigger_condition: {args.trigger}')
    print(f'- escalation_summary: {args.summary}')
    print(f'- exact_next_dcoir_step: {step}')
    print(f'- expected_next_evidence: {evidence}')
    print(f'- bounded_confidence_note: {args.confidence_note}')
    print('- routing_rule: keep description dense enough to preserve correct delegation and the exact next DCOIR lane')
if __name__ == '__main__':
    main()
