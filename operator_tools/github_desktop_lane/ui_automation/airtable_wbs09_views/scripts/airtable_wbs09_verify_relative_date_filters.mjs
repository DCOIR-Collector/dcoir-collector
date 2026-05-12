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

const TOOL_VERSION = '2026-05-12.wbs09-verify-relative-date-filters.1';
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
    allSupportedRelativeDateTargets: false,
    targetKeys: [],
    maxTargets: 0,
    failOnGap: false
  };
  for (let i = 2; i < argv.length; i += 1) {
    const a = argv[i];
    const next = () => argv[++i];
    if (a === '--manifest') parsed.manifest = next();
    else if (a === '--capability-map') parsed.capabilityMap = next();
    else if (a === '--output-dir') parsed.outputDir = next();
    else if (a === '--base-url') parsed.baseUrl = next();
    else if (a === '--target-key') parsed.targetKeys.push(next());
    else if (a === '--all-supported-relative-date-targets') parsed.allSupportedRelativeDateTargets = true;
    else if (a === '--max-targets') parsed.maxTargets = Number(next());
    else if (a === '--enable-screenshots') parsed.enableScreenshots = true;
    else if (a === '--headless') parsed.headless = true;
    else if (a === '--use-chrome-channel') parsed.useChromeChannel = true;
    else if (a === '--user-data-dir') parsed.userDataDir = next();
    else if (a === '--connect-cdp-url') parsed.connectCdpUrl = next();
    else if (a === '--browser-launch-timeout-ms') parsed.browserLaunchTimeoutMs = Number(next());
    else if (a === '--operator-ready-before-launch') parsed.operatorReadyBeforeLaunch = true;
    else if (a === '--keep-browser-open-on-failure') parsed.keepBrowserOpenOnFailure = true;
    else if (a === '--fail-on-gap') parsed.failOnGap = true;
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
function stripReadbackPhasePrefix(message) {
  return String(message || '').replace(/^(before_refresh|after_refresh):\s*/i, '');
}
function summarizeMissing(missing) {
  const unique = Array.from(new Set((missing || []).map(stripReadbackPhasePrefix)));
  return {
    unique,
    filter_missing: unique.filter((item) => /filter row/i.test(item)),
    sort_missing: unique.filter((item) => /sort row/i.test(item)),
    extraction_or_other: unique.filter((item) => !/filter row|sort row/i.test(item))
  };
}

function primitiveEntryFromCapabilityMap(capabilityMap) {
  const entries = Array.isArray(capabilityMap?.primitives) ? capabilityMap.primitives : [];
  return entries.find((entry) => entry?.primitive_id === SUPPORTED_PRIMITIVE) || null;
}

function capabilityViewMap(capabilityMap) {
  const out = new Map();
  for (const item of Array.isArray(capabilityMap?.views) ? capabilityMap.views : []) {
    if (item?.view_key) out.set(String(item.view_key).toLowerCase(), item);
  }
  return out;
}

function manifestTargetsForSupportedPrimitive(manifest, capabilityMap) {
  const primitive = primitiveEntryFromCapabilityMap(capabilityMap);
  if (!primitive) throw new Error(`Capability map does not contain primitive ${SUPPORTED_PRIMITIVE}.`);
  if (primitive.schema_supported !== true || primitive.ui_discovery_supported !== true) {
    throw new Error(`Capability map does not mark ${SUPPORTED_PRIMITIVE} as schema-supported and UI-observed.`);
  }
  const capViews = capabilityViewMap(capabilityMap);
  const wantedKeys = [];
  for (const view of Array.isArray(manifest?.views) ? manifest.views : []) {
    const key = targetKeyOf({ table_name: view.table_name, view_name: view.view_name }).toLowerCase();
    const filters = Array.isArray(view.filters) ? view.filters : [];
    const hasExpectedFilter = filters.length === 1 && isRelativeDateTodayFilter(filters[0]);
    if (!hasExpectedFilter) continue;
    const capView = capViews.get(key) || capViews.get(String(view.view_key || '').toLowerCase());
    const capFilters = Array.isArray(capView?.filters) ? capView.filters : [];
    const capAllows = capFilters.some((filter) => filter?.primitive_id === SUPPORTED_PRIMITIVE && filter?.schema_supported === true);
    if (capAllows) wantedKeys.push(targetKeyOf({ table_name: view.table_name, view_name: view.view_name }));
  }
  return wantedKeys;
}

function assertVerifySupportedTarget(target, capabilityMap) {
  if (!Array.isArray(target.expected_filters) || target.expected_filters.length !== 1) {
    throw new Error(`Target ${targetKeyOf(target)} is not supported: expected exactly one manifest filter.`);
  }
  if (!isRelativeDateTodayFilter(target.expected_filters[0])) {
    throw new Error(`Target ${targetKeyOf(target)} is not supported: expected one relative-date filter with operator "on or before" and value "today".`);
  }
  const capView = capabilityViewMap(capabilityMap).get(targetKeyOf(target).toLowerCase()) || capabilityViewMap(capabilityMap).get(String(target.view_key || '').toLowerCase());
  const capFilters = Array.isArray(capView?.filters) ? capView.filters : [];
  if (!capFilters.some((filter) => filter?.primitive_id === SUPPORTED_PRIMITIVE && filter?.schema_supported === true)) {
    throw new Error(`Capability map does not mark target as schema-supported for ${SUPPORTED_PRIMITIVE}: ${targetKeyOf(target)}`);
  }
}

const args = parseArgs(process.argv);
if (!args.manifest) throw new Error('--manifest is required.');
if (!args.capabilityMap) throw new Error('--capability-map is required.');
if (!args.outputDir) throw new Error('--output-dir is required.');
if (!args.allSupportedRelativeDateTargets && args.targetKeys.length < 1) throw new Error('Use --all-supported-relative-date-targets or one or more --target-key arguments.');
if (args.maxTargets && (!Number.isInteger(args.maxTargets) || args.maxTargets < 1 || args.maxTargets > 100)) throw new Error('--max-targets must be an integer from 1 to 100.');

ensureDir(args.outputDir);
const outputDir = args.outputDir;
const logPath = path.join(outputDir, 'verify_relative_date_filters.log');
let page;
let browser;
let context;
let cdpBrowser;
let success = false;
const results = [];

function log(message, obj) {
  const line = `${nowIso()} ${message}${obj ? ' ' + JSON.stringify(obj) : ''}`;
  fs.appendFileSync(logPath, line + '\n', 'utf8');
  console.log(line);
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
  await rl.question('Read-only WBS09 relative-date verification: close unrelated Chrome windows or confirm the DCOIR Chrome profile is ready, then press Enter to launch Airtable browser automation. Ctrl+C aborts before browser launch.');
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
  } else if (args.userDataDir) {
    log('Launching persistent browser context.', { user_data_dir: args.userDataDir, chrome_channel: !!args.useChromeChannel, timeout_ms: args.browserLaunchTimeoutMs });
    context = await withTimeout(chromium.launchPersistentContext(args.userDataDir, {
      headless: !!args.headless,
      channel: args.useChromeChannel ? 'chrome' : undefined,
      viewport: { width: 1500, height: 980 }
    }), args.browserLaunchTimeoutMs, 'launchPersistentContext');
    page = context.pages()[0] || await withTimeout(context.newPage(), args.browserLaunchTimeoutMs, 'newPage after persistent launch');
  } else {
    log('Launching browser.', { chrome_channel: !!args.useChromeChannel, timeout_ms: args.browserLaunchTimeoutMs });
    browser = await withTimeout(chromium.launch({ headless: !!args.headless, channel: args.useChromeChannel ? 'chrome' : undefined }), args.browserLaunchTimeoutMs, 'launchBrowser');
    context = await withTimeout(browser.newContext({ viewport: { width: 1500, height: 980 } }), args.browserLaunchTimeoutMs, 'newContext after browser launch');
    page = await withTimeout(context.newPage(), args.browserLaunchTimeoutMs, 'newPage after browser launch');
  }
  log('Browser context ready.', { pages: context.pages().length });
  await page.goto(baseUrl, { waitUntil: 'domcontentloaded', timeout: 15000 }).catch((error) => log('Initial Airtable navigation warning.', { error: String(error?.message || error) }));
  await page.waitForLoadState('networkidle', { timeout: 12000 }).catch(() => {});
  await safeMousePark(page, 'after-open-base-url');
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

async function captureTargetReadback(target) {
  const result = {
    timestamp_utc: nowIso(),
    tool_version: TOOL_VERSION,
    shared_panel_readback_version: AIRTABLE_PANEL_READBACK_VERSION,
    primitive_id: SUPPORTED_PRIMITIVE,
    target,
    status: 'started',
    steps: [],
    snapshots: []
  };
  log('Verify target starting.', { target_key: targetKeyOf(target) });
  result.steps.push({ action: 'select_target', ...(await selectAirtableTableAndView(page, target)) });
  result.snapshots.push(await captureDomEvidence(page, outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_00_target_loaded`, args));

  result.before_filter = await captureAirtablePanelState(page, outputDir, target, 'filter', 'before_refresh', args);
  result.before_sort = await captureAirtablePanelState(page, outputDir, target, 'sort', 'before_refresh', args);

  await page.reload({ waitUntil: 'domcontentloaded', timeout: 15000 }).catch(() => {});
  await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
  await page.waitForTimeout(1200);
  result.steps.push({ action: 'reload_for_saved_view_persistence_check', ok: true, url: page.url() });
  result.steps.push({ action: 'reselect_after_reload', ...(await selectAirtableTableAndView(page, target)) });
  result.snapshots.push(await captureDomEvidence(page, outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_10_after_refresh_target_loaded`, args));

  result.after_filter = await captureAirtablePanelState(page, outputDir, target, 'filter', 'after_refresh', args);
  result.after_sort = await captureAirtablePanelState(page, outputDir, target, 'sort', 'after_refresh', args);
  result.comparison = compareAirtablePanelReadback(result);
  result.missing_summary = summarizeMissing(result.comparison.missing);
  result.status = result.comparison.ok ? 'already_correct_verified_read_only' : 'verification_gap_found';
  result.completed_at_utc = nowIso();
  const reportPath = path.join(outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_relative_date_verify_report.json`);
  writeJson(reportPath, result);
  result.report_path = reportPath;
  log('Verify target completed.', { target_key: targetKeyOf(target), status: result.status, missing: result.comparison.missing });
  return result;
}

try {
  log('Starting DCOIR WBS09 verify relative-date filters.', {
    version: TOOL_VERSION,
    shared_panel_readback_version: AIRTABLE_PANEL_READBACK_VERSION,
    primitive_id: SUPPORTED_PRIMITIVE
  });
  const manifest = readJsonFile(args.manifest);
  const capabilityMap = readJsonFile(args.capabilityMap);
  const selectedTargetKeys = args.allSupportedRelativeDateTargets
    ? manifestTargetsForSupportedPrimitive(manifest, capabilityMap)
    : args.targetKeys;
  if (selectedTargetKeys.length < 1) throw new Error('No supported relative-date targets selected.');
  const limitedKeys = args.maxTargets > 0 ? selectedTargetKeys.slice(0, args.maxTargets) : selectedTargetKeys;
  const targets = selectManifestTargets(manifest, { targetKeys: limitedKeys });
  for (const target of targets) {
    target.base_id = target.base_id || manifest.base_id || undefined;
    assertVerifySupportedTarget(target, capabilityMap);
  }
  const baseUrl = args.baseUrl || `https://airtable.com/${manifest.base_id || targets[0]?.base_id || ''}`;
  writeJson(path.join(outputDir, 'selected_relative_date_targets.json'), {
    timestamp_utc: nowIso(),
    tool_version: TOOL_VERSION,
    primitive_id: SUPPORTED_PRIMITIVE,
    requested_target_count: selectedTargetKeys.length,
    selected_target_count: targets.length,
    max_targets: args.maxTargets,
    targets: targets.map((target) => ({ target_key: targetKeyOf(target), table_name: target.table_name, view_name: target.view_name, expected_filters: target.expected_filters, expected_sorts: target.expected_sorts }))
  });

  await openBrowser(baseUrl);
  if (!args.headless) {
    const rl = readline.createInterface({ input, output });
    await rl.question(`Read-only verification for ${targets.length} WBS09 relative-date filter target(s). Confirm Airtable is open, then press Enter. No mutation token is required. Ctrl+C aborts.`);
    rl.close();
  }

  for (const target of targets) {
    try {
      results.push(await captureTargetReadback(target));
    } catch (error) {
      const failure = {
        timestamp_utc: nowIso(),
        tool_version: TOOL_VERSION,
        shared_panel_readback_version: AIRTABLE_PANEL_READBACK_VERSION,
        primitive_id: SUPPORTED_PRIMITIVE,
        target,
        status: 'verification_failed',
        error: String(error?.message || error),
        stack: String(error?.stack || '')
      };
      try {
        failure.snapshot = await captureDomEvidence(page, outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_relative_date_verify_failure`, args);
      } catch (snapshotError) {
        failure.snapshot = { error: String(snapshotError?.message || snapshotError) };
      }
      const reportPath = path.join(outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_relative_date_verify_failed.json`);
      writeJson(reportPath, failure);
      failure.report_path = reportPath;
      results.push(failure);
      log('Verify target failed.', { target_key: targetKeyOf(target), error: failure.error });
    }
  }

  const rollup = {
    timestamp_utc: nowIso(),
    tool_version: TOOL_VERSION,
    shared_panel_readback_version: AIRTABLE_PANEL_READBACK_VERSION,
    primitive_id: SUPPORTED_PRIMITIVE,
    status: 'UNKNOWN',
    target_count: targets.length,
    pass_count: results.filter((r) => r.status === 'already_correct_verified_read_only').length,
    gap_count: results.filter((r) => r.status === 'verification_gap_found').length,
    failed_count: results.filter((r) => r.status === 'verification_failed').length,
    results: results.map((r) => ({
      target_key: targetKeyOf(r.target),
      table_name: r.target.table_name,
      view_name: r.target.view_name,
      status: r.status,
      missing: r.comparison?.missing || [],
      missing_summary: r.missing_summary || null,
      error: r.error || null,
      report_path: r.report_path
    }))
  };
  rollup.status = rollup.failed_count > 0 ? 'FAILED_TARGETS' : (rollup.gap_count > 0 ? 'GAP_FOUND' : 'PASS');
  writeJson(path.join(outputDir, 'verify_relative_date_filters_rollup.json'), rollup);
  log('Verify relative-date filters completed.', rollup);
  success = rollup.failed_count === 0 && (!args.failOnGap || rollup.gap_count === 0);
  process.exitCode = success ? 0 : 1;
} catch (error) {
  const failure = {
    timestamp_utc: nowIso(),
    tool_version: TOOL_VERSION,
    status: 'fatal_failed',
    error: String(error?.message || error),
    stack: String(error?.stack || ''),
    results
  };
  try { writeJson(path.join(outputDir, 'verify_relative_date_filters_fatal_error.json'), failure); } catch {}
  console.error(failure.error);
  process.exitCode = 1;
} finally {
  await closeBrowser().catch((error) => console.error(String(error?.message || error)));
}
