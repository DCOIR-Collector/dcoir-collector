#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import readline from 'node:readline/promises';
import { stdin as input, stdout as output } from 'node:process';
import { chromium } from 'playwright';
import { ensureDir, readJsonFile, writeJson, nowIso, safeName, norm } from '../../shared/dcoir_ui_common.mjs';
import { safeMousePark } from '../../shared/dcoir_airtable_ui_geometry.mjs';
import {
  AIRTABLE_PANEL_READBACK_VERSION,
  selectManifestTargets,
  selectAirtableTableAndView,
  captureDomEvidence,
  captureAirtablePanelState,
  compareAirtablePanelReadback
} from '../../shared/dcoir_airtable_panel_readback.mjs';
import {
  AIRTABLE_PANEL_ACTIONS_VERSION,
  ensureSingleRelativeDateFilter
} from '../../shared/dcoir_airtable_panel_actions.mjs';

const TOOL_VERSION = '2026-05-12.wbs09-apply-relative-date-filter.3';
const REQUIRED_TOKEN = 'APPLY_WBS09_RELATIVE_DATE_FILTER';
const SUPPORTED_PRIMITIVE = 'filter.relative_date.on_or_before_today';

function parseArgs(argv) {
  const parsed = {
    enableScreenshots: false,
    headless: false,
    useChromeChannel: false,
    userDataDir: null,
    connectCdpUrl: null,
    keepBrowserOpenOnFailure: false,
    operatorReadyBeforeLaunch: false,
    browserLaunchTimeoutMs: 45000,
    targetKeys: [],
    confirmToken: null,
    capabilityMap: null
  };
  for (let i = 2; i < argv.length; i += 1) {
    const a = argv[i];
    const next = () => argv[++i];
    if (a === '--manifest') parsed.manifest = next();
    else if (a === '--capability-map') parsed.capabilityMap = next();
    else if (a === '--output-dir') parsed.outputDir = next();
    else if (a === '--base-url') parsed.baseUrl = next();
    else if (a === '--target-key') parsed.targetKeys.push(next());
    else if (a === '--confirm-token') parsed.confirmToken = next();
    else if (a === '--enable-screenshots') parsed.enableScreenshots = true;
    else if (a === '--headless') parsed.headless = true;
    else if (a === '--use-chrome-channel') parsed.useChromeChannel = true;
    else if (a === '--user-data-dir') parsed.userDataDir = next();
    else if (a === '--connect-cdp-url') parsed.connectCdpUrl = next();
    else if (a === '--browser-launch-timeout-ms') parsed.browserLaunchTimeoutMs = Number(next());
    else if (a === '--operator-ready-before-launch') parsed.operatorReadyBeforeLaunch = true;
    else if (a === '--keep-browser-open-on-failure') parsed.keepBrowserOpenOnFailure = true;
    else throw new Error(`Unknown argument: ${a}`);
  }
  return parsed;
}

function normalizeText(value) {
  return String(value || '').replace(/[\u2192\u27f6\u2794]/g, ' -> ').replace(/\s+/g, ' ').trim();
}
function lowerText(value) { return normalizeText(value).toLowerCase(); }
function targetKeyOf(target) { return `${norm(target.table_name)}::${norm(target.view_name)}`; }
function isRelativeDateTodayFilter(filter) {
  return filter && lowerText(filter.operator) === 'on or before' && lowerText(filter.value) === 'today';
}
function isSortMissing(missing) { return /sort row/i.test(String(missing || '')); }
function isFilterMissing(missing) { return /filter row/i.test(String(missing || '')); }

function assertSupportedTarget(target) {
  const key = targetKeyOf(target);
  if (!Array.isArray(target.expected_filters) || target.expected_filters.length !== 1) {
    throw new Error(`Target ${key} is not supported: expected exactly one manifest filter.`);
  }
  const filter = target.expected_filters[0];
  if (!isRelativeDateTodayFilter(filter)) {
    throw new Error(`Target ${key} is not supported: expected one relative-date filter with operator "on or before" and value "today".`);
  }
  if (!/^[A-Za-z0-9_ -]+$/.test(String(filter.field || ''))) {
    throw new Error(`Target ${key} has an unsafe filter field name: ${filter.field}`);
  }
  if (Array.isArray(target.expected_sorts) && target.expected_sorts.length > 1) {
    throw new Error(`Target ${key} is not supported: this primitive does not normalize multi-sort views.`);
  }
}

