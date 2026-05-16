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
  captureAirtableGridRowState,
  captureAirtablePanelState,
  compareAirtablePanelReadback,
  openAirtablePanel,
  closeOpenAirtablePanel,
  reloadPageWithRetry,
  targetKeyOfReadbackTarget
} from '../../shared/dcoir_airtable_panel_readback.mjs';

const TOOL_VERSION = '2026-05-16.wbs09-add-missing-sort-row.2.1-sort-only-verify';
const REQUIRED_TOKEN = 'APPLY_WBS09_ADD_MISSING_SORT_ROW_BATCH';

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
    ? [/z\s*->\s*a/i, /9\s*->\s*1/i, /latest\s*->\s*earliest/i, /last\s*->\s*first/i, /descending/i, /^desc$/i]
    : [/a\s*->\s*z/i, /1\s*->\s*9/i, /earliest\s*->\s*latest/i, /first\s*->\s*last/i, /ascending/i, /^asc$/i];
}
function textMatchesDirection(text, direction) {
  const value = normalize(text);
  return directionPatterns(direction).some((rx) => rx.test(value));
}
function sleep(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }

function loadTargetKeys(filePath) {
  const raw = fs.readFileSync(filePath, 'utf8');
  let parsed = null;
  try { parsed = JSON.parse(raw); } catch {}
  if (Array.isArray(parsed)) return parsed.map(String).filter(Boolean);
  if (parsed && Array.isArray(parsed.target_keys)) return parsed.target_keys.map(String).filter(Boolean);
  return raw.split(/\r?\n/).map((line) => line.trim()).filter((line) => line && !line.startsWith('#'));
}

const args = parseArgs(process.argv);
const downloads = process.env.DCOIR_DOWNLOADS_DIR;
if (!downloads || !downloads.trim()) {
  console.error('Missing required Local Configuration Registry variable: DCOIR_DOWNLOADS_DIR');
  process.exit(2);
}
if (!['dryrun', 'apply'].includes(args.mode)) {
  console.error('Mode must be dryrun or apply.');
  process.exit(2);
}
if (args.mode === 'apply' && args.confirmToken !== REQUIRED_TOKEN) {
  console.error(`Apply mode requires --confirm-token ${REQUIRED_TOKEN}`);
  process.exit(2);
}
if (args.mode === 'dryrun' && args.confirmToken) {
  console.error('DryRun mode must not receive an apply token.');
  process.exit(2);
}

const outputDir = args.outputDir || path.join(downloads, `dcoir_wbs09_add_missing_sort_row_${args.mode}_${new Date().toISOString().replace(/[:.]/g, '')}`);
ensureDir(outputDir);
const logPath = path.join(outputDir, 'add_missing_sort_row.log');
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
  log('Opening browser for add-missing-sort-row tool.', { base_url: baseUrl, mode: args.mode, timeout_ms: args.browserLaunchTimeoutMs });
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
  await page.goto(baseUrl, { waitUntil: 'domcontentloaded', timeout: args.browserLaunchTimeoutMs });
  await page.waitForLoadState('networkidle', { timeout: args.networkIdleTimeoutMs }).catch(() => {});
  await safeMousePark(page, 'after-open-base-url');
  log('Browser launch/navigation phase complete.', { url: page.url() });
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

function sortRowsFromState(sortState) {
  const rows = Array.isArray(sortState?.rows) ? sortState.rows : [];
  return rows.map((row, index) => normalize(row.text || Object.values(row.cells || {}).join(' ') || `row-${index + 1}`))
    .filter((text) => text && !/^add another sort$/i.test(text) && !/^copy from a view$/i.test(text) && !/^sort by$/i.test(text) && !/^find a field$/i.test(text));
}

function compareSortOnly(target, sortState) {
  const rows = sortRowsFromState(sortState);
  const expectedSorts = Array.isArray(target.expected_sorts) ? target.expected_sorts : [];
  const missing = [];

  if (!sortState || sortState?.panel_extraction?.ok === false) {
    missing.push('sort panel extraction failed');
  }

  if (expectedSorts.length !== 1) {
    missing.push(`unsupported expected sort count ${expectedSorts.length}`);
  } else {
    const expected = expectedSorts[0];
    const haystack = normalize(rows.join(' | '));
    const fieldOk = lower(haystack).includes(lower(expected.field));
    const directionOk = textMatchesDirection(haystack, expected.direction);

    if (!fieldOk) missing.push(`sort missing field ${expected.field}`);
    if (fieldOk && !directionOk) missing.push(`sort direction mismatch for ${expected.field}`);
  }

  return {
    ok: missing.length === 0,
    missing,
    sort_only: true,
    filter_scope: 'not_evaluated_by_add_missing_sort_row_operation_class'
  };
}

