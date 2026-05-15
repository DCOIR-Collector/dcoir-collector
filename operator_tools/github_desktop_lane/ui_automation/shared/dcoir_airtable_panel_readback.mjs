import path from 'node:path';
import { writeJson, safeName, nowIso, norm } from './dcoir_ui_common.mjs';
import { clickAirtableToolbarButton, clickAirtableViewInSidebar, dismissTransientUi, safeMousePark, AIRTABLE_UI_GEOMETRY_VERSION } from './dcoir_airtable_ui_geometry.mjs';

export const AIRTABLE_PANEL_READBACK_VERSION = '2026-05-14.panel-readback.6';

export function normalizeTargetKey(tableName, viewName) {
  return `${norm(tableName)}::${norm(viewName)}`;
}

export function expectedViewStateFromManifestView(view) {
  return {
    table_name: view.table_name,
    table_id: view.table_id,
    view_name: view.view_name,
    view_key: view.view_key || normalizeTargetKey(view.table_name, view.view_name),
    expected_filters: Array.isArray(view.filters) ? view.filters.map((filter, index) => ({
      index: index + 1,
      field: filter.field,
      operator: filter.operator,
      value: filter.value
    })) : [],
    expected_sorts: Array.isArray(view.sorts) ? view.sorts.map((sort, index) => ({
      index: index + 1,
      field: sort.field,
      direction: sort.direction
    })) : []
  };
}

export function selectManifestTargets(manifest, options = {}) {
  const views = Array.isArray(manifest.views) ? manifest.views : [];
  let selected;
  if (options.allViews) {
    selected = views;
  } else if (Array.isArray(options.targetKeys) && options.targetKeys.length > 0) {
    const wanted = new Set(options.targetKeys.map((key) => norm(key).toLowerCase()));
    selected = views.filter((view) => wanted.has(normalizeTargetKey(view.table_name, view.view_name).toLowerCase()) || wanted.has(String(view.view_key || '').toLowerCase()));
  } else if (Array.isArray(options.defaultTargetKeys) && options.defaultTargetKeys.length > 0) {
    const wanted = new Set(options.defaultTargetKeys.map((key) => norm(key).toLowerCase()));
    selected = views.filter((view) => wanted.has(normalizeTargetKey(view.table_name, view.view_name).toLowerCase()) || wanted.has(String(view.view_key || '').toLowerCase()));
  } else {
    selected = [];
  }
  if (selected.length < 1) throw new Error('No Airtable view panel readback targets selected from manifest. Check target keys.');
  return selected.map(expectedViewStateFromManifestView);
}

export function targetKeyOfReadbackTarget(target) {
  return normalizeTargetKey(target?.table_name || '', target?.view_name || '');
}

export function normalizeTargetKeyList(values = []) {
  const out = [];
  for (const value of values || []) {
    const text = norm(value);
    if (!text) continue;
    if (!out.some((existing) => existing.toLowerCase() === text.toLowerCase())) out.push(text);
  }
  return out;
}

function findTargetIndexByKey(targets, key, label) {
  const wanted = norm(key).toLowerCase();
  if (!wanted) return -1;
  const index = (targets || []).findIndex((target) => {
    const canonical = targetKeyOfReadbackTarget(target).toLowerCase();
    const manifestKey = norm(target?.view_key || '').toLowerCase();
    return canonical === wanted || manifestKey === wanted;
  });
  if (index < 0) throw new Error(`${label} was not found in selected target set: ${key}`);
  return index;
}

export function filterReadbackTargetsForResume(targets, options = {}) {
  let selected = Array.isArray(targets) ? targets.slice() : [];
  if (options.afterTargetKey) {
    const index = findTargetIndexByKey(selected, options.afterTargetKey, '--after-target-key');
    selected = selected.slice(index + 1);
  }
  if (options.startAtTargetKey) {
    const index = findTargetIndexByKey(selected, options.startAtTargetKey, '--start-at-target-key');
    selected = selected.slice(index);
  }
  if (Number.isInteger(options.maxTargets) && options.maxTargets > 0) {
    selected = selected.slice(0, options.maxTargets);
  }
  if (selected.length < 1) throw new Error('Resume/target selection produced zero readback targets.');
  return selected;
}

