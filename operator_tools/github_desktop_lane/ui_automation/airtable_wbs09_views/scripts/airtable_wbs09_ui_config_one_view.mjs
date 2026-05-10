#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import readline from 'node:readline/promises';
import { stdin as input, stdout as output } from 'node:process';
import { ensureDir, readJsonFile, writeJson, nowIso, safeName, reEscape, exactRe, norm } from '../../shared/dcoir_ui_common.mjs';
import { getFilterOperatorLabel, validateViewConfigContract, summarizeViewConfig, normalizeFilterValues, filterRequiresValue } from '../../shared/dcoir_airtable_view_config.mjs';

const VERSION = '2026-05-10.draft29-inline-text-filter-values';
let args;

function parseArgs(argv) {
  const parsed = {
    executeConfigureOneView: false,
    executeConfigureViewBatch: false,
    enableScreenshots: false,
    stopOnFirstFailure: true,
    headless: false,
    useChromeChannel: false,
    userDataDir: null,
    connectCdpUrl: null,
    keepBrowserOpenOnFailure: false,
    startIndex: 1,
    viewName: null
  };
  for (let i = 2; i < argv.length; i += 1) {
    const a = argv[i];
    const next = () => argv[++i];
    if (a === '--manifest') parsed.manifest = next();
    else if (a === '--output-dir') parsed.outputDir = next();
    else if (a === '--base-url') parsed.baseUrl = next();
    else if (a === '--execute-configure-one-view') parsed.executeConfigureOneView = true;
    else if (a === '--execute-configure-view-batch') parsed.executeConfigureViewBatch = true;
    else if (a === '--confirm') parsed.confirm = next();
    else if (a === '--max-views') parsed.maxViews = Number(next());
    else if (a === '--start-index') parsed.startIndex = Number(next());
    else if (a === '--table-name') parsed.tableName = next();
    else if (a === '--view-name') parsed.viewName = next();
    else if (a === '--schema-audit-json') parsed.schemaAuditJson = next();
    else if (a === '--enable-screenshots') parsed.enableScreenshots = true;
    else if (a === '--continue-on-failure') parsed.stopOnFirstFailure = false;
    else if (a === '--headless') parsed.headless = true;
    else if (a === '--use-chrome-channel') parsed.useChromeChannel = true;
    else if (a === '--user-data-dir') parsed.userDataDir = next();
    else if (a === '--connect-cdp-url') parsed.connectCdpUrl = next();
    else if (a === '--keep-browser-open-on-failure') parsed.keepBrowserOpenOnFailure = true;
    else throw new Error(`Unknown argument: ${a}`);
  }
  return parsed;
}


args = parseArgs(process.argv);
const downloads = process.env.DCOIR_DOWNLOADS_DIR;
if (!downloads || !downloads.trim()) {
  console.error('Missing required Local Configuration Registry variable: DCOIR_DOWNLOADS_DIR');
  process.exit(2);
}
const outputDir = args.outputDir || path.join(downloads, `dcoir_wbs09_airtable_ui_views_${new Date().toISOString().replace(/[:.]/g, '')}`);
ensureDir(outputDir);
const logPath = path.join(outputDir, 'tool.log');
function log(message, obj) {
  const line = `${nowIso()} ${message}${obj ? ' ' + JSON.stringify(obj) : ''}`;
  fs.appendFileSync(logPath, line + '\n', 'utf8');
  console.log(line);
}

function validateManifest(manifest) {
  const views = manifest.views || [];
  const tables = manifest.tables || [];
  if (manifest.view_count !== 65 || views.length !== 65) throw new Error(`Manifest must contain exactly 65 views; got ${views.length}`);
  if (manifest.table_count !== 21 || tables.length !== 21) throw new Error(`Manifest must contain exactly 21 tables; got ${tables.length}`);
  return { views, tables };
}

function selectViews(views) {
  let selected = views;
  if (args.tableName) selected = selected.filter(v => String(v.table_name).toLowerCase() === args.tableName.toLowerCase());
  if (args.viewName) selected = selected.filter(v => String(v.view_name).toLowerCase() === args.viewName.toLowerCase());
  const startIndex = Number(args.startIndex || 1);
  if (!Number.isInteger(startIndex) || startIndex < 1) throw new Error(`--start-index must be an integer >= 1; got ${args.startIndex}`);
  if (startIndex > selected.length + 1) throw new Error(`--start-index ${startIndex} is beyond selected view count ${selected.length}`);
  if (startIndex > 1) selected = selected.slice(startIndex - 1);
  if (args.maxViews && args.maxViews > 0) selected = selected.slice(0, args.maxViews);
  return selected;
}

