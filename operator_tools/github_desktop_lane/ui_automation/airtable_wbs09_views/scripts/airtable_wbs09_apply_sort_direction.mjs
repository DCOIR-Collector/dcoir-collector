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
  compareAirtablePanelReadback,
  openAirtablePanel,
  closeOpenAirtablePanel
} from '../../shared/dcoir_airtable_panel_readback.mjs';
import {
  AIRTABLE_PANEL_DISCOVERY_VERSION,
  buildAirtableViewChangePlan,
  captureAirtablePanelDiscovery
} from '../../shared/dcoir_airtable_panel_discovery.mjs';

const TOOL_VERSION = '2026-05-10.wbs09-apply-sort-direction.1';
const REQUIRED_TOKEN = 'APPLY_WBS09_SORT_DIRECTION';

function parseArgs(argv) {
  const parsed = {
    enableScreenshots: false,
    headless: false,
    useChromeChannel: false,
    userDataDir: null,
    connectCdpUrl: null,
    keepBrowserOpenOnFailure: false,
    targetKeys: [],
    confirmToken: null,
    maxDropdownProbes: 8
  };
  for (let i = 2; i < argv.length; i += 1) {
    const a = argv[i];
    const next = () => argv[++i];
    if (a === '--manifest') parsed.manifest = next();
    else if (a === '--output-dir') parsed.outputDir = next();
    else if (a === '--base-url') parsed.baseUrl = next();
    else if (a === '--target-key') parsed.targetKeys.push(next());
    else if (a === '--confirm-token') parsed.confirmToken = next();
    else if (a === '--enable-screenshots') parsed.enableScreenshots = true;
    else if (a === '--headless') parsed.headless = true;
    else if (a === '--use-chrome-channel') parsed.useChromeChannel = true;
    else if (a === '--user-data-dir') parsed.userDataDir = next();
    else if (a === '--connect-cdp-url') parsed.connectCdpUrl = next();
    else if (a === '--keep-browser-open-on-failure') parsed.keepBrowserOpenOnFailure = true;
    else if (a === '--max-dropdown-probes') parsed.maxDropdownProbes = Number(next());
    else throw new Error(`Unknown argument: ${a}`);
  }
  return parsed;
}

function norm(value) {
  return String(value || '').replace(/[\u2192\u27f6\u2794]/g, ' -> ').replace(/\s+/g, ' ').trim();
}
function lower(value) { return norm(value).toLowerCase(); }
function directionLabels(direction) {
  return String(direction || '').toLowerCase() === 'desc'
    ? [/z\s*->\s*a/i, /9\s*->\s*1/i, /latest\s*->\s*earliest/i, /descending/i]
    : [/a\s*->\s*z/i, /1\s*->\s*9/i, /earliest\s*->\s*latest/i, /ascending/i];
}
function probeHasDirectionOption(probe, direction) {
  return (probe?.options || []).some((option) => {
    const text = `${option.text || ''} ${option.aria || ''}`;
    return directionLabels(direction).some((rx) => rx.test(text));
  });
}
function optionMatchingDirection(probe, direction) {
  return (probe?.options || []).find((option) => {
    const text = `${option.text || ''} ${option.aria || ''}`;
    return directionLabels(direction).some((rx) => rx.test(text));
  });
}
function triggerLooksLikeCurrentDirection(probe, currentDirection) {
  const text = `${probe?.trigger_text || ''}`;
  return directionLabels(currentDirection).some((rx) => rx.test(text));
}
function expectedSort(target) {
  if (!Array.isArray(target.expected_sorts) || target.expected_sorts.length !== 1) {
    throw new Error('This tool only supports exactly one expected sort row for a single targeted view.');
  }
  return target.expected_sorts[0];
}
function summarizeMutationAllowed(plan, discovery, sort) {
  const probes = discovery?.dropdown_probes || [];
  const directionProbes = probes.filter((probe) => triggerLooksLikeCurrentDirection(probe, sort.direction === 'desc' ? 'asc' : 'desc'));
  const matching = directionProbes.find((probe) => probeHasDirectionOption(probe, sort.direction));
  return {
    expected_sort: sort,
    plan_sort_action: plan?.planned_actions?.sort_action || null,
    requires_mutation: Boolean(plan?.planned_actions?.requires_mutation),
    direction_probe_count: directionProbes.length,
    matching_probe_found: Boolean(matching),
    matching_probe: matching || null,
    allowed: Boolean(plan?.planned_actions?.requires_mutation) && plan?.planned_actions?.sort_action === 'change_sort_direction' && Boolean(matching)
  };
}

const args = parseArgs(process.argv);
const downloads = process.env.DCOIR_DOWNLOADS_DIR;
if (!downloads || !downloads.trim()) {
  console.error('Missing required Local Configuration Registry variable: DCOIR_DOWNLOADS_DIR');
  process.exit(2);
}
if (args.confirmToken !== REQUIRED_TOKEN) {
  console.error(`Missing required --confirm-token ${REQUIRED_TOKEN}`);
  process.exit(2);
}

