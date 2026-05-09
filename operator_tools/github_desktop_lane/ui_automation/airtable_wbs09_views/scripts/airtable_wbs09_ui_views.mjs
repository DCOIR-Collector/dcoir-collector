#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import readline from 'node:readline/promises';
import { stdin as input, stdout as output } from 'node:process';

const VERSION = '2026-05-09.draft7-sidebar-geometry-create-flow';
let args;

function parseArgs(argv) {
  const parsed = {
    dryRun: false,
    executeCreateViewsOnly: false,
    experimentalConfigureFilters: false,
    enableScreenshots: false,
    stopOnFirstFailure: true,
    capabilityReport: false,
    calibrationMode: false,
    headless: false,
    useChromeChannel: false,
    userDataDir: null,
    connectCdpUrl: null,
    keepBrowserOpenOnFailure: false
  };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    const next = () => argv[++i];
    if (a === '--manifest') parsed.manifest = next();
    else if (a === '--output-dir') parsed.outputDir = next();
    else if (a === '--base-url') parsed.baseUrl = next();
    else if (a === '--dry-run') parsed.dryRun = true;
    else if (a === '--execute-create-views-only') parsed.executeCreateViewsOnly = true;
    else if (a === '--experimental-configure-filters') parsed.experimentalConfigureFilters = true;
    else if (a === '--confirm') parsed.confirm = next();
    else if (a === '--max-views') parsed.maxViews = Number(next());
    else if (a === '--table-name') parsed.tableName = next();
    else if (a === '--enable-screenshots') parsed.enableScreenshots = true;
    else if (a === '--continue-on-failure') parsed.stopOnFirstFailure = false;
    else if (a === '--capability-report') parsed.capabilityReport = true;
    else if (a === '--calibration-mode') parsed.calibrationMode = true;
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
  const keys = new Set();
  for (const view of views) {
    for (const required of ['table_name', 'table_id', 'view_name', 'view_type']) {
      if (!view[required]) throw new Error(`Manifest view missing ${required}: ${JSON.stringify(view)}`);
    }
    const key = `${view.table_name}::${view.view_name}`;
    if (keys.has(key)) throw new Error(`Duplicate manifest view key: ${key}`);
    keys.add(key);
  }
  return { views, tables };
}

function selectViews(views) {
  let selected = views;
  if (args.tableName) selected = selected.filter(v => v.table_name.toLowerCase() === args.tableName.toLowerCase());
  if (args.maxViews && args.maxViews > 0) selected = selected.slice(0, args.maxViews);
  return selected;
}

async function clickFirst(page, candidates, options = {}) {
  const timeout = options.timeout ?? 2000;
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

async function getVisibleDomSnapshot(page) {
  return await page.evaluate(() => {
    const elements = Array.from(document.querySelectorAll('button, [role="button"], input, textarea, [aria-label], [placeholder], div, span, a')).slice(0, 2500);
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
        text: (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 300),
        x: Math.round(box.x),
        y: Math.round(box.y),
        w: Math.round(box.width),
        h: Math.round(box.height)
      };
    }).filter(x => x.text || x.aria || x.placeholder || x.role || x.type).slice(0, 700);
  });
}

async function captureDomEvidence(page, outputDir, index, view, reason, result) {
  const base = `failure_${String(index).padStart(3, '0')}_${safeName(view.table_name)}_${safeName(view.view_name)}_${safeName(reason)}`;
  if (args.enableScreenshots) {
    const screenshotPath = path.join(outputDir, `${base}.png`);
    await page.screenshot({ path: screenshotPath, fullPage: true });
    result.screenshot = screenshotPath;
  }
  const dom = await getVisibleDomSnapshot(page);
  const domPath = path.join(outputDir, `${base}.dom.json`);
  writeJson(domPath, { timestamp_utc: nowIso(), reason, url: page.url(), title: await page.title(), elements: dom });
  result.dom_evidence = domPath;
}

