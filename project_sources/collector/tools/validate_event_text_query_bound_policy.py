#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List

DIAGNOSTIC_CONTEXT_REL = 'project_sources/collector/source/parts/DCOIR_Collector.04E_Diagnostic_Context_Overrides.ps1'
REPORT_NAME = 'validate_event_text_query_bound_policy_report.json'


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='ignore') if path.exists() else ''


def extract_function_body(text: str, function_name: str) -> str:
    match = re.search(r'^\s*function\s+' + re.escape(function_name) + r'\b', text, re.MULTILINE)
    if not match:
        return ''
    brace_start = text.find('{', match.end())
    if brace_start == -1:
        return ''
    depth = 0
    for index in range(brace_start, len(text)):
        char = text[index]
        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                return text[brace_start:index + 1]
    return text[brace_start:]


def add_missing_errors(prefix: str, checks: Dict[str, object], required_keys: List[str], errors: List[str]) -> None:
    for key in required_keys:
        if not checks.get(key):
            errors.append(prefix + key)


def validate_policy(source_dir: Path) -> Dict[str, object]:
    errors: List[str] = []
    source_path = source_dir / DIAGNOSTIC_CONTEXT_REL
    text = read_text(source_path)
    checks: Dict[str, object] = {
        'path': DIAGNOSTIC_CONTEXT_REL,
        'source_present': bool(text),
    }

    if not text:
        errors.append('event text diagnostic context source is missing: ' + DIAGNOSTIC_CONTEXT_REL)
        return {'success': False, 'checks': checks, 'errors': errors}

    helper = extract_function_body(text, 'Invoke-CollectorBoundedWinEventQuery')
    high_signal = extract_function_body(text, 'Get-SecurityHighSignalSummaryText')
    event_text = extract_function_body(text, 'Get-EventText')
    helper_query = 'Get-WinEvent -FilterHashtable $FilterHashtable -MaxEvents $MaxEvents -ErrorAction Stop'
    helper_sort = 'Sort-Object TimeCreated -Descending'
    helper_query_pos = helper.find(helper_query)
    helper_sort_pos = helper.find(helper_sort)
    legacy_unbounded_sort = re.compile(
        r'Get-WinEvent\s+-FilterHashtable\s+\$fh\s+-ErrorAction\s+Stop\s*\|\s*Sort-Object\s+TimeCreated\s+-Descending\s*\|\s*Select-Object\s+-First',
        re.IGNORECASE | re.DOTALL,
    )
    direct_fh_get_winevent = re.compile(r'Get-WinEvent\s+-FilterHashtable\s+\$fh\b', re.IGNORECASE)

    checks.update({
        'bounded_helper_present': bool(helper),
        'high_signal_function_present': bool(high_signal),
        'event_text_function_present': bool(event_text),
        'helper_applies_maxevents_at_query': helper_query in helper,
        'helper_returns_empty_for_nonpositive_limit': 'if ($MaxEvents -lt 1)' in helper and 'return @()' in helper,
        'helper_sorts_only_after_maxevents': helper_query_pos != -1 and helper_sort_pos != -1 and helper_query_pos < helper_sort_pos,
        'legacy_high_signal_unbounded_sort_absent': legacy_unbounded_sort.search(high_signal) is None,
        'legacy_event_text_unbounded_sort_absent': legacy_unbounded_sort.search(event_text) is None,
        'high_signal_direct_get_winevent_absent': direct_fh_get_winevent.search(high_signal) is None,
        'event_text_direct_get_winevent_absent': direct_fh_get_winevent.search(event_text) is None,
        'high_signal_uses_take_x4_query_limit': '$queryLimit = [Math]::Max(0, ($Take * 4))' in high_signal,
        'high_signal_uses_bounded_helper': 'Invoke-CollectorBoundedWinEventQuery -FilterHashtable $fh -MaxEvents $queryLimit' in high_signal,
        'event_text_uses_take_query_limit': '$queryLimit = [Math]::Max(0, $Take)' in event_text,
        'event_text_uses_bounded_helper': 'Invoke-CollectorBoundedWinEventQuery -FilterHashtable $fh -MaxEvents $queryLimit' in event_text,
        'high_signal_preserves_explicit_end_time': '$fh.EndTime = $window.EndTime' in high_signal,
        'event_text_preserves_explicit_end_time': '$fh.EndTime = $window.EndTime' in event_text,
        'event_text_preserves_event_id_filter': '$fh.Id = $Ids' in event_text,
        'high_signal_metadata_uses_take': "Get-CollectorEventWindowMetadataLines -Window $window -Channel 'Security' -Ids $ids -Take $Take" in high_signal,
        'event_text_metadata_uses_take': 'Get-CollectorEventWindowMetadataLines -Window $window -Channel $Channel -Ids $Ids -Take $Take' in event_text,
        'high_signal_raw_event_count_from_bounded_events': 'RAW_EVENT_COUNT={0}' in high_signal and '@($events).Count' in high_signal,
        'event_text_event_count_from_bounded_events': 'EVENT_COUNT={0}' in event_text and '@($events).Count' in event_text,
        'non_elevated_security_message_preserved': 'Get-NonElevatedSecurityVisibilityMessage' in high_signal and 'Get-NonElevatedSecurityVisibilityMessage' in event_text,
    })

    add_missing_errors('event text query bound policy failed: ', checks, [
        'bounded_helper_present',
        'high_signal_function_present',
        'event_text_function_present',
        'helper_applies_maxevents_at_query',
        'helper_returns_empty_for_nonpositive_limit',
        'helper_sorts_only_after_maxevents',
        'legacy_high_signal_unbounded_sort_absent',
        'legacy_event_text_unbounded_sort_absent',
        'high_signal_direct_get_winevent_absent',
        'event_text_direct_get_winevent_absent',
        'high_signal_uses_take_x4_query_limit',
        'high_signal_uses_bounded_helper',
        'event_text_uses_take_query_limit',
        'event_text_uses_bounded_helper',
        'high_signal_preserves_explicit_end_time',
        'event_text_preserves_explicit_end_time',
        'event_text_preserves_event_id_filter',
        'high_signal_metadata_uses_take',
        'event_text_metadata_uses_take',
        'high_signal_raw_event_count_from_bounded_events',
        'event_text_event_count_from_bounded_events',
        'non_elevated_security_message_preserved',
    ], errors)

    return {
        'success': not errors,
        'checks': checks,
        'errors': errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-dir', required=True)
    parser.add_argument('--output-dir', required=True)
    args = parser.parse_args()

    source_dir = Path(args.source_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    report = validate_policy(source_dir)
    report['source_dir'] = str(source_dir)
    (output_dir / REPORT_NAME).write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if report['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
