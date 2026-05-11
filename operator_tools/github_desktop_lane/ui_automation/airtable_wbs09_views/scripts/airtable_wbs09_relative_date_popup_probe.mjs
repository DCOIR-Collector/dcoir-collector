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
  openAirtablePanel,
  closeOpenAirtablePanel,
  extractOpenAirtablePanel
} from '../../shared/dcoir_airtable_panel_readback.mjs';

const TOOL_VERSION = '2026-05-10.wbs09-relative-date-popup-probe.1';

function parseArgs(argv) {
  const parsed = { enableScreenshots: false, headless: false, useChromeChannel: false, userDataDir: null, connectCdpUrl: null, keepBrowserOpenOnFailure: false, targetKeys: [], fieldName: 'review_after' };
  for (let i = 2; i < argv.length; i += 1) {
    const a = argv[i];
    const next = () => argv[++i];
    if (a === '--manifest') parsed.manifest = next();
    else if (a === '--output-dir') parsed.outputDir = next();
    else if (a === '--base-url') parsed.baseUrl = next();
    else if (a === '--target-key') parsed.targetKeys.push(next());
    else if (a === '--field-name') parsed.fieldName = next();
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
  return String(value || '').replace(/[\u2192\u27f6\u2794]/g, ' -> ').replace(/[\u2026]/g, '...').replace(/\s+/g, ' ').trim();
}
function lowerText(value) { return normalizeText(value).toLowerCase(); }
function fieldToken(value) { return lowerText(value).replace(/\s+/g, '_'); }

function chooseValueControlPoint(panelState, fieldName) {
  const wanted = fieldToken(fieldName);
  const rows = Array.isArray(panelState?.rows) ? panelState.rows : [];
  const row = rows.find((candidate) => {
    const text = lowerText(`${candidate?.text || ''} ${Object.values(candidate?.cells || {}).join(' ')}`);
    return text.includes(wanted) && /before|after|exact date|today|week|month|date|gmt|cest/.test(text);
  });
  if (!row) return null;
  const elements = Array.isArray(row.elements) ? row.elements : [];
  const buttons = elements
    .filter((element) => String(element.role || '').toLowerCase() === 'button')
    .filter((element) => !/remove item|reorder item/i.test(`${element.text || ''} ${element.aria || ''}`))
    .map((element) => ({
      x: Number(element.cx ?? (Number(element.x || 0) + Number(element.w || 0) / 2)),
      y: Number(element.cy ?? (Number(element.y || 0) + Number(element.h || 0) / 2)),
      source: element,
      text: lowerText(`${element.text || ''} ${element.aria || ''}`)
    }))
    .sort((a, b) => a.x - b.x);
  const valueButton = buttons.find((button) => /exact date|today|tomorrow|yesterday|week|month|days/.test(button.text))
    || buttons.find((button) => button.x > 600)
    || null;
  if (valueButton) return { ...valueButton, row };
  const panel = panelState.panel || { x: 285, y: 129 };
  return { x: Number(panel.x || 285) + 390, y: Number(row.y || Number(panel.y || 129) + 140), source: { fallback: true }, row };
}

async function collectPopupDiagnostics(page, label, outputDir, screenshotOptions = {}) {
  const diagnostic = await page.evaluate(() => {
    const normalize = (s) => String(s || '').replace(/[\u2192\u27f6\u2794]/g, ' -> ').replace(/[\u2026]/g, '...').replace(/\s+/g, ' ').trim();
    function visible(el) {
      const style = window.getComputedStyle(el);
      const box = el.getBoundingClientRect();
      return style && style.visibility !== 'hidden' && style.display !== 'none' && box.width > 0 && box.height > 0;
    }
    function rectObj(box) { return { x: Math.round(box.x), y: Math.round(box.y), w: Math.round(box.width), h: Math.round(box.height), right: Math.round(box.right), bottom: Math.round(box.bottom) }; }
    function elementInfo(el) {
      const box = el.getBoundingClientRect();
      const cx = Math.round(box.x + box.width / 2);
      const cy = Math.round(box.y + box.height / 2);
      const top = document.elementFromPoint(Math.max(0, Math.min(window.innerWidth - 1, cx)), Math.max(0, Math.min(window.innerHeight - 1, cy)));
      const rawText = String(el.innerText || el.textContent || '');
      const lines = rawText.split(/\n+/).map((line) => normalize(line)).filter(Boolean);
      return {
        tag: el.tagName,
        role: el.getAttribute('role') || '',
        aria: normalize(el.getAttribute('aria-label') || ''),
        className: String(el.className || '').slice(0, 300),
        testId: el.getAttribute('data-testid') || '',
        rect: rectObj(box),
        scrollTop: Math.round(el.scrollTop || 0),
        scrollHeight: Math.round(el.scrollHeight || 0),
        clientHeight: Math.round(el.clientHeight || 0),
        text: normalize(rawText).slice(0, 1000),
        lines: lines.slice(0, 40),
        lineCount: lines.length,
        topAtCenter: top ? { tag: top.tagName, role: top.getAttribute('role') || '', text: normalize(top.innerText || top.textContent || top.getAttribute('aria-label') || '').slice(0, 240), className: String(top.className || '').slice(0, 160) } : null,
        outerHTML: String(el.outerHTML || '').slice(0, 12000)
      };
    }
    const needleText = /today|tomorrow|yesterday|one week ago|one week from now|one month ago|exact date|number of days/i;
    const popupCandidates = Array.from(document.querySelectorAll('select, option, [role="listbox"], [role="option"], [role="menu"], [role="menuitem"], [data-testid], [class], div, span, button'))
      .filter(visible)
      .filter((el) => {
        const box = el.getBoundingClientRect();
        if (box.width < 8 || box.height < 8) return false;
        const text = normalize(el.innerText || el.textContent || el.getAttribute('aria-label') || '');
        if (!needleText.test(text)) return false;
        if (/help \/ quick tips|sort records|filter records|learn more about/i.test(text)) return false;
        return true;
      })
      .map(elementInfo)
      .sort((a, b) => {
        const ar = ['listbox', 'menu', 'option', 'menuitem'].includes(String(a.role || '').toLowerCase()) ? 0 : 1;
        const br = ['listbox', 'menu', 'option', 'menuitem'].includes(String(b.role || '').toLowerCase()) ? 0 : 1;
        const areaA = a.rect.w * a.rect.h;
        const areaB = b.rect.w * b.rect.h;
        return ar - br || areaA - areaB || a.rect.y - b.rect.y || a.rect.x - b.rect.x;
      })
      .slice(0, 80);

    const nativeSelects = Array.from(document.querySelectorAll('select'))
      .filter(visible)
      .map((el) => ({ ...elementInfo(el), options: Array.from(el.options || []).map((option) => ({ text: normalize(option.textContent || ''), value: option.value, selected: option.selected })) }));

    const active = document.activeElement;
    return {
      viewport: { width: window.innerWidth, height: window.innerHeight },
      url: location.href,
      title: document.title,
      activeElement: active ? elementInfo(active) : null,
      nativeSelects,
      popupCandidates
    };
  });
  writeJson(path.join(outputDir, `${safeName(label)}_popup_diagnostics.json`), diagnostic);
  const htmlParts = [];
  htmlParts.push(`<!-- ${label} scoped popup candidates generated ${nowIso()} -->`);
  for (const [i, candidate] of diagnostic.popupCandidates.entries()) {
    htmlParts.push(`\n<!-- candidate ${i} role=${candidate.role} rect=${JSON.stringify(candidate.rect)} scrollTop=${candidate.scrollTop} scrollHeight=${candidate.scrollHeight} clientHeight=${candidate.clientHeight} -->`);
    htmlParts.push(candidate.outerHTML || '');
  }
  fs.writeFileSync(path.join(outputDir, `${safeName(label)}_scoped_popup_outerhtml.html`), htmlParts.join('\n'), 'utf8');
  await captureDomEvidence(page, outputDir, `${safeName(label)}_popup_open`, screenshotOptions);
  return diagnostic;
}

const args = parseArgs(process.argv);
const downloads = process.env.DCOIR_DOWNLOADS_DIR;
if (!downloads || !downloads.trim()) {
  console.error('Missing required Local Configuration Registry variable: DCOIR_DOWNLOADS_DIR');
  process.exit(2);
}
const outputDir = args.outputDir || path.join(downloads, `dcoir_wbs09_relative_date_popup_probe_${new Date().toISOString().replace(/[:.]/g, '')}`);
ensureDir(outputDir);
const logPath = path.join(outputDir, 'relative_date_popup_probe.log');
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
    context = await chromium.launchPersistentContext(args.userDataDir, { headless: args.headless, channel: args.useChromeChannel ? 'chrome' : undefined, viewport: { width: 1600, height: 1000 } });
    page = context.pages()[0] || await context.newPage();
    closeMode = 'persistent';
  } else {
    browser = await chromium.launch({ headless: args.headless, channel: args.useChromeChannel ? 'chrome' : undefined });
    context = await browser.newContext({ viewport: { width: 1600, height: 1000 } });
    page = await context.newPage();
  }
  await page.goto(baseUrl, { waitUntil: 'domcontentloaded', timeout: 90000 }).catch(() => {});
  await page.waitForLoadState('domcontentloaded', { timeout: 30000 }).catch(() => {});
  return page;
}

