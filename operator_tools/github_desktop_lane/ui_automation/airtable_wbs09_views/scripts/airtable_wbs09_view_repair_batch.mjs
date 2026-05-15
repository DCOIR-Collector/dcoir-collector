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
  openAirtablePanel,
  closeOpenAirtablePanel,
  reloadPageWithRetry,
  targetKeyOfReadbackTarget
} from '../../shared/dcoir_airtable_panel_readback.mjs';

const TOOL_VERSION = '2026-05-15.wbs09-view-repair-batch.1';
const REQUIRED_TOKEN = 'APPLY_WBS09_VIEW_REPAIR_BATCH';

function parseArgs(argv) {
  const parsed = {
    mode: 'dryrun',
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
    failOnSkipped: false,
    confirmToken: null
  };
  for (let i = 2; i < argv.length; i += 1) {
    const a = argv[i];
    const next = () => argv[++i];
    if (a === '--manifest') parsed.manifest = next();
    else if (a === '--output-dir') parsed.outputDir = next();
    else if (a === '--target-list-file') parsed.targetListFile = next();
    else if (a === '--mode') parsed.mode = String(next() || '').toLowerCase();
    else if (a === '--confirm-token') parsed.confirmToken = next();
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
    else if (a === '--fail-on-skipped') parsed.failOnSkipped = true;
    else throw new Error(`Unknown argument: ${a}`);
  }
  return parsed;
}

function normalize(value) {
  return String(value || '').replace(/[\u2192\u27f6\u2794]/g, ' -> ').replace(/\s+/g, ' ').trim();
}
function lower(value) { return normalize(value).toLowerCase(); }
function isDesc(direction) { return String(direction || '').toLowerCase() === 'desc'; }
function directionPatterns(direction) {
  return isDesc(direction)
    ? [/z\s*->\s*a/i, /9\s*->\s*1/i, /latest\s*->\s*earliest/i, /descending/i]
    : [/a\s*->\s*z/i, /1\s*->\s*9/i, /earliest\s*->\s*latest/i, /ascending/i];
}

function readTargetList(filePath) {
  const raw = fs.readFileSync(filePath, 'utf8').trim();
  if (!raw) return [];
  if (raw.startsWith('{')) {
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed.target_keys)) throw new Error('Target list JSON object must contain target_keys array.');
    return parsed.target_keys.map(String);
  }
  if (raw.startsWith('[')) {
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) throw new Error('Target list JSON must be an array.');
    return parsed.map(String);
  }
  return raw.split(/\r?\n/).map((line) => line.trim()).filter((line) => line && !line.startsWith('#'));
}

function assertTimeout(value, label) {
  if (!Number.isFinite(value) || value < 10000 || value > 300000) {
    throw new Error(`${label} must be between 10000 and 300000 milliseconds.`);
  }
}
function withTimeout(promise, timeoutMs, label) {
  let timer;
  const timeout = new Promise((_, reject) => {
    timer = setTimeout(() => reject(new Error(`${label} timed out after ${timeoutMs}ms.`)), timeoutMs);
  });
  return Promise.race([promise, timeout]).finally(() => clearTimeout(timer));
}

const args = parseArgs(process.argv);
if (!args.manifest) throw new Error('Missing --manifest');
if (!args.outputDir) throw new Error('Missing --output-dir');
if (!args.targetListFile) throw new Error('Missing --target-list-file');
if (!['dryrun', 'apply'].includes(args.mode)) throw new Error('--mode must be dryrun or apply');
if (args.mode === 'apply' && args.confirmToken !== REQUIRED_TOKEN) throw new Error(`Apply mode requires --confirm-token ${REQUIRED_TOKEN}`);
if (args.mode === 'dryrun' && args.confirmToken) throw new Error('DryRun mode must not include a confirmation token.');
assertTimeout(args.browserLaunchTimeoutMs, 'browserLaunchTimeoutMs');
assertTimeout(args.reloadTimeoutMs, 'reloadTimeoutMs');
assertTimeout(args.networkIdleTimeoutMs, 'networkIdleTimeoutMs');