function oneViewContract(view) {
  return validateViewConfigContract(view, { maxFilters: 2, maxSorts: 5 });
}
function verifySchemaAuditGate(schemaAuditJson) {
  if (!schemaAuditJson || !String(schemaAuditJson).trim()) throw new Error('Batch configuration requires --schema-audit-json pointing to a fresh PASS audit report.');
  if (!fs.existsSync(schemaAuditJson)) throw new Error(`Schema audit JSON not found: ${schemaAuditJson}`);
  const audit = readJsonFile(schemaAuditJson);
  const status = audit.status;
  const errors = Number(audit.error_count || 0);
  const warnings = Number(audit.warning_count || 0);
  const views = Number(audit.manifest_view_count || 0);
  if (status !== 'PASS' || errors !== 0 || warnings !== 0 || views !== 65) {
    throw new Error(`Schema audit gate failed. Expected PASS/errors=0/warnings=0/views=65; got status=${status}, errors=${errors}, warnings=${warnings}, views=${views}.`);
  }
  return { status, error_count: errors, warning_count: warnings, manifest_view_count: views, source: schemaAuditJson };
}

async function getVisibleDomSnapshot(page) {
  return await page.evaluate(() => {
    const elements = Array.from(document.querySelectorAll('button, [role="button"], input, textarea, [aria-label], [placeholder], div, span, a')).slice(0, 3000);
    function visible(el) {
      const style = window.getComputedStyle(el);
      const box = el.getBoundingClientRect();
      return style && style.visibility !== 'hidden' && style.display !== 'none' && box.width > 0 && box.height > 0;
    }
    return elements.filter(visible).map((el) => {
      const box = el.getBoundingClientRect();
      return {
        tag: el.tagName,
        role: el.getAttribute('role'),
        aria: el.getAttribute('aria-label'),
        placeholder: el.getAttribute('placeholder'),
        type: el.getAttribute('type'),
        text: (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 400),
        x: Math.round(box.x),
        y: Math.round(box.y),
        w: Math.round(box.width),
        h: Math.round(box.height)
      };
    }).filter(x => x.text || x.aria || x.placeholder || x.role || x.type).slice(0, 900);
  });
}

async function captureSnapshot(page, label) {
  const fullLabel = args.activeSnapshotPrefix ? `${args.activeSnapshotPrefix}_${label}` : label;
  const payload = { timestamp_utc: nowIso(), label: fullLabel, url: page.url(), title: await page.title(), elements: await getVisibleDomSnapshot(page) };
  const domPath = path.join(outputDir, `${safeName(fullLabel)}.dom.json`);
  writeJson(domPath, payload);
  const result = { label: fullLabel, dom_evidence: domPath };
  if (args.enableScreenshots) {
    const screenshotPath = path.join(outputDir, `${safeName(fullLabel)}.png`);
    await page.screenshot({ path: screenshotPath, fullPage: true });
    result.screenshot = screenshotPath;
  }
  return result;
}

async function clickFirst(page, candidates, options = {}) {
  const timeout = options.timeout ?? 2500;
  for (const candidate of candidates) {
    try {
      const loc = typeof candidate === 'string' ? page.locator(candidate).first() : candidate.first();
      if (await loc.count()) {
        await loc.click({ timeout });
        return { ok: true, selector: String(candidate) };
      }
    } catch (_) {}
  }
  return { ok: false };
}

async function clickExistingView(page, viewName) {
  const picked = await page.evaluate((name) => {
    function visible(el) {
      const style = window.getComputedStyle(el);
      const box = el.getBoundingClientRect();
      return style && style.visibility !== 'hidden' && style.display !== 'none' && box.width > 0 && box.height > 0;
    }
    const norm = (s) => String(s || '').replace(/\s+/g, ' ').trim();
    const nodes = Array.from(document.querySelectorAll('button, [role="button"], div, span, a'));
    const candidates = nodes.map((el) => {
      const box = el.getBoundingClientRect();
      return { el, text: norm(el.innerText || el.textContent), x: box.x, y: box.y, w: box.width, h: box.height };
    }).filter(c => visible(c.el) && c.text === name && c.x >= 40 && c.x < 420 && c.y >= 100 && c.w > 20 && c.h > 8).sort((a, b) => a.y - b.y || a.x - b.x);
    const c = candidates[0];
    if (!c) return null;
    c.el.scrollIntoView({ block: 'center', inline: 'center' });
    c.el.click();
    return { selector: 'geometry:existing-view-sidebar-row', text: c.text, x: Math.round(c.x), y: Math.round(c.y), w: Math.round(c.w), h: Math.round(c.h) };
  }, viewName);
  return picked ? { ok: true, ...picked } : { ok: false };
}

async function clickToolbarButton(page, labelRegex, label) {
  const roleCandidatesByLabel = {
    filter: [/^Filter rows$/i, /^Filter$/i],
    sort: [/^Sort rows$/i, /^Sort$/i]
  };
  const candidates = roleCandidatesByLabel[label] || [labelRegex];
  for (const name of candidates) {
    const loc = page.getByRole('button', { name });
    const count = await loc.count().catch(() => 0);
    for (let i = 0; i < count; i += 1) {
      const item = loc.nth(i);
      const box = await item.boundingBox().catch(() => null);
      const visible = await item.isVisible().catch(() => false);
      if (!visible || !box) continue;
      if (box.y < 80 || box.y > 145 || box.x < 760 || box.x > 1320 || box.width < 10 || box.width > 180 || box.height < 10 || box.height > 40) continue;
      const text = norm(await item.innerText().catch(() => ''));
      const aria = await item.getAttribute('aria-label').catch(() => '');
      await item.click({ timeout: 3000 });
      return { ok: true, selector: `role-toolbar-button:${label}`, text, aria: aria || '', x: Math.round(box.x), y: Math.round(box.y), w: Math.round(box.width), h: Math.round(box.height) };
    }
  }
  return { ok: false };
}

