#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List

EVENT_TEXT_REVIEW_REL = 'project_sources/collector/source/parts/DCOIR_Collector.03B_Enrich_Actions_Review.ps1'
RETRIEVAL_ACTIONS_REL = 'project_sources/collector/source/parts/DCOIR_Collector.03C_Enrich_Actions_Retrieval.ps1'
EVENT_WINDOW_OVERRIDES_REL = 'project_sources/collector/source/parts/DCOIR_Collector.04C_Explicit_Event_Window_Overrides.ps1'
DIAGNOSTIC_CONTEXT_REL = 'project_sources/collector/source/parts/DCOIR_Collector.04E_Diagnostic_Context_Overrides.ps1'
PR186_FIXES_REL = 'project_sources/collector/source/parts/DCOIR_Collector.04F_PR186_Review_Fixes.ps1'
REPORT_NAME = 'validate_event_text_query_bound_policy_report.json'
COUNT_CAP_PARAMETER_NAMES = ('Take', 'MaxEvents')


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='ignore') if path.exists() else ''


def extract_parenthesized_text(text: str, open_paren_index: int) -> str:
    if open_paren_index < 0 or open_paren_index >= len(text) or text[open_paren_index] != '(':
        return ''
    depth = 0
    for index in range(open_paren_index, len(text)):
        char = text[index]
        if char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
            if depth == 0:
                return text[open_paren_index:index + 1]
    return ''


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


def extract_function_param_block(function_body: str) -> str:
    match = re.search(r'^\s*param\s*\(', function_body, re.MULTILINE | re.IGNORECASE)
    if not match:
        return ''
    open_paren = function_body.find('(', match.start())
    params = extract_parenthesized_text(function_body, open_paren)
    return function_body[match.start():open_paren] + params if params else ''


def extract_quoted_switch_case_bodies(text: str, case_name: str) -> List[str]:
    pattern = re.compile(r'^\s*"' + re.escape(case_name) + r'"\s*{', re.MULTILINE)
    bodies: List[str] = []
    for match in pattern.finditer(text):
        brace_start = text.find('{', match.start())
        if brace_start == -1:
            continue
        depth = 0
        for index in range(brace_start, len(text)):
            char = text[index]
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    bodies.append(text[brace_start:index + 1])
                    break
    return bodies


def extract_powershell_command_spans(text: str, command_name: str) -> List[str]:
    pattern = re.compile(r'\b' + re.escape(command_name) + r'\b', re.IGNORECASE)
    closing_for_open = {'(': ')', '[': ']', '{': '}'}
    spans: List[str] = []
    for match in pattern.finditer(text):
        cursor = match.end()
        expected_closers: List[str] = []
        quote = ''
        while cursor < len(text):
            char = text[cursor]
            if quote:
                if char == '`':
                    cursor += 2 if cursor + 1 < len(text) else 1
                    continue
                if char == quote:
                    if cursor + 1 < len(text) and text[cursor + 1] == quote:
                        cursor += 2
                        continue
                    quote = ''
                cursor += 1
                continue
            if char in ("'", '"'):
                quote = char
                cursor += 1
                continue
            continuation = re.match(r'`[ \t]*(?:\r\n|\n|\r)[ \t]*', text[cursor:])
            if continuation:
                cursor += continuation.end()
                continue
            if char == '`':
                cursor += 2 if cursor + 1 < len(text) else 1
                continue
            if char in closing_for_open:
                expected_closers.append(closing_for_open[char])
                cursor += 1
                continue
            if expected_closers and char == expected_closers[-1]:
                expected_closers.pop()
                cursor += 1
                continue
            if char in '\r\n' and not expected_closers:
                break
            cursor += 1
        spans.append(text[match.start():cursor])
    return spans


def normalize_powershell_command_span(command_span: str) -> str:
    return re.sub(r'`[ \t]*(?:\r\n|\n|\r)[ \t]*', ' ', command_span)


def powershell_parameter_is_count_cap(parameter_name: str) -> bool:
    parameter = parameter_name.strip().lstrip('-').lower()
    return bool(parameter) and any(
        canonical.lower().startswith(parameter)
        for canonical in COUNT_CAP_PARAMETER_NAMES
    )


def powershell_command_count_cap_parameters(command_span: str) -> List[str]:
    normalized = normalize_powershell_command_span(command_span)
    parameters = re.findall(r'(?<![\w-])-(?!-)([A-Za-z][\w-]*)', normalized)
    return [parameter for parameter in parameters if powershell_parameter_is_count_cap(parameter)]


