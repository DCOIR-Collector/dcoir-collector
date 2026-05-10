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
  captureAirtablePanelState
} from '../../shared/dcoir_airtable_panel_readback.mjs';
import {
  AIRTABLE_PANEL_DISCOVERY_VERSION,
  buildAirtableViewChangePlan,
  captureAirtablePanelDiscovery
} from '../../shared/dcoir_airtable_panel_discovery.mjs';

const WBS09_VIEW_DISCOVERY_VERSION = '2026-05-10.wbs09-view-discovery.4';
const WBS09_DEFAULT_DISCOVERY_TARGET_KEYS = Object.freeze([
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
    targetKeys: [],
    probeDropdownOptions: false,
    maxDropdownProbes: 0
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
    else if (a === '--probe-dropdown-options') parsed.probeDropdownOptions = true;
    else if (a === '--max-dropdown-probes') parsed.maxDropdownProbes = Number(next());
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

const outputDir = args.outputDir || path.join(downloads, `dcoir_wbs09_view_discovery_${new Date().toISOString().replace(/[:.]/g, '')}`);
ensureDir(outputDir);
const logPath = path.join(outputDir, 'view_discovery.log');
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
const discoveryResults = [];

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

async function discoverOneTarget(target) {
  const result = {
    timestamp_utc: nowIso(),
    tool_version: WBS09_VIEW_DISCOVERY_VERSION,
    shared_panel_readback_version: AIRTABLE_PANEL_READBACK_VERSION,
    shared_panel_discovery_version: AIRTABLE_PANEL_DISCOVERY_VERSION,
    target,
    steps: [],
    snapshots: [],
    status: 'started',
    safety: {
      read_only: true,
      mutation_controls_clicked: false,
      note: 'Discovery selects a table/view, opens panels, extracts current state/control inventory, optionally opens dropdowns to read option text, and never types/selects/adds/removes/saves.'
    }
  };

  log('View discovery target starting.', { table_name: target.table_name, view_name: target.view_name });
  result.steps.push(await selectAirtableTableAndView(page, target));
  result.snapshots.push(await captureDomEvidence(page, outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_00_target_loaded`, args));

  result.current_filter = await captureAirtablePanelState(page, outputDir, target, 'filter', 'current', args);
  result.current_sort = await captureAirtablePanelState(page, outputDir, target, 'sort', 'current', args);
  result.change_plan = buildAirtableViewChangePlan(target, result.current_filter, result.current_sort);

  result.filter_discovery = await captureAirtablePanelDiscovery(page, outputDir, target, 'filter', 'current', {
    ...args,
    maxDropdownProbes: args.maxDropdownProbes || 0
  });
  result.sort_discovery = await captureAirtablePanelDiscovery(page, outputDir, target, 'sort', 'current', {
    ...args,
    maxDropdownProbes: args.maxDropdownProbes || 0
  });

  result.completed_at_utc = nowIso();
  result.status = 'discovery_complete';
  const reportPath = path.join(outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_view_discovery_report.json`);
  writeJson(reportPath, result);
  result.report_path = reportPath;
  discoveryResults.push(result);
  log('View discovery target completed.', {
    table_name: target.table_name,
    view_name: target.view_name,
    status: result.status,
    requires_mutation: result.change_plan.planned_actions.requires_mutation,
    missing: result.change_plan.comparison.missing_unique
  });
  return result;
}

try {
  log('Starting DCOIR WBS09 Airtable view discovery.', {
    version: WBS09_VIEW_DISCOVERY_VERSION,
    shared_panel_readback_version: AIRTABLE_PANEL_READBACK_VERSION,
    shared_panel_discovery_version: AIRTABLE_PANEL_DISCOVERY_VERSION,
    probe_dropdown_options: Boolean(args.probeDropdownOptions),
    max_dropdown_probes: args.maxDropdownProbes || 0
  });
  if (!args.manifest) throw new Error('Missing --manifest');
  const manifest = readJsonFile(args.manifest);
  const targets = selectManifestTargets(manifest, {
    allViews: args.allManifestViews,
    targetKeys: args.targetKeys,
    defaultTargetKeys: WBS09_DEFAULT_DISCOVERY_TARGET_KEYS
  });
  const baseUrl = args.baseUrl || `https://airtable.com/${manifest.base_id}`;
  for (const target of targets) target.base_id = manifest.base_id;

  await openBrowser(baseUrl);
  rl = readline.createInterface({ input, output });
  await rl.question('Read-only view discovery: log into Airtable, confirm the DCOIR base is open, then press Enter. No configure token is required. Ctrl+C aborts. ');

  for (const target of targets) {
    try {
      await discoverOneTarget(target);
    } catch (error) {
      const failure = {
        timestamp_utc: nowIso(),
        tool_version: WBS09_VIEW_DISCOVERY_VERSION,
        shared_panel_readback_version: AIRTABLE_PANEL_READBACK_VERSION,
        shared_panel_discovery_version: AIRTABLE_PANEL_DISCOVERY_VERSION,
        target,
        status: 'view_discovery_failed',
        error: String(error && error.message ? error.message : error),
        snapshot: await captureDomEvidence(page, outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_view_discovery_failure`, args).catch((e) => ({ error: String(e) }))
      };
      const reportPath = path.join(outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_view_discovery_failed.json`);
      writeJson(reportPath, failure);
      failure.report_path = reportPath;
      discoveryResults.push(failure);
      log('View discovery target failed.', { table_name: target.table_name, view_name: target.view_name, error: failure.error });
    }
  }

  const rollup = {
    timestamp_utc: nowIso(),
    tool_version: WBS09_VIEW_DISCOVERY_VERSION,
    shared_panel_readback_version: AIRTABLE_PANEL_READBACK_VERSION,
    shared_panel_discovery_version: AIRTABLE_PANEL_DISCOVERY_VERSION,
    status: discoveryResults.some((r) => r.status === 'view_discovery_failed') ? 'DISCOVERY_FAILED' : 'DISCOVERY_COMPLETE',
    target_count: targets.length,
    completed_count: discoveryResults.filter((r) => r.status === 'discovery_complete').length,
    failed_count: discoveryResults.filter((r) => r.status === 'view_discovery_failed').length,
    mutation_required_count: discoveryResults.filter((r) => r.change_plan?.planned_actions?.requires_mutation).length,
    results: discoveryResults.map((r) => ({
      table_name: r.target.table_name,
      view_name: r.target.view_name,
      status: r.status,
      requires_mutation: Boolean(r.change_plan?.planned_actions?.requires_mutation),
      planned_actions: r.change_plan?.planned_actions || null,
      missing: r.change_plan?.comparison?.missing_unique || [],
      report_path: r.report_path
    }))
  };
  writeJson(path.join(outputDir, 'view_discovery_rollup.json'), rollup);
  log('View discovery completed.', rollup);
  await closeBrowser(rollup.failed_count === 0);
  process.exit(rollup.failed_count === 0 ? 0 : 1);
} catch (error) {
  const failure = { timestamp_utc: nowIso(), error: String(error && error.message ? error.message : error), results: discoveryResults };
  log('View discovery fatal failure.', { error: failure.error });
  writeJson(path.join(outputDir, 'view_discovery_fatal_error.json'), failure);
  await closeBrowser(false).catch(() => {});
  process.exit(1);
} finally {
  if (rl) rl.close();
}