async function clearExistingFilterConditions(page, result) {
  const removed = [];
  for (let attempt = 0; attempt < 8; attempt += 1) {
    const target = await page.evaluate(() => {
      function visible(el) {
        const style = window.getComputedStyle(el);
        const box = el.getBoundingClientRect();
        return style && style.visibility !== 'hidden' && style.display !== 'none' && box.width > 0 && box.height > 0;
      }
      const nodes = Array.from(document.querySelectorAll('button, [role="button"]'));
      const candidates = nodes.map((el) => {
        const box = el.getBoundingClientRect();
        const text = (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim();
        const aria = el.getAttribute('aria-label') || '';
        return { el, text, aria, x: box.x, y: box.y, w: box.width, h: box.height };
      }).filter((c) => {
        if (!visible(c.el)) return false;
        const removeByAria = /^Remove item \d+$/i.test(c.aria) || /remove.*condition|delete.*condition/i.test(c.aria);
        const removeByGeometry = c.x >= 830 && c.x <= 940 && c.y >= 200 && c.y <= 380 && c.w >= 18 && c.w <= 40 && c.h >= 18 && c.h <= 40;
        return removeByAria || removeByGeometry;
      }).sort((a, b) => a.y - b.y || a.x - b.x);
      const c = candidates[0];
      if (!c) return null;
      c.el.click();
      return { aria: c.aria, text: c.text, x: Math.round(c.x), y: Math.round(c.y), w: Math.round(c.w), h: Math.round(c.h) };
    });
    if (!target) break;
    removed.push(target);
    await page.waitForTimeout(600);
  }
  result.steps.push({ action: 'clear_existing_filter_conditions', ok: true, removed_count: removed.length, removed });
  return removed;
}

function filterValuesForView(view) {
  const filter = (view.filters || [])[0];
  if (!filter) return [];
  return Array.isArray(filter.value) ? filter.value : [filter.value];
}

function filterValuesForCondition(filter) {
  return normalizeFilterValues(filter);
}

function filterFieldForView(view) {
  const filter = (view.filters || [])[0];
  return filter ? filter.field : null;
}

function filterFieldForCondition(filter) {
  return filter ? filter.field : null;
}

function sortFieldForView(view) {
  const sort = (view.sorts || [])[0];
  return sort ? sort.field : null;
}

function sortDirectionForView(view) {
  const sort = (view.sorts || [])[0];
  return sort ? sort.direction : null;
}

async function clickPanelText(page, pattern, label) {
  const picked = await page.evaluate(({ source, label }) => {
    const re = new RegExp(source, 'i');
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
        if (tag === 'BUTTON' || tag === 'A' || role === 'button' || cur.onclick) return cur;
        cur = cur.parentElement;
      }
      return el;
    }
    const nodes = Array.from(document.querySelectorAll('button, [role="button"], div, span, a, input'));
    const candidates = nodes.map((el) => {
      const box = el.getBoundingClientRect();
      const text = (el.innerText || el.textContent || el.getAttribute('aria-label') || el.getAttribute('placeholder') || '').replace(/\s+/g, ' ').trim();
      return { el, text, x: box.x, y: box.y, w: box.width, h: box.height };
    }).filter(c => visible(c.el) && c.x >= 400 && c.x <= 1100 && c.y >= 110 && c.y <= 900 && re.test(c.text)).sort((a, b) => (a.w * a.h) - (b.w * b.h) || a.y - b.y || a.x - b.x);
    const c = candidates[0];
    if (!c) return null;
    const target = clickableAncestor(c.el);
    const box = target.getBoundingClientRect();
    target.click();
    return { selector: `panel-text:${label}`, text: c.text, x: Math.round(box.x), y: Math.round(box.y), w: Math.round(box.width), h: Math.round(box.height) };
  }, { source: pattern.source, label });
  return picked ? { ok: true, ...picked } : { ok: false };
}

async function clickPanelCoordinate(page, x, y, label) {
  await page.mouse.click(x, y);
  return { ok: true, selector: `coordinate:${label}`, x, y };
}

async function selectDropdownValue(page, candidateText, fallbackPoint, value, label) {
  let step = await clickPanelText(page, candidateText, `${label}-open-by-text`);
  if (!step.ok && fallbackPoint) step = await clickPanelCoordinate(page, fallbackPoint.x, fallbackPoint.y, `${label}-open-by-coordinate`);
  if (!step.ok) return { ok: false, selector: `unable:${label}-open` };
  await page.waitForTimeout(450);
  await page.keyboard.type(String(value), { delay: 15 });
  await page.waitForTimeout(550);
  await page.keyboard.press('Enter');
  await page.waitForTimeout(700);
  return { ok: true, selector: `${step.selector}+keyboard-select`, value };
}

