import path from 'node:path';
import { writeJson, safeName, nowIso, norm } from './dcoir_ui_common.mjs';
import { safeMousePark } from './dcoir_airtable_ui_geometry.mjs';
import {
  AIRTABLE_PANEL_READBACK_VERSION,
  captureDomEvidence,
  openAirtablePanel,
  extractOpenAirtablePanel,
  closeOpenAirtablePanel,
  compareAirtablePanelReadback
} from './dcoir_airtable_panel_readback.mjs';

export const AIRTABLE_PANEL_DISCOVERY_VERSION = '2026-05-10.panel-discovery.4';

function normalizeText(value) {
  return String(value || '')
    .replace(/[\u2192\u27f6\u2794]/g, ' -> ')
    .replace(/\s+/g, ' ')
    .trim();
}

function lowerText(value) {
  return normalizeText(value).toLowerCase();
}

function uniqueByText(items) {
  const out = [];
  const seen = new Set();
  for (const item of items) {
    const key = lowerText(item.text || item.aria || item.placeholder || item.value || '');
    if (!key || seen.has(key)) continue;
    seen.add(key);
    out.push(item);
  }
  return out;
}

function stripPhasePrefix(message) {
  return String(message || '').replace(/^(before_refresh|after_refresh):\s*/i, '').trim();
}

function summarizeRows(state) {
  return (state?.rows || []).map((row, index) => ({
    index: row.index || index + 1,
    text: normalizeText(row.text || ''),
    cells: row.cells || {},
    y: row.y,
    element_count: Array.isArray(row.elements) ? row.elements.length : 0
  }));
}

function expectedTextPresent(rows, expected) {
  const haystack = normalizeText((rows || []).map((row) => `${row.text || ''} ${Object.values(row.cells || {}).join(' ')}`).join(' | ')).toLowerCase();
  return Object.values(expected || {}).every((value) => {
    if (value === null || value === undefined || value === '') return true;
    return haystack.includes(normalizeText(value).toLowerCase());
  });
}

function sortDirectionObservedForField(rows, expectedSort) {
  const field = normalizeText(expectedSort?.field || '').toLowerCase();
  if (!field) return false;
  const wanted = String(expectedSort?.direction || '').toLowerCase() === 'desc' ? 'desc' : 'asc';
  for (const row of rows || []) {
    const text = normalizeText(`${row.text || ''} ${Object.values(row.cells || {}).join(' ')}`).toLowerCase();
    if (!text.includes(field)) continue;
    const hasAsc = /a\s*->\s*z|1\s*->\s*9|earliest\s*->\s*latest|ascending/.test(text);
    const hasDesc = /z\s*->\s*a|9\s*->\s*1|latest\s*->\s*earliest|descending/.test(text);
    if (wanted === 'desc' && hasDesc) return true;
    if (wanted === 'asc' && hasAsc) return true;
  }
  return false;
}

function sortFieldObserved(rows, expectedSort) {
  const field = normalizeText(expectedSort?.field || '').toLowerCase();
  if (!field) return false;
  return (rows || []).some((row) => normalizeText(`${row.text || ''} ${Object.values(row.cells || {}).join(' ')}`).toLowerCase().includes(field));
}

function chooseFilterAction(expectedFilters, currentFilterRows, filterMissing) {
  if (expectedFilters.length === 0 && currentFilterRows.length === 0) return 'noop';
  if (filterMissing.length === 0) return 'noop';
  if (currentFilterRows.length === 0) return 'add_or_build_filters';
  return 'replace_or_normalize_filters';
}

function chooseSortAction(expectedSorts, currentSortRows, sortMissing) {
  if (expectedSorts.length === 0 && currentSortRows.length === 0) return 'noop';
  if (sortMissing.length === 0) return 'noop';
  if (currentSortRows.length === 0) return 'add_or_build_sorts';
  if (expectedSorts.length === 1 && currentSortRows.length >= 1 && sortFieldObserved(currentSortRows, expectedSorts[0]) && !sortDirectionObservedForField(currentSortRows, expectedSorts[0])) {
    return 'change_sort_direction';
  }
  return 'replace_or_normalize_sorts';
}