const outputDir = args.outputDir || path.join(downloads, `dcoir_wbs09_apply_sort_direction_${new Date().toISOString().replace(/[:.]/g, '')}`);
ensureDir(outputDir);
const logPath = path.join(outputDir, 'apply_sort_direction.log');
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

async function clickDirectionOptionFromProbe(probe, direction) {
  const trigger = probe.trigger_bounds;
  if (!trigger) throw new Error('Matching probe did not include trigger bounds.');
  const optionHint = optionMatchingDirection(probe, direction);
  if (!optionHint) throw new Error(`Matching probe did not include target direction option: ${direction}`);

  await safeMousePark(page, 'before-direction-trigger-click');
  await page.mouse.click(Number(trigger.cx || (trigger.x + trigger.w / 2)), Number(trigger.cy || (trigger.y + trigger.h / 2)));
  await page.waitForTimeout(800);

  const clicked = await page.evaluate(({ direction }) => {
    const normalize = (s) => String(s || '').replace(/[\u2192\u27f6\u2794]/g, ' -> ').replace(/\s+/g, ' ').trim();
    const patterns = direction === 'desc'
      ? [/z\s*->\s*a/i, /9\s*->\s*1/i, /latest\s*->\s*earliest/i, /descending/i]
      : [/a\s*->\s*z/i, /1\s*->\s*9/i, /earliest\s*->\s*latest/i, /ascending/i];
    function visible(el) {
      const style = window.getComputedStyle(el);
      const box = el.getBoundingClientRect();
      return style && style.visibility !== 'hidden' && style.display !== 'none' && box.width > 0 && box.height > 0;
    }
    function topVisible(el, box) {
      const cx = Math.max(0, Math.min(window.innerWidth - 1, box.x + box.width / 2));
      const cy = Math.max(0, Math.min(window.innerHeight - 1, box.y + box.height / 2));
      const top = document.elementFromPoint(cx, cy);
      return !!top && (el === top || el.contains(top) || top.contains(el));
    }
    const candidates = Array.from(document.querySelectorAll('[role="option"], [role="menuitem"], button, [role="button"], li, div, span'))
      .filter(visible)
      .map((el) => {
        const box = el.getBoundingClientRect();
        const text = normalize(el.innerText || el.textContent || el.getAttribute('aria-label') || '');
        const aria = normalize(el.getAttribute('aria-label') || '');
        return { el, text, aria, role: el.getAttribute('role') || '', box, top: topVisible(el, box) };
      })
      .filter((item) => item.top && item.text && item.text.length <= 120)
      .filter((item) => patterns.some((rx) => rx.test(`${item.text} ${item.aria}`)))
      .sort((a, b) => {
        const aRole = /^(option|menuitem)$/i.test(a.role) ? 0 : 1;
        const bRole = /^(option|menuitem)$/i.test(b.role) ? 0 : 1;
        return aRole - bRole || a.box.y - b.box.y || a.box.x - b.box.x;
      });
    const picked = candidates[0];
    if (!picked) return { ok: false, reason: 'target_direction_option_not_visible' };
    picked.el.click();
    return {
      ok: true,
      clicked: {
        text: picked.text,
        aria: picked.aria,
        role: picked.role,
        x: Math.round(picked.box.x),
        y: Math.round(picked.box.y),
        w: Math.round(picked.box.width),
        h: Math.round(picked.box.height)
      }
    };
  }, { direction });
  await page.waitForTimeout(1000);
  if (!clicked.ok) throw new Error(`Could not click target direction option: ${clicked.reason || direction}`);
  return clicked;
}

async function verifyTarget(target, phase) {
  const filter = await captureAirtablePanelState(page, outputDir, target, 'filter', phase, args);
  const sort = await captureAirtablePanelState(page, outputDir, target, 'sort', phase, args);
  const comparison = compareAirtablePanelReadback({ target, before_filter: filter, after_filter: filter, before_sort: sort, after_sort: sort });
  return { filter, sort, comparison };
}