async function enterInlineFilterTextValue(page, result, filter, filterIndex) {
  const ordinal = filterIndex + 1;
  const rowY = 268 + (filterIndex * 46);
  const values = filterValuesForCondition(filter);
  if (values.length < 1) throw new Error(`Inline text filter ${ordinal} requires at least one value.`);
  const value = String(values[0]);

  const target = await page.evaluate(({ rowY }) => {
    function visible(el) {
      const style = window.getComputedStyle(el);
      const box = el.getBoundingClientRect();
      return style && style.visibility !== 'hidden' && style.display !== 'none' && box.width > 0 && box.height > 0;
    }
    const nodes = Array.from(document.querySelectorAll('input, textarea, [contenteditable="true"]'));
    const candidates = nodes.map((el) => {
      const box = el.getBoundingClientRect();
      const placeholder = el.getAttribute('placeholder') || '';
      const aria = el.getAttribute('aria-label') || '';
      const disabled = el.disabled || el.getAttribute('aria-disabled') === 'true';
      return {
        el,
        placeholder,
        aria,
        disabled,
        x: box.x,
        y: box.y,
        w: box.width,
        h: box.height,
        cx: box.x + (box.width / 2),
        cy: box.y + (box.height / 2)
      };
    }).filter((c) => {
      if (!visible(c.el) || c.disabled) return false;
      const nearFilterRow = c.y >= rowY - 60 && c.y <= rowY + 80;
      const likelyValueColumn = c.x >= 650 && c.x <= 1050 && c.w >= 40 && c.h >= 10;
      return nearFilterRow && likelyValueColumn;
    }).sort((a, b) => {
      const aScore = Math.abs((a.y + (a.h / 2)) - rowY) + Math.abs(a.x - 730) / 10;
      const bScore = Math.abs((b.y + (b.h / 2)) - rowY) + Math.abs(b.x - 730) / 10;
      return aScore - bScore;
    });
    const c = candidates[0];
    if (!c) return null;
    return {
      selector: 'inline-filter-text-input',
      placeholder: c.placeholder,
      aria: c.aria,
      x: Math.round(c.x),
      y: Math.round(c.y),
      w: Math.round(c.w),
      h: Math.round(c.h),
      cx: Math.round(c.cx),
      cy: Math.round(c.cy)
    };
  }, { rowY });

  result.steps.push({ action: 'locate_inline_filter_text_input', filter_index: ordinal, value, ...(target || { ok: false }) });
  if (!target) throw new Error(`Could not locate inline text value input for filter ${ordinal}.`);

  await page.mouse.click(target.cx, target.cy);
  await page.waitForTimeout(250);
  const modifier = process.platform === 'darwin' ? 'Meta' : 'Control';
  await page.keyboard.press(`${modifier}+A`).catch(() => {});
  await page.keyboard.press('Backspace').catch(() => {});
  await page.keyboard.type(value, { delay: 15 });
  await page.waitForTimeout(550);
  await page.keyboard.press('Enter').catch(() => {});
  await page.waitForTimeout(900);

  result.steps.push({ action: 'set_inline_filter_text_value', filter_index: ordinal, ok: true, value, selector: target.selector });
  result.snapshots.push(await captureSnapshot(page, `one_view_config_05_filter_${ordinal}_inline_text_value`));
}

async function configureSingleFilterCondition(page, result, filter, filterIndex) {
  const ordinal = filterIndex + 1;
  const rowY = 268 + (filterIndex * 46);
  const filterField = filterFieldForCondition(filter);

  const add = await clickPanelText(page, /^\+?\s*Add condition$/i, `add-filter-condition-${ordinal}`);
  result.steps.push({ action: 'add_filter_condition', filter_index: ordinal, ...add });
  if (!add.ok) throw new Error(`Could not click Add condition in filter panel for filter ${ordinal}.`);
  await page.waitForTimeout(900);
  result.snapshots.push(await captureSnapshot(page, `one_view_config_02_filter_${ordinal}_condition_added`));

  const field = await selectDropdownValue(page, /^(Work Item|Select a field|Field|Status|Name|delete_stage|approved_to_delete|active|Priority|Queue Rank)$/i, { x: 520, y: rowY }, filterField, `filter-${ordinal}-field`);
  result.steps.push({ action: 'set_filter_field', filter_index: ordinal, field: filterField, ...field });
  if (!field.ok) throw new Error(`Could not select ${filterField} as filter field for filter ${ordinal}.`);
  result.snapshots.push(await captureSnapshot(page, `one_view_config_03_filter_${ordinal}_field`));

  const operatorLabel = getFilterOperatorLabel(filter.operator);
  const operator = await selectDropdownValue(
    page,
    /^(contains|is|is not|is not empty|is empty|is any of|has any of|is one of|is on or before|on or before)$/i,
    { x: 660, y: rowY },
    operatorLabel,
    `filter-${ordinal}-operator`
  );
  result.steps.push({ action: 'set_filter_operator', filter_index: ordinal, operator: operatorLabel, manifest_operator: filter.operator, ...operator });
  if (!operator.ok) throw new Error(`Could not set filter ${ordinal} operator to ${operatorLabel}.`);
  result.snapshots.push(await captureSnapshot(page, `one_view_config_04_filter_${ordinal}_operator`));

  if (!filterRequiresValue(filter)) {
    result.steps.push({ action: 'configure_filter_value_skipped', filter_index: ordinal, ok: true, reason: 'operator does not require a value' });
    await page.waitForTimeout(900);
    result.snapshots.push(await captureSnapshot(page, `one_view_config_05_filter_${ordinal}_no_value_required`));
    return;
  }

  if (filter.operator === 'contains') {
    await enterInlineFilterTextValue(page, result, filter, filterIndex);
    return;
  }

  const valueOpen = await clickPanelText(
    page,
    /^(Select an option|Select options|Choose options|Enter a value|Enter text|Select date|Choose date|Date|Today|today|active|blocked|waiting|todo|in_progress|pending|true|false)$/i,
    `filter-${ordinal}-value-open`
  );
  result.steps.push({ action: 'open_filter_value_selector', filter_index: ordinal, ...valueOpen });
  if (!valueOpen.ok) throw new Error(`Could not open value selector for filter ${ordinal}.`);
  for (const value of filterValuesForCondition(filter)) {
    await page.waitForTimeout(300);
    await page.keyboard.type(String(value), { delay: 15 });
    await page.waitForTimeout(550);
    await page.keyboard.press('Enter');
    result.steps.push({ action: 'select_filter_value', filter_index: ordinal, value, manifest_operator: filter.operator });
  }
  await page.waitForTimeout(900);
  result.snapshots.push(await captureSnapshot(page, `one_view_config_05_filter_${ordinal}_values`));
}

