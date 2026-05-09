#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import readline from 'node:readline/promises';
import { stdin as input, stdout as output } from 'node:process';

const VERSION = '2026-05-09.draft5-create-new-sidebar-screenshots';

function parseArgs(argv) {
  const args = {
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
    connectCdpUrl: null
  };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    const next = () => argv[++i];
    if (a === '--manifest') args.manifest = next();
    else if (a === '--output-dir') args.outputDir = next();
    else if (a === '--base-url') args.baseUrl = next();
    else if (a === '--dry-run') args.dryRun = true;
    else if (a === '--execute-create-views-only') args.executeCreateViewsOnly = true;
    else if (a === '--experimental-configure-filters') args.experimentalConfigureFilters = true;
    else if (a === '--confirm') args.confirm = next();
    else if (a === '--max-views') args.maxViews = Number(next());
    else if (a === '--table-name') args.tableName = next();
    else if (a === '--enable-screenshots') args.enableScreenshots = true;
    else if (a === '--continue-on-failure') args.stopOnFirstFailure = false;
    else if (a === '--capability-report') args.capabilityReport = true;
    else if (a === '--calibration-mode') args.calibrationMode = true;
    else if (a === '--headless') args.headless = true;
    else if (a === '--use-chrome-channel') args.useChromeChannel = true;
    else if (a === '--user-data-dir') args.userDataDir = next();
    else if (a === '--connect-cdp-url') args.connectCdpUrl = next();
    else throw new Error(`Unknown argument: ${a}`);
  }
  return args;
}

function ensureDir(p) { fs.mkdirSync(p, { recursive: true }); }
function writeJson(p, obj) { fs.writeFileSync(p, JSON.stringify(obj, null, 2), 'utf8'); }
function nowIso() { return new Date().toISOString(); }
function safeName(s) { return String(s).replace(/[^A-Za-z0-9_.-]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 120) || 'item'; }

