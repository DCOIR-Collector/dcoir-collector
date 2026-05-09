#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import readline from 'node:readline/promises';
import { stdin as input, stdout as output } from 'node:process';

const VERSION = '2026-05-09.draft13-rerun-safe-filter-sort-smoke';
let args;

function parseArgs(argv) {
  const parsed = {
    executeConfigureOneView: false,
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
    else if (a === '--confirm') parsed.confirm = next();
    else if (a === '--max-views') parsed.maxViews = Number(next());
    else if (a === '--start-index') parsed.startIndex = Number(next());
    else if (a === '--table-name') parsed.tableName = next();
    else if (a === '--view-name') parsed.viewName = next();
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

function ensureDir(p) { fs.mkdirSync(p, { recursive: true }); }
function writeJson(p, obj) { fs.writeFileSync(p, JSON.stringify(obj, null, 2), 'utf8'); }
function nowIso() { return new Date().toISOString(); }
function safeName(s) { return String(s).replace(/[^A-Za-z0-9_.-]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 120) || 'item'; }

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
  if (args.tableName) selected = selected.filter(v => v.table_name.toLowerCase() === args.tableName.toLowerCase());
  if (args.viewName) selected = selected.filter(v => v.view_name.toLowerCase() === args.viewName.toLowerCase());
  const startIndex = Number(args.startIndex || 1);
  if (!Number.isInteger(startIndex) || startIndex < 1) throw new Error(`--start-index must be an integer >= 1; got ${args.startIndex}`);
  if (startIndex > selected.length + 1) throw new Error(`--start-index ${startIndex} is beyond selected view count ${selected.length}`);
  if (startIndex > 1) selected = selected.slice(startIndex - 1);
  if (args.maxViews && args.maxViews > 0) selected = selected.slice(0, args.maxViews);
  return selected;
}

function assertSupportedOneView(view) {
  const expectedFilters = JSON.stringify([{ field: 'Status', operator: 'is one of', value: ['active', 'in_progress', 'todo'] }]);
  const expectedSorts = JSON.stringify([{ field: 'Queue Rank', direction: 'asc' }]);
  const actualFilters = JSON.stringify(view.filters || []);
  const actualSorts = JSON.stringify(view.sorts || []);
  if (view.table_name !== 'Work Items' || view.view_name !== 'WBS09 - Active Queue') {
    throw new Error('This draft supports only the first smoke target: Work Items / WBS09 - Active Queue.');
  }
  if (actualFilters !== expectedFilters || actualSorts !== expectedSorts) {
    throw new Error('Manifest target does not match the supported Work Items / Active Queue filter+sort smoke-test contract.');
  }
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
  const payload = { timestamp_utc: nowIso(), label, url: page.url(), title: await page.title(), elements: await getVisibleDomSnapshot(page) };
  const domPath = path.join(outputDir, `${safeName(label)}.dom.json`);
  writeJson(domPath, payload);
  const result = { label, dom_evidence: domPath };
  if (args.enableScreenshots) {
    const screenshotPath = path.join(outputDir, `${safeName(label)}.png`);
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
    }).filter(c => visible(c.el) && c.text === name && c.x >= 40 && c.x < 360 && c.y >= 120 && c.w > 20 && c.h > 8).sort((a, b) => a.y - b.y || a.x - b.x);
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
      const text = (await item.innerText().catch(() => '')).replace(/\s+/g, ' ').trim();
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
        const removeByGeometry = c.x >= 830 && c.x <= 940 && c.y >= 210 && c.y <= 360 && c.w >= 18 && c.w <= 40 && c.h >= 18 && c.h <= 40;
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
  const filter = (view.filters || []).find(f => f.field === 'Status');
  return Array.isArray(filter && filter.value) ? filter.value : ['active', 'in_progress', 'todo'];
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
    }).filter(c => visible(c.el) && c.x >= 430 && c.x <= 1040 && c.y >= 120 && c.y <= 560 && re.test(c.text)).sort((a, b) => (a.w * a.h) - (b.w * b.h) || a.y - b.y || a.x - b.x);
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

async function typeAndEnter(page, text) {
  const mod = process.platform === 'darwin' ? 'Meta' : 'Control';
  await page.keyboard.press(`${mod}+A`).catch(() => {});
  await page.keyboard.type(text, { delay: 15 });
  await page.waitForTimeout(300);
  await page.keyboard.press('Enter');
  await page.waitForTimeout(600);
}