ensureDir(args.outputDir);
const logPath = path.join(args.outputDir, 'view_repair_batch.log');
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
  log('Opening browser for WBS09 view repair batch.', { base_url: baseUrl, mode: args.mode, timeout_ms: args.browserLaunchTimeoutMs });
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
  await page.goto(baseUrl, { waitUntil: 'domcontentloaded', timeout: 30000 }).catch((error) => {
    log('Initial Airtable navigation warning; continuing to operator prompt.', { error: String(error?.message || error) });
  });
  await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
  await safeMousePark(page, 'after-open-base-url');
  log('Browser launch/navigation phase complete.', { url: page.url() });
}

async function waitForOperatorReady() {
  if (args.headless || args.noAirtableReadyPrompt) {
    log('Skipping Airtable-ready operator prompt.', { headless: !!args.headless, no_airtable_ready_prompt: !!args.noAirtableReadyPrompt });
    return;
  }
  if (!process.stdin.isTTY) throw new Error('Interactive stdin is required. Do not pipe this tool through Tee-Object; use Start-Transcript or direct execution.');
  rl = readline.createInterface({ input, output });
  await rl.question('WBS09 view repair batch: log into Airtable, confirm the DCOIR base is open, then press Enter. Ctrl+C aborts. ');
  if (args.mode === 'apply') {
    const typed = await rl.question(`Apply mode can modify saved Airtable view filters/sorts. Type ${REQUIRED_TOKEN} to proceed: `);
    if (typed.trim() !== REQUIRED_TOKEN) throw new Error('Confirmation token mismatch. Aborting before mutation.');
  }
}

async function closeBrowser(success) {
  if (!success && args.keepBrowserOpenOnFailure) {
    console.error('Failure detected. Browser will remain open for inspection. Press Enter in PowerShell after inspection.');
    if (rl) await rl.question('');
    return;
  }
  if (closeMode === 'persistent' && context) await context.close().catch(() => {});
  else if (browser) await browser.close().catch(() => {});
}

function summarizePanelRows(state) {
  return (state?.rows || []).map((row) => normalize(row.text || '')).filter(Boolean);
}

function filterRowsWithoutChrome(rows) {
  return rows.filter((text) => !/^in this view, show records$/i.test(text) && !/^add condition$/i.test(text) && !/^no filter conditions are applied/i.test(text));
}
function sortRowsWithoutChrome(rows) {
  return rows.filter((text) => !/^find a field$/i.test(text) && !/^add another sort$/i.test(text));
}

function expectedHuman(target) {
  return {
    filters: (target.expected_filters || []).map((f) => ({ field: f.field, operator: f.operator, value: f.value })),
    sorts: (target.expected_sorts || []).map((s) => ({ field: s.field, direction: s.direction }))
  };
}

function currentHuman(filterState, sortState) {
  return {
    filters: filterRowsWithoutChrome(summarizePanelRows(filterState)),
    sorts: sortRowsWithoutChrome(summarizePanelRows(sortState))
  };
}

function classFromComparison(comparison) {
  const details = comparison?.gap_details || [];
  const cats = new Set(details.map((d) => d.category).filter(Boolean));
  if ((comparison?.missing || []).some((m) => /panel extraction failed/i.test(m))) cats.add('panel_extraction_gap');
  return Array.from(cats).sort();
}

function simpleOperationPlan(target, comparison, filterState, sortState) {
  const categories = classFromComparison(comparison);
  const filters = target.expected_filters || [];
  const sorts = target.expected_sorts || [];
  const current = currentHuman(filterState, sortState);
  const operations = [];
  const unsupported = [];

  if (categories.includes('panel_extraction_gap')) unsupported.push('panel_extraction_gap_requires_targeted_readback');

  if (categories.includes('filter_gap')) {
    if (filters.length === 0) {
      unsupported.push('filter_gap_but_manifest_has_no_expected_filter');
    } else if (current.filters.length === 0) {
      operations.push({ type: 'replace_filters', reason: 'no_current_filter_rows', expected_filters: filters });
    } else {
      operations.push({ type: 'replace_filters', reason: 'current_filter_rows_differ', expected_filters: filters, current_filters: current.filters });
    }
  }

  if (categories.includes('sort_gap')) {
    if (sorts.length === 0) {
      unsupported.push('sort_gap_but_manifest_has_no_expected_sort');
    } else {
      operations.push({ type: 'replace_sorts', expected_sorts: sorts, current_sorts: current.sorts });
    }
  }

  const applySupported = unsupported.length === 0 && operations.every((op) => ['replace_filters', 'replace_sorts'].includes(op.type));
  return {
    categories,
    expected: expectedHuman(target),
    current,
    operations,
    unsupported,
    apply_supported: applySupported,
    requires_mutation: !comparison.ok
  };
}

