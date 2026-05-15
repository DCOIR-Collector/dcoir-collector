#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import readline from 'node:readline/promises';
import { stdin as input, stdout as output } from 'node:process';
import { chromium } from 'playwright';
import { ensureDir, readJsonFile, writeJson, nowIso, safeName } from '../../shared/dcoir_ui_common.mjs';
import { safeMousePark } from '../../shared/dcoir_airtable_ui_geometry.mjs';
import {
  AIRTABLE_PANEL_READBACK_VERSION,
  selectManifestTargets,
  selectAirtableTableAndView,
  captureDomEvidence,
  captureAirtableGridRowState,
  captureAirtablePanelState,
  compareAirtablePanelReadback,
  filterReadbackTargetsForResume,
  reloadPageWithRetry,
  targetKeyOfReadbackTarget
} from '../../shared/dcoir_airtable_panel_readback.mjs';

const WBS09_PANEL_READBACK_VERSION = '2026-05-14.wbs09-panel-readback.4';
const WBS09_DEFAULT_REPRESENTATIVE_TARGET_KEYS = Object.freeze([
  'Governance Control Plane::WBS09 - Startup Authority',
  'Session Checkpoints::WBS09 - Needs Review',
  'Operator Tools Registry::WBS09 - Active Tools',
  'Work Items::WBS09 - By Parent Plan'
]);

function parseArgs(argv) {
  const parsed = {
    enableScreenshots: false,
    headless: false,
    useChromeChannel: false,
    userDataDir: null,
    connectCdpUrl: null,
    keepBrowserOpenOnFailure: false,
    noAirtableReadyPrompt: false,
    browserLaunchTimeoutMs: 90000,
    reloadAttempts: 3,
    reloadTimeoutMs: 30000,
    reloadBackoffMs: 4000,
    reloadSettleMs: 1200,
    networkIdleTimeoutMs: 12000,
    targetListFile: null,
    startAtTargetKey: null,
    afterTargetKey: null,
    maxTargets: 0,
    defaultRepresentativeTargets: false,
    allManifestViews: false,
    targetKeys: []
  };
  for (let i = 2; i < argv.length; i += 1) {
    const a = argv[i];
    const next = () => argv[++i];
    if (a === '--manifest') parsed.manifest = next();
    else if (a === '--output-dir') parsed.outputDir = next();
    else if (a === '--base-url') parsed.baseUrl = next();
    else if (a === '--enable-screenshots') parsed.enableScreenshots = true;
    else if (a === '--headless') parsed.headless = true;
    else if (a === '--use-chrome-channel') parsed.useChromeChannel = true;
    else if (a === '--user-data-dir') parsed.userDataDir = next();
    else if (a === '--connect-cdp-url') parsed.connectCdpUrl = next();
    else if (a === '--keep-browser-open-on-failure') parsed.keepBrowserOpenOnFailure = true;
    else if (a === '--no-airtable-ready-prompt') parsed.noAirtableReadyPrompt = true;
    else if (a === '--browser-launch-timeout-ms') parsed.browserLaunchTimeoutMs = Number(next());
    else if (a === '--reload-attempts') parsed.reloadAttempts = Number(next());
    else if (a === '--reload-timeout-ms') parsed.reloadTimeoutMs = Number(next());
    else if (a === '--reload-backoff-ms') parsed.reloadBackoffMs = Number(next());
    else if (a === '--reload-settle-ms') parsed.reloadSettleMs = Number(next());
    else if (a === '--network-idle-timeout-ms') parsed.networkIdleTimeoutMs = Number(next());
    else if (a === '--target-list-file') parsed.targetListFile = next();
    else if (a === '--start-at-target-key') parsed.startAtTargetKey = next();
    else if (a === '--after-target-key') parsed.afterTargetKey = next();
    else if (a === '--max-targets') parsed.maxTargets = Number(next());
    else if (a === '--default-representative-targets') parsed.defaultRepresentativeTargets = true;
    else if (a === '--all-manifest-views') parsed.allManifestViews = true;
    else if (a === '--target-key') parsed.targetKeys.push(next());
    else throw new Error(`Unknown argument: ${a}`);
  }
  return parsed;
}