export function buildAirtableViewChangePlan(target, filterState, sortState) {
  const synthetic = {
    target,
    before_filter: filterState,
    after_filter: filterState,
    before_sort: sortState,
    after_sort: sortState
  };
  const comparison = compareAirtablePanelReadback(synthetic);
  const missingUnique = Array.from(new Set((comparison.missing || []).map(stripPhasePrefix).filter(Boolean)));
  const filterMissing = missingUnique.filter((message) => /^filter\b/i.test(message));
  const sortMissing = missingUnique.filter((message) => /^sort\b/i.test(message));
  const expectedFilters = target.expected_filters || [];
  const expectedSorts = target.expected_sorts || [];
  const currentFilterRows = summarizeRows(filterState).filter((row) => !/^in this view, show records$/i.test(row.text) && !/^add condition$/i.test(row.text));
  const currentSortRows = summarizeRows(sortState).filter((row) => !/^add another sort$/i.test(row.text));
  const filterAction = chooseFilterAction(expectedFilters, currentFilterRows, filterMissing);
  const sortAction = chooseSortAction(expectedSorts, currentSortRows, sortMissing);
  const requiresMutation = missingUnique.length > 0 || filterAction !== 'noop' || sortAction !== 'noop';
  const planConsistency = {
    missing_requires_mutation: missingUnique.length > 0 ? requiresMutation === true : true,
    missing_count: missingUnique.length,
    filter_missing_count: filterMissing.length,
    sort_missing_count: sortMissing.length
  };

  return {
    timestamp_utc: nowIso(),
    tool_version: AIRTABLE_PANEL_DISCOVERY_VERSION,
    readback_version: AIRTABLE_PANEL_READBACK_VERSION,
    target: {
      table_name: target.table_name,
      view_name: target.view_name,
      table_id: target.table_id,
      view_key: target.view_key || `${norm(target.table_name)}::${norm(target.view_name)}`
    },
    expected: {
      filters: expectedFilters,
      sorts: expectedSorts
    },
    current: {
      filters: currentFilterRows,
      sorts: currentSortRows
    },
    comparison: {
      ok: comparison.ok,
      missing_unique: missingUnique,
      missing_raw: comparison.missing || []
    },
    planned_actions: {
      filter_action: filterAction,
      sort_action: sortAction,
      requires_mutation: requiresMutation,
      safe_to_execute_without_option_discovery: false,
      required_pre_execute_gate: 'discover selectable options for each intended field/operator/value/sort-direction control before mutation',
      plan_consistency: planConsistency
    }
  };
}

function rowIndexForElement(element, rows) {
  if (!Array.isArray(rows) || rows.length < 1) return null;
  const cy = Number(element.cy || element.y || 0);
  let best = null;
  let bestDistance = Infinity;
  for (const row of rows) {
    const rowY = Number(row.y || 0);
    const distance = Math.abs(cy - rowY);
    if (distance < bestDistance) {
      best = row.index || row.row_index || null;
      bestDistance = distance;
    }
  }
  return bestDistance <= 80 ? best : null;
}

function classifyControl(element) {
  const content = lowerText(`${element.text || ''} ${element.aria || ''} ${element.placeholder || ''} ${element.value || ''}`);
  const tag = String(element.tag || '').toLowerCase();
  const role = String(element.role || '').toLowerCase();
  const type = String(element.type || '').toLowerCase();
  if (type === 'checkbox') return 'checkbox';
  if (tag === 'input' || tag === 'textarea' || element.placeholder) return 'input';
  if (role === 'button' || tag === 'button') return 'button';
  if (/add condition|add another sort|pick another field to sort by/.test(content)) return 'add-control';
  if (/remove|delete/.test(content)) return 'remove-control';
  if (/copy from another view/.test(content)) return 'copy-control';
  return 'text-or-container';
}

function likelyDropdownTrigger(element) {
  const kind = classifyControl(element);
  const content = lowerText(`${element.text || ''} ${element.aria || ''} ${element.placeholder || ''} ${element.value || ''}`);
  if (!['button', 'text-or-container'].includes(kind)) return false;
  if (!content || content.length > 100) return false;
  if (/add condition|add another sort|pick another field to sort by|copy from another view|remove|delete|filter|sort by|automatically sort/.test(content)) return false;
  if (Number(element.w || 0) > 360 || Number(element.h || 0) > 60) return false;
  return true;
}

export function buildPanelControlInventory(panelExtraction) {
  const rawElements = panelExtraction?.raw_elements || [];
  const rows = panelExtraction?.rows || [];
  const controls = rawElements.map((element, index) => {
    const text = normalizeText(`${element.text || ''}`);
    const aria = normalizeText(`${element.aria || ''}`);
    const placeholder = normalizeText(`${element.placeholder || ''}`);
    const value = normalizeText(`${element.value || ''}`);
    const content = normalizeText([text, aria, placeholder, value].filter(Boolean).join(' | '));
    return {
      index: index + 1,
      kind: classifyControl(element),
      likely_dropdown_trigger: likelyDropdownTrigger(element),
      row_index: rowIndexForElement(element, rows),
      tag: element.tag || '',
      role: element.role || '',
      type: element.type || '',
      text,
      aria,
      placeholder,
      value,
      content,
      x: element.x,
      y: element.y,
      w: element.w,
      h: element.h,
      cx: element.cx,
      cy: element.cy
    };
  });

  const triggers = controls.filter((control) => control.likely_dropdown_trigger).sort((a, b) => {
    const aRow = a.row_index || 999;
    const bRow = b.row_index || 999;
    return aRow - bRow || Number(a.y || 0) - Number(b.y || 0) || Number(a.x || 0) - Number(b.x || 0);
  });

  return {
    rows: summarizeRows(panelExtraction),
    control_count: controls.length,
    dropdown_trigger_count: triggers.length,
    controls,
    dropdown_triggers: triggers
  };
}