async function captureLivePlan(target, phase) {
  const result = {
    timestamp_utc: nowIso(),
    tool_version: TOOL_VERSION,
    shared_panel_readback_version: AIRTABLE_PANEL_READBACK_VERSION,
    target_key: targetKeyOfReadbackTarget(target),
    target: { table_name: target.table_name, view_name: target.view_name, table_id: target.table_id },
    phase,
    status: 'started'
  };
  result.steps = [await selectAirtableTableAndView(page, target)];
  result.row_state = await captureAirtableGridRowState(page, args.outputDir, target, `${phase}_target_loaded`).catch((e) => ({ ok: false, row_state: 'unknown', error: String(e) }));
  result.before_filter = await captureAirtablePanelState(page, args.outputDir, target, 'filter', `${phase}_filter`, args);
  result.before_sort = await captureAirtablePanelState(page, args.outputDir, target, 'sort', `${phase}_sort`, args);
  result.comparison = compareAirtablePanelReadback({ target, before_filter: result.before_filter, after_filter: result.before_filter, before_sort: result.before_sort, after_sort: result.before_sort });
  result.repair_plan = simpleOperationPlan(target, result.comparison, result.before_filter, result.before_sort);
  result.status = result.comparison.ok ? 'already_correct_noop' : 'repair_plan_created';
  return result;
}

async function visibleControls() {
  return page.evaluate(() => {
    function norm(s) { return String(s || '').replace(/[\u2192\u27f6\u2794]/g, ' -> ').replace(/\s+/g, ' ').trim(); }
    function visible(el) {
      const style = window.getComputedStyle(el);
      const box = el.getBoundingClientRect();
      return style && style.visibility !== 'hidden' && style.display !== 'none' && box.width > 0 && box.height > 0;
    }
    return Array.from(document.querySelectorAll('button, [role="button"], [role="option"], [role="menuitem"], input, textarea, [contenteditable="true"], div, span'))
      .filter(visible)
      .map((el) => {
        const box = el.getBoundingClientRect();
        return {
          text: norm(el.innerText || el.textContent || ''),
          aria: norm(el.getAttribute('aria-label') || ''),
          placeholder: norm(el.getAttribute('placeholder') || ''),
          role: norm(el.getAttribute('role') || ''),
          tag: el.tagName.toLowerCase(),
          x: box.x, y: box.y, w: box.width, h: box.height, cx: box.x + box.width / 2, cy: box.y + box.height / 2
        };
      })
      .filter((item) => (item.text || item.aria || item.placeholder) && item.w > 0 && item.h > 0);
  });
}

async function clickFirstMatching(patterns, label, opts = {}) {
  const controls = await visibleControls();
  const rx = patterns.map((p) => p instanceof RegExp ? p : new RegExp(String(p), 'i'));
  const matches = controls.filter((c) => {
    const hay = `${c.text} ${c.aria} ${c.placeholder}`;
    if (opts.role && !String(c.role || '').match(opts.role)) return false;
    if (opts.maxWidth && c.w > opts.maxWidth) return false;
    if (opts.minY && c.y < opts.minY) return false;
    return rx.some((r) => r.test(hay));
  }).sort((a, b) => (a.y - b.y) || (a.x - b.x));
  if (matches.length < 1) throw new Error(`Could not find clickable control for ${label}`);
  const picked = matches[0];
  await page.mouse.click(picked.cx, picked.cy);
  await page.waitForTimeout(opts.waitMs || 600);
  return picked;
}

async function clickOptionByText(text, label) {
  const escaped = text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  try {
    return await clickFirstMatching([new RegExp(`(^|\\b)${escaped}(\\b|$)`, 'i')], label, { waitMs: 700 });
  } catch (error) {
    await page.keyboard.type(text, { delay: 15 });
    await page.waitForTimeout(500);
    await page.keyboard.press('Enter');
    await page.waitForTimeout(700);
    return { typed: text, via_keyboard: true };
  }
}