const args = parseArgs(process.argv);
const downloads = process.env.DCOIR_DOWNLOADS_DIR;
if (!downloads || !downloads.trim()) {
  console.error('Missing required Local Configuration Registry variable: DCOIR_DOWNLOADS_DIR');
  process.exit(2);
}

const outputDir = args.outputDir || path.join(downloads, `dcoir_wbs09_view_panel_readback_${new Date().toISOString().replace(/[:.]/g, '')}`);
ensureDir(outputDir);
const logPath = path.join(outputDir, 'view_panel_readback.log');
function log(message, obj) {
  const line = `${nowIso()} ${message}${obj ? ' ' + JSON.stringify(obj) : ''}`;
  fs.appendFileSync(logPath, line + '\n', 'utf8');
  console.log(line);
}

let browser = null;
let context = null;
let page = null;
let rl = null;
let closeMode = 'launched';
const readbackResults = [];

function assertTimeout(value, label) {
  if (!Number.isFinite(value) || value < 10000 || value > 300000) {
    throw new Error(`${label} must be between 10000 and 300000 milliseconds.`);
  }
}

function withTimeout(promise, timeoutMs, label) {
  let timer;
  const timeout = new Promise((_, reject) => {
    timer = setTimeout(() => reject(new Error(`${label} timed out after ${timeoutMs}ms. Close extra Chrome instances, verify the profile is not locked, or retry with a fresh DCOIR Chrome profile.`)), timeoutMs);
  });
  return Promise.race([promise, timeout]).finally(() => clearTimeout(timer));
}

function assertPositiveInteger(value, label, min, max) {
  if (!Number.isInteger(value) || value < min || value > max) {
    throw new Error(`${label} must be an integer from ${min} to ${max}.`);
  }
}

function readTargetListFile(filePath) {
  if (!filePath) return [];
  const raw = fs.readFileSync(filePath, 'utf8').trim();
  if (!raw) return [];
  if (raw.startsWith('[')) {
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) throw new Error('--target-list-file JSON must be an array.');
    return parsed.map((item) => String(item));
  }
  return raw.split(/\r?\n/).map((line) => line.trim()).filter((line) => line && !line.startsWith('#'));
}

async function waitForAirtableReadyPrompt() {
  if (args.headless || args.noAirtableReadyPrompt) {
    log('Skipping Airtable-ready operator prompt.', { headless: !!args.headless, no_airtable_ready_prompt: !!args.noAirtableReadyPrompt });
    return;
  }
  if (!process.stdin.isTTY) {
    throw new Error('Airtable-ready prompt requires interactive stdin. Do not pipe this Node process through Tee-Object; use Start-Transcript or the provided v3 runner instead.');
  }
  rl = readline.createInterface({ input, output });
  await rl.question('Read-only panel readback: log into Airtable, confirm the DCOIR base is open, then press Enter. No configure token is required. Ctrl+C aborts. ');
}