async function applyOneTarget(target) {
  const result = {
    timestamp_utc: nowIso(),
    tool_version: TOOL_VERSION,
    shared_panel_readback_version: AIRTABLE_PANEL_READBACK_VERSION,
    shared_panel_discovery_version: AIRTABLE_PANEL_DISCOVERY_VERSION,
    target,
    status: 'started',
    safety: {
      one_view_only: true,
      supported_mutation: 'change existing single sort row direction only',
      disallowed_mutations: ['create_view', 'delete_view', 'add_filter', 'delete_filter', 'add_sort', 'delete_sort', 'change_field', 'type_values'],
      exact_token_required: REQUIRED_TOKEN
    },
    steps: []
  };

  log('Sort-direction apply target starting.', { table_name: target.table_name, view_name: target.view_name });
  result.steps.push(await selectAirtableTableAndView(page, target));
  result.snapshots = [await captureDomEvidence(page, outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_00_target_loaded`, args)];

  result.before = await verifyTarget(target, 'before_apply');
  result.plan = buildAirtableViewChangePlan(target, result.before.filter, result.before.sort);
  const sort = expectedSort(target);

  if (result.before.comparison.ok) {
    result.status = 'already_correct_noop';
    result.completed_at_utc = nowIso();
    return result;
  }

  if (result.plan.planned_actions.sort_action !== 'change_sort_direction') {
    throw new Error(`Unsupported plan for this safe executor: ${JSON.stringify(result.plan.planned_actions)}`);
  }

  result.sort_discovery = await captureAirtablePanelDiscovery(page, outputDir, target, 'sort', 'pre_execute', {
    ...args,
    probeDropdownOptions: true,
    maxDropdownProbes: args.maxDropdownProbes || 8
  });
  result.pre_execute_gate = summarizeMutationAllowed(result.plan, result.sort_discovery, sort);
  if (!result.pre_execute_gate.allowed) {
    throw new Error(`Pre-execute option gate failed: ${JSON.stringify(result.pre_execute_gate)}`);
  }

  const opened = await openAirtablePanel(page, 'sort');
  result.execute_panel_opened = opened;
  await page.waitForTimeout(500);
  result.execute_click = await clickDirectionOptionFromProbe(result.pre_execute_gate.matching_probe, sort.direction);
  result.mutation_attempted = true;
  result.mutation_type = 'sort_direction_click';

  result.after_click = await verifyTarget(target, 'after_click');
  if (!result.after_click.comparison.ok) {
    throw new Error(`After-click verification failed: ${JSON.stringify(result.after_click.comparison.missing || [])}`);
  }

  await page.reload({ waitUntil: 'domcontentloaded', timeout: 15000 });
  await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
  await page.waitForTimeout(1200);
  result.after_reload_select = await selectAirtableTableAndView(page, target);
  result.after_refresh = await verifyTarget(target, 'after_refresh');
  result.status = result.after_refresh.comparison.ok ? 'sort_direction_verified_after_refresh' : 'sort_direction_gap_after_refresh';
  result.completed_at_utc = nowIso();
  return result;
}

try {
  log('Starting DCOIR WBS09 apply sort direction tool.', {
    version: TOOL_VERSION,
    shared_panel_readback_version: AIRTABLE_PANEL_READBACK_VERSION,
    shared_panel_discovery_version: AIRTABLE_PANEL_DISCOVERY_VERSION
  });
  if (!args.manifest) throw new Error('Missing --manifest');
  const manifest = readJsonFile(args.manifest);
  const targets = selectManifestTargets(manifest, { targetKeys: args.targetKeys });
  if (targets.length !== 1) throw new Error('This tool requires exactly one -TargetKey.');
  const target = targets[0];
  target.base_id = manifest.base_id;
  const baseUrl = args.baseUrl || `https://airtable.com/${manifest.base_id}`;

  await openBrowser(baseUrl);
  rl = readline.createInterface({ input, output });
  await rl.question('Airtable one-view sort-direction apply: log into Airtable, confirm the DCOIR base is open, then press Enter. Ctrl+C aborts before mutation gate. ');
  const typed = await rl.question(`About to change one existing sort direction only for ${target.table_name} / ${target.view_name}. Type ${REQUIRED_TOKEN} again to proceed: `);
  if (typed.trim() !== REQUIRED_TOKEN) throw new Error('Confirmation token mismatch. Aborting before mutation.');

  const result = await applyOneTarget(target);
  const reportPath = path.join(outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_apply_sort_direction_report.json`);
  writeJson(reportPath, result);
  const rollup = {
    timestamp_utc: nowIso(),
    tool_version: TOOL_VERSION,
    status: result.status,
    target_count: 1,
    mutation_attempted: Boolean(result.mutation_attempted),
    report_path: reportPath
  };
  writeJson(path.join(outputDir, 'apply_sort_direction_rollup.json'), rollup);
  log('Apply sort direction completed.', rollup);
  const ok = ['already_correct_noop', 'sort_direction_verified_after_refresh'].includes(result.status);
  await closeBrowser(ok);
  process.exit(ok ? 0 : 1);
} catch (error) {
  const failure = {
    timestamp_utc: nowIso(),
    tool_version: TOOL_VERSION,
    status: 'apply_sort_direction_failed',
    error: String(error && error.message ? error.message : error)
  };
  try {
    if (page) failure.snapshot = await captureDomEvidence(page, outputDir, 'apply_sort_direction_failure', args);
  } catch {}
  writeJson(path.join(outputDir, 'apply_sort_direction_failed.json'), failure);
  log('Apply sort direction failed.', { error: failure.error });
  await closeBrowser(false);
  process.exit(1);
} finally {
  if (rl) rl.close();
}