async function captureSortComparison(target, phase) {
  const sort = await captureAirtablePanelState(page, outputDir, target, 'sort', phase, args);
  const comparison = compareSortOnly(target, sort);
  return { sort, comparison, rows: sortRowsFromState(sort) };
}

async function findSortFieldSearchInput() {
  return await page.evaluate(() => {
    function visible(el) {
      const style = window.getComputedStyle(el);
      const box = el.getBoundingClientRect();
      return style && style.visibility !== 'hidden' && style.display !== 'none' && box.width > 0 && box.height > 0;
    }
    const nodes = Array.from(document.querySelectorAll('input, textarea, [contenteditable="true"], [role="textbox"]'));
    const candidates = nodes.map((el) => {
      const box = el.getBoundingClientRect();
      const text = (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim();
      const placeholder = el.getAttribute('placeholder') || '';
      const aria = el.getAttribute('aria-label') || '';
      return { el, text, placeholder, aria, x: box.x, y: box.y, w: box.width, h: box.height, cx: box.x + box.width / 2, cy: box.y + box.height / 2 };
    }).filter((c) => {
      if (!visible(c.el)) return false;
      const labels = `${c.text} ${c.placeholder} ${c.aria}`;
      const inVisibleSortPanelBand =
        c.x >= Math.max(520, window.innerWidth * 0.35) &&
        c.x <= window.innerWidth - 20 &&
        c.y >= 120 &&
        c.y <= 260 &&
        c.w >= 120 &&
        c.h >= 20;
      return inVisibleSortPanelBand && /find a field|search|field/i.test(labels);
    }).sort((a, b) => a.y - b.y || a.x - b.x);
    const c = candidates[0];
    if (!c) return null;
    return { x: Math.round(c.x), y: Math.round(c.y), w: Math.round(c.w), h: Math.round(c.h), cx: Math.round(c.cx), cy: Math.round(c.cy), placeholder: c.placeholder, aria: c.aria, text: c.text };
  });
}

async function clickSearchAndTypeField(field) {
  const search = await findSortFieldSearchInput();
  if (!search) return { ok: false, reason: 'sort_field_search_input_not_found' };
  await page.mouse.click(search.cx, search.cy);
  await sleep(250);
  await page.keyboard.press(process.platform === 'darwin' ? 'Meta+A' : 'Control+A').catch(() => {});
  await page.keyboard.type(String(field), { delay: 15 });
  await sleep(650);
  return { ok: true, search };
}

async function findSortFieldOption(field) {
  return await page.evaluate((field) => {
    const wanted = String(field || '').replace(/\s+/g, ' ').trim().toLowerCase();
    function normalize(s) { return String(s || '').replace(/\s+/g, ' ').trim(); }
    function visible(el) {
      const style = window.getComputedStyle(el);
      const box = el.getBoundingClientRect();
      return style && style.visibility !== 'hidden' && style.display !== 'none' && box.width > 0 && box.height > 0;
    }
    function clickableAncestor(el) {
      let cur = el;
      for (let i = 0; cur && i < 7; i += 1) {
        const tag = cur.tagName;
        const role = cur.getAttribute('role');
        if (tag === 'BUTTON' || tag === 'A' || role === 'button' || role === 'option' || cur.onclick) return cur;
        cur = cur.parentElement;
      }
      return el;
    }
    const nodes = Array.from(document.querySelectorAll('button, [role="button"], [role="option"], div, span, li'));
    const candidates = nodes.map((el) => {
      const box = el.getBoundingClientRect();
      const text = normalize(el.innerText || el.textContent || el.getAttribute('aria-label') || '');
      return { el, text, x: box.x, y: box.y, w: box.width, h: box.height, cx: box.x + box.width / 2, cy: box.y + box.height / 2 };
    }).filter((c) => {
      if (!visible(c.el)) return false;
      const text = normalize(c.text);
      if (!text || text.toLowerCase() !== wanted) return false;
      // Sort panel field-picker list is in the right-side Airtable toolbar panel.
      // Older probes assumed a left-side panel and missed the real field picker.
      if (c.x < Math.max(520, window.innerWidth * 0.35) || c.x > window.innerWidth - 20 || c.y < 115 || c.y > 900) return false;
      // Explicitly avoid Airtable's Copy from a view header control and other toolbar/header buttons.
      if (/copy from a view/i.test(text)) return false;
      if (c.w > 420 || c.h > 72) return false;
      return true;
    }).sort((a, b) => {
      const idealX = Math.max(890, window.innerWidth * 0.60);
      const aScore = Math.abs(a.x - idealX) + Math.abs(a.y - 160) / 4 + (a.w * a.h) / 20000;
      const bScore = Math.abs(b.x - idealX) + Math.abs(b.y - 160) / 4 + (b.w * b.h) / 20000;
      return aScore - bScore;
    });
    const c = candidates[0];
    if (!c) return null;
    const target = clickableAncestor(c.el);
    const box = target.getBoundingClientRect();
    return { text: c.text, x: Math.round(box.x), y: Math.round(box.y), w: Math.round(box.width), h: Math.round(box.height), cx: Math.round(box.x + box.width / 2), cy: Math.round(box.y + box.height / 2) };
  }, field);
}

async function findAndMaybeClickSortField(field, clickIt) {
  const search = await clickSearchAndTypeField(field);
  if (!search.ok) return { ok: false, ...search };
  const option = await findSortFieldOption(field);
  if (!option) return { ok: false, reason: 'expected_sort_field_option_not_found_after_search', search };
  if (clickIt) {
    await page.mouse.click(option.cx, option.cy);
    await sleep(900);
  }
  return { ok: true, search, option, clicked: Boolean(clickIt) };
}

async function findDirectionButton() {
  return await page.evaluate(() => {
    function normalize(s) { return String(s || '').replace(/[\u2192\u27f6\u2794]/g, ' -> ').replace(/\s+/g, ' ').trim(); }
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
    const directionRx = /a\s*->\s*z|z\s*->\s*a|1\s*->\s*9|9\s*->\s*1|earliest\s*->\s*latest|latest\s*->\s*earliest|first\s*->\s*last|last\s*->\s*first|ascending|descending|\basc\b|\bdesc\b/i;
    const nodes = Array.from(document.querySelectorAll('button, [role="button"], div, span'));
    const candidates = nodes.map((el) => {
      const box = el.getBoundingClientRect();
      const text = normalize(el.innerText || el.textContent || el.getAttribute('aria-label') || '');
      const role = el.getAttribute('role') || '';
      return { el, text, role, x: box.x, y: box.y, w: box.width, h: box.height, cx: box.x + box.width / 2, cy: box.y + box.height / 2, box };
    }).filter((c) => {
      if (!visible(c.el) || !topVisible(c.el, c.box)) return false;
      if (!directionRx.test(c.text)) return false;
      if (/copy from a view|remove sort|add another sort|sort by|find a field/i.test(c.text)) return false;
      // Direction controls live inside the same right-side sort panel after selecting a field.
      if (c.x < Math.max(520, window.innerWidth * 0.35) || c.x > window.innerWidth - 20 || c.y < 115 || c.y > 420 || c.w < 35 || c.w > 300 || c.h < 18 || c.h > 80) return false;
      return true;
    }).sort((a, b) => {
      const aRole = /button/i.test(a.role) ? 0 : 1;
      const bRole = /button/i.test(b.role) ? 0 : 1;
      return aRole - bRole || a.y - b.y || a.x - b.x || (a.w * a.h) - (b.w * b.h);
    });
    const c = candidates[0];
    if (!c) return null;
    return { text: c.text, role: c.role, x: Math.round(c.x), y: Math.round(c.y), w: Math.round(c.w), h: Math.round(c.h), cx: Math.round(c.cx), cy: Math.round(c.cy) };
  });
}

async function clickDirectionOption(direction) {
  return await page.evaluate((direction) => {
    function normalize(s) { return String(s || '').replace(/[\u2192\u27f6\u2794]/g, ' -> ').replace(/\s+/g, ' ').trim(); }
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
    const desc = String(direction || '').toLowerCase() === 'desc';
    const patterns = desc
      ? [/z\s*->\s*a/i, /9\s*->\s*1/i, /latest\s*->\s*earliest/i, /last\s*->\s*first/i, /descending/i, /^desc$/i]
      : [/a\s*->\s*z/i, /1\s*->\s*9/i, /earliest\s*->\s*latest/i, /first\s*->\s*last/i, /ascending/i, /^asc$/i];
    const nodes = Array.from(document.querySelectorAll('[role="option"], [role="menuitem"], button, [role="button"], div, span'));
    const candidates = nodes.map((el) => {
      const box = el.getBoundingClientRect();
      const text = normalize(el.innerText || el.textContent || el.getAttribute('aria-label') || '');
      const role = el.getAttribute('role') || '';
      return { el, text, role, x: box.x, y: box.y, w: box.width, h: box.height, box };
    }).filter((c) => {
      if (!visible(c.el) || !topVisible(c.el, c.box)) return false;
      if (!patterns.some((rx) => rx.test(c.text))) return false;
      if (/copy from a view|remove sort|add another sort|sort by|find a field/i.test(c.text)) return false;
      if (c.x < Math.max(500, window.innerWidth * 0.30) || c.x > window.innerWidth - 10 || c.y < 80 || c.y > 760 || c.w < 30 || c.h < 15) return false;
      return true;
    }).sort((a, b) => {
      const aRole = /^(option|menuitem)$/i.test(a.role) ? 0 : (/button/i.test(a.role) ? 1 : 2);
      const bRole = /^(option|menuitem)$/i.test(b.role) ? 0 : (/button/i.test(b.role) ? 1 : 2);
      return aRole - bRole || a.y - b.y || a.x - b.x || (a.w * a.h) - (b.w * b.h);
    });
    const c = candidates[0];
    if (!c) return null;
    c.el.click();
    return { text: c.text, role: c.role, x: Math.round(c.x), y: Math.round(c.y), w: Math.round(c.w), h: Math.round(c.h) };
  }, direction);
}

async function setDirectionIfNeeded(direction) {
  const button = await findDirectionButton();
  if (!button) {
    if (!isDesc(direction)) return { ok: true, assumed_default_ascending: true };
    return { ok: false, reason: 'direction_button_not_found_for_desc' };
  }
  if (textMatchesDirection(button.text, direction)) {
    return { ok: true, already_correct: true, button };
  }
  await page.mouse.click(button.cx, button.cy);
  await sleep(650);
  const option = await clickDirectionOption(direction);
  if (!option) return { ok: false, reason: 'target_direction_option_not_found', button };
  await sleep(900);
  return { ok: true, button, option };
}

async function applyOneTarget(target) {
  const targetKey = targetKeyOfReadbackTarget(target);
  const expectedSorts = Array.isArray(target.expected_sorts) ? target.expected_sorts : [];
  const result = {
    timestamp_utc: nowIso(),
    tool_version: TOOL_VERSION,
    shared_panel_readback_version: AIRTABLE_PANEL_READBACK_VERSION,
    mode: args.mode,
    target_key: targetKey,
    target,
    status: 'started',
    safety: {
      operation_class: 'add_missing_sort_row_only',
      disallowed: ['copy_from_view', 'filter_repair', 'replace_existing_sort_field', 'delete_sort_rows', 'create_view', 'delete_view', 'rename_view'],
      panel_probe_fix: 'v2 uses right-side Airtable sort-panel bounds and explicitly avoids Copy from a view',
      mutation_attempted: false
    },
    steps: []
  };

  if (expectedSorts.length !== 1) {
    result.status = 'skipped_unsupported_expected_sort_count';
    result.unsupported = [`expected_sort_count_${expectedSorts.length}`];
    return result;
  }
  const expected = expectedSorts[0];
  result.expected_sort = expected;
  log('Add-missing-sort-row target starting.', { target_key: targetKey, mode: args.mode, expected_sort: expected });
  result.steps.push(await selectAirtableTableAndView(page, target));
  result.grid_row_state = await captureAirtableGridRowState(page, outputDir, target, 'before_apply_or_dryrun', args).catch((error) => ({ state: 'unknown', error: String(error?.message || error) }));
  result.before = await captureSortComparison(target, 'before_add_missing_sort_row');
  result.snapshots = [await captureDomEvidence(page, outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_${args.mode}_before_sort_state`, args)];

  if (result.before.comparison.ok) {
    result.status = 'already_correct_noop';
    result.completed_at_utc = nowIso();
    return result;
  }
  if (result.before.rows.some((row) => lower(row).includes(lower(expected.field)) && /->|ascending|descending/i.test(row))) {
    result.status = 'skipped_existing_sort_row_present';
    result.unsupported = ['existing_sort_row_present_use_different_operation_class'];
    result.completed_at_utc = nowIso();
    return result;
  }

  const opened = await openAirtablePanel(page, 'sort');
  result.steps.push({ action: 'open_sort_panel_for_field_picker', ...opened });
  await sleep(700);
  result.snapshots.push(await captureDomEvidence(page, outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_${args.mode}_sort_field_picker`, args));

  const fieldProbe = await findAndMaybeClickSortField(expected.field, args.mode === 'apply');
  result.steps.push({ action: args.mode === 'apply' ? 'select_sort_field' : 'probe_sort_field', field: expected.field, ...fieldProbe });
  if (!fieldProbe.ok) {
    result.status = 'skipped_expected_field_not_reachable';
    result.unsupported = [fieldProbe.reason || 'expected_field_not_reachable'];
    result.completed_at_utc = nowIso();
    await closeOpenAirtablePanel(page);
    return result;
  }

  if (args.mode === 'dryrun') {
    result.status = 'dry_run_supported_add_missing_sort_row';
    result.mutation_attempted = false;
    result.completed_at_utc = nowIso();
    await page.keyboard.press('Escape').catch(() => {});
    await closeOpenAirtablePanel(page).catch(() => {});
    return result;
  }

  result.safety.mutation_attempted = true;
  result.mutation_attempted = true;
  result.direction_step = await setDirectionIfNeeded(expected.direction);
  result.steps.push({ action: 'set_sort_direction_if_needed', direction: expected.direction, ...result.direction_step });
  if (!result.direction_step.ok) {
    result.status = 'apply_failed_direction_control';
    result.error = result.direction_step.reason || 'direction_control_failed_after_field_selection';
    result.completed_at_utc = nowIso();
    return result;
  }

  result.after_click = await captureSortComparison(target, 'after_add_sort_row_click');
  result.snapshots.push(await captureDomEvidence(page, outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_${args.mode}_after_add_sort_row`, args));
  if (!result.after_click.comparison.ok) {
    result.status = 'apply_gap_after_click';
    result.error = JSON.stringify(result.after_click.comparison.missing || []);
    result.completed_at_utc = nowIso();
    return result;
  }

  result.reload = await reloadPageWithRetry(page, {
    maxAttempts: args.reloadAttempts,
    reloadTimeoutMs: args.reloadTimeoutMs,
    networkIdleTimeoutMs: args.networkIdleTimeoutMs,
    backoffMs: args.reloadBackoffMs,
    settleMs: args.reloadSettleMs,
    log
  });
  result.after_reload_select = await selectAirtableTableAndView(page, target);
  result.after_reload = await captureSortComparison(target, 'after_add_sort_row_reload');
  result.status = result.after_reload.comparison.ok ? 'apply_verified_after_reload' : 'apply_gap_after_reload';
  if (result.status !== 'apply_verified_after_reload') result.error = JSON.stringify(result.after_reload.comparison.missing || []);
  result.completed_at_utc = nowIso();
  return result;
}

try {
  log('Starting DCOIR WBS09 add-missing-sort-row operation-class tool.', {
    version: TOOL_VERSION,
    mode: args.mode,
    shared_panel_readback_version: AIRTABLE_PANEL_READBACK_VERSION
  });
  if (!args.manifest) throw new Error('Missing --manifest');
  if (!args.targetListFile) throw new Error('Missing --target-list-file');
  const manifest = readJsonFile(args.manifest);
  const targetKeys = loadTargetKeys(args.targetListFile);
  const targets = selectManifestTargets(manifest, { targetKeys });
  targets.forEach((target) => { target.base_id = manifest.base_id; });
  const baseUrl = args.baseUrl || `https://airtable.com/${manifest.base_id}`;

  await openBrowser(baseUrl);
  rl = readline.createInterface({ input, output });
  if (!args.noAirtableReadyPrompt) {
    await rl.question(`Airtable WBS09 add-missing-sort-row ${args.mode}: log into Airtable, confirm the DCOIR base is open, then press Enter. Ctrl+C aborts before mutation gate. `);
  }
  if (args.mode === 'apply') {
    const typed = await rl.question(`Apply mode can add saved Airtable sort rows. Type ${REQUIRED_TOKEN} to proceed: `);
    if (typed.trim() !== REQUIRED_TOKEN) throw new Error('Confirmation token mismatch. Aborting before mutation.');
  }

  const reports = [];
  for (let i = 0; i < targets.length; i += 1) {
    const target = targets[i];
    const targetKey = targetKeyOfReadbackTarget(target);
    try {
      log('Add-missing-sort-row batch target starting.', { index: i + 1, total: targets.length, target_key: targetKey, mode: args.mode });
      const report = await applyOneTarget(target);
      const reportPath = path.join(outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_add_missing_sort_row_report.json`);
      writeJson(reportPath, report);
      reports.push({ target_key: targetKey, status: report.status, report_path: reportPath, mutation_attempted: Boolean(report.mutation_attempted), unsupported: report.unsupported || [], error: report.error || null });
      log('Add-missing-sort-row batch target completed.', { target_key: targetKey, status: report.status });
    } catch (error) {
      const failure = { timestamp_utc: nowIso(), tool_version: TOOL_VERSION, mode: args.mode, target_key: targetKey, status: 'failed', error: String(error?.message || error), mutation_attempted: false };
      try { failure.snapshot = await captureDomEvidence(page, outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_${args.mode}_failure`, args); } catch {}
      const reportPath = path.join(outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_add_missing_sort_row_failed.json`);
      writeJson(reportPath, failure);
      reports.push({ target_key: targetKey, status: 'failed', report_path: reportPath, mutation_attempted: false, unsupported: [], error: failure.error });
      log('Add-missing-sort-row batch target failed.', { target_key: targetKey, error: failure.error });
      if (args.mode === 'apply') break;
    }
  }

  const statusCounts = reports.reduce((acc, item) => { acc[item.status] = (acc[item.status] || 0) + 1; return acc; }, {});
  const skipped = reports.filter((item) => /^skipped|^dry_run_unsupported/.test(item.status));
  const failed = reports.filter((item) => item.status === 'failed' || item.status.startsWith('apply_failed') || item.status.startsWith('apply_gap'));
  const rollup = {
    timestamp_utc: nowIso(),
    tool_version: TOOL_VERSION,
    shared_panel_readback_version: AIRTABLE_PANEL_READBACK_VERSION,
    mode: args.mode,
    status: failed.length > 0 || (args.failOnSkipped && skipped.length > 0) ? 'failed_or_incomplete' : 'completed',
    target_count: reports.length,
    status_counts: statusCounts,
    dry_run_supported_count: reports.filter((r) => r.status === 'dry_run_supported_add_missing_sort_row').length,
    apply_verified_count: reports.filter((r) => r.status === 'apply_verified_after_reload').length,
    already_correct_count: reports.filter((r) => r.status === 'already_correct_noop').length,
    skipped_count: skipped.length,
    failed_count: failed.length,
    skipped_targets: skipped,
    failed_targets: failed,
    reports
  };
  writeJson(path.join(outputDir, 'add_missing_sort_row_rollup.json'), rollup);
  log('Add-missing-sort-row operation-class tool completed.', rollup);
  const success = rollup.status === 'completed';
  await closeBrowser(success);
  process.exit(success ? 0 : 1);
} catch (error) {
  const failure = { timestamp_utc: nowIso(), tool_version: TOOL_VERSION, mode: args.mode, status: 'fatal_error', error: String(error?.message || error) };
  try { if (page) failure.snapshot = await captureDomEvidence(page, outputDir, `${args.mode}_fatal_error`, args); } catch {}
  writeJson(path.join(outputDir, 'add_missing_sort_row_fatal_error.json'), failure);
  log('Add-missing-sort-row operation-class tool fatal error.', { error: failure.error });
  await closeBrowser(false);
  process.exit(1);
} finally {
  if (rl) rl.close();
}