async function removePanelRows(kind) {
  const label = kind === 'filter' ? 'Remove item' : 'Remove sort';
  for (let i = 0; i < 20; i += 1) {
    const controls = await visibleControls();
    const remove = controls
      .filter((c) => new RegExp(label, 'i').test(`${c.text} ${c.aria}`))
      .sort((a, b) => b.y - a.y || b.x - a.x)[0];
    if (!remove) return i;
    await page.mouse.click(remove.cx, remove.cy);
    await page.waitForTimeout(500);
  }
  throw new Error(`Exceeded maximum ${kind} row removal attempts.`);
}

async function openFieldPickerFromPanel(kind) {
  if (kind === 'sort') {
    const controls = await visibleControls();
    const find = controls.find((c) => /find a field/i.test(`${c.text} ${c.aria} ${c.placeholder}`));
    if (find) { await page.mouse.click(find.cx, find.cy); await page.waitForTimeout(400); return find; }
    const add = controls.find((c) => /add another sort|pick another field to sort by/i.test(`${c.text} ${c.aria}`));
    if (add) { await page.mouse.click(add.cx, add.cy); await page.waitForTimeout(600); return add; }
  } else {
    await clickFirstMatching([/add condition/i], 'Add condition', { waitMs: 800 });
    const controls = await visibleControls();
    const field = controls.find((c) => /field|where/i.test(`${c.text} ${c.aria} ${c.placeholder}`) && c.w < 260);
    if (field) { await page.mouse.click(field.cx, field.cy); await page.waitForTimeout(500); return field; }
  }
  throw new Error(`Could not open ${kind} field picker.`);
}

async function setSortDirection(direction) {
  const patterns = directionPatterns(direction);
  const controls = await visibleControls();
  const currentDirectionButton = controls
    .filter((c) => /first\s*->\s*last|last\s*->\s*first|earliest\s*->\s*latest|latest\s*->\s*earliest|a\s*->\s*z|z\s*->\s*a|1\s*->\s*9|9\s*->\s*1/i.test(`${c.text} ${c.aria}`))
    .sort((a, b) => a.y - b.y || a.x - b.x)[0];
  if (!currentDirectionButton) throw new Error('Could not find sort direction control.');
  const hay = `${currentDirectionButton.text} ${currentDirectionButton.aria}`;
  if (patterns.some((rx) => rx.test(hay))) return { changed: false, already: true };
  await page.mouse.click(currentDirectionButton.cx, currentDirectionButton.cy);
  await page.waitForTimeout(600);
  const opts = await visibleControls();
  const option = opts.filter((c) => patterns.some((rx) => rx.test(`${c.text} ${c.aria}`))).sort((a, b) => a.y - b.y || a.x - b.x)[0];
  if (!option) throw new Error(`Could not find target sort direction option ${direction}.`);
  await page.mouse.click(option.cx, option.cy);
  await page.waitForTimeout(700);
  return { changed: true, option };
}

async function applySorts(expectedSorts) {
  await openAirtablePanel(page, 'sort');
  await page.waitForTimeout(700);
  const removed = await removePanelRows('sort');
  const actions = [{ action: 'remove_existing_sorts', count: removed }];
  for (const sort of expectedSorts || []) {
    await openFieldPickerFromPanel('sort');
    await clickOptionByText(sort.field, `sort field ${sort.field}`);
    await page.waitForTimeout(800);
    actions.push({ action: 'add_sort_field', field: sort.field });
    const direction = await setSortDirection(sort.direction);
    actions.push({ action: 'set_sort_direction', direction: sort.direction, detail: direction });
  }
  await closeOpenAirtablePanel(page).catch(() => {});
  return actions;
}

async function setFilterOperator(operator) {
  const op = String(operator || '').toLowerCase();
  const controls = await visibleControls();
  const operatorButton = controls
    .filter((c) => /is any of|is one of|is not empty|contains|on or before|is$|is checked|is unchecked|equals|empty/i.test(`${c.text} ${c.aria}`))
    .filter((c) => c.w < 260)
    .sort((a, b) => a.y - b.y || a.x - b.x)[0];
  if (operatorButton) {
    await page.mouse.click(operatorButton.cx, operatorButton.cy);
    await page.waitForTimeout(500);
  }
  let target = operator;
  if (op === 'is one of') target = 'is any of';
  if (op === '=') target = 'is';
  await clickOptionByText(target, `filter operator ${operator}`);
  return { operator, ui_operator: target };
}