async function clickVisibleTextFallback(page, pattern, label, options = {}) {
  const timeout = options.timeout ?? 3000;
  const handle = await page.evaluateHandle((source) => {
    const re = new RegExp(source, 'i');
    const elements = Array.from(document.querySelectorAll('button, [role="button"], div, span, a'));
    function visible(el) {
      const style = window.getComputedStyle(el);
      const box = el.getBoundingClientRect();
      return style && style.visibility !== 'hidden' && style.display !== 'none' && box.width > 0 && box.height > 0;
    }
    for (const el of elements) {
      const text = (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim();
      if (visible(el) && re.test(text)) return el;
    }
    return null;
  }, pattern.source);
  const el = handle.asElement();
  if (!el) return { ok: false };
  await el.click({ timeout });
  return { ok: true, selector: `visible-text-fallback:${label}` };
}

async function clickSidebarCreateNew(page) {
  const picked = await page.evaluate(() => {
    function visible(el) {
      const style = window.getComputedStyle(el);
      const box = el.getBoundingClientRect();
      return style && style.visibility !== 'hidden' && style.display !== 'none' && box.width > 0 && box.height > 0;
    }
    const candidates = Array.from(document.querySelectorAll('button, [role="button"]')).map((el) => {
      const box = el.getBoundingClientRect();
      const text = (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim();
      return { el, text, x: box.x, y: box.y, w: box.width, h: box.height };
    }).filter((c) => {
      return visible(c.el)
        && /^\+?\s*Create new\.{0,3}\s*$/i.test(c.text)
        && c.x >= 40 && c.x < 360
        && c.y >= 120
        && c.w >= 80;
    }).sort((a, b) => a.y - b.y || a.x - b.x);
    const c = candidates[0];
    if (!c) return null;
    c.el.scrollIntoView({ block: 'center', inline: 'center' });
    c.el.click();
    return { selector: 'geometry:sidebar-create-new-button', text: c.text, x: Math.round(c.x), y: Math.round(c.y), w: Math.round(c.w), h: Math.round(c.h) };
  });
  return picked ? { ok: true, ...picked } : { ok: false };
}

async function clickGridOptionFromCreateMenu(page) {
  const picked = await page.evaluate(() => {
    function visible(el) {
      const style = window.getComputedStyle(el);
      const box = el.getBoundingClientRect();
      return style && style.visibility !== 'hidden' && style.display !== 'none' && box.width > 0 && box.height > 0;
    }
    function clickableAncestor(el) {
      let cur = el;
      for (let i = 0; cur && i < 5; i += 1) {
        const tag = cur.tagName;
        const role = cur.getAttribute('role');
        if (tag === 'BUTTON' || tag === 'A' || role === 'button' || cur.onclick) return cur;
        cur = cur.parentElement;
      }
      return el;
    }
    const nodes = Array.from(document.querySelectorAll('button, [role="button"], div, span, a'));
    const candidates = nodes.map((el) => {
      const box = el.getBoundingClientRect();
      const text = (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim();
      return { el, text, x: box.x, y: box.y, w: box.width, h: box.height };
    }).filter((c) => {
      return visible(c.el)
        && /^Grid$/i.test(c.text)
        && c.x >= 40 && c.x < 520
        && c.y >= 160
        && c.w > 8 && c.h > 8;
    }).sort((a, b) => a.y - b.y || a.x - b.x);
    const c = candidates[0];
    if (!c) return null;
    const target = clickableAncestor(c.el);
    const targetBox = target.getBoundingClientRect();
    target.click();
    return { selector: 'geometry:create-menu-grid-option', text: c.text, x: Math.round(c.x), y: Math.round(c.y), w: Math.round(c.w), h: Math.round(c.h), target_x: Math.round(targetBox.x), target_y: Math.round(targetBox.y), target_w: Math.round(targetBox.width), target_h: Math.round(targetBox.height) };
  });
  return picked ? { ok: true, ...picked } : { ok: false };
}

async function fillNewViewNameInput(page, viewName) {
  const handle = await page.evaluateHandle(() => {
    function visible(el) {
      const style = window.getComputedStyle(el);
      const box = el.getBoundingClientRect();
      return style && style.visibility !== 'hidden' && style.display !== 'none' && box.width > 0 && box.height > 0;
    }
    const inputs = Array.from(document.querySelectorAll('input, textarea')).map((el) => {
      const box = el.getBoundingClientRect();
      const aria = el.getAttribute('aria-label') || '';
      const placeholder = el.getAttribute('placeholder') || '';
      const type = el.getAttribute('type') || '';
      return { el, aria, placeholder, type, x: box.x, y: box.y, w: box.width, h: box.height };
    }).filter((c) => {
      const label = `${c.aria} ${c.placeholder}`;
      if (!visible(c.el)) return false;
      if (/find a view/i.test(label)) return false;
      if (c.type && !/^(text|search)$/i.test(c.type)) return false;
      return c.w >= 40 && c.h >= 16;
    }).sort((a, b) => {
      const scoreA = (/view name|name/i.test(`${a.aria} ${a.placeholder}`) ? 0 : 1);
      const scoreB = (/view name|name/i.test(`${b.aria} ${b.placeholder}`) ? 0 : 1);
      return scoreA - scoreB || a.y - b.y || a.x - b.x;
    });
    const c = inputs[0];
    return c ? c.el : null;
  });
  const el = handle.asElement();
  if (!el) return { ok: false };
  const box = await el.boundingBox();
  await el.click({ timeout: 3000 });
  const modifier = process.platform === 'darwin' ? 'Meta' : 'Control';
  await page.keyboard.press(`${modifier}+A`);
  await page.keyboard.type(viewName, { delay: 10 });
  return { ok: true, selector: 'geometry:new-view-name-input-excluding-find-view', x: box ? Math.round(box.x) : null, y: box ? Math.round(box.y) : null, w: box ? Math.round(box.width) : null, h: box ? Math.round(box.height) : null };
}

async function clickFinalCreateButton(page) {
  const picked = await page.evaluate(() => {
    function visible(el) {
      const style = window.getComputedStyle(el);
      const box = el.getBoundingClientRect();
      return style && style.visibility !== 'hidden' && style.display !== 'none' && box.width > 0 && box.height > 0;
    }
    const buttons = Array.from(document.querySelectorAll('button, [role="button"]')).map((el) => {
      const box = el.getBoundingClientRect();
      const text = (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim();
      const aria = el.getAttribute('aria-label') || '';
      const disabled = el.disabled || el.getAttribute('aria-disabled') === 'true';
      return { el, text, aria, disabled, x: box.x, y: box.y, w: box.width, h: box.height };
    }).filter((c) => {
      const label = `${c.text} ${c.aria}`.trim();
      if (!visible(c.el) || c.disabled) return false;
      if (/^\+?\s*Create new\.{0,3}$/i.test(label)) return false;
      if (/Create new\.{0,3}\s+No matching views/i.test(label)) return false;
      return /^(Create|Create view|Create new view|Create grid view)$/i.test(c.text)
        || /Create view|Create new view|Create grid view/i.test(c.aria);
    }).sort((a, b) => b.y - a.y || b.x - a.x);
    const c = buttons[0];
    if (!c) return null;
    c.el.click();
    return { selector: 'geometry:final-create-button', text: c.text, aria: c.aria, x: Math.round(c.x), y: Math.round(c.y), w: Math.round(c.w), h: Math.round(c.h) };
  });
  if (picked) return { ok: true, ...picked };
  return await clickVisibleTextFallback(page, /\bCreate (new |grid )?view\b|^Create$/i, 'final create visible text', { timeout: 3000 });
}

async function createGridViewAttempt(page, view, outputDir, index) {
  const result = {
    index,
    table_name: view.table_name,
    table_id: view.table_id,
    view_name: view.view_name,
    status: 'started',
    attempted_at_utc: nowIso(),
    notes: []
  };

  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(250);
  await page.mouse.move(520, 90).catch(() => {});

  const tableClick = await clickFirst(page, [
    page.getByText(view.table_name, { exact: true }),
    `[title="${view.table_name.replace(/"/g, '\\"')}"]`,
    `text="${view.table_name.replace(/"/g, '\\"')}"`
  ], { timeout: 3000 });
  if (!tableClick.ok) {
    result.status = 'needs_manual_table_selection';
    result.notes.push(`Could not safely click table tab/name: ${view.table_name}.`);
    await captureDomEvidence(page, outputDir, index, view, 'table_selection_not_found', result);
    return result;
  }
  result.notes.push(`Selected table using ${tableClick.selector}`);
  await page.waitForTimeout(800);
  await page.keyboard.press('Escape').catch(() => {});
  await page.mouse.move(520, 90).catch(() => {});

  const createNew = await clickSidebarCreateNew(page);
  if (!createNew.ok) {
    result.status = 'selector_create_new_not_found';
    result.notes.push('Could not find the left-sidebar Create new... button.');
    await captureDomEvidence(page, outputDir, index, view, 'create_new_not_found', result);
    return result;
  }
  result.notes.push(`Clicked create-new control using ${createNew.selector} at x=${createNew.x}, y=${createNew.y}.`);
  await page.waitForTimeout(900);
  await page.mouse.move(520, 90).catch(() => {});

  const gridChoice = await clickGridOptionFromCreateMenu(page);
  if (!gridChoice.ok) {
    result.status = 'selector_grid_choice_not_found';
    result.notes.push('Could not choose Grid from the create-new popup without touching the current Grid view control.');
    await captureDomEvidence(page, outputDir, index, view, 'grid_choice_not_found', result);
    return result;
  }
  result.notes.push(`Selected create-menu Grid option using ${gridChoice.selector} at x=${gridChoice.x}, y=${gridChoice.y}.`);
  await page.waitForTimeout(1000);
  await page.mouse.move(520, 90).catch(() => {});

  const nameFill = await fillNewViewNameInput(page, view.view_name);
  if (!nameFill.ok) {
    result.status = 'selector_view_name_input_not_found';
    result.notes.push('Could not find a new-view name input. The Find a view search box is intentionally excluded.');
    await captureDomEvidence(page, outputDir, index, view, 'view_name_input_not_found', result);
    return result;
  }
  result.notes.push(`Filled view name using ${nameFill.selector} at x=${nameFill.x}, y=${nameFill.y}.`);
  await page.waitForTimeout(800);

  const finalCreate = await clickFinalCreateButton(page);
  if (!finalCreate.ok) {
    result.status = 'selector_final_create_not_found';
    result.notes.push('Could not find final Create/Create view button safely. View name may be staged in UI but create was not clicked.');
    await captureDomEvidence(page, outputDir, index, view, 'final_create_not_found', result);
    return result;
  }
  result.status = 'create_clicked_unverified';
  result.notes.push(`Clicked final create using ${finalCreate.selector}. Verify in Airtable before continuing.`);
  await page.waitForTimeout(1500);

  if (args.enableScreenshots) {
    const screenshotPath = path.join(outputDir, `after_${String(index).padStart(3, '0')}_${safeName(view.table_name)}_${safeName(view.view_name)}.png`);
    await page.screenshot({ path: screenshotPath, fullPage: true });
    result.screenshot = screenshotPath;
  }
  return result;
}

try {
  log('Starting DCOIR WBS09 Airtable UI view tool.', { version: VERSION });
  if (!args.manifest) throw new Error('Missing --manifest');
  const manifest = JSON.parse(fs.readFileSync(args.manifest, 'utf8'));
  const { views, tables } = validateManifest(manifest);
  const selected = selectViews(views);
  const summary = {
    timestamp_utc: nowIso(),
    tool_version: VERSION,
    mode: args.executeCreateViewsOnly ? 'execute_create_views_only' : (args.calibrationMode ? 'calibration' : 'dry_run'),
    manifest_view_count: views.length,
    manifest_table_count: tables.length,
    selected_view_count: selected.length,
    output_dir: outputDir,
    downloads_env_var: 'DCOIR_DOWNLOADS_DIR',
    repo_root_env_var: 'DCOIR_REPO_ROOT',
    base_id: manifest.base_id,
    base_url: args.baseUrl || `https://airtable.com/${manifest.base_id}`,
    dry_run: !args.executeCreateViewsOnly,
    experimental_configure_filters: Boolean(args.experimentalConfigureFilters),
    keep_browser_open_on_failure: Boolean(args.keepBrowserOpenOnFailure),
    views: selected.map(v => ({ table_name: v.table_name, table_id: v.table_id, view_name: v.view_name, view_type: v.view_type, filter_count: (v.filters || []).length, sort_count: (v.sorts || []).length }))
  };
  writeJson(path.join(outputDir, args.executeCreateViewsOnly ? 'execution_plan.json' : 'dry_run_report.json'), summary);
  log('Validated manifest and wrote plan.', { selected_view_count: selected.length });

  if (args.capabilityReport) {
    writeJson(path.join(outputDir, 'capability_report.json'), {
      timestamp_utc: nowIso(),
      node_version: process.version,
      playwright_required_for_execute: true,
      dry_run_requires_browser: false,
      execution_requires_confirm: 'CREATE_WBS09_NATIVE_VIEWS',
      filters_and_sorts: 'not configured in this draft; view creation only',
      known_risk: 'Airtable UI selectors may drift; execute one view first and verify before bulk run.'
    });
  }

  if (!args.executeCreateViewsOnly && !args.calibrationMode) {
    log('Dry run complete. No browser opened and no Airtable mutation attempted.');
    process.exit(0);
  }
  if (args.experimentalConfigureFilters) throw new Error('Filter/sort UI automation is intentionally blocked in this draft. Create views first; configure filters only after explicit selector-calibrated approval.');
  if (args.executeCreateViewsOnly && args.confirm !== 'CREATE_WBS09_NATIVE_VIEWS') throw new Error('Execute mode requires --confirm CREATE_WBS09_NATIVE_VIEWS');

  let chromium;
  try { ({ chromium } = await import('playwright')); }
  catch { throw new Error('Playwright is required. Run the installer script first: Install-DcoirAirtableWbs09UiViewPrereqs.ps1'); }

  const baseUrl = args.baseUrl || `https://airtable.com/${manifest.base_id}`;
  let browser = null;
  let context = null;
  let page = null;
  let closeMode = 'launched';

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
    context = await chromium.launchPersistentContext(args.userDataDir, {
      headless: Boolean(args.headless),
      channel: args.useChromeChannel ? 'chrome' : undefined,
      viewport: { width: 1440, height: 1000 }
    });
    browser = context.browser();
    page = context.pages()[0] || await context.newPage();
  } else {
    log('Launching browser context.', { chrome_channel: Boolean(args.useChromeChannel) });
    browser = await chromium.launch({ headless: Boolean(args.headless), channel: args.useChromeChannel ? 'chrome' : undefined });
    context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    page = await context.newPage();
  }

  await page.goto(baseUrl, { waitUntil: 'domcontentloaded' });
  const rl = readline.createInterface({ input, output });
  await rl.question('Log into Airtable, confirm the DCOIR base is open, then press Enter. Ctrl+C aborts before any create click. ');

  if (args.calibrationMode) {
    const calibration = { timestamp_utc: nowIso(), url: page.url(), title: await page.title(), note: 'Calibration mode opened Airtable and recorded page metadata only. No view creation attempted.' };
    if (args.enableScreenshots) {
      const screenshotPath = path.join(outputDir, 'calibration_page.png');
      await page.screenshot({ path: screenshotPath, fullPage: true });
      calibration.screenshot = screenshotPath;
    }
    writeJson(path.join(outputDir, 'calibration_report.json'), calibration);
    if (closeMode === 'persistent_context') await context.close();
    else await browser.close();
    log('Calibration complete. No Airtable mutation attempted.');
    process.exit(0);
  }

  const confirm2 = await rl.question(`About to attempt ${selected.length} native Airtable grid view create action(s), one at a time. Type CREATE_WBS09_NATIVE_VIEWS again to proceed: `);
  if (confirm2 !== 'CREATE_WBS09_NATIVE_VIEWS') throw new Error('Second interactive confirmation did not match; stopped before create-clicks.');

  const results = [];
  let index = 0;
  for (const view of selected) {
    index += 1;
    log('Starting create attempt.', { index, table: view.table_name, view: view.view_name });
    const result = await createGridViewAttempt(page, view, outputDir, index);
    results.push(result);
    writeJson(path.join(outputDir, 'execution_report.partial.json'), { timestamp_utc: nowIso(), results });
    log('Create attempt result.', result);
    if (result.status !== 'create_clicked_unverified' && args.stopOnFirstFailure) break;
  }
  writeJson(path.join(outputDir, 'execution_report.json'), { timestamp_utc: nowIso(), results });
  const failures = results.filter(r => r.status !== 'create_clicked_unverified');
  if (failures.length && args.keepBrowserOpenOnFailure) {
    writeJson(path.join(outputDir, 'keep_open_failure_report.json'), { timestamp_utc: nowIso(), reason: 'failure_detected', failure_count: failures.length, results });
    await rl.question('Failure detected. Browser will remain open for inspection. Press Enter in PowerShell only after you finish inspecting/uploading screenshots. ');
  }
  if (closeMode === 'persistent_context') await context.close();
  else await browser.close();
  log('Execution branch ended.', { result_count: results.length, failure_count: failures.length });
  process.exit(failures.length ? 1 : 0);
} catch (e) {
  const errorReport = { timestamp_utc: nowIso(), error: String(e && e.message ? e.message : e), stack: e && e.stack ? e.stack : null };
  try { writeJson(path.join(outputDir, 'error_report.json'), errorReport); } catch {}
  console.error(errorReport.error);
  process.exit(1);
}