export async function reloadPageWithRetry(page, options = {}) {
  const maxAttempts = Number.isInteger(options.maxAttempts) && options.maxAttempts > 0 ? options.maxAttempts : 3;
  const reloadTimeoutMs = Number.isFinite(options.reloadTimeoutMs) ? options.reloadTimeoutMs : 30000;
  const networkIdleTimeoutMs = Number.isFinite(options.networkIdleTimeoutMs) ? options.networkIdleTimeoutMs : 12000;
  const settleMs = Number.isFinite(options.settleMs) ? options.settleMs : 1200;
  const backoffMs = Number.isFinite(options.backoffMs) ? options.backoffMs : 4000;
  const waitUntil = options.waitUntil || 'domcontentloaded';
  const log = typeof options.log === 'function' ? options.log : null;
  const attempts = [];

  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    const item = { attempt, max_attempts: maxAttempts, started_at_utc: nowIso(), ok: false, before_url: page.url() };
    try {
      if (log) log('Reload attempt starting.', item);
      await page.reload({ waitUntil, timeout: reloadTimeoutMs });
      await page.waitForLoadState('networkidle', { timeout: networkIdleTimeoutMs }).catch((error) => {
        item.network_idle_warning = String(error?.message || error);
      });
      if (settleMs > 0) await page.waitForTimeout(settleMs);
      item.ok = true;
      item.after_url = page.url();
      item.completed_at_utc = nowIso();
      attempts.push(item);
      if (log) log('Reload attempt completed.', item);
      return { ok: true, attempts, final_url: item.after_url };
    } catch (error) {
      item.error = String(error?.message || error);
      item.after_url = page.url();
      item.completed_at_utc = nowIso();
      attempts.push(item);
      if (log) log('Reload attempt failed.', item);
      if (attempt < maxAttempts && backoffMs > 0) {
        await page.waitForTimeout(backoffMs);
      }
    }
  }
  return { ok: false, attempts, final_url: page.url(), error: attempts[attempts.length - 1]?.error || 'reload failed' };
}

export async function getVisibleElements(page, options = {}) {
  const limit = options.limit || 6000;
  return await page.evaluate((limit) => {
    function visible(el) {
      const style = window.getComputedStyle(el);
      const box = el.getBoundingClientRect();
      return style && style.visibility !== 'hidden' && style.display !== 'none' && box.width > 0 && box.height > 0;
    }
    function panelPriority(item) {
      const content = String(`${item.text} ${item.aria} ${item.placeholder} ${item.value}`).toLowerCase();
      const inPanelBand = item.x >= 250 && item.x <= 1250 && item.y >= 70 && item.y <= 760 && item.w <= 1000 && item.h <= 760;
      const hasPanelSignal = /sort by|add another sort|automatically sort records|filter|in this view, show records|add condition|copy from another view|enter a date|gmt/.test(content);
      return inPanelBand && hasPanelSignal ? 0 : 1;
    }
    return Array.from(document.querySelectorAll('button, [role="button"], input, textarea, [aria-label], [placeholder], [contenteditable="true"], div, span, a'))
      .slice(0, limit)
      .map((el) => {
        const box = el.getBoundingClientRect();
        return {
          tag: el.tagName,
          role: el.getAttribute('role') || '',
          aria: el.getAttribute('aria-label') || '',
          placeholder: el.getAttribute('placeholder') || '',
          type: el.getAttribute('type') || '',
          value: String(el.value || '').replace(/\s+/g, ' ').trim().slice(0, 500),
          text: (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 500),
          x: Math.round(box.x),
          y: Math.round(box.y),
          w: Math.round(box.width),
          h: Math.round(box.height),
          visible: visible(el)
        };
      })
      .filter((item) => item.visible && (item.text || item.aria || item.placeholder || item.role || item.type || item.value))
      .sort((a, b) => panelPriority(a) - panelPriority(b) || a.y - b.y || a.x - b.x || (a.w * a.h) - (b.w * b.h))
      .slice(0, 1600);
  }, limit);
}