async function readVisibleOptionOverlay(page, trigger, label) {
  return await page.evaluate(({ trigger, label }) => {
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
    const tx = Number(trigger.x || 0);
    const ty = Number(trigger.y || 0);
    const tw = Number(trigger.w || 0);
    const th = Number(trigger.h || 0);
    const search = {
      xMin: Math.max(250, tx - 80),
      xMax: Math.min(window.innerWidth - 20, tx + Math.max(tw, 160) + 520),
      yMin: Math.max(90, ty - 35),
      yMax: Math.min(window.innerHeight - 20, ty + Math.max(th, 30) + 520)
    };
    const triggerText = normalize(trigger.content || trigger.text || '').toLowerCase();
    const reject = /hide fields|filtered by|sort by|in this view|automatically sort records|copy from another view|add condition$|add another sort$|row colors|row height|view list options|open .* column menu|insert new record|add record/i;
    const nodes = Array.from(document.querySelectorAll('[role="option"], [role="menuitem"], [role="menu"], [role="listbox"], [data-testid], button, [role="button"], div, span'));
    const options = nodes.map((el) => {
      const box = el.getBoundingClientRect();
      const text = normalize(el.innerText || el.textContent || el.getAttribute('aria-label') || '');
      const aria = normalize(el.getAttribute('aria-label') || '');
      const role = el.getAttribute('role') || '';
      return {
        text,
        aria,
        role,
        tag: el.tagName || '',
        x: Math.round(box.x),
        y: Math.round(box.y),
        w: Math.round(box.width),
        h: Math.round(box.height),
        top: topVisible(el, box)
      };
    }).filter((item) => {
      if (!item.top) return false;
      if (!item.text || item.text.length > 120) return false;
      if (reject.test(item.text) || reject.test(item.aria)) return false;
      if (item.w < 10 || item.h < 8 || item.w > 560 || item.h > 90) return false;
      if (item.x < search.xMin || item.x > search.xMax || item.y < search.yMin || item.y > search.yMax) return false;
      const t = item.text.toLowerCase();
      if (t === triggerText) return false;
      return true;
    });
    const seen = new Set();
    const unique = [];
    for (const option of options) {
      const key = `${option.text.toLowerCase()}|${option.role}|${option.x}|${option.y}`;
      if (seen.has(key)) continue;
      seen.add(key);
      unique.push({ text: option.text, aria: option.aria, role: option.role, tag: option.tag, x: option.x, y: option.y, w: option.w, h: option.h });
    }
    const likelyOpened = unique.some((item) => ['option', 'menuitem'].includes(String(item.role || '').toLowerCase())) || unique.length >= 2;
    return { label, trigger, search_bounds: search, overlay_open_observed: likelyOpened, option_count: likelyOpened ? unique.length : 0, options: likelyOpened ? unique.slice(0, 80) : [] };
  }, { trigger, label });
}

function triggerPriority(control, panelKind) {
  const content = lowerText(control.content || '');
  if (!control.row_index) return 1000;
  let score = control.row_index * 100;
  if (panelKind === 'sort') {
    if (/a\s*->\s*z|z\s*->\s*a|1\s*->\s*9|9\s*->\s*1|earliest\s*->\s*latest|latest\s*->\s*earliest/.test(content)) score -= 40;
    if (/^[a-z0-9_ -]+$/i.test(content) && !/->/.test(content)) score -= 20;
  } else {
    if (/contains|is|is not|on or before|on or after|before|after/.test(content)) score -= 30;
    if (/enter a value|enter a date|today|tomorrow|yesterday|exact date/.test(content)) score -= 40;
  }
  return score;
}