async function setFilterValue(filter) {
  const op = String(filter.operator || '').toLowerCase();
  if (/not empty/.test(op)) return { skipped: true, reason: 'operator_has_no_value' };
  if (filter.value === true || filter.value === false) {
    return { skipped: true, reason: 'checkbox_operator_value_is_embedded' };
  }
  const values = Array.isArray(filter.value) ? filter.value : [filter.value];
  for (const value of values) {
    if (value === null || value === undefined || value === '') continue;
    await clickOptionByText(String(value), `filter value ${value}`);
    await page.waitForTimeout(400);
  }
  return { values: values.filter((v) => v !== null && v !== undefined) };
}

async function applyFilters(expectedFilters) {
  await openAirtablePanel(page, 'filter');
  await page.waitForTimeout(700);
  const removed = await removePanelRows('filter');
  const actions = [{ action: 'remove_existing_filters', count: removed }];
  for (const filter of expectedFilters || []) {
    await openFieldPickerFromPanel('filter');
    await clickOptionByText(filter.field, `filter field ${filter.field}`);
    await page.waitForTimeout(700);
    actions.push({ action: 'add_filter_field', field: filter.field });
    actions.push({ action: 'set_filter_operator', detail: await setFilterOperator(filter.operator) });
    actions.push({ action: 'set_filter_value', detail: await setFilterValue(filter) });
  }
  await closeOpenAirtablePanel(page).catch(() => {});
  return actions;
}

async function applyOperations(target, plan) {
  const actions = [];
  for (const op of plan.operations || []) {
    if (op.type === 'replace_filters') actions.push({ type: op.type, actions: await applyFilters(op.expected_filters) });
    else if (op.type === 'replace_sorts') actions.push({ type: op.type, actions: await applySorts(op.expected_sorts) });
    else throw new Error(`Unsupported operation type: ${op.type}`);
  }
  const reload = await reloadPageWithRetry(page, {
    maxAttempts: args.reloadAttempts,
    reloadTimeoutMs: args.reloadTimeoutMs,
    networkIdleTimeoutMs: args.networkIdleTimeoutMs,
    settleMs: args.reloadSettleMs,
    backoffMs: args.reloadBackoffMs,
    log
  });
  if (!reload.ok) throw new Error(`Reload failed after mutation: ${reload.error || 'unknown'}`);
  await selectAirtableTableAndView(page, target);
  return { actions, reload };
}

