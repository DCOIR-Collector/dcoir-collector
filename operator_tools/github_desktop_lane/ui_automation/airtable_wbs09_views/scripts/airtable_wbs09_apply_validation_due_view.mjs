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
  compareAirtablePanelReadback,
  openAirtablePanel,
  closeOpenAirtablePanel,
  extractOpenAirtablePanel
} from '../../shared/dcoir_airtable_panel_readback.mjs';
import {
  AIRTABLE_PANEL_DISCOVERY_VERSION,
  buildAirtableViewChangePlan,
  captureAirtablePanelDiscovery
} from '../../shared/dcoir_airtable_panel_discovery.mjs';
import {
  AIRTABLE_PANEL_ACTIONS_VERSION,
  ensureSingleRelativeDateFilter
} from '../../shared/dcoir_airtable_panel_actions.mjs';

const TOOL_VERSION = '2026-05-10.wbs09-apply-validation-due-view.4';
const REQUIRED_TOKEN = 'APPLY_WBS09_VALIDATION_DUE_VIEW';
const SUPPORTED_TARGET_KEY = 'Operator Tools Registry::WBS09 - Validation Due';

function parseArgs(argv) {
  const parsed = {
    enableScreenshots: false,
    headless: false,
    useChromeChannel: false,
    userDataDir: null,
    connectCdpUrl: null,
    keepBrowserOpenOnFailure: false,
    targetKeys: [],
    confirmToken: null
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
    else throw new Error(`Unknown argument: ${a}`);
  }
  return parsed;
}

function normalizeText(value) {
  return String(value || '').replace(/[\u2192\u27f6\u2794]/g, ' -> ').replace(/\s+/g, ' ').trim();
}
function lowerText(value) { return normalizeText(value).toLowerCase(); }
function regexEscape(value) { return String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }
function exactTextPattern(value) { return new RegExp(`^${regexEscape(normalizeText(value))}$`, 'i'); }

function assertSupportedTarget(target) {
  const key = `${norm(target.table_name)}::${norm(target.view_name)}`;
  if (key !== SUPPORTED_TARGET_KEY) {
    throw new Error(`Unsupported target for this narrow mutation helper: ${key}. Expected ${SUPPORTED_TARGET_KEY}.`);
  }
  if (!Array.isArray(target.expected_filters) || target.expected_filters.length !== 1) throw new Error('Expected exactly one filter in target contract.');
  if (!Array.isArray(target.expected_sorts) || target.expected_sorts.length !== 1) throw new Error('Expected exactly one sort in target contract.');
  const filter = target.expected_filters[0];
  const sort = target.expected_sorts[0];
  const value = Array.isArray(filter.value) ? filter.value.join(',') : String(filter.value || '');
  if (filter.field !== 'review_after' || filter.operator !== 'on or before' || value !== 'today') {
    throw new Error(`Unsupported filter contract: ${JSON.stringify(filter)}. Only review_after on or before today is supported.`);
  }
  if (sort.field !== 'review_after' || String(sort.direction || '').toLowerCase() !== 'asc') {
    throw new Error(`Unsupported sort contract: ${JSON.stringify(sort)}. Only review_after asc is supported.`);
  }
}

function relevantFilterRows(state) {
  return (Array.isArray(state?.rows) ? state.rows : []).filter((row) => {
    const text = lowerText(`${row.text || ''} ${Object.values(row.cells || {}).join(' ')}`);
    if (!text) return false;
    if (/no filter conditions are applied|add condition|learn more about filtering/.test(text)) return false;
    return /where|review_after| is |before|after|today/.test(text);
  });
}

function relevantSortRows(state) {
  return (Array.isArray(state?.rows) ? state.rows : []).filter((row) => {
    const text = lowerText(`${row.text || ''} ${Object.values(row.cells || {}).join(' ')}`);
    if (!text) return false;
    if (/add another sort|find a field|copy from another view|sort by/.test(text) && !/review_after/.test(text)) return false;
    return /review_after/.test(text) && /earliest\s*->\s*latest|latest\s*->\s*earliest|ascending|descending|a\s*->\s*z|z\s*->\s*a|1\s*->\s*9|9\s*->\s*1/.test(text);
  });
}

