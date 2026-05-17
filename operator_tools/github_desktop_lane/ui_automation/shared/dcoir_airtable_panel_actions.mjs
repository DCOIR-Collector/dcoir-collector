import path from 'node:path';
import { safeName, nowIso, writeJson } from './dcoir_ui_common.mjs';
import {
  AIRTABLE_PANEL_READBACK_VERSION,
  captureDomEvidence,
  openAirtablePanel,
  closeOpenAirtablePanel,
  extractOpenAirtablePanel
} from './dcoir_airtable_panel_readback.mjs';

export const AIRTABLE_PANEL_ACTIONS_VERSION = '2026-05-17.panel-actions.8-export-dropdown-scroll';

function normalizeText(value) {
  return String(value || '')
    .replace(/[\u2192\u27f6\u2794]/g, ' -> ')
    .replace(/[\u2026]/g, '...')
    .replace(/\s+/g, ' ')
    .trim();
}

function lowerText(value) {
  return normalizeText(value).toLowerCase();
}

function regexEscape(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function exactTextPattern(value) {
  return new RegExp(`^${regexEscape(normalizeText(value))}$`, 'i');
}

function fieldToken(fieldName) {
  return lowerText(fieldName).replace(/\s+/g, '_');
}

function rowText(row) {
  return lowerText(`${row?.text || ''} ${Object.values(row?.cells || {}).join(' ')}`);
}

function isInstructionFilterRow(row) {
  const text = rowText(row);
  return !text || /in this view, show records|add condition|learn more about filtering/.test(text);
}

export function isExpectedRelativeDateFilterRow(row, spec = {}) {
  const text = rowText(row);
  if (!text) return false;
  const field = fieldToken(spec.field || '');
  const operator = lowerText(spec.operator || '').replace(/^is\s+/, '');
  const value = lowerText(spec.value || '');
  return text.includes(field)
    && text.includes(operator)
    && (!value || text.includes(value));
}

export function summarizeFilterRowsForField(panelState, fieldName) {
  const wanted = fieldToken(fieldName);
  const rows = Array.isArray(panelState?.rows) ? panelState.rows : [];
  return rows
    .filter((row) => !isInstructionFilterRow(row))
    .filter((row) => rowText(row).includes(wanted))
    .map((row) => ({ ...row, normalized_text: rowText(row) }));
}

function clickableElementFromRow(row, matcher, fallbackPoint = null) {
  const elements = Array.isArray(row?.elements) ? row.elements : [];
  const matches = elements
    .filter((element) => {
      const text = lowerText(`${element.text || ''} ${element.aria || ''} ${element.placeholder || ''} ${element.value || ''}`);
      return matcher(element, text);
    })
    .sort((a, b) => {
      const aButton = String(a.role || '').toLowerCase() === 'button' ? 0 : 1;
      const bButton = String(b.role || '').toLowerCase() === 'button' ? 0 : 1;
      const areaA = Number(a.w || 0) * Number(a.h || 0);
      const areaB = Number(b.w || 0) * Number(b.h || 0);
      return aButton - bButton || areaA - areaB || Number(a.x || 0) - Number(b.x || 0);
    });
  const element = matches[0];
  if (element) {
    return {
      x: Number(element.cx ?? (Number(element.x || 0) + Number(element.w || 0) / 2)),
      y: Number(element.cy ?? (Number(element.y || 0) + Number(element.h || 0) / 2)),
      source: { text: element.text || '', aria: element.aria || '', role: element.role || '', x: element.x, y: element.y, w: element.w, h: element.h }
    };
  }
  return fallbackPoint ? { ...fallbackPoint, source: { fallback: true } } : null;
}

function chooseFieldPoint(row, fieldName, panel) {
  const wanted = fieldToken(fieldName);
  return clickableElementFromRow(row, (element, text) => {
    if (String(element.role || '').toLowerCase() !== 'button') return false;
    return text === wanted || text.includes(wanted);
  }, { x: Number(panel?.x || 285) + 150, y: Number(row?.y || Number(panel?.y || 129) + 138) });
}

function chooseOperatorPoint(row, panel) {
  return clickableElementFromRow(row, (element, text) => {
    if (String(element.role || '').toLowerCase() !== 'button') return false;
    if (/remove item|reorder item/.test(text)) return false;
    return /^(is|is not|is on or before|is on or after|is before|is after|contains|does not contain)/.test(text);
  }, { x: Number(panel?.x || 285) + 276, y: Number(row?.y || Number(panel?.y || 129) + 138) });
}

function chooseValuePoint(row, panel) {
  return clickableElementFromRow(row, (element, text) => {
    if (String(element.role || '').toLowerCase() !== 'button') return false;
    if (/remove item|reorder item/.test(text)) return false;
    return /today|tomorrow|yesterday|exact date|enter a date|this week|this month|gmt|cest/.test(text);
  }, { x: Number(panel?.x || 285) + 450, y: Number(row?.y || Number(panel?.y || 129) + 138) });
}

async function clickPoint(page, point, label, steps) {
  if (!point || !Number.isFinite(Number(point.x)) || !Number.isFinite(Number(point.y))) {
    throw new Error(`Cannot click ${label}: missing finite coordinates.`);
  }
  await page.mouse.click(Math.round(Number(point.x)), Math.round(Number(point.y)));
  const step = { action: label, x: Math.round(Number(point.x)), y: Math.round(Number(point.y)), source: point.source || null };
  if (steps) steps.push(step);
  return step;
}

async function clickVisibleOption(page, pattern, label, bounds = {}) {
  // Return the exact visible option coordinates from the DOM, then click them with
  // Playwright's native mouse. Airtable's custom dropdowns often ignore el.click()
  // synthetic DOM events even when the option node is visible and correctly matched.
  const found = await page.evaluate(({ source, flags, bounds, label }) => {
    const re = new RegExp(source, flags);
    const normalize = (s) => String(s || '').replace(/[\u2192\u27f6\u2794]/g, ' -> ').replace(/[\u2026]/g, '...').replace(/\s+/g, ' ').trim();
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
    const xMin = Number.isFinite(bounds.xMin) ? bounds.xMin : 0;
    const xMax = Number.isFinite(bounds.xMax) ? bounds.xMax : window.innerWidth;
    const yMin = Number.isFinite(bounds.yMin) ? bounds.yMin : 0;
    const yMax = Number.isFinite(bounds.yMax) ? bounds.yMax : window.innerHeight;
    const candidates = Array.from(document.querySelectorAll('[role="option"], [role="menuitem"], li, button, [role="button"], div, span'))
      .filter(visible)
      .map((el) => {
        const box = el.getBoundingClientRect();
        return {
          text: normalize(el.innerText || el.textContent || el.getAttribute('aria-label') || ''),
          aria: normalize(el.getAttribute('aria-label') || ''),
          role: el.getAttribute('role') || '',
          tag: el.tagName || '',
          x: box.x,
          y: box.y,
          w: box.width,
          h: box.height,
          cx: box.x + box.width / 2,
          cy: box.y + box.height / 2,
          area: box.width * box.height,
          top: topVisible(el, box)
        };
      })
      .filter((item) => {
        if (!item.top) return false;
        if (!item.text || item.text.length > 160) return false;
        if (!re.test(item.text) && !re.test(item.aria)) return false;
        if (item.x < xMin || item.x > xMax || item.y < yMin || item.y > yMax) return false;
        if (item.w < 8 || item.h < 8 || item.w > 720 || item.h > 120) return false;
        if (/help \/ quick tips|learn more about|sort records|filter records/.test(item.text.toLowerCase())) return false;
        return true;
      })
      .sort((a, b) => {
        const ar = ['option', 'menuitem'].includes(String(a.role || '').toLowerCase()) || String(a.tag || '').toLowerCase() === 'li' ? 0 : 1;
        const br = ['option', 'menuitem'].includes(String(b.role || '').toLowerCase()) || String(b.tag || '').toLowerCase() === 'li' ? 0 : 1;
        return ar - br || a.area - b.area || a.y - b.y || a.x - b.x;
      });
    const chosen = candidates[0];
    if (!chosen) return { ok: false, label, method: 'native-visible-option' };
    return {
      ok: true,
      label,
      method: 'native-visible-option',
      text: chosen.text,
      aria: chosen.aria,
      role: chosen.role,
      tag: chosen.tag,
      x: Math.round(chosen.x),
      y: Math.round(chosen.y),
      w: Math.round(chosen.w),
      h: Math.round(chosen.h),
      cx: Math.round(chosen.cx),
      cy: Math.round(chosen.cy)
    };
  }, { source: pattern.source, flags: pattern.flags, bounds, label });

  if (!found.ok) return found;
  await page.mouse.click(found.cx, found.cy).catch(async () => {
    await page.mouse.move(found.cx, found.cy).catch(() => {});
    await page.waitForTimeout(100).catch(() => {});
    await page.mouse.down().catch(() => {});
    await page.mouse.up().catch(() => {});
  });
  await page.waitForTimeout(650).catch(() => {});
  return found;
}


async function clickOptionFromCompositePopupText(page, pattern, label, bounds = {}, steps = null) {
  const result = await page.evaluate(({ source, flags, bounds, label }) => {
    const re = new RegExp(source, flags);
    const normalize = (s) => String(s || '')
      .replace(/[\u2192\u27f6\u2794]/g, ' -> ')
      .replace(/[\u2026]/g, '...')
      .replace(/\s+/g, ' ')
      .trim();
    function visible(el) {
      const style = window.getComputedStyle(el);
      const box = el.getBoundingClientRect();
      return style && style.visibility !== 'hidden' && style.display !== 'none' && box.width > 0 && box.height > 0;
    }
    function topVisibleAt(x, y, el) {
      const top = document.elementFromPoint(Math.max(0, Math.min(window.innerWidth - 1, x)), Math.max(0, Math.min(window.innerHeight - 1, y)));
      return !!top && (el === top || el.contains(top) || top.contains(el));
    }
    const xMin = Number.isFinite(bounds.xMin) ? bounds.xMin : 0;
    const xMax = Number.isFinite(bounds.xMax) ? bounds.xMax : window.innerWidth;
    const yMin = Number.isFinite(bounds.yMin) ? bounds.yMin : 0;
    const yMax = Number.isFinite(bounds.yMax) ? bounds.yMax : window.innerHeight;
    const menuNeedles = ['today', 'tomorrow', 'yesterday', 'one week ago', 'exact date'];
    const candidates = Array.from(document.querySelectorAll('div, [role="listbox"], [role="menu"], [class], [data-testid]'))
      .filter(visible)
      .map((el) => {
        const box = el.getBoundingClientRect();
        const raw = String(el.innerText || el.textContent || '');
        const text = normalize(raw);
        const lines = raw.split(/\n+/).map((line) => normalize(line)).filter(Boolean);
        return { el, box, text, lines, role: el.getAttribute('role') || '' };
      })
      .filter((item) => {
        const box = item.box;
        if (box.x < xMin - 60 || box.x > xMax + 60 || box.y < yMin - 80 || box.y > yMax + 80) return false;
        if (box.width < 80 || box.width > 520 || box.height < 60 || box.height > 460) return false;
        const lower = item.text.toLowerCase();
        if (/help \/ quick tips|sort records|filter records|learn more about/i.test(lower)) return false;
        const needleHits = menuNeedles.filter((needle) => lower.includes(needle)).length;
        if (needleHits < 3) return false;
        if (!item.lines.some((line) => re.test(line))) return false;
        return true;
      })
      .sort((a, b) => {
        const ar = ['listbox', 'menu'].includes(String(a.role || '').toLowerCase()) ? 0 : 1;
        const br = ['listbox', 'menu'].includes(String(b.role || '').toLowerCase()) ? 0 : 1;
        const areaA = a.box.width * a.box.height;
        const areaB = b.box.width * b.box.height;
        return ar - br || areaA - areaB || a.box.y - b.box.y || a.box.x - b.box.x;
      });
    const menu = candidates[0];
    if (!menu) return { ok: false, label, method: 'composite-popup-text', reason: 'no-composite-popup' };
    const targetIndex = menu.lines.findIndex((line) => re.test(line));
    if (targetIndex < 0) return { ok: false, label, method: 'composite-popup-text', reason: 'target-line-not-found', lines: menu.lines.slice(0, 14) };
    const box = menu.box;
    const rowHeight = Math.max(22, Math.min(40, box.height / Math.max(menu.lines.length, 1)));
    const clickX = Math.round(box.x + Math.min(Math.max(32, box.width * 0.28), box.width - 24));
    const clickY = Math.round(box.y + rowHeight * targetIndex + rowHeight / 2);
    if (!topVisibleAt(clickX, clickY, menu.el)) {
      return { ok: false, label, method: 'composite-popup-text', reason: 'click-point-not-top-visible', x: clickX, y: clickY, targetLine: menu.lines[targetIndex], lines: menu.lines.slice(0, 14) };
    }
    return {
      ok: true,
      label,
      method: 'composite-popup-text',
      targetLine: menu.lines[targetIndex],
      targetIndex,
      x: clickX,
      y: clickY,
      box: { x: Math.round(box.x), y: Math.round(box.y), w: Math.round(box.width), h: Math.round(box.height) },
      lines: menu.lines.slice(0, 14)
    };
  }, { source: pattern.source, flags: pattern.flags, bounds, label });
  if (result.ok && Number.isFinite(Number(result.x)) && Number.isFinite(Number(result.y))) {
    await page.mouse.click(Number(result.x), Number(result.y)).catch(async () => {
      await page.mouse.move(Number(result.x), Number(result.y)).catch(() => {});
      await page.waitForTimeout(100).catch(() => {});
      await page.mouse.down().catch(() => {});
      await page.mouse.up().catch(() => {});
    });
  }
  await page.waitForTimeout(700).catch(() => {});
  if (steps) steps.push({ action: label, ...result });
  return result;
}

async function scrollCandidateDropdown(page, bounds = {}, mode = 'top', offset = 0) {
  return page.evaluate(({ bounds, mode, offset }) => {
    const xMin = Number.isFinite(bounds.xMin) ? bounds.xMin : 0;
    const xMax = Number.isFinite(bounds.xMax) ? bounds.xMax : window.innerWidth;
    const yMin = Number.isFinite(bounds.yMin) ? bounds.yMin : 0;
    const yMax = Number.isFinite(bounds.yMax) ? bounds.yMax : window.innerHeight;
    function visible(el) {
      const style = window.getComputedStyle(el);
      const box = el.getBoundingClientRect();
      return style && style.visibility !== 'hidden' && style.display !== 'none' && box.width > 0 && box.height > 0;
    }
    function intersects(box) {
      return box.x + box.width >= xMin - 40
        && box.x <= xMax + 40
        && box.y + box.height >= yMin - 40
        && box.y <= yMax + 40;
    }
    const candidates = Array.from(document.querySelectorAll('div, [role="listbox"], [role="menu"], [data-testid], [class]'))
      .filter(visible)
      .map((el) => {
        const box = el.getBoundingClientRect();
        return {
          el,
          x: box.x,
          y: box.y,
          w: box.width,
          h: box.height,
          area: box.width * box.height,
          scrollHeight: el.scrollHeight,
          clientHeight: el.clientHeight,
          scrollTop: el.scrollTop,
          role: el.getAttribute('role') || '',
          text: String(el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 240)
        };
      })
      .filter((item) => {
        if (!intersects(item)) return false;
        if (item.w < 80 || item.w > 760 || item.h < 40 || item.h > 720) return false;
        if (item.scrollHeight <= item.clientHeight + 8) return false;
        if (/help \/ quick tips|sort records|filter records/i.test(item.text)) return false;
        return true;
      })
      .sort((a, b) => {
        const aRole = ['listbox', 'menu'].includes(String(a.role || '').toLowerCase()) ? 0 : 1;
        const bRole = ['listbox', 'menu'].includes(String(b.role || '').toLowerCase()) ? 0 : 1;
        return aRole - bRole || a.area - b.area || b.scrollHeight - a.scrollHeight || a.y - b.y;
      });
    const chosen = candidates[0];
    if (!chosen) return { ok: false, mode, reason: 'no-scrollable-dropdown-found' };
    const maxScroll = Math.max(0, chosen.el.scrollHeight - chosen.el.clientHeight);
    if (mode === 'top') chosen.el.scrollTop = 0;
    else if (mode === 'bottom') chosen.el.scrollTop = maxScroll;
    else if (mode === 'delta') chosen.el.scrollTop = Math.max(0, Math.min(maxScroll, chosen.el.scrollTop + Number(offset || 0)));
    else if (mode === 'position') chosen.el.scrollTop = Math.max(0, Math.min(maxScroll, Number(offset || 0)));
    chosen.el.dispatchEvent(new Event('scroll', { bubbles: true }));
    return {
      ok: true,
      mode,
      x: Math.round(chosen.x),
      y: Math.round(chosen.y),
      w: Math.round(chosen.w),
      h: Math.round(chosen.h),
      role: chosen.role,
      beforeScrollTop: Math.round(chosen.scrollTop),
      afterScrollTop: Math.round(chosen.el.scrollTop),
      maxScroll: Math.round(maxScroll)
    };
  }, { bounds, mode, offset });
}


async function findOpenDropdownBox(page, bounds = {}) {
  return page.evaluate(({ bounds }) => {
    const normalize = (s) => String(s || '')
      .replace(/[\u2192\u27f6\u2794]/g, ' -> ')
      .replace(/[\u2026]/g, '...')
      .replace(/\s+/g, ' ')
      .trim();
    function visible(el) {
      const style = window.getComputedStyle(el);
      const box = el.getBoundingClientRect();
      return style && style.visibility !== 'hidden' && style.display !== 'none' && box.width > 0 && box.height > 0;
    }
    function topVisibleAt(x, y, el) {
      const top = document.elementFromPoint(Math.max(0, Math.min(window.innerWidth - 1, x)), Math.max(0, Math.min(window.innerHeight - 1, y)));
      return !!top && (el === top || el.contains(top) || top.contains(el));
    }
    const xMin = Number.isFinite(bounds.xMin) ? bounds.xMin : 0;
    const xMax = Number.isFinite(bounds.xMax) ? bounds.xMax : window.innerWidth;
    const yMin = Number.isFinite(bounds.yMin) ? bounds.yMin : 0;
    const yMax = Number.isFinite(bounds.yMax) ? bounds.yMax : window.innerHeight;
    const menuNeedles = ['today', 'tomorrow', 'yesterday', 'one week ago', 'one week from now', 'one month ago', 'one month from now', 'exact date'];
    const candidates = Array.from(document.querySelectorAll('[role="listbox"], [role="menu"], [data-testid], [class], div'))
      .filter(visible)
      .map((el) => {
        const box = el.getBoundingClientRect();
        const text = normalize(el.innerText || el.textContent || el.getAttribute('aria-label') || '');
        const lower = text.toLowerCase();
        const needleHits = menuNeedles.filter((needle) => lower.includes(needle)).length;
        const centerX = box.x + box.width / 2;
        const centerY = box.y + Math.min(Math.max(24, box.height / 2), box.height - 12);
        return {
          el,
          role: el.getAttribute('role') || '',
          text,
          lower,
          needleHits,
          x: box.x,
          y: box.y,
          w: box.width,
          h: box.height,
          area: box.width * box.height,
          centerX,
          centerY,
          top: topVisibleAt(centerX, centerY, el),
          scrollHeight: el.scrollHeight,
          clientHeight: el.clientHeight,
          scrollTop: el.scrollTop
        };
      })
      .filter((item) => {
        if (!item.top) return false;
        if (item.w < 80 || item.w > 760 || item.h < 40 || item.h > 720) return false;
        if (item.x > xMax + 120 || item.x + item.w < xMin - 120 || item.y > yMax + 220 || item.y + item.h < yMin - 220) return false;
        if (/help \/ quick tips|sort records|filter records|learn more about/i.test(item.lower)) return false;
        if (item.needleHits < 3) return false;
        return true;
      })
      .sort((a, b) => {
        const ar = ['listbox', 'menu'].includes(String(a.role || '').toLowerCase()) ? 0 : 1;
        const br = ['listbox', 'menu'].includes(String(b.role || '').toLowerCase()) ? 0 : 1;
        return ar - br || b.needleHits - a.needleHits || a.area - b.area || a.y - b.y;
      });
    const chosen = candidates[0];
    if (!chosen) return { ok: false, reason: 'no-open-dropdown-box-found' };
    return {
      ok: true,
      role: chosen.role,
      x: Math.round(chosen.x),
      y: Math.round(chosen.y),
      w: Math.round(chosen.w),
      h: Math.round(chosen.h),
      centerX: Math.round(chosen.centerX),
      centerY: Math.round(chosen.centerY),
      needleHits: chosen.needleHits,
      scrollHeight: Math.round(chosen.scrollHeight || 0),
      clientHeight: Math.round(chosen.clientHeight || 0),
      scrollTop: Math.round(chosen.scrollTop || 0),
      text_sample: chosen.text.slice(0, 180)
    };
  }, { bounds });
}

async function mouseWheelOpenDropdownTowardOption(page, pattern, label, bounds = {}, steps = null) {
  const attempts = [];
  let dropdown = await findOpenDropdownBox(page, bounds).catch((error) => ({ ok: false, error: String(error?.message || error) }));
  let center = dropdown.ok
    ? { x: dropdown.centerX, y: dropdown.centerY }
    : {
        x: Math.round((Number(bounds.xMin || 0) + Number(bounds.xMax || (bounds.xMin || 0) + 400)) / 2),
        y: Math.round((Number(bounds.yMin || 0) + Number(bounds.yMax || (bounds.yMin || 0) + 420)) / 2)
      };

  const wheelPlan = [
    { name: 'pre-visible', dy: 0 },
    { name: 'wheel-up-large-1', dy: -900 },
    { name: 'wheel-up-large-2', dy: -900 },
    { name: 'wheel-up-large-3', dy: -900 },
    { name: 'wheel-up-small', dy: -360 },
    { name: 'wheel-down-small', dy: 360 },
    { name: 'wheel-down-large', dy: 900 },
    { name: 'wheel-up-reset', dy: -1400 }
  ];

  for (const wheel of wheelPlan) {
    dropdown = await findOpenDropdownBox(page, bounds).catch((error) => ({ ok: false, error: String(error?.message || error) }));
    if (dropdown.ok) center = { x: dropdown.centerX, y: dropdown.centerY };
    await page.mouse.move(center.x, center.y).catch(() => {});
    if (wheel.dy) await page.mouse.wheel(0, wheel.dy).catch(() => {});
    await page.waitForTimeout(wheel.dy ? 450 : 150).catch(() => {});
    const clicked = await clickVisibleOption(page, pattern, `${label}-${wheel.name}`, bounds);
    attempts.push({ method: wheel.name, dropdown, center, clicked });
    if (clicked.ok) {
      const step = { action: label, method: `mouse-wheel-${wheel.name}`, dropdown, center, ...clicked };
      if (steps) steps.push(step);
      return { ok: true, label, method: `mouse-wheel-${wheel.name}`, dropdown, center, attempts };
    }
  }

  if (steps) steps.push({ action: label, ok: false, method: 'mouse-wheel-dropdown-search', dropdown, center, attempts });
  return { ok: false, label, method: 'mouse-wheel-dropdown-search', dropdown, center, attempts };
}


async function pressHomeEnterForOpenDropdown(page, label, steps) {
  const before = await page.evaluate(() => {
    const active = document.activeElement;
    const box = active?.getBoundingClientRect ? active.getBoundingClientRect() : null;
    return {
      active_tag: active?.tagName || '',
      active_role: active?.getAttribute?.('role') || '',
      active_text: String(active?.innerText || active?.textContent || active?.getAttribute?.('aria-label') || active?.getAttribute?.('placeholder') || '').replace(/\s+/g, ' ').trim().slice(0, 160),
      active_x: box ? Math.round(box.x) : null,
      active_y: box ? Math.round(box.y) : null,
      active_w: box ? Math.round(box.width) : null,
      active_h: box ? Math.round(box.height) : null
    };
  }).catch((error) => ({ error: String(error?.message || error) }));

  const keySteps = [];
  for (const key of ['Home', 'Enter']) {
    await page.keyboard.press(key).catch(async () => {
      // Some Airtable menus only respond after a small mouse nudge/focus settle.
      await page.waitForTimeout(100).catch(() => {});
      await page.keyboard.press(key).catch(() => {});
    });
    keySteps.push(key);
    await page.waitForTimeout(key === 'Home' ? 350 : 700).catch(() => {});
  }

  const after = await page.evaluate(() => {
    const active = document.activeElement;
    const box = active?.getBoundingClientRect ? active.getBoundingClientRect() : null;
    return {
      active_tag: active?.tagName || '',
      active_role: active?.getAttribute?.('role') || '',
      active_text: String(active?.innerText || active?.textContent || active?.getAttribute?.('aria-label') || active?.getAttribute?.('placeholder') || '').replace(/\s+/g, ' ').trim().slice(0, 160),
      active_x: box ? Math.round(box.x) : null,
      active_y: box ? Math.round(box.y) : null,
      active_w: box ? Math.round(box.width) : null,
      active_h: box ? Math.round(box.height) : null
    };
  }).catch((error) => ({ error: String(error?.message || error) }));

  const result = { ok: true, label, method: 'keyboard-home-enter', keys: keySteps, active_before: before, active_after: after };
  if (steps) steps.push({ action: label, ...result });
  return result;
}

async function pressTypeaheadEnterForOpenDropdown(page, query, label, steps) {
  if (!query) return { ok: false, label, method: 'keyboard-typeahead-enter', reason: 'missing-query' };
  await page.keyboard.type(String(query), { delay: 30 }).catch(() => {});
  await page.waitForTimeout(300).catch(() => {});
  await page.keyboard.press('Enter').catch(() => {});
  await page.waitForTimeout(700).catch(() => {});
  const result = { ok: true, label, method: 'keyboard-typeahead-enter', query: String(query) };
  if (steps) steps.push({ action: label, ...result });
  return result;
}

export async function clickOptionWithDropdownScroll(page, pattern, query, label, bounds, steps) {
  const attempts = [];
  let clicked = await clickVisibleOption(page, pattern, `${label}-visible`, bounds);
  attempts.push({ method: 'visible-option', clicked });
  if (clicked.ok) {
    if (steps) steps.push({ action: label, method: 'visible-option', ...clicked });
    return clicked;
  }

  for (const scrollAttempt of [
    { mode: 'top', offset: 0 },
    { mode: 'delta', offset: 180 },
    { mode: 'delta', offset: 180 },
    { mode: 'delta', offset: 240 },
    { mode: 'bottom', offset: 0 },
    { mode: 'top', offset: 0 }
  ]) {
    const scrolled = await scrollCandidateDropdown(page, bounds, scrollAttempt.mode, scrollAttempt.offset).catch((error) => ({ ok: false, error: String(error?.message || error), ...scrollAttempt }));
    await page.waitForTimeout(250).catch(() => {});
    clicked = await clickVisibleOption(page, pattern, `${label}-scroll-${scrollAttempt.mode}`, bounds);
    attempts.push({ method: `scroll-${scrollAttempt.mode}`, scrolled, clicked });
    if (clicked.ok) {
      if (steps) steps.push({ action: label, method: `scroll-${scrollAttempt.mode}`, scrolled, ...clicked });
      return clicked;
    }
  }

  if (query) {
    await page.keyboard.type(String(query), { delay: 15 }).catch(() => {});
    await page.waitForTimeout(500).catch(() => {});
    clicked = await clickVisibleOption(page, pattern, `${label}-typeahead`, bounds);
    attempts.push({ method: 'typeahead-visible-option', clicked });
    if (clicked.ok) {
      if (steps) steps.push({ action: label, method: 'typeahead-visible-option', ...clicked });
      return clicked;
    }
  }

  // Airtable relative-date menus can be virtualized and only respond to native wheel
  // events. Try mouse-wheel scrolling over the opened popup before keyboard fallbacks.
  const wheelClicked = await mouseWheelOpenDropdownTowardOption(page, pattern, label, bounds, steps).catch((error) => ({ ok: false, method: 'mouse-wheel-dropdown-search', error: String(error?.message || error) }));
  attempts.push({ method: 'mouse-wheel-dropdown-search', clicked: wheelClicked });
  if (wheelClicked.ok) return { ok: true, label, method: wheelClicked.method || 'mouse-wheel-dropdown-search', attempts };

  // Final non-preferred fallback only. Composite popup text may include all options even
  // when the visible scroll position is elsewhere, so never use it before real option-node
  // search and native wheel attempts. The caller's panel readback remains authoritative.
  clicked = await clickOptionFromCompositePopupText(page, pattern, `${label}-composite-popup-final`, bounds, steps).catch((error) => ({ ok: false, method: 'composite-popup-text-final', error: String(error?.message || error) }));
  attempts.push({ method: 'composite-popup-text-final', clicked });
  if (clicked.ok) {
    return { ok: true, label, method: 'composite-popup-text-final', attempts };
  }

  // Airtable's relative-date dropdown can focus the selected control/list instead of exposing
  // each option as a clean clickable DOM node. Use keyboard as a final fallback only; the
  // caller performs post-action panel readback before trusting success.
  const keyboardHomeEnter = await pressHomeEnterForOpenDropdown(page, label, steps).catch((error) => ({ ok: false, method: 'keyboard-home-enter', error: String(error?.message || error) }));
  attempts.push({ method: 'keyboard-home-enter', clicked: keyboardHomeEnter });
  if (keyboardHomeEnter.ok) return { ok: true, label, method: 'keyboard-home-enter', attempts };

  if (query) {
    const keyboardTypeahead = await pressTypeaheadEnterForOpenDropdown(page, query, label, steps).catch((error) => ({ ok: false, method: 'keyboard-typeahead-enter', error: String(error?.message || error) }));
    attempts.push({ method: 'keyboard-typeahead-enter', clicked: keyboardTypeahead });
    if (keyboardTypeahead.ok) return { ok: true, label, method: 'keyboard-typeahead-enter', attempts };
  }

  if (steps) steps.push({ action: label, ok: false, method: 'dropdown-scroll-visible-option', bounds, attempts });
  return { ok: false, label, attempts };
}

async function clickOptionWithTypeahead(page, pattern, query, label, bounds, steps) {
  return clickOptionWithDropdownScroll(page, pattern, query, label, bounds, steps);
}

async function extractFilterPanel(page, label, steps = null) {
  const extracted = await extractOpenAirtablePanel(page, 'filter');
  if (steps) steps.push({ action: label, ok: extracted.ok, reason: extracted.reason || null, panel: extracted.panel || null, row_count: Array.isArray(extracted.rows) ? extracted.rows.length : 0 });
  return extracted;
}

async function addFirstFilterRow(page, panel, steps) {
  const clicked = await page.evaluate(() => {
    const normalize = (s) => String(s || '').replace(/\s+/g, ' ').trim();
    function visible(el) {
      const style = window.getComputedStyle(el);
      const box = el.getBoundingClientRect();
      return style && style.visibility !== 'hidden' && style.display !== 'none' && box.width > 0 && box.height > 0;
    }
    const candidates = Array.from(document.querySelectorAll('button, [role="button"], div, span'))
      .filter(visible)
      .map((el) => {
        const box = el.getBoundingClientRect();
        const text = normalize(el.innerText || el.textContent || el.getAttribute('aria-label') || '');
        return { el, text, role: el.getAttribute('role') || '', x: box.x, y: box.y, w: box.width, h: box.height };
      })
      .filter((item) => /^Add condition$/i.test(item.text) && item.x >= 250 && item.x <= 1250 && item.y >= 120 && item.y <= 500)
      .sort((a, b) => a.y - b.y || a.x - b.x);
    const chosen = candidates[0];
    if (!chosen) return { ok: false };
    chosen.el.click();
    return { ok: true, text: chosen.text, role: chosen.role, x: Math.round(chosen.x), y: Math.round(chosen.y), w: Math.round(chosen.w), h: Math.round(chosen.h) };
  });
  steps.push({ action: 'click_add_filter_condition', ...clicked });
  if (!clicked.ok) throw new Error('Could not click Add condition in filter panel.');
  await page.waitForTimeout(850).catch(() => {});
}

async function setFilterField(page, panel, row, spec, steps) {
  const point = chooseFieldPoint(row, spec.field, panel);
  await clickPoint(page, point, 'open_filter_field_control', steps);
  await page.waitForTimeout(450).catch(() => {});
  const bounds = { xMin: Math.max(250, point.x - 160), xMax: Math.min(1450, point.x + 620), yMin: Math.max(80, point.y - 80), yMax: Math.min(900, point.y + 620) };
  const option = await clickOptionWithTypeahead(page, exactTextPattern(spec.field), spec.field, 'select_filter_field', bounds, steps);
  if (!option.ok) throw new Error(`Could not select filter field ${spec.field}.`);
}

async function setFilterOperator(page, panel, row, spec, steps) {
  const point = chooseOperatorPoint(row, panel);
  await clickPoint(page, point, 'open_filter_operator_control', steps);
  await page.waitForTimeout(450).catch(() => {});
  const desired = String(spec.operator || '').trim().replace(/^is\s+/i, '');
  const patterns = [];
  if (/on or before/i.test(desired)) patterns.push(/^is\s+on\s+or\s+before(\.{3}|…)?$/i, /^on\s+or\s+before(\.{3}|…)?$/i);
  else patterns.push(new RegExp(`^${regexEscape(desired)}(\\.{3}|…)?$`, 'i'));
  const bounds = { xMin: Math.max(250, point.x - 220), xMax: Math.min(1450, point.x + 560), yMin: Math.max(80, point.y - 80), yMax: Math.min(900, point.y + 620) };
  for (const pattern of patterns) {
    const option = await clickOptionWithTypeahead(page, pattern, `is ${desired}`, 'select_filter_operator', bounds, steps);
    if (option.ok) return;
  }
  throw new Error(`Could not select filter operator ${spec.operator}.`);
}

async function setRelativeDateValue(page, panel, row, spec, steps) {
  const point = chooseValuePoint(row, panel);
  await clickPoint(page, point, 'open_relative_date_value_control', steps);
  await page.waitForTimeout(500).catch(() => {});
  const bounds = { xMin: Math.max(250, point.x - 180), xMax: Math.min(1450, point.x + 620), yMin: Math.max(80, point.y - 120), yMax: Math.min(900, point.y + 620) };
  const value = String(spec.value || '').trim();
  const option = await clickOptionWithTypeahead(page, exactTextPattern(value), value, 'select_relative_date_value', bounds, steps);
  if (!option.ok) throw new Error(`Could not select relative date value ${value}.`);
}

function chooseSingleFilterRow(panelState, spec) {
  const rowsForField = summarizeFilterRowsForField(panelState, spec.field);
  if (rowsForField.length === 0) return null;
  if (rowsForField.length > 1) {
    throw new Error(`Refusing to normalize filter: found ${rowsForField.length} ${spec.field} rows.`);
  }
  return rowsForField[0];
}

export async function ensureSingleRelativeDateFilter(page, options = {}) {
  const spec = {
    field: options.field,
    operator: options.operator,
    value: options.value
  };
  if (!spec.field || !spec.operator || !spec.value) throw new Error('ensureSingleRelativeDateFilter requires field, operator, and value.');
  const outputDir = options.outputDir || process.cwd();
  const evidenceLabel = options.evidenceLabel || `${spec.field}_${spec.operator}_${spec.value}`;
  const screenshotOptions = options.screenshotOptions || {};
  const steps = [];
  const snapshots = [];

  const opened = await openAirtablePanel(page, 'filter');
  await page.waitForTimeout(600).catch(() => {});
  steps.push({ action: 'open_filter_panel', opened });
  let panelState = await extractFilterPanel(page, 'extract_filter_panel_initial', steps);
  let row = chooseSingleFilterRow(panelState, spec);

  if (row && isExpectedRelativeDateFilterRow(row, spec)) {
    await closeOpenAirtablePanel(page).catch(() => {});
    return { status: 'already_correct', steps, snapshots };
  }

  if (!row) {
    await addFirstFilterRow(page, panelState.panel, steps);
    snapshots.push(await captureDomEvidence(page, outputDir, `${safeName(evidenceLabel)}_filter_row_added`, screenshotOptions));
    panelState = await extractFilterPanel(page, 'extract_filter_panel_after_add', steps);
    row = chooseSingleFilterRow(panelState, spec) || (Array.isArray(panelState.rows) ? panelState.rows.find((candidate) => !isInstructionFilterRow(candidate)) : null);
    if (!row) throw new Error('Could not find a filter row after Add condition.');
  }

  const currentText = rowText(row);
  if (!currentText.includes(fieldToken(spec.field))) {
    await setFilterField(page, panelState.panel, row, spec, steps);
    await page.waitForTimeout(850).catch(() => {});
    panelState = await extractFilterPanel(page, 'extract_filter_panel_after_field', steps);
    row = chooseSingleFilterRow(panelState, spec);
    if (!row) throw new Error(`Could not verify filter field ${spec.field} after selection.`);
  }

  if (!isExpectedRelativeDateFilterRow(row, { ...spec, value: '' })) {
    await setFilterOperator(page, panelState.panel, row, spec, steps);
    await page.waitForTimeout(1000).catch(() => {});
    panelState = await extractFilterPanel(page, 'extract_filter_panel_after_operator', steps);
    row = chooseSingleFilterRow(panelState, spec);
    if (!row) throw new Error(`Could not verify filter row for ${spec.field} after operator selection.`);
  }

  if (!isExpectedRelativeDateFilterRow(row, spec)) {
    await setRelativeDateValue(page, panelState.panel, row, spec, steps);
    await page.waitForTimeout(1000).catch(() => {});
    panelState = await extractFilterPanel(page, 'extract_filter_panel_after_value', steps);
    row = chooseSingleFilterRow(panelState, spec);
  }

  snapshots.push(await captureDomEvidence(page, outputDir, `${safeName(evidenceLabel)}_filter_normalized`, screenshotOptions));
  const verified = row && isExpectedRelativeDateFilterRow(row, spec);
  const report = {
    timestamp_utc: nowIso(),
    shared_panel_actions_version: AIRTABLE_PANEL_ACTIONS_VERSION,
    shared_panel_readback_version: AIRTABLE_PANEL_READBACK_VERSION,
    status: verified ? 'relative_date_filter_verified' : 'relative_date_filter_gap_after_actions',
    spec,
    final_row: row ? { text: row.text || '', normalized_text: rowText(row), y: row.y, cells: row.cells || {} } : null,
    steps,
    snapshots
  };
  writeJson(path.join(outputDir, `${safeName(evidenceLabel)}_panel_action_report.json`), report);
  await closeOpenAirtablePanel(page).catch(() => {});
  if (!verified) throw new Error(`Relative date filter action failed to verify ${spec.field} ${spec.operator} ${spec.value}.`);
  return report;
}