async function processOneTarget(target, index, total) {
  const targetKey = targetKeyOfReadbackTarget(target);
  log('Repair batch target starting.', { index, total, target_key: targetKey, mode: args.mode });
  const report = {
    timestamp_utc: nowIso(),
    tool_version: TOOL_VERSION,
    target_key: targetKey,
    target: { table_name: target.table_name, view_name: target.view_name, table_id: target.table_id },
    mode: args.mode,
    status: 'started'
  };
  try {
    report.preflight = await captureLivePlan(target, 'preflight');
    report.repair_plan = report.preflight.repair_plan;
    if (report.preflight.comparison.ok) {
      report.status = 'already_correct_noop';
    } else if (args.mode === 'dryrun') {
      report.status = report.repair_plan.apply_supported ? 'dry_run_apply_supported' : 'dry_run_apply_unsupported';
    } else if (!report.repair_plan.apply_supported) {
      report.status = 'skipped_apply_unsupported';
    } else {
      report.apply = await applyOperations(target, report.repair_plan);
      report.after_apply = await captureLivePlan(target, 'after_apply');
      report.status = report.after_apply.comparison.ok ? 'apply_verified_after_reload' : 'apply_gap_after_reload';
    }
  } catch (error) {
    report.status = args.mode === 'apply' ? 'apply_failed' : 'dry_run_failed';
    report.error = String(error && error.message ? error.message : error);
    try { report.failure_snapshot = await captureDomEvidence(page, args.outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_repair_failure`, args); } catch {}
  }
  report.completed_at_utc = nowIso();
  const fileName = `${safeName(target.table_name)}_${safeName(target.view_name)}_view_repair_batch_report.json`;
  const reportPath = path.join(args.outputDir, fileName);
  writeJson(reportPath, report);
  report.report_path = reportPath;
  log('Repair batch target completed.', { target_key: targetKey, status: report.status });
  return report;
}

function rollupReports(reports) {
  const counts = {};
  for (const r of reports) counts[r.status] = (counts[r.status] || 0) + 1;
  const failed = reports.filter((r) => /failed|gap_after_reload/.test(r.status));
  const skipped = reports.filter((r) => /unsupported/.test(r.status));
  const mutated = reports.filter((r) => r.status === 'apply_verified_after_reload');
  const drySupported = reports.filter((r) => r.status === 'dry_run_apply_supported');
  const dryUnsupported = reports.filter((r) => r.status === 'dry_run_apply_unsupported');
  return {
    timestamp_utc: nowIso(),
    tool_version: TOOL_VERSION,
    shared_panel_readback_version: AIRTABLE_PANEL_READBACK_VERSION,
    mode: args.mode,
    status: failed.length ? 'failed_or_incomplete' : (skipped.length && args.mode === 'apply' ? 'completed_with_skips' : 'completed'),
    target_count: reports.length,
    status_counts: counts,
    apply_verified_count: mutated.length,
    dry_run_apply_supported_count: drySupported.length,
    dry_run_apply_unsupported_count: dryUnsupported.length,
    skipped_count: skipped.length,
    failed_count: failed.length,
    skipped_targets: skipped.map((r) => ({ target_key: r.target_key, status: r.status, unsupported: r.repair_plan?.unsupported || [] })),
    failed_targets: failed.map((r) => ({ target_key: r.target_key, status: r.status, error: r.error || null })),
    reports: reports.map((r) => ({ target_key: r.target_key, status: r.status, report_path: r.report_path, apply_supported: !!r.repair_plan?.apply_supported, operations: r.repair_plan?.operations || [], unsupported: r.repair_plan?.unsupported || [] }))
  };
}

try {
  log('Starting DCOIR WBS09 view repair batch.', { version: TOOL_VERSION, mode: args.mode });
  const manifest = readJsonFile(args.manifest);
  const targetKeys = readTargetList(args.targetListFile);
  if (targetKeys.length < 1) throw new Error('Target list is empty.');
  const targets = selectManifestTargets(manifest, { targetKeys });
  if (targets.length !== targetKeys.length) throw new Error(`Selected ${targets.length} targets but target list had ${targetKeys.length}.`);
  for (const target of targets) target.base_id = manifest.base_id;
  writeJson(path.join(args.outputDir, 'selected_view_repair_batch_targets.json'), { timestamp_utc: nowIso(), target_count: targets.length, target_keys: targets.map(targetKeyOfReadbackTarget) });
  const baseUrl = args.baseUrl || `https://airtable.com/${manifest.base_id}`;

  await openBrowser(baseUrl);
  await waitForOperatorReady();

  const reports = [];
  for (let i = 0; i < targets.length; i += 1) {
    reports.push(await processOneTarget(targets[i], i + 1, targets.length));
  }
  const plan = {
    timestamp_utc: nowIso(),
    tool_version: TOOL_VERSION,
    mode: args.mode,
    target_count: reports.length,
    targets: reports.map((r) => ({ target_key: r.target_key, status: r.status, expected: r.repair_plan?.expected || null, current: r.repair_plan?.current || null, operations: r.repair_plan?.operations || [], apply_supported: !!r.repair_plan?.apply_supported, unsupported: r.repair_plan?.unsupported || [] }))
  };
  writeJson(path.join(args.outputDir, 'view_repair_batch_plan.json'), plan);
  const rollup = rollupReports(reports);
  writeJson(path.join(args.outputDir, 'view_repair_batch_rollup.json'), rollup);
  log('View repair batch completed.', rollup);
  const ok = rollup.failed_count === 0 && (!args.failOnSkipped || rollup.skipped_count === 0);
  await closeBrowser(ok);
  process.exit(ok ? 0 : 1);
} catch (error) {
  const failure = { timestamp_utc: nowIso(), tool_version: TOOL_VERSION, status: 'view_repair_batch_fatal_error', error: String(error && error.message ? error.message : error) };
  try { if (page) failure.snapshot = await captureDomEvidence(page, args.outputDir, 'view_repair_batch_fatal_error', args); } catch {}
  writeJson(path.join(args.outputDir, 'view_repair_batch_fatal_error.json'), failure);
  log('View repair batch fatal error.', { error: failure.error });
  await closeBrowser(false);
  process.exit(1);
} finally {
  if (rl) rl.close();
}
