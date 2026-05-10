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
  captureAirtablePanelState,
  compareAirtablePanelReadback
} from '../../shared/dcoir_airtable_panel_readback.mjs';

const WBS09_PANEL_READBACK_VERSION = '2026-05-10.wbs09-panel-readback.1';
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

async function openBrowser(baseUrl) {
  if (args.connectCdpUrl) {
    browser = await chromium.connectOverCDP(args.connectCdpUrl);
    context = browser.contexts()[0] || await browser.newContext();
    page = context.pages()[0] || await context.newPage();
    closeMode = 'cdp';
  } else if (args.userDataDir) {
    context = await chromium.launchPersistentContext(args.userDataDir, {
      headless: args.headless,
      channel: args.useChromeChannel ? 'chrome' : undefined,
      viewport: { width: 1500, height: 980 }
    });
    page = context.pages()[0] || await context.newPage();
    closeMode = 'persistent';
  } else {
    browser = await chromium.launch({ headless: args.headless, channel: args.useChromeChannel ? 'chrome' : undefined });
    context = await browser.newContext({ viewport: { width: 1500, height: 980 } });
    page = await context.newPage();
    closeMode = 'launched';
  }

  await page.goto(baseUrl, { waitUntil: 'domcontentloaded', timeout: 15000 });
  await page.waitForLoadState('networkidle', { timeout: 12000 }).catch(() => {});
  await safeMousePark(page, 'after-open-base-url');
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

  result.before_filter = await captureAirtablePanelState(page, outputDir, target, 'filter', 'before_refresh', args);
  result.before_sort = await captureAirtablePanelState(page, outputDir, target, 'sort', 'before_refresh', args);

  await page.reload({ waitUntil: 'domcontentloaded', timeout: 15000 });
  await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
  await page.waitForTimeout(1200);
  result.steps.push({ action: 'reload_for_saved_view_persistence_check', ok: true, url: page.url() });
  result.steps.push(await selectAirtableTableAndView(page, target));
  result.snapshots.push(await captureDomEvidence(page, outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_10_after_refresh_target_loaded`, args));

  result.after_filter = await captureAirtablePanelState(page, outputDir, target, 'filter', 'after_refresh', args);
  result.after_sort = await captureAirtablePanelState(page, outputDir, target, 'sort', 'after_refresh', args);

  result.comparison = compareAirtablePanelReadback(result);
  result.status = result.comparison.ok ? 'expected_panel_state_observed_after_refresh' : 'panel_state_gap_found';
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
  const manifest = readJsonFile(args.manifest);
  const targets = selectManifestTargets(manifest, {
    allViews: args.allManifestViews,
    targetKeys: args.targetKeys,
    defaultTargetKeys: WBS09_DEFAULT_REPRESENTATIVE_TARGET_KEYS
  });
  const baseUrl = args.baseUrl || `https://airtable.com/${manifest.base_id}`;
  for (const target of targets) target.base_id = manifest.base_id;

  await openBrowser(baseUrl);
  rl = readline.createInterface({ input, output });
  await rl.question('Read-only panel readback: log into Airtable, confirm the DCOIR base is open, then press Enter. No configure token is required. Ctrl+C aborts. ');

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
        snapshot: await captureDomEvidence(page, outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_panel_readback_failure`, args).catch((e) => ({ error: String(e) }))
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
    results: readbackResults.map((r) => ({ table_name: r.target.table_name, view_name: r.target.view_name, status: r.status, missing: r.comparison?.missing || [], report_path: r.report_path }))
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