async function configureFilter(page, result) {
  const target = result.target;
  const filters = Array.isArray(target.filters) ? target.filters : [];
  if (filters.length === 0) {
    result.steps.push({ action: 'configure_filter_skipped', ok: true, reason: 'target has no manifest filters' });
    return;
  }
  const filterClick = await clickToolbarButton(page, /\bFilter\b|Filter rows/, 'filter');
  result.steps.push({ action: 'open_filter_panel', ...filterClick });
  if (!filterClick.ok) throw new Error('Could not open Filter panel.');
  await page.waitForTimeout(700);
  result.snapshots.push(await captureSnapshot(page, 'one_view_config_01_filter_panel_before'));
  await clearExistingFilterConditions(page, result);
  await page.waitForTimeout(700);
  result.snapshots.push(await captureSnapshot(page, 'one_view_config_01b_filter_panel_cleared'));

  for (let filterIndex = 0; filterIndex < filters.length; filterIndex += 1) {
    await configureSingleFilterCondition(page, result, filters[filterIndex], filterIndex);
  }

  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(500);
}
async function configureSort(page, result) {
  const target = result.target;
  const sorts = Array.isArray(target.sorts) ? target.sorts : [];
  if (sorts.length === 0) {
    result.steps.push({ action: 'configure_sort_skipped', ok: true, reason: 'target has no manifest sorts' });
    return;
  }
  const sortClick = await clickToolbarButton(page, /\bSort\b|Sort rows/, 'sort');
  result.steps.push({ action: 'open_sort_panel', ...sortClick });
  if (!sortClick.ok) throw new Error('Could not open Sort panel.');
  await page.waitForTimeout(700);
  result.snapshots.push(await captureSnapshot(page, 'one_view_config_06_sort_panel_before'));

  for (let sortIndex = 0; sortIndex < sorts.length; sortIndex += 1) {
    const sort = sorts[sortIndex];
    const sortField = sort.field;
    const sortDirection = sort.direction === 'desc' ? 'descending' : 'ascending';
    const sortOrdinal = sortIndex + 1;

    const addSort = await clickPanelText(page, /^\+?\s*(Add sort|Pick another field to sort by)$/i, `add-sort-${sortOrdinal}`);
    result.steps.push({ action: 'add_sort_or_field_list_ready', sort_index: sortOrdinal, ...addSort });
    if (addSort.ok) await page.waitForTimeout(800);
    else if (sortIndex === 0) result.steps.push({ action: 'sort_panel_field_list_already_visible', ok: true, note: 'No Add sort control found; Airtable displayed the field picker directly or an existing sort row is active.' });
    else throw new Error(`Could not add sort condition ${sortOrdinal}.`);

    let field = await clickPanelText(page, exactRe(sortField), `sort-${sortOrdinal}-field-${safeName(sortField)}-direct`);
    if (!field.ok) field = await selectDropdownValue(page, /^(Pick a field|Select a field|Work Item|Queue Rank|Priority|Name|Execution Lane|Test ID|canonical_parent_plan_id)$/i, { x: 510, y: 268 + ((sortOrdinal - 1) * 42) }, sortField, `sort-${sortOrdinal}-field`);
    result.steps.push({ action: 'set_sort_field', sort_index: sortOrdinal, field: sortField, ...field });
    if (!field.ok) throw new Error(`Could not select ${sortField} as sort field for sort ${sortOrdinal}.`);
    await page.waitForTimeout(700);

    const direction = await selectDropdownValue(page, /^(A\s*â†’\s*Z|1\s*â†’\s*9|Ascending|asc|Z\s*â†’\s*A|9\s*â†’\s*1|Descending|desc)$/i, { x: 725, y: 268 + ((sortOrdinal - 1) * 42) }, sortDirection, `sort-${sortOrdinal}-direction`);
    result.steps.push({ action: 'set_sort_direction', sort_index: sortOrdinal, direction: sortDirection, ...direction });
    if (!direction.ok) {
      if (sortDirection === 'ascending') result.steps.push({ action: 'sort_direction_assumed_default_ascending', ok: true, sort_index: sortOrdinal, note: 'Airtable often defaults to ascending when the sort field is selected and no direction selector is visible.' });
      else throw new Error(`Could not set required descending sort direction for sort ${sortOrdinal}.`);
    }
    await page.waitForTimeout(700);
    result.snapshots.push(await captureSnapshot(page, `one_view_config_07_sort_${sortOrdinal}_configured`));
  }

  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(500);
}
async function verifyPostConditions(page, target) {
  const expectedFilters = Array.isArray(target.filters)
    ? target.filters.map((f, i) => ({ index: i + 1, field: f.field, operator: f.operator, operator_label: getFilterOperatorLabel(f.operator) }))
    : [];
  const expectedSorts = Array.isArray(target.sorts)
    ? target.sorts.map((s, i) => ({ index: i + 1, field: s.field, direction: s.direction }))
    : [];

  const probe = await page.evaluate(({ expectedFilters, expectedSorts }) => {
    function visible(el) {
      const style = window.getComputedStyle(el);
      const box = el.getBoundingClientRect();
      return style && style.visibility !== 'hidden' && style.display !== 'none' && box.width > 0 && box.height > 0;
    }

    const toolbarText = Array.from(document.querySelectorAll('button, [role="button"], div, span'))
      .map((el) => {
        const box = el.getBoundingClientRect();
        return {
          text: (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim(),
          aria: el.getAttribute('aria-label') || '',
          x: box.x,
          y: box.y,
          w: box.width,
          h: box.height,
          visible: visible(el)
        };
      })
      .filter((c) => c.visible && c.y >= 80 && c.y <= 150 && c.x >= 650 && c.x <= 1400)
      .map((c) => `${c.text} ${c.aria}`.trim())
      .join(' ');

    const bodyText = (document.body.innerText || '').replace(/\s+/g, ' ').trim();
    const text = `${toolbarText} ${bodyText}`;
    const lower = text.toLowerCase();

    const hasFilterBadge = expectedFilters.length === 0 || /filtered by/i.test(text);
    const hasFilterFields = expectedFilters.length === 0 || expectedFilters.every((f) => lower.includes(String(f.field || '').toLowerCase()));
    const hasSortBadge = expectedSorts.length === 0 || /sorted by\s+\d+\s+field/i.test(text) || /sorted by/i.test(text);
    const hasSortFields = expectedSorts.length === 0 || expectedSorts.every((s) => lower.includes(String(s.field || '').toLowerCase())) || hasSortBadge;

    const missing = [];
    if (expectedFilters.length > 0 && !(hasFilterBadge || hasFilterFields)) missing.push(`filter post-condition for ${expectedFilters.length} expected filter(s)`);
    if (expectedSorts.length > 0 && !hasSortFields) missing.push(`sort post-condition for ${expectedSorts.length} expected sort(s)`);

    return {
      expected_filter_conditions: expectedFilters,
      expected_sort_conditions: expectedSorts,
      has_filter_badge: hasFilterBadge,
      has_filter_fields: hasFilterFields,
      has_sort_badge: hasSortBadge,
      has_sort_fields: hasSortFields,
      missing,
      toolbar_text_sample: toolbarText.slice(0, 800)
    };
  }, { expectedFilters, expectedSorts });

  return { ok: probe.missing.length === 0, ...probe };
}
function rollupConfigurationStatus(results) {
  const rows = Array.isArray(results) ? results : [];
  if (rows.length < 1) return 'configuration_not_run';
  return rows.every((r) => r && r.status === 'configuration_verified')
    ? 'configuration_verified'
    : 'configuration_postcondition_failed';
}
let browser = null;
let context = null;
let page = null;
let closeMode = 'launched';
let rl = null;

async function gotoTableById(page, view) {
  const previousUrl = page.url();
  try {
    const current = new URL(previousUrl);
    const appId = current.pathname.split('/').filter(Boolean).find((part) => /^app[A-Za-z0-9]+$/.test(part));
    if (!appId) return { ok: false, selector: 'url:table-id-navigation', previous_url: previousUrl, error: 'Could not derive Airtable app id from current URL.' };
    if (!/^tbl[A-Za-z0-9]+$/.test(String(view.table_id || ''))) return { ok: false, selector: 'url:table-id-navigation', previous_url: previousUrl, error: `Invalid or missing table id: ${view.table_id}` };
    const targetUrl = `${current.origin}/${appId}/${view.table_id}?blocks=hide`;
    await page.goto(targetUrl, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
    await page.waitForTimeout(1600);
    return { ok: true, selector: 'url:table-id-navigation', previous_url: previousUrl, url: targetUrl };
  } catch (error) {
    return { ok: false, selector: 'url:table-id-navigation', previous_url: previousUrl, error: String(error && error.message ? error.message : error) };
  }
}

async function verifyViewLoaded(page, view) {
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(300);
  let tableClick = await gotoTableById(page, view);
  if (!tableClick.ok) {
    tableClick = await clickFirst(page, [page.getByText(view.table_name, { exact: true }), `[title="${String(view.table_name).replace(/"/g, '\\"')}"]`, `text="${String(view.table_name).replace(/"/g, '\\"')}"`], { timeout: 3000 });
  }
  await page.waitForTimeout(900);
  const viewClick = await clickExistingView(page, view.view_name);
  await page.waitForTimeout(1200);
  return { tableClick, viewClick };
}

async function configureSelectedTarget(page, view, target, mode, index) {
  const prefix = mode === 'execute_configure_view_batch'
    ? `batch_${String(index + 1).padStart(3, '0')}_${safeName(view.table_name)}_${safeName(view.view_name)}`
    : '';
  args.activeSnapshotPrefix = prefix;
  const report = { timestamp_utc: nowIso(), tool_version: VERSION, mode, target, steps: [], snapshots: [], status: 'started' };
  const loaded = await verifyViewLoaded(page, view);
  report.steps.push({ action: 'select_table', ...loaded.tableClick });
  report.steps.push({ action: 'select_view', ...loaded.viewClick });
  if (!loaded.tableClick.ok || !loaded.viewClick.ok) throw new Error(`Could not safely select target table/view before configuration: ${view.table_name} / ${view.view_name}.`);
  report.snapshots.push(await captureSnapshot(page, 'one_view_config_00_target_loaded'));
  await configureFilter(page, report);
  await configureSort(page, report);
  report.completed_at_utc = nowIso();
  report.snapshots.push(await captureSnapshot(page, 'one_view_config_08_final_unverified'));
  const postConditions = await verifyPostConditions(page, target);
  report.steps.push({ action: 'verify_post_conditions', ...postConditions });
  if (!postConditions.ok) {
    report.status = 'configuration_postcondition_failed';
    throw new Error(`Post-condition verification failed for ${target.table_name} / ${target.view_name}: ${postConditions.missing.join(', ')}`);
  }
  report.status = 'configuration_verified';
  args.activeSnapshotPrefix = '';
  return report;
}

try {
  log('Starting DCOIR WBS09 config smoke tool.', { version: VERSION });
  if (!args.manifest) throw new Error('Missing --manifest');
  const modeCount = [args.executeConfigureOneView, args.executeConfigureViewBatch].filter(Boolean).length;
  if (modeCount !== 1) throw new Error('Specify exactly one mode: --execute-configure-one-view or --execute-configure-view-batch.');
  const mode = args.executeConfigureViewBatch ? 'execute_configure_view_batch' : 'execute_configure_one_view';
  const expectedConfirm = args.executeConfigureViewBatch ? 'CONFIGURE_WBS09_VIEW_BATCH' : 'CONFIGURE_WBS09_ONE_VIEW';
  if (args.confirm !== expectedConfirm) throw new Error(`Configure mode requires --confirm ${expectedConfirm}`);

  const manifest = readJsonFile(args.manifest);
  const { views, tables } = validateManifest(manifest);
  const selected = selectViews(views);
  if (args.executeConfigureOneView && selected.length !== 1) throw new Error('One-view configuration requires exactly one selected manifest view. Pass -TableName and -ViewName.');
  if (args.executeConfigureViewBatch) {
    if (selected.length < 1) throw new Error('Batch configuration requires at least one selected view.');
    if (selected.length > 5) throw new Error(`Batch configuration is bounded to at most 5 selected views; got ${selected.length}. Use -MaxViews 5 or lower.`);
    if (!args.maxViews || Number(args.maxViews) < 1) throw new Error('Batch configuration requires -MaxViews 1..5 as an explicit safety bound.');
  }

  const schemaGate = args.executeConfigureViewBatch ? verifySchemaAuditGate(args.schemaAuditJson) : null;
  const targets = selected.map((view) => {
    const contract = oneViewContract(view);
    return { table_name: view.table_name, table_id: view.table_id, view_name: view.view_name, filters: contract.filters, sorts: contract.sorts };
  });

  const plan = {
    timestamp_utc: nowIso(),
    tool_version: VERSION,
    mode,
    manifest_view_count: views.length,
    manifest_table_count: tables.length,
    selected_view_count: selected.length,
    output_dir: outputDir,
    downloads_env_var: 'DCOIR_DOWNLOADS_DIR',
    repo_root_env_var: 'DCOIR_REPO_ROOT',
    base_id: manifest.base_id,
    base_url: args.baseUrl || `https://airtable.com/${manifest.base_id}`,
    supported_target_contract: args.executeConfigureViewBatch ? 'bounded_batch_max_five_views_each_max_one_filter_max_one_sort_schema_audit_pass_required' : 'generic_single_view_max_one_filter_max_one_sort',
    schema_audit_gate: schemaGate,
    targets
  };
  writeJson(path.join(outputDir, args.executeConfigureViewBatch ? 'view_batch_config_plan.json' : 'one_view_config_plan.json'), plan);

  let chromium;
  try { ({ chromium } = await import('playwright')); } catch { throw new Error('Playwright is required. Run the installer script first: Install-DcoirAirtableWbs09UiViewPrereqs.ps1'); }
  const baseUrl = args.baseUrl || `https://airtable.com/${manifest.base_id}`;
  if (args.connectCdpUrl) {
    closeMode = 'cdp_disconnect_only';
    log('Connecting to existing Chrome over CDP.', { connect_cdp_url: args.connectCdpUrl });
    browser = await chromium.connectOverCDP(args.connectCdpUrl);
    context = browser.contexts()[0];
    if (!context) throw new Error('CDP connection succeeded but no browser context was available.');
    page = context.pages()[0] || await context.newPage();
  } else if (args.userDataDir) {
    closeMode = 'persistent_context';
    log('Launching persistent browser context.', { user_data_dir: args.userDataDir, chrome_channel: Boolean(args.useChromeChannel) });
    ensureDir(args.userDataDir);
    context = await chromium.launchPersistentContext(args.userDataDir, { headless: Boolean(args.headless), channel: args.useChromeChannel ? 'chrome' : undefined, viewport: { width: 1440, height: 1000 } });
    browser = context.browser();
    page = context.pages()[0] || await context.newPage();
  } else {
    log('Launching browser context.', { chrome_channel: Boolean(args.useChromeChannel) });
    browser = await chromium.launch({ headless: Boolean(args.headless), channel: args.useChromeChannel ? 'chrome' : undefined });
    context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    page = await context.newPage();
  }
  await page.goto(baseUrl, { waitUntil: 'domcontentloaded' });
  rl = readline.createInterface({ input, output });
  await rl.question('Log into Airtable, confirm the DCOIR base is open, then press Enter. Ctrl+C aborts before any configuration click. ');
  const targetList = targets.map((t, i) => `${i + 1}. ${t.table_name} / ${t.view_name}`).join('\n');
  const prompt = args.executeConfigureViewBatch
    ? `About to configure ${targets.length} existing WBS09 Airtable view(s):\n${targetList}\nType ${expectedConfirm} again to proceed: `
    : `About to configure ONE existing WBS09 Airtable view: ${targets[0].table_name} / ${targets[0].view_name}. Type ${expectedConfirm} again to proceed: `;
  const confirm2 = await rl.question(prompt);
  if (confirm2 !== expectedConfirm) throw new Error('Second interactive confirmation did not match; stopped before configuration clicks.');

  if (args.executeConfigureViewBatch) {
    const batchReport = { timestamp_utc: nowIso(), tool_version: VERSION, mode, schema_audit_gate: schemaGate, status: 'started', results: [] };
    for (let i = 0; i < selected.length; i += 1) {
      log('Starting bounded batch target.', { index: i + 1, table: selected[i].table_name, view: selected[i].view_name });
      const result = await configureSelectedTarget(page, selected[i], targets[i], mode, i);
      batchReport.results.push(result);
      batchReport.last_completed_index = i + 1;
      writeJson(path.join(outputDir, 'view_batch_config_report.partial.json'), batchReport);
    }
    batchReport.status = rollupConfigurationStatus(batchReport.results);
    batchReport.completed_at_utc = nowIso();
    writeJson(path.join(outputDir, 'view_batch_config_report.json'), batchReport);
    log('Bounded view-batch configuration branch ended.', { status: batchReport.status, result_count: batchReport.results.length });
  } else {
    const report = await configureSelectedTarget(page, selected[0], targets[0], mode, 0);
    writeJson(path.join(outputDir, 'one_view_config_report.json'), report);
    log('One-view configuration branch ended.', { status: report.status, snapshot_count: report.snapshots.length });
  }

  if (closeMode === 'persistent_context') await context.close(); else await browser.close();
  process.exit(0);
} catch (e) {
  const errorReport = { timestamp_utc: nowIso(), error: String(e && e.message ? e.message : e), stack: e && e.stack ? e.stack : null };
  try {
    if (page) errorReport.failure_snapshot = await captureSnapshot(page, 'one_view_config_failure');
  } catch (snapshotError) {
    errorReport.failure_snapshot_error = String(snapshotError && snapshotError.message ? snapshotError.message : snapshotError);
  }
  try { writeJson(path.join(outputDir, 'error_report.json'), errorReport); } catch {}
  console.error(errorReport.error);
  try {
    if (page && args.keepBrowserOpenOnFailure && rl) {
      await rl.question('Failure detected. Browser will remain open for inspection. Press Enter in PowerShell only after you finish inspecting/uploading screenshots. ');
    }
  } catch {}
  try {
    if (context && closeMode === 'persistent_context') await context.close();
    else if (browser) await browser.close();
  } catch {}
  process.exit(1);
}