function sortDirectionObservedForField(rows, expectedSort) {
  const field = lowerText(expectedSort?.field || '');
  if (!field) return false;
  const wanted = String(expectedSort?.direction || '').toLowerCase() === 'desc' ? 'desc' : 'asc';
  for (const row of rows || []) {
    const text = lowerText(`${row.text || ''} ${Object.values(row.cells || {}).join(' ')}`);
    if (!text.includes(field)) continue;
    const hasAsc = /a\s*->\s*z|1\s*->\s*9|earliest\s*->\s*latest|ascending/.test(text);
    const hasDesc = /z\s*->\s*a|9\s*->\s*1|latest\s*->\s*earliest|descending/.test(text);
    if (wanted === 'desc' && hasDesc) return true;
    if (wanted === 'asc' && hasAsc) return true;
  }
  return false;
}

function stripReadbackPhasePrefix(message) {
  return String(message || '')
    .replace(/^(before_refresh|after_refresh|before_apply|after_apply|after_click|after_filter_click):\s*/i, '')
    .trim();
}

function expectedReviewAfterTodayFilter(plan) {
  const filters = plan?.expected?.filters || plan?.target?.expected_filters || [];
  return Array.isArray(filters) && filters.length === 1
    && String(filters[0]?.field || '') === 'review_after'
    && String(filters[0]?.operator || '').toLowerCase() === 'on or before'
    && String(filters[0]?.value || '').toLowerCase() === 'today';
}

function expectedReviewAfterAscendingSort(plan) {
  const sorts = plan?.expected?.sorts || plan?.target?.expected_sorts || [];
  return Array.isArray(sorts) && sorts.length === 1
    && String(sorts[0]?.field || '') === 'review_after'
    && String(sorts[0]?.direction || '').toLowerCase() === 'asc';
}

function collectPlanMissing(plan, before) {
  const values = [];
  for (const v of plan?.comparison?.missing_unique || []) values.push(v);
  for (const v of plan?.comparison?.missing_raw || []) values.push(v);
  for (const v of before?.comparison?.missing || []) values.push(v);
  return Array.from(new Set(values.map(stripReadbackPhasePrefix).filter(Boolean)));
}