async function main() {
  log('Starting DCOIR WBS09 relative-date popup probe.', { version: TOOL_VERSION, readback_version: AIRTABLE_PANEL_READBACK_VERSION, field_name: args.fieldName });
  const manifest = readJsonFile(args.manifest);
  const targets = selectManifestTargets(manifest, { targetKeys: args.targetKeys.length ? args.targetKeys : ['Operator Tools Registry::WBS09 - Validation Due'] });
  if (targets.length !== 1) throw new Error(`Expected exactly one target, found ${targets.length}.`);
  const target = targets[0];
  const baseUrl = args.baseUrl || `https://airtable.com/${target.base_id || 'appM4KSwnVf3G3OTK'}/${target.table_id || ''}/${target.view_id || ''}?blocks=hide`;
  page = await openBrowser(baseUrl);
  await safeMousePark(page).catch(() => {});
  rl = readline.createInterface({ input, output });
  await rl.question('Read-only popup probe: log into Airtable, confirm the DCOIR base is open, then press Enter. Ctrl+C aborts.');
  await selectAirtableTableAndView(page, target, { outputDir, screenshotOptions: { fullPage: false } });
  await page.waitForTimeout(900).catch(() => {});
  await openAirtablePanel(page, 'filter');
  await page.waitForTimeout(700).catch(() => {});
  const panelState = await extractOpenAirtablePanel(page, 'filter');
  writeJson(path.join(outputDir, 'filter_panel_before_popup.json'), panelState);
  await captureDomEvidence(page, outputDir, 'filter_panel_before_popup', { fullPage: false });
  const point = chooseValueControlPoint(panelState, args.fieldName);
  if (!point) throw new Error(`Could not locate value control for field ${args.fieldName}.`);
  writeJson(path.join(outputDir, 'value_control_point.json'), { point });
  await page.mouse.click(Math.round(point.x), Math.round(point.y));
  await page.waitForTimeout(800).catch(() => {});
  const before = await collectPopupDiagnostics(page, 'relative_date_popup_before_scroll', outputDir, { fullPage: false });

  // Read-only scroll probe: emulate the operator's mouse-wheel observation without clicking any option.
  const candidate = before.popupCandidates?.[0];
  if (candidate?.rect) {
    const wheelX = Math.round(candidate.rect.x + Math.min(candidate.rect.w - 8, Math.max(8, candidate.rect.w * 0.55)));
    const wheelY = Math.round(candidate.rect.y + Math.min(candidate.rect.h - 8, Math.max(8, candidate.rect.h * 0.5)));
    await page.mouse.move(wheelX, wheelY).catch(() => {});
    await page.mouse.wheel(0, -900).catch(() => {});
    await page.waitForTimeout(500).catch(() => {});
    writeJson(path.join(outputDir, 'wheel_probe_point.json'), { x: wheelX, y: wheelY, source_candidate_rect: candidate.rect, delta_y: -900 });
    await collectPopupDiagnostics(page, 'relative_date_popup_after_wheel_up', outputDir, { fullPage: false });
  }

  await closeOpenAirtablePanel(page).catch(() => {});
  const result = { timestamp_utc: nowIso(), tool_version: TOOL_VERSION, status: 'success', target, field_name: args.fieldName, output_dir: outputDir };
  writeJson(path.join(outputDir, 'relative_date_popup_probe_report.json'), result);
  console.log(JSON.stringify(result, null, 2));
}

main().catch(async (error) => {
  const message = String(error?.message || error);
  log('Relative-date popup probe failed.', { error: message });
  await captureDomEvidence(page, outputDir, 'relative_date_popup_probe_failure', { fullPage: false }).catch(() => null);
  writeJson(path.join(outputDir, 'relative_date_popup_probe_failed.json'), { timestamp_utc: nowIso(), tool_version: TOOL_VERSION, status: 'failed', error: message });
  if (args.keepBrowserOpenOnFailure && rl) {
    await rl.question('Failure detected. Browser will remain open for inspection. Press Enter in PowerShell after inspecting.').catch(() => {});
  }
  process.exitCode = 1;
}).finally(async () => {
  if (rl) rl.close();
  if (context && closeMode === 'persistent') await context.close().catch(() => {});
  else if (browser && closeMode !== 'cdp') await browser.close().catch(() => {});
});