function primitiveEntryFromCapabilityMap(capabilityMap) {
  const entries = Array.isArray(capabilityMap?.primitives) ? capabilityMap.primitives : [];
  return entries.find((entry) => entry?.primitive_id === SUPPORTED_PRIMITIVE) || null;
}

function assertCapabilityMapAllowsTarget(capabilityMap, target) {
  if (!capabilityMap) return { checked: false, reason: 'capability-map-not-provided' };
  const primitive = primitiveEntryFromCapabilityMap(capabilityMap);
  if (!primitive) throw new Error(`Capability map does not contain primitive ${SUPPORTED_PRIMITIVE}.`);
  if (primitive.schema_supported !== true || primitive.ui_discovery_supported !== true) {
    throw new Error(`Capability map does not mark ${SUPPORTED_PRIMITIVE} as schema-supported and UI-observed.`);
  }
  const key = targetKeyOf(target);
  const views = Array.isArray(capabilityMap?.views) ? capabilityMap.views : [];
  const view = views.find((item) => String(item?.view_key || '') === key);
  if (!view) throw new Error(`Capability map does not contain target ${key}.`);
  const filters = Array.isArray(view.filters) ? view.filters : [];
  const hasPrimitive = filters.some((filter) => filter?.primitive_id === SUPPORTED_PRIMITIVE && filter?.schema_supported === true);
  if (!hasPrimitive) throw new Error(`Capability map target ${key} is not schema-supported for ${SUPPORTED_PRIMITIVE}.`);
  return {
    checked: true,
    primitive_status: primitive.status,
    manifest_use_count: primitive.manifest_use_count,
    target_schema_supported: true
  };
}

function rowLooksLikeFilterCondition(row) {
  const text = lowerText(`${row?.text || ''} ${row?.cells?.field_text || ''} ${row?.cells?.operator_text || ''} ${row?.cells?.value_text || ''}`);
  if (!text) return false;
  if (/add condition|copy from another view|filter conditions|where all of the following condition/.test(text) && !/remove item/.test(text)) return false;
  return /remove item|reorder item|where|is on or before|is before|is after|contains|is empty|is not empty|is checked|is unchecked|is any of|is one of|\bis\b/.test(text);
}

function rowMentionsField(row, fieldName) {
  const token = lowerText(fieldName).replace(/[_ -]+/g, ' ');
  const text = lowerText(`${row?.text || ''} ${row?.cells?.field_text || ''}`).replace(/[_ -]+/g, ' ');
  return token && text.includes(token);
}

function assertNoUnexpectedFilterRows(filterState, expectedField) {
  const rows = Array.isArray(filterState?.rows) ? filterState.rows : [];
  const conditionRows = rows.filter(rowLooksLikeFilterCondition);
  const unexpected = conditionRows.filter((row) => !rowMentionsField(row, expectedField));
  if (unexpected.length > 0) {
    throw new Error(`Filter mutation refused: found ${unexpected.length} existing filter row(s) not for ${expectedField}.`);
  }
  const forField = conditionRows.filter((row) => rowMentionsField(row, expectedField));
  if (forField.length > 1) {
    throw new Error(`Filter mutation refused: found ${forField.length} existing filter rows for ${expectedField}.`);
  }
  return { condition_row_count: conditionRows.length, expected_field_row_count: forField.length };
}

function stripReadbackPhasePrefix(message) {
  return String(message || '').replace(/^(before_refresh|after_refresh):\s*/i, '');
}

function collectComparison(beforeFilter, beforeSort, afterFilter, afterSort, target) {
  return compareAirtablePanelReadback({
    target,
    before_filter: beforeFilter,
    before_sort: beforeSort,
    after_filter: afterFilter || beforeFilter,
    after_sort: afterSort || beforeSort
  });
}

