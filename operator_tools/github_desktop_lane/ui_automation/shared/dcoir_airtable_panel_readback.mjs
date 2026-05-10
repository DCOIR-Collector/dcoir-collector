import path from 'node:path';
import { writeJson, safeName, nowIso, norm } from './dcoir_ui_common.mjs';
import { clickAirtableToolbarButton, clickAirtableViewInSidebar, dismissTransientUi, safeMousePark, AIRTABLE_UI_GEOMETRY_VERSION } from './dcoir_airtable_ui_geometry.mjs';

export const AIRTABLE_PANEL_READBACK_VERSION = '2026-05-10.panel-readback.3';

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
        if (c.markerHits < 2) return false;
        if (c.x < 250 || c.y < 70 || c.w < 250 || c.h < 90) return false;
        if (c.w > 1050 || c.h > 760) return false;
        return true;
      })
      .sort((a, b) => b.markerHits - a.markerHits || a.area - b.area || a.y - b.y || a.x - b.x);

    const panel = containers[0];
    if (!panel) return { ok: false, reason: 'panel_container_not_found', panel: null, rows: [], raw_elements: [] };

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
  const opened = await openAirtablePanel(page, kind);
  const extracted = await extractOpenAirtablePanel(page, kind);
  const snapshot = await captureDomEvidence(page, outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_${phase}_${kind}_panel`, options);
  const state = {
    timestamp_utc: nowIso(),
    tool_version: AIRTABLE_PANEL_READBACK_VERSION,
    geometry_version: AIRTABLE_UI_GEOMETRY_VERSION,
    target,
    phase,
    kind,
    opened,
    panel_extraction: { ok: extracted.ok, reason: extracted.reason || null, panel: extracted.panel || null },
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

export function compareAirtablePanelReadback(recon) {
  const expectedFilters = recon?.target?.expected_filters || [];
  const expectedSorts = recon?.target?.expected_sorts || [];
  const missing = [];
  missing.push(...compareFiltersForState(recon.before_filter, expectedFilters, 'before_refresh'));
  missing.push(...compareFiltersForState(recon.after_filter, expectedFilters, 'after_refresh'));
  missing.push(...compareSortsForState(recon.before_sort, expectedSorts, 'before_refresh'));
  missing.push(...compareSortsForState(recon.after_sort, expectedSorts, 'after_refresh'));
  return { ok: missing.length === 0, missing };
}

export const testInternals = Object.freeze({
  includesWholePhrase,
  rowMatchesFilter,
  rowMatchesSort,
  compareAirtablePanelReadback,
  uniqueNonEmpty
});