export async function probePanelDropdownOptions(page, panelKind, inventory, options = {}) {
  const maxProbes = Math.max(0, Number(options.maxDropdownProbes || 0));
  if (!maxProbes) return [];
  const rowControls = (inventory.dropdown_triggers || [])
    .filter((trigger) => trigger.row_index && trigger.kind !== 'add-control' && trigger.kind !== 'remove-control')
    .sort((a, b) => triggerPriority(a, panelKind) - triggerPriority(b, panelKind) || Number(a.y || 0) - Number(b.y || 0) || Number(a.x || 0) - Number(b.x || 0));

  // Deduplicate nested Airtable elements for the same visible control. Prefer explicit role=button,
  // then the largest clickable rectangle for the same row/content/band. This avoids probing five
  // wrappers around the same "A -> Z" control and missing the real option overlay.
  const grouped = new Map();
  for (const trigger of rowControls) {
    const content = lowerText(trigger.content || '');
    const directionBand = /a\s*->\s*z|z\s*->\s*a|1\s*->\s*9|9\s*->\s*1|earliest\s*->\s*latest|latest\s*->\s*earliest/.test(content) ? 'direction' : 'field-or-value';
    const key = `${panelKind}|${trigger.row_index}|${directionBand}|${content}`;
    const current = grouped.get(key);
    if (!current) {
      grouped.set(key, trigger);
      continue;
    }
    const currentButton = String(current.role || '').toLowerCase() === 'button';
    const triggerButton = String(trigger.role || '').toLowerCase() === 'button';
    const currentArea = Number(current.w || 0) * Number(current.h || 0);
    const triggerArea = Number(trigger.w || 0) * Number(trigger.h || 0);
    if ((triggerButton && !currentButton) || (triggerButton === currentButton && triggerArea > currentArea)) {
      grouped.set(key, trigger);
    }
  }

  const triggers = Array.from(grouped.values())
    .sort((a, b) => triggerPriority(a, panelKind) - triggerPriority(b, panelKind) || Number(a.y || 0) - Number(b.y || 0) || Number(a.x || 0) - Number(b.x || 0))
    .slice(0, maxProbes);

  const probes = [];
  for (const trigger of triggers) {
    await safeMousePark(page, `before-dropdown-probe-${panelKind}-${trigger.index}`).catch(() => {});
    await page.mouse.click(Number(trigger.cx || (trigger.x + trigger.w / 2)), Number(trigger.cy || (trigger.y + trigger.h / 2))).catch(() => {});
    await page.waitForTimeout(850).catch(() => {});
    const overlay = await readVisibleOptionOverlay(page, trigger, `${panelKind}-trigger-${trigger.index}`);
    probes.push({
      panel_kind: panelKind,
      trigger_index: trigger.index,
      row_index: trigger.row_index,
      trigger_text: trigger.content,
      trigger_kind: trigger.kind,
      trigger_role: trigger.role,
      trigger_bounds: { x: trigger.x, y: trigger.y, w: trigger.w, h: trigger.h, cx: trigger.cx, cy: trigger.cy },
      overlay_open_observed: Boolean(overlay.overlay_open_observed),
      search_bounds: overlay.search_bounds,
      option_count: overlay.option_count,
      options: uniqueByText(overlay.options || [])
    });
    await page.keyboard.press('Escape').catch(() => {});
    await page.waitForTimeout(350).catch(() => {});
  }
  return probes;
}

export async function captureAirtablePanelDiscovery(page, outputDir, target, kind, phase, options = {}) {
  const opened = await openAirtablePanel(page, kind);
  await page.waitForTimeout(400).catch(() => {});
  const extracted = await extractOpenAirtablePanel(page, kind);
  const inventory = buildPanelControlInventory(extracted);
  const dropdown_probes = options.probeDropdownOptions
    ? await probePanelDropdownOptions(page, kind, inventory, options)
    : [];
  const snapshot = await captureDomEvidence(page, outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_${phase}_${kind}_discovery`, options);
  const discovery = {
    timestamp_utc: nowIso(),
    tool_version: AIRTABLE_PANEL_DISCOVERY_VERSION,
    readback_version: AIRTABLE_PANEL_READBACK_VERSION,
    target,
    phase,
    kind,
    opened,
    panel_extraction: { ok: extracted.ok, reason: extracted.reason || null, panel: extracted.panel || null },
    rows: extracted.rows || [],
    inventory,
    dropdown_probes,
    snapshot,
    safety: {
      read_only: true,
      mutation_controls_clicked: false,
      option_probe_mode: Boolean(options.probeDropdownOptions),
      note: 'Discovery opens panels and may open dropdowns to read options, but it does not type values, select options, add rows, remove rows, or save changes.'
    }
  };
  const discoveryPath = path.join(outputDir, `${safeName(target.table_name)}_${safeName(target.view_name)}_${phase}_${kind}_discovery.json`);
  writeJson(discoveryPath, discovery);
  await closeOpenAirtablePanel(page);
  return { ...discovery, discovery_path: discoveryPath };
}