function summarizeMissing(missing) {
  const unique = Array.from(new Set((missing || []).map(stripReadbackPhasePrefix)));
  return {
    unique,
    filter_missing: unique.filter(isFilterMissing),
    sort_missing: unique.filter(isSortMissing)
  };
}

const args = parseArgs(process.argv);
if (!args.manifest) throw new Error('--manifest is required.');
if (!args.outputDir) throw new Error('--output-dir is required.');
if (args.confirmToken !== REQUIRED_TOKEN) throw new Error(`This mutation helper requires --confirm-token ${REQUIRED_TOKEN}.`);
if (args.targetKeys.length !== 1) throw new Error('This guarded helper requires exactly one --target-key.');
ensureDir(args.outputDir);
const outputDir = args.outputDir;
let page;
let browser;
let context;
let cdpBrowser;
let success = false;

function log(message, obj) {
  const suffix = obj ? ` ${JSON.stringify(obj)}` : '';
  console.log(`${nowIso()} ${message}${suffix}`);
}

function assertValidTimeout(value, label) {
  if (!Number.isFinite(value) || value < 10000 || value > 300000) {
    throw new Error(`${label} must be between 10000 and 300000 milliseconds.`);
  }
}

function withTimeout(promise, timeoutMs, label) {
  let timer;
  const timeout = new Promise((_, reject) => {
    timer = setTimeout(() => reject(new Error(`${label} timed out after ${timeoutMs}ms. Close extra Chrome instances, verify the profile is not locked, or retry with --connect-cdp-url.`)), timeoutMs);
  });
  return Promise.race([promise, timeout]).finally(() => clearTimeout(timer));
}

async function waitForOperatorReadyBeforeLaunch() {
  if (!args.operatorReadyBeforeLaunch || args.headless) return;
  const rl = readline.createInterface({ input, output });
  await rl.question('Close unrelated Chrome windows or confirm the DCOIR Chrome profile is ready, then press Enter to launch Airtable browser automation. Ctrl+C aborts before browser launch.');
  rl.close();
}

async function openBrowser(baseUrl) {
  assertValidTimeout(args.browserLaunchTimeoutMs, 'browserLaunchTimeoutMs');
  await waitForOperatorReadyBeforeLaunch();

  if (args.connectCdpUrl) {
    log('Connecting to existing browser over CDP.', { cdp_url: args.connectCdpUrl, timeout_ms: args.browserLaunchTimeoutMs });
    cdpBrowser = await withTimeout(chromium.connectOverCDP(args.connectCdpUrl), args.browserLaunchTimeoutMs, 'connectOverCDP');
    context = cdpBrowser.contexts()[0] || await withTimeout(cdpBrowser.newContext(), args.browserLaunchTimeoutMs, 'newContext after CDP connect');
    page = context.pages()[0] || await withTimeout(context.newPage(), args.browserLaunchTimeoutMs, 'newPage after CDP connect');
    log('Browser context ready.', { mode: 'cdp', pages: context.pages().length });
    await page.goto(baseUrl, { waitUntil: 'domcontentloaded', timeout: 15000 }).catch((error) => log('Initial Airtable navigation warning.', { error: String(error?.message || error) }));
    return;
  }
  if (args.userDataDir) {
    log('Launching persistent browser context.', { user_data_dir: args.userDataDir, chrome_channel: !!args.useChromeChannel, timeout_ms: args.browserLaunchTimeoutMs });
    context = await withTimeout(chromium.launchPersistentContext(args.userDataDir, {
      headless: !!args.headless,
      channel: args.useChromeChannel ? 'chrome' : undefined,
      viewport: { width: 1440, height: 900 }
    }), args.browserLaunchTimeoutMs, 'launchPersistentContext');
    page = context.pages()[0] || await withTimeout(context.newPage(), args.browserLaunchTimeoutMs, 'newPage after persistent launch');
    log('Browser context ready.', { mode: 'persistent', pages: context.pages().length });
    await page.goto(baseUrl, { waitUntil: 'domcontentloaded', timeout: 15000 }).catch((error) => log('Initial Airtable navigation warning.', { error: String(error?.message || error) }));
    return;
  }
  log('Launching browser.', { chrome_channel: !!args.useChromeChannel, timeout_ms: args.browserLaunchTimeoutMs });
  browser = await withTimeout(chromium.launch({ headless: !!args.headless, channel: args.useChromeChannel ? 'chrome' : undefined }), args.browserLaunchTimeoutMs, 'launchBrowser');
  context = await withTimeout(browser.newContext({ viewport: { width: 1440, height: 900 } }), args.browserLaunchTimeoutMs, 'newContext after browser launch');
  page = await withTimeout(context.newPage(), args.browserLaunchTimeoutMs, 'newPage after browser launch');
  log('Browser context ready.', { mode: 'ephemeral', pages: context.pages().length });
  await page.goto(baseUrl, { waitUntil: 'domcontentloaded', timeout: 15000 }).catch((error) => log('Initial Airtable navigation warning.', { error: String(error?.message || error) }));
}