async function openBrowser(baseUrl) {
  assertTimeout(args.browserLaunchTimeoutMs, 'browserLaunchTimeoutMs');
  log('Opening browser for Airtable panel readback.', {
    base_url: baseUrl,
    connect_cdp: !!args.connectCdpUrl,
    persistent_profile: !!args.userDataDir,
    use_chrome_channel: !!args.useChromeChannel,
    timeout_ms: args.browserLaunchTimeoutMs
  });

  if (args.connectCdpUrl) {
    browser = await withTimeout(chromium.connectOverCDP(args.connectCdpUrl), args.browserLaunchTimeoutMs, 'connectOverCDP');
    context = browser.contexts()[0] || await withTimeout(browser.newContext(), args.browserLaunchTimeoutMs, 'newContext after CDP connect');
    page = context.pages()[0] || await withTimeout(context.newPage(), args.browserLaunchTimeoutMs, 'newPage after CDP connect');
    closeMode = 'cdp';
  } else if (args.userDataDir) {
    context = await withTimeout(chromium.launchPersistentContext(args.userDataDir, {
      headless: args.headless,
      channel: args.useChromeChannel ? 'chrome' : undefined,
      viewport: { width: 1500, height: 980 }
    }), args.browserLaunchTimeoutMs, 'launchPersistentContext');
    page = context.pages()[0] || await withTimeout(context.newPage(), args.browserLaunchTimeoutMs, 'newPage after persistent launch');
    closeMode = 'persistent';
  } else {
    browser = await withTimeout(chromium.launch({ headless: args.headless, channel: args.useChromeChannel ? 'chrome' : undefined }), args.browserLaunchTimeoutMs, 'launchBrowser');
    context = await withTimeout(browser.newContext({ viewport: { width: 1500, height: 980 } }), args.browserLaunchTimeoutMs, 'newContext after browser launch');
    page = await withTimeout(context.newPage(), args.browserLaunchTimeoutMs, 'newPage after browser launch');
    closeMode = 'launched';
  }

  log('Browser context ready; navigating to Airtable.', { pages: context.pages().length });
  await page.goto(baseUrl, { waitUntil: 'domcontentloaded', timeout: 30000 }).catch((error) => {
    log('Initial Airtable navigation warning; continuing to operator login prompt.', { error: String(error?.message || error) });
  });
  await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
  await safeMousePark(page, 'after-open-base-url');
  log('Browser launch/navigation phase complete; waiting for Airtable-ready confirmation if enabled.', { url: page.url() });
}
async function closeBrowser(success) {
  if (!success && args.keepBrowserOpenOnFailure) {
    console.error('Failure detected. Browser will remain open for inspection. Press Enter in PowerShell after you finish inspecting/uploading screenshots.');
    if (rl) await rl.question('');
    return;
  }
  if (closeMode === 'persistent' && context) await context.close().catch(() => {});
  else if (browser) await browser.close().catch(() => {});
}


function effectiveRowState(record) {
  const candidates = [
    record?.row_state,
    record?.comparison?.row_state,
    record?.row_state_after?.row_state,
    record?.row_state_before?.row_state,
    record?.row_state?.row_state
  ];
  for (const candidate of candidates) {
    if (candidate === 'visible' || candidate === 'none' || candidate === 'unknown') return candidate;
  }
  return 'unknown';
}