async function selectDropdownValue(page, candidateText, fallbackPoint, value, label) {
  let step = await clickPanelText(page, candidateText, `${label}-open-by-text`);
  if (!step.ok && fallbackPoint) step = await clickPanelCoordinate(page, fallbackPoint.x, fallbackPoint.y, `${label}-open-by-coordinate`);
  if (!step.ok) return { ok: false, selector: `unable:${label}-open` };
  await page.waitForTimeout(450);
  await page.keyboard.type(value, { delay: 15 });
  await page.waitForTimeout(500);
  await page.keyboard.press('Enter');
  await page.waitForTimeout(700);
  return { ok: true, selector: `${step.selector}+keyboard-select`, value };
}

async function configureFilter(page, result) {
  const filterClick = await clickToolbarButton(page, /\bFilter\b|Filter rows/, 'filter');
  result.steps.push({ action: 'open_filter_panel', ...filterClick });
  if (!filterClick.ok) throw new Error('Could not open Filter panel.');
  await page.waitForTimeout(700);
  result.snapshots.push(await captureSnapshot(page, 'one_view_config_01_filter_panel_before'));
  await clearExistingFilterConditions(page, result);
  await page.waitForTimeout(700);
  result.snapshots.push(await captureSnapshot(page, 'one_view_config_01b_filter_panel_cleared'));

  const add = await clickPanelText(page, /^\+?\s*Add condition$/i, 'add-filter-condition');
  result.steps.push({ action: 'add_filter_condition', ...add });
  if (!add.ok) throw new Error('Could not click Add condition in filter panel.');
  await page.waitForTimeout(900);
  result.snapshots.push(await captureSnapshot(page, 'one_view_config_02_filter_condition_added'));

  const field = await selectDropdownValue(page, /^(Work Item|Select a field|Field|Status)$/i, { x: 520, y: 268 }, 'Status', 'filter-field');
  result.steps.push({ action: 'set_filter_field_status', ...field });
  if (!field.ok) throw new Error('Could not select Status as filter field.');
  result.snapshots.push(await captureSnapshot(page, 'one_view_config_03_filter_field_status'));

  const operator = await selectDropdownValue(page, /^(contains|is|is not|is any of|has any of|is one of)$/i, { x: 660, y: 268 }, 'is any of', 'filter-operator');
  result.steps.push({ action: 'set_filter_operator_is_any_of', ...operator });
  if (!operator.ok) throw new Error('Could not set filter operator to is any of.');
  result.snapshots.push(await captureSnapshot(page, 'one_view_config_04_filter_operator'));

  const valueOpen = await clickPanelText(page, /^(Select an option|Select options|Choose options|Enter a value|active|planned|in_progress)$/i, 'filter-value-open');
  result.steps.push({ action: 'open_filter_value_selector', ...valueOpen });
  if (!valueOpen.ok) throw new Error('Could not open filter value selector.');
  for (const value of filterValuesForView(result.target || {})) {
    await page.waitForTimeout(300);
    await page.keyboard.type(value, { delay: 15 });
    await page.waitForTimeout(500);
    await page.keyboard.press('Enter');
    result.steps.push({ action: 'select_filter_value', value });
  }
  await page.waitForTimeout(900);
  result.snapshots.push(await captureSnapshot(page, 'one_view_config_05_filter_values'));
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(500);
}

async function configureSort(page, result) {
  const sortClick = await clickToolbarButton(page, /\bSort\b|Sort rows/, 'sort');
  result.steps.push({ action: 'open_sort_panel', ...sortClick });
  if (!sortClick.ok) throw new Error('Could not open Sort panel.');
  await page.waitForTimeout(700);
  result.snapshots.push(await captureSnapshot(page, 'one_view_config_06_sort_panel_before'));

  const addSort = await clickPanelText(page, /^\+?\s*(Add sort|Pick another field to sort by)$/i, 'add-sort');
  result.steps.push({ action: 'add_sort_or_field_list_ready', ...addSort });
  if (addSort.ok) await page.waitForTimeout(800);
  else result.steps.push({ action: 'sort_panel_field_list_already_visible', ok: true, note: 'No Add sort control found; Airtable displayed the field picker directly.' });

  let field = await clickPanelText(page, /^Queue Rank$/i, 'sort-field-queue-rank-direct');
  if (!field.ok) field = await selectDropdownValue(page, /^(Pick a field|Select a field|Work Item|Queue Rank)$/i, { x: 510, y: 268 }, 'Queue Rank', 'sort-field');
  result.steps.push({ action: 'set_sort_field_queue_rank', ...field });
  if (!field.ok) throw new Error('Could not select Queue Rank as sort field.');
  await page.waitForTimeout(700);

  const direction = await selectDropdownValue(page, /^(A\s*→\s*Z|1\s*→\s*9|Ascending|asc|Z\s*→\s*A|Descending)$/i, { x: 725, y: 268 }, 'ascending', 'sort-direction');
  result.steps.push({ action: 'set_sort_direction_ascending', ...direction });
  if (!direction.ok) result.steps.push({ action: 'sort_direction_assumed_default_ascending', ok: true, note: 'Airtable number sort defaults to ascending when Queue Rank is selected and no direction selector is visible.' });
  await page.waitForTimeout(900);
  result.snapshots.push(await captureSnapshot(page, 'one_view_config_07_sort_configured'));
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(500);
}