function summarizePlanSafety(plan, before) {
  const filterRows = relevantFilterRows(before.filter);
  const sortRows = relevantSortRows(before.sort);
  const planned = plan?.planned_actions || {};
  const originalFilterAction = planned.filter_action || null;
  const originalSortAction = planned.sort_action || null;
  const missing = collectPlanMissing(plan, before);
  const filterMissing = missing.some((message) => /filter row not observed/i.test(message) || (/\bfilter\b/i.test(message) && /review_after/i.test(message)));
  const sortMissing = missing.some((message) => /sort row not observed|sort panel extraction failed/i.test(message) || (/\bsort\b/i.test(message) && /review_after/i.test(message)));

  let filterAction = originalFilterAction;
  let sortAction = originalSortAction;

  // The generic planner cannot always distinguish an empty filter panel from an unsafe
  // replace/normalize case. For this purpose-specific helper, the allowed filter
  // mutations are deliberately narrow: add a missing first review_after/today row,
  // or normalize one existing review_after row that is currently exact-date/unset.
  if (filterRows.length === 0 && expectedReviewAfterTodayFilter(plan) && filterMissing && originalFilterAction === 'replace_or_normalize_filters') {
    filterAction = 'add_or_build_filters';
  }
  if (filterRows.length === 1 && expectedReviewAfterTodayFilter(plan) && filterMissing && originalFilterAction === 'replace_or_normalize_filters') {
    const onlyFilterText = lowerText(filterRows[0]?.text || '');
    if (/review_after/.test(onlyFilterText) && !(/on or before/.test(onlyFilterText) && /today/.test(onlyFilterText))) {
      filterAction = 'normalize_single_relative_date_filter';
    }
  }

  // Treat an empty/failed sort panel readback as the safe add-first-sort case only for
  // the exact supported review_after ascending contract.
  if (sortRows.length === 0 && expectedReviewAfterAscendingSort(plan) && sortMissing && originalSortAction === 'replace_or_normalize_sorts') {
    sortAction = 'add_or_build_sorts';
  }

  const filterAllowed = filterAction === 'noop'
    || (filterAction === 'add_or_build_filters' && filterRows.length === 0)
    || (filterAction === 'normalize_single_relative_date_filter' && filterRows.length === 1);
  const sortAllowed = sortAction === 'noop' || (sortAction === 'add_or_build_sorts' && sortRows.length === 0);
  return {
    original_filter_action: originalFilterAction,
    original_sort_action: originalSortAction,
    filter_action: filterAction,
    sort_action: sortAction,
    filter_rows_observed: filterRows.length,
    sort_rows_observed: sortRows.length,
    missing,
    filter_missing: filterMissing,
    sort_missing: sortMissing,
    filter_allowed: filterAllowed,
    sort_allowed: sortAllowed,
    allowed: filterAllowed && sortAllowed,
    hard_stop_reason: filterAllowed && sortAllowed ? null : 'This helper only adds missing first filter/sort rows or no-ops when already correct; it will not replace/delete/normalize existing rows.'
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

const outputDir = args.outputDir || path.join(downloads, `dcoir_wbs09_apply_validation_due_view_${new Date().toISOString().replace(/[:.]/g, '')}`);
ensureDir(outputDir);
const logPath = path.join(outputDir, 'apply_validation_due_view.log');
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

async function verifyTarget(target, phase) {
  const filter = await captureAirtablePanelState(page, outputDir, target, 'filter', phase, args);
  const sort = await captureAirtablePanelState(page, outputDir, target, 'sort', phase, args);
  const comparison = compareAirtablePanelReadback({ target, before_filter: filter, after_filter: filter, before_sort: sort, after_sort: sort });
  return { filter, sort, comparison };
}

async function clickVisibleText(pattern, label, bounds = {}) {
  const source = pattern instanceof RegExp ? pattern.source : String(pattern);
  const flags = pattern instanceof RegExp ? pattern.flags : 'i';
  const picked = await page.evaluate(({ source, flags, label, bounds }) => {
    const re = new RegExp(source, flags.includes('i') ? 'i' : undefined);
    const normalize = (s) => String(s || '').replace(/[\u2192\u27f6\u2794]/g, ' -> ').replace(/\s+/g, ' ').trim();
    function visible(el) {
      const style = window.getComputedStyle(el);
      const box = el.getBoundingClientRect();
      return style && style.visibility !== 'hidden' && style.display !== 'none' && box.width > 0 && box.height > 0;
    }
    function clickableAncestor(el) {
      let cur = el;
      for (let i = 0; cur && i < 8; i += 1) {
        const tag = cur.tagName;
        const role = cur.getAttribute('role');
        if (tag === 'BUTTON' || tag === 'A' || role === 'button' || role === 'option' || role === 'menuitem' || cur.onclick) return cur;
        cur = cur.parentElement;
      }
      return el;
    }
    const xMin = Number(bounds.xMin ?? 250);
    const xMax = Number(bounds.xMax ?? window.innerWidth);
    const yMin = Number(bounds.yMin ?? 90);
    const yMax = Number(bounds.yMax ?? window.innerHeight);
    const nodes = Array.from(document.querySelectorAll('[role="option"], [role="menuitem"], button, [role="button"], div, span, a, input'));
    const candidates = nodes.map((el) => {
      const box = el.getBoundingClientRect();
      const text = normalize(el.innerText || el.textContent || el.getAttribute('aria-label') || el.getAttribute('placeholder') || el.value || '');
      const role = el.getAttribute('role') || '';
      return { el, text, role, x: box.x, y: box.y, w: box.width, h: box.height, area: box.width * box.height };
    }).filter((c) => {
      if (!visible(c.el)) return false;
      if (!c.text || c.text.length > 160) return false;
      if (c.x < xMin || c.x > xMax || c.y < yMin || c.y > yMax) return false;
      if (c.w < 8 || c.h < 8 || c.w > 800 || c.h > 100) return false;
      return re.test(c.text);
    }).sort((a, b) => {
      const ar = /^(option|menuitem|button)$/i.test(a.role) ? 0 : 1;
      const br = /^(option|menuitem|button)$/i.test(b.role) ? 0 : 1;
      return ar - br || a.area - b.area || a.y - b.y || a.x - b.x;
    });
    const c = candidates[0];
    if (!c) return null;
    const target = clickableAncestor(c.el);
    const box = target.getBoundingClientRect();
    target.click();
    return { selector: `visible-text:${label}`, text: c.text, role: c.role, x: Math.round(box.x), y: Math.round(box.y), w: Math.round(box.width), h: Math.round(box.height), cx: Math.round(box.x + box.width / 2), cy: Math.round(box.y + box.height / 2) };
  }, { source, flags, label, bounds });
  return picked ? { ok: true, ...picked } : { ok: false, selector: `visible-text:${label}` };
}

async function clickAt(point, label) {
  await page.mouse.click(Math.round(point.x), Math.round(point.y));
  return { ok: true, selector: `coordinate:${label}`, x: Math.round(point.x), y: Math.round(point.y) };
}

async function keyboardSelectAt(point, value, label) {
  const opened = await clickAt(point, `${label}-open`);
  await page.waitForTimeout(450);
  await page.keyboard.type(String(value), { delay: 15 });
  await page.waitForTimeout(550);
  await page.keyboard.press('Enter');
  await page.waitForTimeout(900);
  return { ok: true, selector: `${opened.selector}+keyboard-select`, value };
}

async function clickOpenOptionExact(value, label, bounds = {}) {
  const exact = exactTextPattern(value);
  let clicked = await clickVisibleText(exact, label, bounds);
  if (clicked.ok) return clicked;
  await page.keyboard.type(String(value), { delay: 15 });
  await page.waitForTimeout(500);
  clicked = await clickVisibleText(exact, `${label}-after-typeahead`, bounds);
  if (clicked.ok) return clicked;
  await page.keyboard.press('Enter').catch(() => {});
  await page.waitForTimeout(700);
  return { ok: true, selector: `keyboard-typeahead-enter:${label}`, value };
}

async function openPanelAndExtract(kind) {
  const opened = await openAirtablePanel(page, kind);
  await page.waitForTimeout(500);
  const extracted = await extractOpenAirtablePanel(page, kind);
  return { opened, extracted };
}

function pointFromPanel(panel, relX, fallbackY) {
  if (!panel) return { x: relX, y: fallbackY };
  return { x: panel.x + relX, y: fallbackY ?? panel.y + 138 };
}

function rowYFromExtraction(extracted, fallback) {
  const rows = Array.isArray(extracted?.rows) ? extracted.rows : [];
  const row = rows.find((candidate) => /where|review_after|is on or before|today/i.test(String(candidate.text || '')) && !/add condition/i.test(String(candidate.text || '')));
  return Number(row?.y || fallback || 268);
}

async function addReviewAfterFilter(target, result) {
  const expectedFilter = target.expected_filters[0];
  const opened = await openPanelAndExtract('filter');
  result.steps.push({ action: 'open_filter_panel_for_mutation', opened: opened.opened, panel_extraction: { ok: opened.extracted.ok, reason: opened.extracted.reason || null, panel: opened.extracted.panel || null } });

  const beforeRows = relevantFilterRows({ rows: opened.extracted.rows || [], panel_extraction: { ok: opened.extracted.ok } });
  if (beforeRows.length > 0) {
    throw new Error('Filter mutation refused: existing filter-like rows are present. This helper only adds a missing first filter row.');
  }

  const add = await clickVisibleText(/^Add condition$/i, 'filter-add-condition', { xMin: 450, xMax: 1120, yMin: 160, yMax: 420 });
  result.steps.push({ action: 'click_add_filter_condition', ...add });
  if (!add.ok) throw new Error('Could not click Add condition in filter panel.');
  await page.waitForTimeout(900);
  result.snapshots.push(await captureDomEvidence(page, outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_filter_condition_added`, args));

  const afterAdd = await extractOpenAirtablePanel(page, 'filter');
  const panel = afterAdd.panel || opened.extracted.panel || { x: 521, y: 129 };
  const rowY = rowYFromExtraction(afterAdd, (panel.y || 129) + 138);
  result.steps.push({ action: 'filter_after_add_extraction', ok: afterAdd.ok, reason: afterAdd.reason || null, panel: afterAdd.panel || null, row_y: rowY });

  const fieldPoint = pointFromPanel(panel, 151, rowY);
  const field = await keyboardSelectAt(fieldPoint, expectedFilter.field, 'filter-field-review_after');
  result.steps.push({ action: 'set_filter_field', field: expectedFilter.field, ...field });

  const operatorPoint = pointFromPanel(panel, 276, rowY);
  const operator = await keyboardSelectAt(operatorPoint, 'is on or before', 'filter-operator-is-on-or-before');
  result.steps.push({ action: 'set_filter_operator', operator: 'is on or before', ...operator });

  await page.waitForTimeout(700);
  const maybeDefault = await extractOpenAirtablePanel(page, 'filter');
  const maybeState = { panel_extraction: { ok: maybeDefault.ok }, rows: maybeDefault.rows || [] };
  const alreadyToday = relevantFilterRows(maybeState).some((row) => /review_after/i.test(row.text || '') && /on or before/i.test(row.text || '') && /today/i.test(row.text || ''));
  result.steps.push({ action: 'relative_date_value_default_probe', already_today: alreadyToday });
  if (!alreadyToday) {
    const valuePanel = maybeDefault.panel || panel;
    const valueY = rowYFromExtraction(maybeDefault, rowY);
    const valuePoint = pointFromPanel(valuePanel, 443, valueY);
    const openValue = await clickAt(valuePoint, 'filter-relative-date-value-open');
    await page.waitForTimeout(500);
    const today = await clickOpenOptionExact('today', 'filter-relative-date-today-option', { xMin: Math.max(250, valuePoint.x - 120), xMax: Math.min(1450, valuePoint.x + 550), yMin: Math.max(90, valuePoint.y - 60), yMax: Math.min(900, valuePoint.y + 540) });
    result.steps.push({ action: 'set_filter_relative_date_value', value: 'today', open: openValue, option: today });
  }

  await page.waitForTimeout(1000);
  result.snapshots.push(await captureDomEvidence(page, outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_filter_configured`, args));
  await closeOpenAirtablePanel(page);
}

async function addReviewAfterSort(target, result) {
  const expectedSort = target.expected_sorts[0];
  const opened = await openPanelAndExtract('sort');
  result.steps.push({ action: 'open_sort_panel_for_mutation', opened: opened.opened, panel_extraction: { ok: opened.extracted.ok, reason: opened.extracted.reason || null, panel: opened.extracted.panel || null } });

  const existingSortRows = relevantSortRows({ rows: opened.extracted.rows || [], panel_extraction: { ok: opened.extracted.ok } });
  if (existingSortRows.length > 0) {
    if (sortDirectionObservedForField(existingSortRows, expectedSort)) {
      result.steps.push({ action: 'sort_already_present', ok: true, rows: existingSortRows.map((row) => row.text) });
      await closeOpenAirtablePanel(page);
      return;
    }
    throw new Error('Sort mutation refused: existing sort-like rows are present but not the expected review_after ascending row. This helper will not replace/normalize sorts.');
  }

  let fieldClick = await clickVisibleText(exactTextPattern(expectedSort.field), 'sort-field-review_after-direct', { xMin: 760, xMax: 1260, yMin: 130, yMax: 820 });
  if (!fieldClick.ok) {
    const panel = opened.extracted.panel || { x: 891, y: 130 };
    const searchPoint = { x: panel.x + 28, y: panel.y + 64 };
    await clickAt(searchPoint, 'sort-field-search-open');
    await page.waitForTimeout(250);
    await page.keyboard.type(expectedSort.field, { delay: 15 });
    await page.waitForTimeout(700);
    fieldClick = await clickVisibleText(exactTextPattern(expectedSort.field), 'sort-field-review_after-after-search', { xMin: 760, xMax: 1260, yMin: 130, yMax: 820 });
    if (!fieldClick.ok) {
      await page.keyboard.press('Enter');
      fieldClick = { ok: true, selector: 'keyboard-enter:sort-field-review_after-after-search', value: expectedSort.field };
    }
  }
  result.steps.push({ action: 'set_sort_field', field: expectedSort.field, ...fieldClick });
  await page.waitForTimeout(1200);
  result.snapshots.push(await captureDomEvidence(page, outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_sort_field_selected`, args));

  const postField = await extractOpenAirtablePanel(page, 'sort');
  const postRows = relevantSortRows({ rows: postField.rows || [], panel_extraction: { ok: postField.ok } });
  const directionOk = sortDirectionObservedForField(postRows, expectedSort);
  result.steps.push({ action: 'sort_direction_after_field_select_probe', direction_ok: directionOk, rows: postRows.map((row) => row.text), panel_extraction: { ok: postField.ok, reason: postField.reason || null, panel: postField.panel || null } });

  if (!directionOk) {
    const panel = postField.panel || opened.extracted.panel;
    if (!panel) throw new Error('Cannot set sort direction: no sort panel geometry after field select.');
    const rowY = rowYFromExtraction(postField, panel.y + 70);
    const directionPoint = { x: panel.x + Math.min(333, Math.max(260, panel.w - 120)), y: rowY };
    await clickAt(directionPoint, 'sort-direction-open');
    await page.waitForTimeout(500);
    const option = await clickVisibleText(/^(Earliest\s*->\s*Latest|A\s*->\s*Z|1\s*->\s*9|Ascending)$/i, 'sort-direction-earliest-latest', { xMin: Math.max(250, directionPoint.x - 150), xMax: Math.min(1450, directionPoint.x + 400), yMin: Math.max(90, directionPoint.y - 80), yMax: Math.min(900, directionPoint.y + 420) });
    result.steps.push({ action: 'set_sort_direction_ascending', option });
    if (!option.ok) throw new Error('Could not click ascending sort direction option.');
  }

  await page.waitForTimeout(900);
  result.snapshots.push(await captureDomEvidence(page, outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_sort_configured`, args));
  await closeOpenAirtablePanel(page);
}

async function applyOneTarget(target) {
  assertSupportedTarget(target);
  const result = {
    timestamp_utc: nowIso(),
    tool_version: TOOL_VERSION,
    shared_panel_readback_version: AIRTABLE_PANEL_READBACK_VERSION,
    shared_panel_discovery_version: AIRTABLE_PANEL_DISCOVERY_VERSION,
    shared_panel_actions_version: AIRTABLE_PANEL_ACTIONS_VERSION,
    target,
    status: 'started',
    safety: {
      one_view_only: true,
      supported_target_key: SUPPORTED_TARGET_KEY,
      supported_mutation: 'add missing first review_after on-or-before today filter, normalize one existing review_after exact-date/unset filter, and add missing first sort review_after ascending only',
      disallowed_mutations: ['create_view', 'delete_view', 'delete_filter', 'delete_sort', 'replace_unrelated_filter', 'replace_existing_sort', 'multi_filter', 'multi_sort', 'non_review_after_field'],
      exact_token_required: REQUIRED_TOKEN
    },
    steps: [],
    snapshots: []
  };

  log('Validation-due view apply target starting.', { table_name: target.table_name, view_name: target.view_name });
  result.steps.push(await selectAirtableTableAndView(page, target));
  result.snapshots.push(await captureDomEvidence(page, outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_00_target_loaded`, args));

  result.before = await verifyTarget(target, 'before_apply');
  if (result.before.comparison.ok) {
    result.status = 'already_correct_noop';
    result.completed_at_utc = nowIso();
    return result;
  }

  result.plan = buildAirtableViewChangePlan(target, result.before.filter, result.before.sort);
  result.pre_execute_gate = summarizePlanSafety(result.plan, result.before);
  if (!result.pre_execute_gate.allowed) {
    throw new Error(`Pre-execute safety gate failed: ${JSON.stringify(result.pre_execute_gate)}`);
  }

  result.discovery_before_filter = await captureAirtablePanelDiscovery(page, outputDir, target, 'filter', 'pre_execute', {
    ...args,
    probeDropdownOptions: false,
    maxDropdownProbes: 0
  });
  result.discovery_before_sort = await captureAirtablePanelDiscovery(page, outputDir, target, 'sort', 'pre_execute', {
    ...args,
    probeDropdownOptions: false,
    maxDropdownProbes: 0
  });

  if (['add_or_build_filters', 'normalize_single_relative_date_filter'].includes(result.pre_execute_gate.filter_action)) {
    const filterAction = await ensureSingleRelativeDateFilter(page, {
      field: 'review_after',
      operator: 'on or before',
      value: 'today',
      outputDir,
      evidenceLabel: `${safeName(target.table_name)}_${safeName(target.view_name)}_review_after_on_or_before_today`,
      screenshotOptions: args
    });
    result.steps.push({ action: 'shared_ensure_single_relative_date_filter', status: filterAction.status, report: filterAction });
    result.snapshots.push(...(filterAction.snapshots || []));
    result.mutation_attempted = true;
    result.mutation_types = [...(result.mutation_types || []), result.pre_execute_gate.filter_action === 'add_or_build_filters' ? 'add_filter_review_after_on_or_before_today' : 'normalize_filter_review_after_on_or_before_today'];
  }

  result.after_filter_click = await verifyTarget(target, 'after_filter_click');

  if (result.pre_execute_gate.sort_action === 'add_or_build_sorts') {
    await addReviewAfterSort(target, result);
    result.mutation_attempted = true;
    result.mutation_types = [...(result.mutation_types || []), 'add_sort_review_after_ascending'];
  }

  result.after_click = await verifyTarget(target, 'after_click');
  if (!result.after_click.comparison.ok) {
    throw new Error(`After-click verification failed: ${JSON.stringify(result.after_click.comparison.missing || [])}`);
  }

  await page.reload({ waitUntil: 'domcontentloaded', timeout: 15000 });
  await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
  await page.waitForTimeout(1200);
  result.after_reload_select = await selectAirtableTableAndView(page, target);
  result.after_refresh = await verifyTarget(target, 'after_refresh');
  result.status = result.after_refresh.comparison.ok ? 'validation_due_view_verified_after_refresh' : 'validation_due_view_gap_after_refresh';
  result.completed_at_utc = nowIso();
  return result;
}

try {
  log('Starting DCOIR WBS09 apply validation-due view tool.', {
    version: TOOL_VERSION,
    shared_panel_readback_version: AIRTABLE_PANEL_READBACK_VERSION,
    shared_panel_discovery_version: AIRTABLE_PANEL_DISCOVERY_VERSION,
    shared_panel_actions_version: AIRTABLE_PANEL_ACTIONS_VERSION
  });
  if (!args.manifest) throw new Error('Missing --manifest');
  const manifest = readJsonFile(args.manifest);
  const targets = selectManifestTargets(manifest, { targetKeys: args.targetKeys });
  if (targets.length !== 1) throw new Error('This tool requires exactly one -TargetKey.');
  const target = targets[0];
  target.base_id = manifest.base_id;
  assertSupportedTarget(target);
  const baseUrl = args.baseUrl || `https://airtable.com/${manifest.base_id}`;

  await openBrowser(baseUrl);
  rl = readline.createInterface({ input, output });
  await rl.question('Airtable validation-due apply: log into Airtable, confirm the DCOIR base is open, then press Enter. Ctrl+C aborts before mutation gate. ');
  const typed = await rl.question(`About to add/verify only the ${SUPPORTED_TARGET_KEY} review_after filter/sort. Type ${REQUIRED_TOKEN} again to proceed: `);
  if (typed.trim() !== REQUIRED_TOKEN) throw new Error('Confirmation token mismatch. Aborting before mutation.');

  const result = await applyOneTarget(target);
  const reportPath = path.join(outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_apply_validation_due_view_report.json`);
  writeJson(reportPath, result);
  const rollup = {
    timestamp_utc: nowIso(),
    tool_version: TOOL_VERSION,
    status: result.status,
    target_count: 1,
    mutation_attempted: Boolean(result.mutation_attempted),
    mutation_types: result.mutation_types || [],
    report_path: reportPath
  };
  writeJson(path.join(outputDir, 'apply_validation_due_view_rollup.json'), rollup);
  log('Apply validation-due view completed.', rollup);
  const ok = ['already_correct_noop', 'validation_due_view_verified_after_refresh'].includes(result.status);
  await closeBrowser(ok);
  process.exit(ok ? 0 : 1);
} catch (error) {
  const failure = {
    timestamp_utc: nowIso(),
    tool_version: TOOL_VERSION,
    status: 'apply_validation_due_view_failed',
    error: String(error && error.message ? error.message : error)
  };
  try {
    if (page) failure.snapshot = await captureDomEvidence(page, outputDir, 'apply_validation_due_view_failure', args);
  } catch {}
  writeJson(path.join(outputDir, 'apply_validation_due_view_failed.json'), failure);
  log('Apply validation-due view failed.', { error: failure.error });
  await closeBrowser(false);
  process.exit(1);
} finally {
  if (rl) rl.close();
}