async function readbackOneTarget(target) {
  const result = {
    timestamp_utc: nowIso(),
    tool_version: WBS09_PANEL_READBACK_VERSION,
    shared_panel_readback_version: AIRTABLE_PANEL_READBACK_VERSION,
    target,
    steps: [],
    snapshots: [],
    status: 'started'
  };

  log('Panel readback target starting.', { table_name: target.table_name, view_name: target.view_name });
  result.steps.push(await selectAirtableTableAndView(page, target));
  result.snapshots.push(await captureDomEvidence(page, outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_00_target_loaded`, args));
  result.row_state_before = await captureAirtableGridRowState(page, outputDir, target, 'before_refresh_target_loaded');

  result.before_filter = await captureAirtablePanelState(page, outputDir, target, 'filter', 'before_refresh', args);
  result.before_sort = await captureAirtablePanelState(page, outputDir, target, 'sort', 'before_refresh', args);

  result.reload = await reloadPageWithRetry(page, {
    maxAttempts: args.reloadAttempts,
    reloadTimeoutMs: args.reloadTimeoutMs,
    networkIdleTimeoutMs: args.networkIdleTimeoutMs,
    settleMs: args.reloadSettleMs,
    backoffMs: args.reloadBackoffMs,
    log
  });
  result.steps.push({ action: 'reload_for_saved_view_persistence_check', ok: result.reload.ok, attempts: result.reload.attempts, url: page.url() });
  if (!result.reload.ok) {
    throw new Error(`reload_for_saved_view_persistence_check failed after ${args.reloadAttempts} attempts: ${result.reload.error || 'unknown reload failure'}`);
  }
  result.steps.push(await selectAirtableTableAndView(page, target));
  result.snapshots.push(await captureDomEvidence(page, outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_10_after_refresh_target_loaded`, args));
  result.row_state_after = await captureAirtableGridRowState(page, outputDir, target, 'after_refresh_target_loaded');

  result.after_filter = await captureAirtablePanelState(page, outputDir, target, 'filter', 'after_refresh', args);
  result.after_sort = await captureAirtablePanelState(page, outputDir, target, 'sort', 'after_refresh', args);

  result.comparison = compareAirtablePanelReadback(result);
  result.status = result.comparison.ok ? 'expected_panel_state_observed_after_refresh' : 'panel_state_gap_found';
  result.gap_details = result.comparison.gap_details || [];
  result.gap_summary = result.comparison.gap_summary || { total: 0 };
  result.row_state = result.comparison.row_state || result.row_state_after?.row_state || result.row_state_before?.row_state || 'unknown';
  result.completed_at_utc = nowIso();

  const reportPath = path.join(outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_panel_readback_report.json`);
  writeJson(reportPath, result);
  result.report_path = reportPath;
  readbackResults.push(result);
  log('Panel readback target completed.', { table_name: target.table_name, view_name: target.view_name, status: result.status, missing: result.comparison.missing });
  return result;
}

try {
  log('Starting DCOIR WBS09 Airtable view panel readback.', { version: WBS09_PANEL_READBACK_VERSION, shared_panel_readback_version: AIRTABLE_PANEL_READBACK_VERSION });
  if (!args.manifest) throw new Error('Missing --manifest');
  assertPositiveInteger(args.reloadAttempts, '--reload-attempts', 1, 8);
  assertTimeout(args.reloadTimeoutMs, 'reloadTimeoutMs');
  assertTimeout(args.networkIdleTimeoutMs, 'networkIdleTimeoutMs');
  if (args.maxTargets && (!Number.isInteger(args.maxTargets) || args.maxTargets < 1 || args.maxTargets > 100)) throw new Error('--max-targets must be an integer from 1 to 100.');

  const manifest = readJsonFile(args.manifest);
  const targetKeysFromFile = readTargetListFile(args.targetListFile);
  const effectiveTargetKeys = [...targetKeysFromFile, ...args.targetKeys];
  let targets = selectManifestTargets(manifest, {
    allViews: args.allManifestViews && effectiveTargetKeys.length < 1,
    targetKeys: effectiveTargetKeys,
    defaultTargetKeys: WBS09_DEFAULT_REPRESENTATIVE_TARGET_KEYS
  });
  targets = filterReadbackTargetsForResume(targets, {
    startAtTargetKey: args.startAtTargetKey,
    afterTargetKey: args.afterTargetKey,
    maxTargets: args.maxTargets
  });
  const baseUrl = args.baseUrl || `https://airtable.com/${manifest.base_id}`;
  for (const target of targets) target.base_id = manifest.base_id;
  writeJson(path.join(outputDir, 'selected_view_panel_readback_targets.json'), {
    timestamp_utc: nowIso(),
    tool_version: WBS09_PANEL_READBACK_VERSION,
    all_manifest_views: !!args.allManifestViews,
    target_list_file: args.targetListFile || null,
    target_keys_requested: effectiveTargetKeys,
    start_at_target_key: args.startAtTargetKey || null,
    after_target_key: args.afterTargetKey || null,
    max_targets: args.maxTargets || 0,
    selected_target_count: targets.length,
    targets: targets.map((target, index) => ({ index: index + 1, target_key: targetKeyOfReadbackTarget(target), table_name: target.table_name, view_name: target.view_name }))
  });

  await openBrowser(baseUrl);
  await waitForAirtableReadyPrompt();

  for (const target of targets) {
    try {
      await readbackOneTarget(target);
    } catch (error) {
      const failure = {
        timestamp_utc: nowIso(),
        tool_version: WBS09_PANEL_READBACK_VERSION,
        shared_panel_readback_version: AIRTABLE_PANEL_READBACK_VERSION,
        target,
        status: 'panel_readback_failed',
        error: String(error && error.message ? error.message : error),
        target_key: targetKeyOfReadbackTarget(target),
        resume_from_target_key: targetKeyOfReadbackTarget(target),
        snapshot: await captureDomEvidence(page, outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_panel_readback_failure`, args).catch((e) => ({ error: String(e) })),
        row_state: await captureAirtableGridRowState(page, outputDir, target, 'failure_target_loaded').catch((e) => ({ ok: false, row_state: 'unknown', error: String(e) }))
      };
      const reportPath = path.join(outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_panel_readback_failed.json`);
      writeJson(reportPath, failure);
      failure.report_path = reportPath;
      readbackResults.push(failure);
      log('Panel readback target failed.', { table_name: target.table_name, view_name: target.view_name, error: failure.error });
    }
  }

  const rollup = {
    timestamp_utc: nowIso(),
    tool_version: WBS09_PANEL_READBACK_VERSION,
    shared_panel_readback_version: AIRTABLE_PANEL_READBACK_VERSION,
    status: readbackResults.every((r) => r.status === 'expected_panel_state_observed_after_refresh') ? 'PASS' : 'GAP_FOUND',
    target_count: targets.length,
    observed_count: readbackResults.filter((r) => r.status === 'expected_panel_state_observed_after_refresh').length,
    gap_count: readbackResults.filter((r) => r.status === 'panel_state_gap_found').length,
    failed_count: readbackResults.filter((r) => r.status === 'panel_readback_failed').length,
    filter_gap_count: readbackResults.reduce((sum, r) => sum + Number(r.gap_summary?.filter_gap_count || r.comparison?.gap_summary?.filter_gap_count || 0), 0),
    sort_gap_count: readbackResults.reduce((sum, r) => sum + Number(r.gap_summary?.sort_gap_count || r.comparison?.gap_summary?.sort_gap_count || 0), 0),
    panel_extraction_gap_count: readbackResults.reduce((sum, r) => sum + Number(r.gap_summary?.panel_extraction_gap_count || r.comparison?.gap_summary?.panel_extraction_gap_count || 0), 0),
    row_state_counts: {
      visible: readbackResults.filter((r) => effectiveRowState(r) === 'visible').length,
      none: readbackResults.filter((r) => effectiveRowState(r) === 'none').length,
      unknown: readbackResults.filter((r) => !['visible', 'none'].includes(effectiveRowState(r))).length
    },
    last_completed_target_key: [...readbackResults].reverse().find((r) => r.status !== 'panel_readback_failed')?.target ? targetKeyOfReadbackTarget([...readbackResults].reverse().find((r) => r.status !== 'panel_readback_failed').target) : null,
    first_failed_target_key: readbackResults.find((r) => r.status === 'panel_readback_failed')?.target ? targetKeyOfReadbackTarget(readbackResults.find((r) => r.status === 'panel_readback_failed').target) : null,
    gap_results: readbackResults
      .filter((r) => r.status !== 'expected_panel_state_observed_after_refresh')
      .map((r) => ({
        target_key: targetKeyOfReadbackTarget(r.target),
        table_name: r.target.table_name,
        view_name: r.target.view_name,
        status: r.status,
        row_state: effectiveRowState(r),
        missing: r.comparison?.missing || [],
        gap_details: r.gap_details || r.comparison?.gap_details || [],
        gap_summary: r.gap_summary || r.comparison?.gap_summary || null,
        error: r.error || null,
        report_path: r.report_path
      })),
    results: readbackResults.map((r) => ({
      table_name: r.target.table_name,
      view_name: r.target.view_name,
      status: r.status,
      row_state: effectiveRowState(r),
      missing: r.comparison?.missing || [],
      gap_details: r.gap_details || r.comparison?.gap_details || [],
      gap_summary: r.gap_summary || r.comparison?.gap_summary || null,
      report_path: r.report_path
    }))
  };
  writeJson(path.join(outputDir, 'view_panel_readback_rollup.json'), rollup);
  log('Panel readback completed.', rollup);
  await closeBrowser(rollup.failed_count === 0);
  process.exit(rollup.failed_count === 0 ? 0 : 1);
} catch (error) {
  const failure = { timestamp_utc: nowIso(), error: String(error && error.message ? error.message : error), results: readbackResults };
  log('Panel readback fatal failure.', { error: failure.error });
  writeJson(path.join(outputDir, 'view_panel_readback_fatal_error.json'), failure);
  await closeBrowser(false).catch(() => {});
  process.exit(1);
} finally {
  if (rl) rl.close();
}