async function captureFailureScreenshot(page, outputDir, index, view, reason, result) {
  if (!args.enableScreenshots) return;
  const screenshotPath = path.join(
    outputDir,
    `failure_${String(index).padStart(3, '0')}_${safeName(view.table_name)}_${safeName(view.view_name)}_${safeName(reason)}.png`
  );
  await page.screenshot({ path: screenshotPath, fullPage: true });
  result.screenshot = screenshotPath;
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

const args = parseArgs(process.argv);
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

async function fillFirst(page, candidates, value, options = {}) {
  const timeout = options.timeout ?? 2000;
  for (const candidate of candidates) {
    try {
      const loc = typeof candidate === 'string' ? page.locator(candidate).first() : candidate.first();
      if (await loc.count()) {
        await loc.fill(value, { timeout });
        return { ok: true, selector: String(candidate) };
      }
    } catch (_) {}
  }
  return { ok: false };
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

  // Airtable UI is not a stable public API. These selectors are conservative and stop loudly.
  const tableClick = await clickFirst(page, [
    page.getByText(view.table_name, { exact: true }),
    `[title="${view.table_name.replace(/"/g, '\\"')}"]`,
    `text="${view.table_name.replace(/"/g, '\\"')}"`
  ], { timeout: 3000 });
  if (!tableClick.ok) {
    result.status = 'needs_manual_table_selection';
    result.notes.push(`Could not safely click table tab/name: ${view.table_name}. Open that table manually and rerun with -TableName and -MaxViews 1.`);
    await captureFailureScreenshot(page, outputDir, index, view, 'table_selection_not_found', result);
    return result;
  }
  result.notes.push(`Selected table using ${tableClick.selector}`);
  await page.waitForTimeout(800);

  let createNew = { ok: false };
  const gridAlreadyVisible = await page.getByText(/^grid$/i).count().catch(() => 0);
  if (gridAlreadyVisible > 0) {
    createNew = { ok: true, selector: 'grid-menu-already-open' };
    result.notes.push('Create-new menu appears already open; proceeding to Grid selection.');
  } else {
    createNew = await clickFirst(page, [
      page.getByText(/^\s*\+?\s*Create new\.{0,3}\s*$/i),
      page.getByText(/Create new\.\.\./i),
      page.getByText(/Create new/i),
      page.getByRole('button', { name: /create new/i }),
      page.getByRole('button', { name: /add view/i }),
      page.getByText(/add view/i),
      '[aria-label*="Create new"]',
      '[aria-label*="Create"]',
      '[data-testid*="create"]'
    ], { timeout: 3000 });
    if (!createNew.ok) {
      createNew = await clickVisibleTextFallback(page, /\bCreate new\b/, 'Create new visible text', { timeout: 3000 });
    }
  }
  if (!createNew.ok) {
    result.status = 'selector_create_new_not_found';
    result.notes.push('Could not find a safe Create new/Add view control. No view created. Screenshot captured when enabled.');
    await captureFailureScreenshot(page, outputDir, index, view, 'create_new_not_found', result);
    return result;
  }
  if (createNew.selector !== 'grid-menu-already-open') {
    result.notes.push(`Clicked create-new control using ${createNew.selector}`);
    await page.waitForTimeout(800);
  }

  const gridChoice = await clickFirst(page, [
    page.getByText(/^grid$/i),
    page.getByRole('button', { name: /grid/i }),
    page.getByText(/grid view/i),
    '[data-testid*="grid"]'
  ], { timeout: 3000 });
  if (!gridChoice.ok) {
    result.status = 'selector_grid_choice_not_found';
    result.notes.push('Could not choose Grid view safely. No view created.');
    await captureFailureScreenshot(page, outputDir, index, view, 'grid_choice_not_found', result);
    return result;
  }
  result.notes.push(`Selected grid view using ${gridChoice.selector}`);
  await page.waitForTimeout(800);

  const nameFill = await fillFirst(page, [
    page.getByLabel(/view name/i),
    page.getByPlaceholder(/view name/i),
    page.getByPlaceholder(/name/i),
    'input[type="text"]'
  ], view.view_name, { timeout: 3000 });
  if (!nameFill.ok) {
    result.status = 'selector_view_name_input_not_found';
    result.notes.push('Could not find view-name input safely. No create confirmation clicked.');
    await captureFailureScreenshot(page, outputDir, index, view, 'view_name_input_not_found', result);
    return result;
  }
  result.notes.push(`Filled view name using ${nameFill.selector}`);
  await page.waitForTimeout(500);

  const finalCreate = await clickFirst(page, [
    page.getByRole('button', { name: /^create$/i }),
    page.getByRole('button', { name: /create view/i }),
    page.getByRole('button', { name: /create new view/i }),
    page.getByRole('button', { name: /create grid view/i }),
    page.getByRole('button', { name: /create .*view/i }),
    page.locator('button:has-text("Create new view")'),
    page.locator('button:has-text("Create grid view")'),
    page.locator('button:has-text("Create view")'),
    page.locator('button:has-text("Create")'),
    page.getByText(/^create$/i),
    page.getByText(/create view/i),
    page.getByText(/create new view/i),
    page.getByText(/create grid view/i)
  ], { timeout: 3000 });
  if (!finalCreate.ok) {
    result.status = 'selector_final_create_not_found';
    result.notes.push('Could not find final Create button safely. View name may be staged in UI but create was not clicked.');
    if (args.enableScreenshots) {
      const screenshotPath = path.join(outputDir, `failure_${String(index).padStart(3, '0')}_${safeName(view.table_name)}_${safeName(view.view_name)}_final_create_not_found.png`);
      await page.screenshot({ path: screenshotPath, fullPage: true });
      result.screenshot = screenshotPath;
    }
    return result;
  }
  result.status = 'create_clicked_unverified';
  result.notes.push(`Clicked final create using ${finalCreate.selector}. Verify in Airtable before continuing.`);
  await page.waitForTimeout(1200);

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
      filters_and_sorts: 'not configured in draft execution; view creation only',
      known_risk: 'Airtable UI selectors may drift; execute one view first and verify before bulk run.'
    });
  }

  if (!args.executeCreateViewsOnly && !args.calibrationMode) {
    log('Dry run complete. No browser opened and no Airtable mutation attempted.');
    process.exit(0);
  }
  if (args.experimentalConfigureFilters) throw new Error('Filter/sort UI automation is intentionally blocked in draft2. Create views first; configure filters manually or approve a selector-calibrated follow-up.');
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
    log('Connecting to existing Chrome over CDP. Use only with a dedicated operator-approved Chrome session.', { connect_cdp_url: args.connectCdpUrl });
    browser = await chromium.connectOverCDP(args.connectCdpUrl);
    context = browser.contexts()[0];
    if (!context) throw new Error('CDP connection succeeded but no browser context was available. Start Chrome with --remote-debugging-port and a dedicated --user-data-dir.');
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
    browser = await chromium.launch({
      headless: Boolean(args.headless),
      channel: args.useChromeChannel ? 'chrome' : undefined
    });
    context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    page = await context.newPage();
  }

  await page.goto(baseUrl, { waitUntil: 'domcontentloaded' });

  const rl = readline.createInterface({ input, output });
  await rl.question('Log into Airtable, confirm the DCOIR base is open, then press Enter. Ctrl+C aborts before any create click. ');

  if (args.calibrationMode) {
    const calibration = {
      timestamp_utc: nowIso(),
      url: page.url(),
      title: await page.title(),
      note: 'Calibration mode opened Airtable and recorded page metadata only. No view creation attempted.'
    };
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
  if (closeMode === 'persistent_context') await context.close();
  else await browser.close();
  const failures = results.filter(r => r.status !== 'create_clicked_unverified');
  log('Execution branch ended.', { result_count: results.length, failure_count: failures.length });
  process.exit(failures.length ? 1 : 0);
} catch (e) {
  const errorReport = { timestamp_utc: nowIso(), error: String(e && e.message ? e.message : e), stack: e && e.stack ? e.stack : null };
  try { writeJson(path.join(outputDir, 'error_report.json'), errorReport); } catch {}
  console.error(errorReport.error);
  process.exit(1);
}