let browser = null;
let context = null;
let page = null;
let closeMode = 'launched';
let rl = null;

async function verifyViewLoaded(page, view) {
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(300);
  const tableClick = await clickFirst(page, [page.getByText(view.table_name, { exact: true }), `[title="${view.table_name.replace(/"/g, '\\"')}"]`, `text="${view.table_name.replace(/"/g, '\\"')}"`], { timeout: 3000 });
  await page.waitForTimeout(900);
  const viewClick = await clickExistingView(page, view.view_name);
  await page.waitForTimeout(1200);
  return { tableClick, viewClick };
}

try {
  log('Starting DCOIR WBS09 one-view config smoke tool.', { version: VERSION });
  if (!args.manifest) throw new Error('Missing --manifest');
  if (!args.executeConfigureOneView) throw new Error('This script only supports --execute-configure-one-view.');
  if (args.confirm !== 'CONFIGURE_WBS09_ONE_VIEW') throw new Error('Configure mode requires --confirm CONFIGURE_WBS09_ONE_VIEW');
  const manifest = JSON.parse(fs.readFileSync(args.manifest, 'utf8'));
  const { views, tables } = validateManifest(manifest);
  const selected = selectViews(views);
  if (selected.length !== 1) throw new Error('One-view configuration requires exactly one selected manifest view. Pass -TableName and -ViewName.');
  const view = selected[0];
  assertSupportedOneView(view);
  const plan = { timestamp_utc: nowIso(), tool_version: VERSION, mode: 'execute_configure_one_view', manifest_view_count: views.length, manifest_table_count: tables.length, selected_view_count: 1, output_dir: outputDir, downloads_env_var: 'DCOIR_DOWNLOADS_DIR', repo_root_env_var: 'DCOIR_REPO_ROOT', base_id: manifest.base_id, base_url: args.baseUrl || `https://airtable.com/${manifest.base_id}`, supported_target_only: true, target: { table_name: view.table_name, table_id: view.table_id, view_name: view.view_name, filters: view.filters || [], sorts: view.sorts || [] } };
  writeJson(path.join(outputDir, 'one_view_config_plan.json'), plan);

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
  const confirm2 = await rl.question('About to configure ONE existing WBS09 Airtable view: Work Items / WBS09 - Active Queue. Type CONFIGURE_WBS09_ONE_VIEW again to proceed: ');
  if (confirm2 !== 'CONFIGURE_WBS09_ONE_VIEW') throw new Error('Second interactive confirmation did not match; stopped before configuration clicks.');

  const report = { timestamp_utc: nowIso(), tool_version: VERSION, mode: 'execute_configure_one_view', target: plan.target, steps: [], snapshots: [], status: 'started' };
  const loaded = await verifyViewLoaded(page, view);
  report.steps.push({ action: 'select_table', ...loaded.tableClick });
  report.steps.push({ action: 'select_view', ...loaded.viewClick });
  if (!loaded.tableClick.ok || !loaded.viewClick.ok) throw new Error('Could not safely select target table/view before configuration.');
  report.snapshots.push(await captureSnapshot(page, 'one_view_config_00_target_loaded'));

  await configureFilter(page, report);
  await configureSort(page, report);
  report.status = 'configuration_clicked_unverified';
  report.completed_at_utc = nowIso();
  report.snapshots.push(await captureSnapshot(page, 'one_view_config_08_final_unverified'));
  writeJson(path.join(outputDir, 'one_view_config_report.json'), report);
  log('One-view configuration branch ended.', { status: report.status, snapshot_count: report.snapshots.length });
  if (closeMode === 'persistent_context') await context.close(); else await browser.close();
  process.exit(0);
} catch (e) {
  const errorReport = { timestamp_utc: nowIso(), error: String(e && e.message ? e.message : e), stack: e && e.stack ? e.stack : null };
  try {
    if (page) {
      errorReport.failure_snapshot = await captureSnapshot(page, 'one_view_config_failure');
    }
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