export async function captureAirtableGridRowState(page, outputDir, target, phase = 'target_loaded') {
  const rowState = await page.evaluate(() => {
    const normalize = (s) => String(s || '').replace(/[\u2192\u27f6\u2794]/g, ' -> ').replace(/\s+/g, ' ').trim();
    function visible(el) {
      const style = window.getComputedStyle(el);
      const box = el.getBoundingClientRect();
      return style && style.visibility !== 'hidden' && style.display !== 'none' && box.width > 0 && box.height > 0;
    }
    function itemFor(el) {
      const box = el.getBoundingClientRect();
      return {
        tag: el.tagName,
        role: el.getAttribute('role') || '',
        testid: el.getAttribute('data-testid') || '',
        aria: normalize(el.getAttribute('aria-label') || ''),
        text: normalize(el.innerText || el.textContent || ''),
        x: Math.round(box.x),
        y: Math.round(box.y),
        w: Math.round(box.width),
        h: Math.round(box.height)
      };
    }
    const bodyText = normalize(document.body ? document.body.innerText : '').toLowerCase();
    const noRecordsSignal = /\b(no records|no records in this view|there are no records|0 records)\b/i.test(bodyText);
    const gridCells = Array.from(document.querySelectorAll('[role="gridcell"], [data-testid*="cell"], [data-testid*="gridCell"], [data-testid*="recordCell"]'))
      .filter(visible)
      .map(itemFor)
      .filter((item) => item.y > 165 && item.w > 8 && item.h > 8 && item.x > 220)
      .slice(0, 80);
    const gridRows = Array.from(document.querySelectorAll('[role="row"], [data-testid*="row"], [data-rowindex]'))
      .filter(visible)
      .map(itemFor)
      .filter((item) => item.y > 165 && item.w > 80 && item.h > 12)
      .slice(0, 80);
    const rowHeaderSignals = Array.from(document.querySelectorAll('[aria-label*="record" i], [data-testid*="record" i], button, div, span'))
      .filter(visible)
      .map(itemFor)
      .filter((item) => item.y > 165 && item.x >= 0 && item.x < 360 && /record|row/i.test(`${item.aria} ${item.testid} ${item.text}`))
      .slice(0, 40);
    let state = 'unknown';
    if (noRecordsSignal) state = 'none';
    else if (gridCells.length > 0 || gridRows.length > 1 || rowHeaderSignals.length > 0) state = 'visible';
    return {
      ok: true,
      row_state: state,
      no_records_signal: noRecordsSignal,
      visible_grid_cell_count: gridCells.length,
      visible_grid_row_count: gridRows.length,
      row_header_signal_count: rowHeaderSignals.length,
      grid_cell_samples: gridCells.slice(0, 10),
      grid_row_samples: gridRows.slice(0, 10),
      row_header_signal_samples: rowHeaderSignals.slice(0, 10)
    };
  }).catch((error) => ({ ok: false, row_state: 'unknown', error: String(error?.message || error) }));
  const payload = {
    timestamp_utc: nowIso(),
    tool_version: AIRTABLE_PANEL_READBACK_VERSION,
    geometry_version: AIRTABLE_UI_GEOMETRY_VERSION,
    target,
    phase,
    ...rowState
  };
  const statePath = path.join(outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_${phase}_row_state.json`);
  writeJson(statePath, payload);
  return { ...payload, state_path: statePath };
}

export async function captureDomEvidence(page, outputDir, label, options = {}) {
  const payload = {
    timestamp_utc: nowIso(),
    tool_version: AIRTABLE_PANEL_READBACK_VERSION,
    geometry_version: AIRTABLE_UI_GEOMETRY_VERSION,
    label,
    url: page.url(),
    title: await page.title(),
    elements: await getVisibleElements(page)
  };
  const domPath = path.join(outputDir, `${safeName(label)}.dom.json`);
  writeJson(domPath, payload);
  const result = { label, dom_evidence: domPath };
  if (options.enableScreenshots) {
    const screenshotPath = path.join(outputDir, `${safeName(label)}.png`);
    await page.screenshot({ path: screenshotPath, fullPage: true });
    result.screenshot = screenshotPath;
  }
  return result;
}

export async function selectAirtableTableAndView(page, target) {
  const result = { table_id: target.table_id, table_name: target.table_name, view_name: target.view_name, steps: [] };
  await dismissTransientUi(page, 'before-table-navigation');
  const current = new URL(page.url());
  const appId = current.pathname.split('/').filter(Boolean).find((part) => /^app[A-Za-z0-9]+$/.test(part)) || target.base_id;
  if (!appId) throw new Error(`Cannot derive Airtable app id for ${target.table_name}`);
  if (!/^tbl[A-Za-z0-9]+$/.test(String(target.table_id || ''))) throw new Error(`Invalid Airtable table id for ${target.table_name}: ${target.table_id}`);
  const url = `${current.origin}/${appId}/${target.table_id}?blocks=hide`;
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 15000 });
  await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
  await page.waitForTimeout(1200);
  result.steps.push({ action: 'goto_table_by_id', ok: true, url });

  const viewClick = await clickAirtableViewInSidebar(page, target.view_name, { xMin: 40, xMax: 420, yMin: 240, iconAvoidWidth: 82 });
  result.steps.push({ action: 'select_view_by_left_sidebar_only_no_top_view_title', ...viewClick });
  if (!viewClick.ok) throw new Error(`Could not select view ${target.table_name} / ${target.view_name}`);
  await page.waitForTimeout(1200);
  await safeMousePark(page, 'after-select-view');
  return result;
}

export async function openAirtablePanel(page, kind) {
  const panelKind = String(kind || '').toLowerCase();
  if (!['filter', 'sort'].includes(panelKind)) throw new Error(`Unsupported Airtable panel kind: ${kind}`);
  const click = await clickAirtableToolbarButton(page, panelKind, { xMin: 560, xMax: 1450, yMin: 75, yMax: 165 });
  await page.waitForTimeout(900);
  return click;
}

export async function closeOpenAirtablePanel(page) {
  await dismissTransientUi(page, 'close-open-airtable-panel');
}

function normalizeText(s) {
  return String(s || '')
    .replace(/[\u2192\u27f6\u2794]/g, ' -> ')
    .replace(/\s+/g, ' ')
    .trim();
}

function lowerText(s) {
  return normalizeText(s).toLowerCase();
}

function uniqueNonEmpty(parts) {
  const out = [];
  for (const part of parts.map(normalizeText).filter(Boolean)) {
    if (!out.some((existing) => existing.toLowerCase() === part.toLowerCase())) out.push(part);
  }
  return out;
}

function includesWholePhrase(text, phrase) {
  const haystack = lowerText(text);
  const needle = lowerText(phrase);
  if (!needle) return true;
  if (needle.includes(' ')) return haystack.includes(needle);
  return new RegExp(`(^|[^a-z0-9_])${needle.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}([^a-z0-9_]|$)`, 'i').test(haystack);
}

export async function extractOpenAirtablePanel(page, kind) {
  return await page.evaluate((kind) => {
    const normalize = (s) => String(s || '').replace(/[\u2192\u27f6\u2794]/g, ' -> ').replace(/\s+/g, ' ').trim();
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

    const markerPhrases = kind === 'sort'
      ? ['sort by', 'add another sort', 'automatically sort records']
      : ['filter', 'in this view, show records', 'add condition', 'copy from another view'];

    const containers = Array.from(document.querySelectorAll('div, section, [role="dialog"], [role="menu"], [data-testid], [class]'))
      .filter(visible)
      .map((el) => {
        const box = el.getBoundingClientRect();
        const text = normalize(el.innerText || el.textContent);
        const lower = text.toLowerCase();
        const markerHits = markerPhrases.filter((phrase) => lower.includes(phrase)).length;
        return { el, text, markerHits, x: box.x, y: box.y, w: box.width, h: box.height, area: box.width * box.height };
      })
      .filter((c) => {
        const lower = c.text.toLowerCase();
        const filterConditionSignal = /where|review_after|is on or before|is before|is after|is empty|is not empty|is checked|is unchecked|today|add condition/.test(lower);
        const sortConditionSignal = /sort by|add another sort|automatically sort records|earliest -> latest|latest -> earliest|ascending|descending|a -> z|z -> a/.test(lower);
        const enoughMarkers = c.markerHits >= 2 || (kind === 'filter' && c.markerHits >= 1 && filterConditionSignal) || (kind === 'sort' && c.markerHits >= 1 && sortConditionSignal);
        if (!enoughMarkers) return false;
        if (c.x < 120 || c.y < 45 || c.w < 170 || c.h < 55) return false;
        if (c.w > 1150 || c.h > 820) return false;
        return true;
      })
      .sort((a, b) => b.markerHits - a.markerHits || a.area - b.area || a.y - b.y || a.x - b.x);

    const panel = containers[0];
    if (!panel) {
      const candidates = Array.from(document.querySelectorAll('button, [role="button"], div, section, [role="dialog"], [role="menu"], [data-testid], [class]'))
        .filter(visible)
        .map((el) => {
          const box = el.getBoundingClientRect();
          const text = normalize(el.innerText || el.textContent);
          const lower = text.toLowerCase();
          const markerHits = markerPhrases.filter((phrase) => lower.includes(phrase)).length;
          return { text: text.slice(0, 300), markerHits, x: Math.round(box.x), y: Math.round(box.y), w: Math.round(box.width), h: Math.round(box.height) };
        })
        .filter((c) => c.markerHits > 0 || /filtered by|sorted by|review_after|is on or before|today|earliest -> latest/i.test(c.text))
        .sort((a, b) => b.markerHits - a.markerHits || a.y - b.y || a.x - b.x)
        .slice(0, 40);
      return { ok: false, reason: 'panel_container_not_found', panel: null, rows: [], raw_elements: [], container_candidates: candidates };
    }

    const bounds = {
      x: Math.round(panel.x),
      y: Math.round(panel.y),
      w: Math.round(panel.w),
      h: Math.round(panel.h),
      right: Math.round(panel.x + panel.w),
      bottom: Math.round(panel.y + panel.h)
    };

    const raw = Array.from(document.querySelectorAll('button, [role="button"], input, textarea, [contenteditable="true"], [aria-label], [placeholder], div, span'))
      .filter(visible)
      .map((el) => {
        const box = el.getBoundingClientRect();
        const text = normalize(el.innerText || el.textContent);
        const aria = normalize(el.getAttribute('aria-label') || '');
        const placeholder = normalize(el.getAttribute('placeholder') || '');
        const value = normalize(el.value || '');
        const cx = box.x + box.width / 2;
        const cy = box.y + box.height / 2;
        return { el, tag: el.tagName, role: el.getAttribute('role') || '', text, aria, placeholder, value, x: box.x, y: box.y, w: box.width, h: box.height, cx, cy, top: topVisible(el, box) };
      })
      .filter((c) => {
        if (!c.top) return false;
        if (c.x < panel.x - 2 || c.y < panel.y - 2 || c.x + c.w > panel.x + panel.w + 2 || c.y + c.h > panel.y + panel.h + 2) return false;
        if (c.w > panel.w * 0.96 && c.h > 60) return false;
        const content = normalize(`${c.text} ${c.aria} ${c.placeholder} ${c.value}`);
        if (!content) return false;
        if (/Describe what you want to see|Copy from another view|Add condition group|Automatically sort records/i.test(content)) return false;
        if (kind === 'filter' && /^Filter$/i.test(content)) return false;
        if (kind === 'sort' && /^Sort by$/i.test(content)) return false;
        return true;
      })
      .map((c) => ({ tag: c.tag, role: c.role, text: c.text, aria: c.aria, placeholder: c.placeholder, value: c.value, x: Math.round(c.x), y: Math.round(c.y), w: Math.round(c.w), h: Math.round(c.h), cx: Math.round(c.cx), cy: Math.round(c.cy) }))
      .sort((a, b) => a.y - b.y || a.x - b.x);

    const rowCandidates = raw.filter((c) => {
      const content = normalize(`${c.text} ${c.aria} ${c.placeholder} ${c.value}`);
      if (/^Add condition$|^Add another sort$|^Add sort$|^Add condition group$/i.test(content)) return false;
      if (kind === 'filter') return c.y >= panel.y + 65 && c.y <= panel.y + panel.h - 24;
      if (kind === 'sort') return c.y >= panel.y + 42 && c.y <= panel.y + panel.h - 42;
      return true;
    });

    const buckets = [];
    for (const el of rowCandidates) {
      const cy = el.y + Math.round(el.h / 2);
      let bucket = buckets.find((row) => Math.abs(row.center_y - cy) <= 14);
      if (!bucket) {
        bucket = { center_y: cy, elements: [] };
        buckets.push(bucket);
      }
      bucket.elements.push(el);
    }

    function partsFromElements(elements) {
      const parts = [];
      for (const el of elements) {
        for (const part of [el.text, el.aria, el.placeholder, el.value]) {
          const item = normalize(part);
          if (!item) continue;
          if (!parts.some((existing) => existing.toLowerCase() === item.toLowerCase())) parts.push(item);
        }
      }
      return parts;
    }

    const rows = buckets.map((bucket, index) => {
      const elements = bucket.elements.sort((a, b) => a.x - b.x);
      const compact = elements.filter((el) => el.w <= Math.max(260, panel.w * 0.48) || ['INPUT', 'TEXTAREA'].includes(el.tag));
      const fieldZone = compact.filter((el) => el.cx <= panel.x + panel.w * 0.48);
      const operatorZone = compact.filter((el) => el.cx >= panel.x + panel.w * 0.33 && el.cx <= panel.x + panel.w * 0.72);
      const valueZone = compact.filter((el) => el.cx >= panel.x + panel.w * 0.55);
      const directionZone = compact.filter((el) => el.cx >= panel.x + panel.w * 0.45);
      const allParts = partsFromElements(elements);
      return {
        row_index: index + 1,
        y: bucket.center_y,
        text: allParts.join(' | '),
        cells: {
          field_text: partsFromElements(fieldZone).join(' | '),
          operator_text: partsFromElements(operatorZone).join(' | '),
          value_text: partsFromElements(valueZone).join(' | '),
          direction_text: partsFromElements(directionZone).join(' | ')
        },
        elements
      };
    }).filter((row) => row.text && !/^Where$|^and$|^or$/i.test(row.text));

    return { ok: true, panel: bounds, rows, raw_elements: raw };
  }, kind);
}

export async function captureAirtablePanelState(page, outputDir, target, kind, phase, options = {}) {
  const readbackAttempts = [];
  let opened = await openAirtablePanel(page, kind);
  let extracted = await extractOpenAirtablePanel(page, kind);
  readbackAttempts.push({ action: 'open_and_extract_initial', opened, ok: extracted.ok, reason: extracted.reason || null, panel: extracted.panel || null, row_count: Array.isArray(extracted.rows) ? extracted.rows.length : 0 });

  if (!extracted.ok) {
    await page.waitForTimeout(650).catch(() => {});
    const retryExtract = await extractOpenAirtablePanel(page, kind);
    readbackAttempts.push({ action: 'extract_retry_after_wait', ok: retryExtract.ok, reason: retryExtract.reason || null, panel: retryExtract.panel || null, row_count: Array.isArray(retryExtract.rows) ? retryExtract.rows.length : 0 });
    if (retryExtract.ok) extracted = retryExtract;
  }

  if (!extracted.ok) {
    await closeOpenAirtablePanel(page).catch(() => {});
    await page.waitForTimeout(350).catch(() => {});
    const reopened = await openAirtablePanel(page, kind);
    await page.waitForTimeout(1100).catch(() => {});
    const reopenedExtract = await extractOpenAirtablePanel(page, kind);
    readbackAttempts.push({ action: 'reopen_and_extract_retry', opened: reopened, ok: reopenedExtract.ok, reason: reopenedExtract.reason || null, panel: reopenedExtract.panel || null, row_count: Array.isArray(reopenedExtract.rows) ? reopenedExtract.rows.length : 0 });
    opened = reopened;
    if (reopenedExtract.ok) extracted = reopenedExtract;
  }

  const snapshot = await captureDomEvidence(page, outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_${phase}_${kind}_panel`, options);
  const state = {
    timestamp_utc: nowIso(),
    tool_version: AIRTABLE_PANEL_READBACK_VERSION,
    geometry_version: AIRTABLE_UI_GEOMETRY_VERSION,
    target,
    phase,
    kind,
    opened,
    readback_attempts: readbackAttempts,
    panel_extraction: { ok: extracted.ok, reason: extracted.reason || null, panel: extracted.panel || null, container_candidates: extracted.container_candidates || [] },
    rows: extracted.rows || [],
    raw_panel_elements: extracted.raw_elements || [],
    snapshot
  };
  const statePath = path.join(outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_${phase}_${kind}_state.json`);
  writeJson(statePath, state);
  await closeOpenAirtablePanel(page);
  return { ...state, state_path: statePath };
}

function operatorLabels(operator) {
  const op = lowerText(operator);
  if (op === '=') return ['is', '='];
  if (op === 'is one of') return ['is any of', 'is one of'];
  if (op === 'is not empty') return ['is not empty'];
  if (op === 'contains') return ['contains'];
  if (op === 'on or before') return ['is on or before', 'on or before'];
  return [op];
}

function filterNeedsValue(filter) {
  return filter && lowerText(filter.operator) !== 'is not empty';
}

function rowMatchesField(row, fieldName) {
  const fieldText = row?.cells?.field_text || '';
  if (includesWholePhrase(fieldText, fieldName)) return true;
  const exactFieldElement = (row.elements || []).some((el) => {
    const content = lowerText(`${el.text} ${el.aria} ${el.placeholder} ${el.value}`);
    const isLeftSide = el.cx <= (Math.min(...(row.elements || []).map((e) => e.cx)) + 360);
    return isLeftSide && lowerText(fieldName) === content;
  });
  return exactFieldElement;
}

function rowMatchesOperator(row, operator) {
  const text = `${row?.cells?.operator_text || ''} | ${row?.text || ''}`;
  return operatorLabels(operator).some((label) => includesWholePhrase(text, label));
}

function rowMatchesBooleanValue(row, value) {
  const text = `${row?.cells?.operator_text || ''} | ${row?.cells?.value_text || ''} | ${row?.text || ''}`;
  if (value === true) return /\b(is checked|checked|true|yes)\b/i.test(text);
  return /\b(is unchecked|unchecked|false|no)\b/i.test(text);
}

function rowMatchesScalarValue(row, value) {
  if (typeof value === 'boolean') return rowMatchesBooleanValue(row, value);
  const valueText = `${row?.cells?.value_text || ''} | ${row?.text || ''}`;
  const wanted = String(value);
  if (lowerText(wanted) === 'today') return includesWholePhrase(valueText, 'today');
  return includesWholePhrase(valueText, wanted);
}

function rowMatchesFilterValue(row, filter) {
  if (!filterNeedsValue(filter)) return true;
  const value = filter.value;
  if (value === null || typeof value === 'undefined') return false;
  if (Array.isArray(value)) return value.every((item) => rowMatchesScalarValue(row, item));
  return rowMatchesScalarValue(row, value);
}

function rowMatchesFilter(row, filter) {
  return rowMatchesField(row, filter.field) && rowMatchesOperator(row, filter.operator) && rowMatchesFilterValue(row, filter);
}

function sortDirectionLabels(direction) {
  const dir = lowerText(direction);
  if (dir === 'asc' || dir === 'ascending') return ['ascending', 'a -> z', '1 -> 9', 'a to z', '1 to 9', 'first -> last', 'earliest -> latest'];
  if (dir === 'desc' || dir === 'descending') return ['descending', 'z -> a', '9 -> 1', 'z to a', '9 to 1', 'last -> first', 'latest -> earliest'];
  return [dir];
}

function rowMatchesSortDirection(row, direction) {
  const text = `${row?.cells?.direction_text || ''} | ${row?.text || ''}`;
  return sortDirectionLabels(direction).some((label) => includesWholePhrase(text, label));
}

function rowMatchesSort(row, sort) {
  return rowMatchesField(row, sort.field) && rowMatchesSortDirection(row, sort.direction);
}

function compareFiltersForState(state, expectedFilters, phaseLabel) {
  const missing = [];
  if (!state?.panel_extraction?.ok) {
    missing.push(`${phaseLabel}: filter panel extraction failed`);
    return missing;
  }
  const rows = Array.isArray(state.rows) ? state.rows : [];
  if (expectedFilters.length === 0) return missing;
  for (const filter of expectedFilters) {
    const matched = rows.some((row) => rowMatchesFilter(row, filter));
    if (!matched) {
      const value = Array.isArray(filter.value) ? filter.value.join(',') : String(filter.value);
      missing.push(`${phaseLabel}: filter row not observed: field=${filter.field}; operator=${filter.operator}; value=${value}`);
    }
  }
  return missing;
}

function rowLooksLikeSortCondition(row) {
  const cells = row?.cells || {};
  const text = `${cells.field_text || ''} | ${cells.direction_text || ''} | ${row?.text || ''}`;
  if (!cells.field_text || !cells.direction_text) return false;
  if (/add another sort|add sort/i.test(cells.field_text)) return false;
  return /a\s*->\s*z|z\s*->\s*a|1\s*->\s*9|9\s*->\s*1|first\s*->\s*last|last\s*->\s*first|earliest\s*->\s*latest|latest\s*->\s*earliest|ascending|descending/i.test(text);
}

function orderedSortRows(state) {
  return (Array.isArray(state?.rows) ? state.rows : [])
    .filter(rowLooksLikeSortCondition)
    .sort((a, b) => (a.y || 0) - (b.y || 0));
}

function compareSortsForState(state, expectedSorts, phaseLabel) {
  const missing = [];
  if (!state?.panel_extraction?.ok) {
    missing.push(`${phaseLabel}: sort panel extraction failed`);
    return missing;
  }
  const rows = orderedSortRows(state);
  for (let i = 0; i < expectedSorts.length; i += 1) {
    const sort = expectedSorts[i];
    const row = rows[i];
    if (!row || !rowMatchesSort(row, sort)) {
      missing.push(`${phaseLabel}: sort row ${i + 1} not observed in order: field=${sort.field}; direction=${sort.direction}`);
    }
  }
  return missing;
}

function classifiedGapFromMissing(message) {
  const text = String(message || '');
  const phaseMatch = text.match(/^(before_refresh|after_refresh):\s*/i);
  const phase = phaseMatch ? phaseMatch[1].toLowerCase() : 'unknown';
  let category = 'unknown_gap';
  if (/filter panel extraction failed/i.test(text)) category = 'panel_extraction_gap';
  else if (/sort panel extraction failed/i.test(text)) category = 'panel_extraction_gap';
  else if (/filter row not observed/i.test(text)) category = 'filter_gap';
  else if (/sort row \d+ not observed/i.test(text)) category = 'sort_gap';
  return { category, phase, message: text };
}

export function summarizeGapDetails(gapDetails = []) {
  const summary = {
    total: gapDetails.length,
    filter_gap_count: gapDetails.filter((g) => g.category === 'filter_gap').length,
    sort_gap_count: gapDetails.filter((g) => g.category === 'sort_gap').length,
    panel_extraction_gap_count: gapDetails.filter((g) => g.category === 'panel_extraction_gap').length,
    unknown_gap_count: gapDetails.filter((g) => g.category === 'unknown_gap').length,
    before_refresh_count: gapDetails.filter((g) => g.phase === 'before_refresh').length,
    after_refresh_count: gapDetails.filter((g) => g.phase === 'after_refresh').length
  };
  summary.categories = Array.from(new Set(gapDetails.map((g) => g.category))).sort();
  return summary;
}

export function classifyAirtablePanelReadback(recon) {
  const expectedFilters = recon?.target?.expected_filters || [];
  const expectedSorts = recon?.target?.expected_sorts || [];
  const missing = [];
  missing.push(...compareFiltersForState(recon.before_filter, expectedFilters, 'before_refresh'));
  missing.push(...compareFiltersForState(recon.after_filter, expectedFilters, 'after_refresh'));
  missing.push(...compareSortsForState(recon.before_sort, expectedSorts, 'before_refresh'));
  missing.push(...compareSortsForState(recon.after_sort, expectedSorts, 'after_refresh'));
  const gap_details = missing.map(classifiedGapFromMissing);
  const gap_summary = summarizeGapDetails(gap_details);
  const before_row_state = recon?.row_state_before?.row_state || recon?.row_state_initial?.row_state || null;
  const after_row_state = recon?.row_state_after?.row_state || null;
  const row_state = after_row_state || before_row_state || 'unknown';
  return { ok: missing.length === 0, missing, gap_details, gap_summary, row_state, before_row_state, after_row_state };
}

export function compareAirtablePanelReadback(recon) {
  return classifyAirtablePanelReadback(recon);
}

export const testInternals = Object.freeze({
  includesWholePhrase,
  rowMatchesFilter,
  rowMatchesSort,
  compareAirtablePanelReadback,
  filterReadbackTargetsForResume,
  reloadPageWithRetry,
  targetKeyOfReadbackTarget,
  classifyAirtablePanelReadback,
  summarizeGapDetails,
  uniqueNonEmpty
});