async function closeBrowser() {
  if (!success && args.keepBrowserOpenOnFailure) {
    console.error('Failure detected. Browser will remain open for inspection. Press Enter after inspection to close this process.');
    const rl = readline.createInterface({ input, output });
    await rl.question('');
    rl.close();
  }
  if (context && !cdpBrowser) await context.close().catch(() => {});
  if (browser) await browser.close().catch(() => {});
  if (cdpBrowser) await cdpBrowser.close().catch(() => {});
}

async function verifyTarget(target, phase) {
  const filter = await captureAirtablePanelState(page, outputDir, target, 'filter', phase, args);
  const sort = await captureAirtablePanelState(page, outputDir, target, 'sort', phase, args);
  return { filter, sort };
}

async function applyOneTarget(target, capabilityMap) {
  assertSupportedTarget(target);
  const expectedFilter = target.expected_filters[0];
  const result = {
    timestamp_utc: nowIso(),
    tool_version: TOOL_VERSION,
    shared_panel_readback_version: AIRTABLE_PANEL_READBACK_VERSION,
    shared_panel_actions_version: AIRTABLE_PANEL_ACTIONS_VERSION,
    primitive_id: SUPPORTED_PRIMITIVE,
    target,
    capability_gate: assertCapabilityMapAllowsTarget(capabilityMap, target),
    safety: {
      single_target_only: true,
      relative_date_filter_only: true,
      no_view_create_delete: true,
      no_record_table_field_mutation: true,
      refuses_unexpected_filter_rows: true,
      sort_is_verified_but_not_mutated: true
    },
    steps: [],
    snapshots: []
  };

  result.steps.push({ action: 'select_target', ...(await selectAirtableTableAndView(page, target)) });
  result.snapshots.push(await captureDomEvidence(page, outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_target_loaded`, args));

  const before = await verifyTarget(target, 'before_apply');
  result.before = before;
  const beforeComparison = collectComparison(before.filter, before.sort, before.filter, before.sort, target);
  result.before_comparison = beforeComparison;
  const beforeMissing = summarizeMissing(beforeComparison.missing);
  result.before_missing_summary = beforeMissing;

  if (beforeComparison.ok) {
    result.status = 'already_correct_before_apply';
    return result;
  }

  if (beforeMissing.sort_missing.length > 0) {
    throw new Error(`Target has sort gap(s); this filter-only primitive refuses to mutate before sort is correct: ${beforeMissing.sort_missing.join(' | ')}`);
  }
  if (beforeMissing.filter_missing.length === 0) {
    const filterReason = before?.filter?.panel_extraction?.reason || 'unknown';
    throw new Error(`Target comparison failed for a non-filter reason this primitive does not handle: ${beforeMissing.unique.join(' | ')}; filter_extraction_reason=${filterReason}`);
  }

  const filterGuard = assertNoUnexpectedFilterRows(before.filter, expectedFilter.field);
  result.filter_guard = filterGuard;

  const actionReport = await ensureSingleRelativeDateFilter(page, {
    field: expectedFilter.field,
    operator: expectedFilter.operator,
    value: expectedFilter.value,
    outputDir,
    evidenceLabel: `${safeName(target.table_name)}_${safeName(target.view_name)}_${safeName(expectedFilter.field)}_relative_date`,
    screenshotOptions: args
  });
  result.filter_action = actionReport;
  await safeMousePark(page, 'after-relative-date-filter-action').catch(() => {});

  const post = await verifyTarget(target, 'post_apply');
  result.post_apply = post;
  result.post_apply_comparison = collectComparison(post.filter, post.sort, post.filter, post.sort, target);
  if (!result.post_apply_comparison.ok) {
    result.status = 'post_apply_gap_found';
    return result;
  }

  result.steps.push({ action: 'reload_and_reselect_for_independent_readback_start' });
  await page.reload({ waitUntil: 'domcontentloaded', timeout: 15000 }).catch(() => {});
  await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
  await page.waitForTimeout(1300);
  result.steps.push({ action: 'reselect_after_reload', ...(await selectAirtableTableAndView(page, target)) });
  const afterReload = await verifyTarget(target, 'after_reload');
  result.after_reload = afterReload;
  result.after_reload_comparison = collectComparison(post.filter, post.sort, afterReload.filter, afterReload.sort, target);
  result.status = result.after_reload_comparison.ok ? 'expected_panel_state_observed_after_reload' : 'after_reload_gap_found';
  return result;
}

try {
  log('Starting DCOIR WBS09 apply relative-date filter.', {
    version: TOOL_VERSION,
    shared_panel_readback_version: AIRTABLE_PANEL_READBACK_VERSION,
    shared_panel_actions_version: AIRTABLE_PANEL_ACTIONS_VERSION
  });
  const manifest = readJsonFile(args.manifest);
  const targets = selectManifestTargets(manifest, { targetKeys: args.targetKeys });
  if (targets.length !== 1) throw new Error(`Expected exactly one selected target, got ${targets.length}.`);
  const target = targets[0];
  target.base_id = target.base_id || manifest.base_id || undefined;
  const capabilityMap = args.capabilityMap && fs.existsSync(args.capabilityMap) ? readJsonFile(args.capabilityMap) : null;
  const baseUrl = args.baseUrl || `https://airtable.com/${target.base_id || manifest.base_id || ''}`;
  await openBrowser(baseUrl);

  if (!args.headless) {
    const rl = readline.createInterface({ input, output });
    await rl.question(`Apply ONE WBS09 relative-date filter target: ${targetKeyOf(target)}. Confirm Airtable is open, then press Enter. Ctrl+C aborts before mutation.`);
    const token = await rl.question(`Type ${REQUIRED_TOKEN} again to proceed: `);
    rl.close();
    if (token !== REQUIRED_TOKEN) throw new Error('Interactive confirmation token mismatch.');
  }

  const result = await applyOneTarget(target, capabilityMap);
  result.completed_at_utc = nowIso();
  writeJson(path.join(outputDir, 'apply_relative_date_filter_rollup.json'), result);
  if (!['already_correct_before_apply', 'expected_panel_state_observed_after_reload'].includes(result.status)) {
    throw new Error(`Relative-date filter apply did not reach passing state: ${result.status}`);
  }
  success = true;
  log('Apply relative-date filter completed.', { status: result.status, target_key: targetKeyOf(target) });
} catch (error) {
  const errorReport = {
    timestamp_utc: nowIso(),
    tool_version: TOOL_VERSION,
    status: 'failed',
    error: String(error?.message || error),
    stack: String(error?.stack || '')
  };
  try { writeJson(path.join(outputDir, 'apply_relative_date_filter_error.json'), errorReport); } catch {}
  console.error(errorReport.error);
  process.exitCode = 1;
} finally {
  await closeBrowser().catch((error) => console.error(String(error?.message || error)));
}