def powershell_command_uses_count_cap_parameter(command_span: str) -> bool:
    return bool(powershell_command_count_cap_parameters(command_span))


def powershell_command_uses_splatting(command_span: str) -> bool:
    normalized = normalize_powershell_command_span(command_span)
    return re.search(r'(?<![\w$])@[A-Za-z_][\w]*', normalized) is not None


def add_missing_errors(prefix: str, checks: Dict[str, object], required_keys: List[str], errors: List[str]) -> None:
    for key in required_keys:
        if not checks.get(key):
            errors.append(prefix + key)


def validate_event_text_query_bound_policy(source_dir: Path) -> Dict[str, object]:
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


def validate_lograw_metadata_truth_policy(source_dir: Path) -> Dict[str, object]:
    # #238 metadata-honesty guard only. If raw EVTX export intentionally gains
    # a count-bounded implementation later, revise these assertions with that design.
    errors: List[str] = []
    review_text = read_text(source_dir / EVENT_TEXT_REVIEW_REL)
    retrieval_text = read_text(source_dir / RETRIEVAL_ACTIONS_REL)
    evtx_text = read_text(source_dir / EVENT_WINDOW_OVERRIDES_REL)
    helper_text = read_text(source_dir / PR186_FIXES_REL)
    checks: Dict[str, object] = {
        'review_path': EVENT_TEXT_REVIEW_REL,
        'retrieval_path': RETRIEVAL_ACTIONS_REL,
        'evtx_path': EVENT_WINDOW_OVERRIDES_REL,
        'helper_path': PR186_FIXES_REL,
        'review_source_present': bool(review_text),
        'retrieval_source_present': bool(retrieval_text),
        'evtx_source_present': bool(evtx_text),
        'helper_source_present': bool(helper_text),
    }

    if not all((review_text, retrieval_text, evtx_text, helper_text)):
        if not review_text:
            errors.append('review action source is missing: ' + EVENT_TEXT_REVIEW_REL)
        if not retrieval_text:
            errors.append('retrieval action source is missing: ' + RETRIEVAL_ACTIONS_REL)
        if not evtx_text:
            errors.append('raw EVTX export source is missing: ' + EVENT_WINDOW_OVERRIDES_REL)
        if not helper_text:
            errors.append('target-details helper source is missing: ' + PR186_FIXES_REL)
        return {'success': False, 'checks': checks, 'errors': errors}

    review_body = extract_function_body(review_text, 'Invoke-EnrichmentAction')
    retrieval_body = extract_function_body(retrieval_text, 'Invoke-EnrichmentAction-Retrieval')
    logtext_blocks = extract_quoted_switch_case_bodies(review_body, 'LogText')
    lograw_blocks = extract_quoted_switch_case_bodies(retrieval_body, 'LogRaw')
    logtext_block = next((block for block in logtext_blocks if 'Get-EventText' in block), '')
    lograw_block = next((block for block in lograw_blocks if 'Export-FilteredEvtx' in block), '')
    target_helper = extract_function_body(helper_text, 'Get-CollectorEventWindowTargetDetails')
    evtx_export = extract_function_body(evtx_text, 'Export-FilteredEvtx')
    evtx_export_param_block = extract_function_param_block(evtx_export)
    negative_param_fixture = extract_function_param_block(extract_function_body(
        '''
function Export-FilteredEvtx {
  [CmdletBinding()]
  param(
    [string]$LogChannel,
    [int]$MaxEvents
  )
}
''',
        'Export-FilteredEvtx',
    ))
    target_detail_negative_fixtures = [
        'Get-CollectorEventWindowTargetDetails -LogName $LogName -Hours $Hours -Ids $EventId -Take 500',
        'Get-CollectorEventWindowTargetDetails -LogName $LogName -Hours $Hours -Ids $EventId -Take $Limit',
        'Get-CollectorEventWindowTargetDetails -LogName $LogName -Hours $Hours -Ids $EventId -MaxEvents $Limit',
    ]
    target_detail_multiline_negative_fixtures = [
        'Get-CollectorEventWindowTargetDetails -LogName $LogName -Hours $Hours -Ids $EventId `\n  -Take $Limit',
        'Get-CollectorEventWindowTargetDetails -LogName $LogName -Hours $Hours -Ids $EventId `\r\n  -MaxEvents $Limit',
    ]
    target_detail_parameter_prefix_negative_fixtures = [
        'Get-CollectorEventWindowTargetDetails -LogName $LogName -Hours $Hours -Ids $EventId -Ta 500',
        'Get-CollectorEventWindowTargetDetails -LogName $LogName -Hours $Hours -Ids $EventId -Max $Limit',
        'Get-CollectorEventWindowTargetDetails -LogName $LogName -Hours $Hours -Ids $EventId `\n  -Ta $Limit',
        'Get-CollectorEventWindowTargetDetails -LogName $LogName -Hours $Hours -Ids $EventId `\r\n  -Max $Limit',
    ]
    target_detail_implicit_continuation_negative_fixtures = [
        'Get-CollectorEventWindowTargetDetails -LogName $LogName -Ids @(\n  $EventId\n) -Take $Limit',
        'Get-CollectorEventWindowTargetDetails -LogName (\n  $LogName\n) -MaxEvents $Limit',
        'Get-CollectorEventWindowTargetDetails -Metadata @{\n  LogName = $LogName\n} -Ta $Limit',
    ]
    target_detail_splat_negative_fixtures = [
        'Get-CollectorEventWindowTargetDetails @TargetDetailArgs',
        'Get-CollectorEventWindowTargetDetails -LogName $LogName `\n  @TargetDetailArgs',
    ]
    target_detail_implicit_continuation_splat_negative_fixtures = [
        'Get-CollectorEventWindowTargetDetails -Ids @(\n  $EventId\n) @TargetDetailArgs',
        'Get-CollectorEventWindowTargetDetails -Metadata @{\n  LogName = $LogName\n} @script:TargetDetailArgs',
    ]
    export_splat_negative_fixtures = [
        'Export-FilteredEvtx @ExportArgs',
        'Export-FilteredEvtx -LogChannel $LogName `\n  @ExportArgs',
    ]
    export_implicit_continuation_negative_fixtures = [
        'Export-FilteredEvtx -LogChannel $LogName -Ids @(\n  $EventId\n) -MaxEvents $MaxEvents',
        'Export-FilteredEvtx -LogChannel (\n  $LogName\n) -Max $MaxEvents',
        'Export-FilteredEvtx -Options @{\n  LogName = $LogName\n} -Ta $Limit',
    ]
    export_implicit_continuation_splat_negative_fixtures = [
        'Export-FilteredEvtx -Ids @(\n  $EventId\n) @ExportArgs',
        'Export-FilteredEvtx -Options @{\n  LogName = $LogName\n} @script:ExportArgs',
    ]

    lograw_target_detail_calls = extract_powershell_command_spans(
        lograw_block,
        'Get-CollectorEventWindowTargetDetails',
    )
    lograw_export_calls = extract_powershell_command_spans(
        lograw_block,
        'Export-FilteredEvtx',
    )
    target_detail_overclaim = any(
        powershell_command_uses_count_cap_parameter(call)
        for call in lograw_target_detail_calls
    )
    target_detail_uses_splatting = any(
        powershell_command_uses_splatting(call)
        for call in lograw_target_detail_calls
    )
    target_detail_negative_fixtures_detect_count_cap = all(
        powershell_command_uses_count_cap_parameter(fixture)
        for fixture in target_detail_negative_fixtures
        + target_detail_multiline_negative_fixtures
        + target_detail_parameter_prefix_negative_fixtures
        + target_detail_implicit_continuation_negative_fixtures
    )
    target_detail_multiline_negative_fixtures_detect_count_cap = all(
        powershell_command_uses_count_cap_parameter(fixture)
        for fixture in target_detail_multiline_negative_fixtures
    )
    target_detail_parameter_prefix_negative_fixtures_detect_count_cap = all(
        powershell_command_uses_count_cap_parameter(fixture)
        for fixture in target_detail_parameter_prefix_negative_fixtures
    )
    target_detail_implicit_continuation_negative_fixtures_detect_count_cap = all(
        powershell_command_uses_count_cap_parameter(fixture)
        for fixture in target_detail_implicit_continuation_negative_fixtures
    )
    target_detail_splat_negative_fixtures_reject_splatting = all(
        powershell_command_uses_splatting(fixture)
        for fixture in target_detail_splat_negative_fixtures
    )
    target_detail_implicit_continuation_splat_negative_fixtures_reject_splatting = all(
        powershell_command_uses_splatting(fixture)
        for fixture in target_detail_implicit_continuation_splat_negative_fixtures
    )
    export_uses_splatting = any(
        powershell_command_uses_splatting(call)
        for call in lograw_export_calls
    )
    export_splat_negative_fixtures_reject_splatting = all(
        powershell_command_uses_splatting(fixture)
        for fixture in export_splat_negative_fixtures
    )
    export_implicit_continuation_negative_fixtures_detect_count_cap = all(
        powershell_command_uses_count_cap_parameter(fixture)
        for fixture in export_implicit_continuation_negative_fixtures
    )
    export_implicit_continuation_splat_negative_fixtures_reject_splatting = all(
        powershell_command_uses_splatting(fixture)
        for fixture in export_implicit_continuation_splat_negative_fixtures
    )
    export_claims_maxevents = any(
        powershell_command_uses_count_cap_parameter(call)
        or re.search(r'\$MaxEvents\b', normalize_powershell_command_span(call), flags=re.IGNORECASE)
        for call in lograw_export_calls
    )
    evtx_param_claims_event_cap = re.search(r'\$(?:MaxEvents|Take)\b', evtx_export_param_block, flags=re.IGNORECASE) is not None
    negative_fixture_detects_event_cap = re.search(r'\$(?:MaxEvents|Take)\b', negative_param_fixture, flags=re.IGNORECASE) is not None
    target_helper_reads_or_exports_events = re.search(r'\b(?:Get-WinEvent|wevtutil|Export-FilteredEvtx)\b', target_helper, flags=re.IGNORECASE) is not None

    checks.update({
        'review_function_present': bool(review_body),
        'retrieval_function_present': bool(retrieval_body),
        'logtext_action_block_present': bool(logtext_block),
        'lograw_action_block_present': bool(lograw_block),
        'target_details_helper_present': bool(target_helper),
        'evtx_export_function_present': bool(evtx_export),
        'evtx_export_param_block_present': bool(evtx_export_param_block),
        'param_block_negative_fixture_detects_maxevents': negative_fixture_detects_event_cap,
        'target_detail_negative_fixtures_detect_count_cap': target_detail_negative_fixtures_detect_count_cap,
        'target_detail_multiline_negative_fixtures_detect_count_cap': target_detail_multiline_negative_fixtures_detect_count_cap,
        'target_detail_parameter_prefix_negative_fixtures_detect_count_cap': target_detail_parameter_prefix_negative_fixtures_detect_count_cap,
        'target_detail_implicit_continuation_negative_fixtures_detect_count_cap': target_detail_implicit_continuation_negative_fixtures_detect_count_cap,
        'target_detail_splat_negative_fixtures_reject_splatting': target_detail_splat_negative_fixtures_reject_splatting,
        'target_detail_implicit_continuation_splat_negative_fixtures_reject_splatting': target_detail_implicit_continuation_splat_negative_fixtures_reject_splatting,
        'export_splat_negative_fixtures_reject_splatting': export_splat_negative_fixtures_reject_splatting,
        'export_implicit_continuation_negative_fixtures_detect_count_cap': export_implicit_continuation_negative_fixtures_detect_count_cap,
        'export_implicit_continuation_splat_negative_fixtures_reject_splatting': export_implicit_continuation_splat_negative_fixtures_reject_splatting,
        'target_helper_metadata_only_no_event_reader': bool(target_helper) and not target_helper_reads_or_exports_events,
        'lograw_target_details_call_count': len(lograw_target_detail_calls),
        'lograw_target_details_omits_maxevents_overclaim': bool(lograw_target_detail_calls) and not target_detail_overclaim and not target_detail_uses_splatting,
        'lograw_target_details_omits_splatting': bool(lograw_target_detail_calls) and not target_detail_uses_splatting,
        'lograw_target_details_keeps_log_window_ids': 'Get-CollectorEventWindowTargetDetails -LogName $LogName -Hours $Hours -Ids $EventId' in normalize_powershell_command_span(lograw_block),
        'lograw_output_initializes_applied_filter_scope': "$rawEvtxFilters = @('LogName','EffectiveEventWindow')" in lograw_block,
        'lograw_output_conditionally_adds_eventids_filter': "if ($EventId -and @($EventId).Count -gt 0) { $rawEvtxFilters += 'EventIds' }" in lograw_block,
        'lograw_output_writes_applied_filter_scope': 'RAW_EVTX_FILTERS=$rawEvtxFiltersText' in lograw_block,
        'lograw_output_states_no_event_count_cap': 'RAW_EVTX_EVENT_COUNT_CAP=NotApplied' in lograw_block,
        'lograw_interpretation_states_no_maxevents_cap': 'MaxEvents does not limit raw EVTX export size.' in lograw_block,
        'lograw_export_call_preserved': 'Export-FilteredEvtx -LogChannel $LogName -WindowHours $Hours -Ids $EventId -OutPath $plannedStagedPath -ScratchDir $sessionLogsDir' in normalize_powershell_command_span(lograw_block),
        'lograw_export_call_omits_maxevents': bool(lograw_export_calls) and not export_claims_maxevents and not export_uses_splatting,
        'lograw_export_call_omits_splatting': bool(lograw_export_calls) and not export_uses_splatting,
        'logtext_still_uses_maxevents_metadata': 'Get-CollectorEventWindowTargetDetails -LogName $LogName -Hours $Hours -Ids $EventId -Take $MaxEvents' in logtext_block,
        'logtext_still_uses_bounded_text_query': 'Get-EventText -Channel $LogName -WindowHours $Hours -Ids $EventId -Take $MaxEvents' in logtext_block,
        'target_helper_still_emits_maxevents_for_text_paths': 'if ($Take -gt 0) { [void]$parts.Add(("MaxEvents={0}" -f $Take)) }' in target_helper,
        'evtx_export_has_no_maxevents_parameter': bool(evtx_export_param_block) and not evtx_param_claims_event_cap,
        'evtx_export_preserves_timediff_filter': 'TimeCreated[timediff(@SystemTime)' in evtx_export,
        'evtx_export_preserves_explicit_window_filter': "TimeCreated[@SystemTime>='$startUtc' and @SystemTime<='$endUtc']" in evtx_export,
        'evtx_export_preserves_event_id_filter': 'EventID=$_' in evtx_export,
    })

    add_missing_errors('lograw metadata truth policy failed: ', checks, [
        'review_function_present',
        'retrieval_function_present',
        'logtext_action_block_present',
        'lograw_action_block_present',
        'target_details_helper_present',
        'evtx_export_function_present',
        'evtx_export_param_block_present',
        'param_block_negative_fixture_detects_maxevents',
        'target_detail_negative_fixtures_detect_count_cap',
        'target_detail_multiline_negative_fixtures_detect_count_cap',
        'target_detail_parameter_prefix_negative_fixtures_detect_count_cap',
        'target_detail_implicit_continuation_negative_fixtures_detect_count_cap',
        'target_detail_splat_negative_fixtures_reject_splatting',
        'target_detail_implicit_continuation_splat_negative_fixtures_reject_splatting',
        'export_splat_negative_fixtures_reject_splatting',
        'export_implicit_continuation_negative_fixtures_detect_count_cap',
        'export_implicit_continuation_splat_negative_fixtures_reject_splatting',
        'target_helper_metadata_only_no_event_reader',
        'lograw_target_details_omits_maxevents_overclaim',
        'lograw_target_details_omits_splatting',
        'lograw_target_details_keeps_log_window_ids',
        'lograw_output_initializes_applied_filter_scope',
        'lograw_output_conditionally_adds_eventids_filter',
        'lograw_output_writes_applied_filter_scope',
        'lograw_output_states_no_event_count_cap',
        'lograw_interpretation_states_no_maxevents_cap',
        'lograw_export_call_preserved',
        'lograw_export_call_omits_maxevents',
        'lograw_export_call_omits_splatting',
        'logtext_still_uses_maxevents_metadata',
        'logtext_still_uses_bounded_text_query',
        'target_helper_still_emits_maxevents_for_text_paths',
        'evtx_export_has_no_maxevents_parameter',
        'evtx_export_preserves_timediff_filter',
        'evtx_export_preserves_explicit_window_filter',
        'evtx_export_preserves_event_id_filter',
    ], errors)

    return {
        'success': not errors,
        'checks': checks,
        'errors': errors,
    }


def validate_policy(source_dir: Path) -> Dict[str, object]:
    checks: Dict[str, object] = {}
    errors: List[str] = []
    event_text_policy = validate_event_text_query_bound_policy(source_dir)
    lograw_policy = validate_lograw_metadata_truth_policy(source_dir)
    checks['event_text_query_bound_policy'] = event_text_policy['checks']
    checks['lograw_metadata_truth_policy'] = lograw_policy['checks']
    errors.extend(event_text_policy['errors'])
    errors.extend(lograw_policy['errors'])
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
