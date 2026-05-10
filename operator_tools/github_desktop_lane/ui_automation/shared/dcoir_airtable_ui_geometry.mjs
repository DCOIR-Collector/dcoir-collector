// DCOIR Airtable UI geometry-safe primitives
// Version: 2026-05-10.panel-readback-geometry.1

export const AIRTABLE_UI_GEOMETRY_VERSION = '2026-05-10.panel-readback-geometry.1';

export async function safeMousePark(page, reason = 'safe-mouse-park') {
  const viewport = page.viewportSize ? page.viewportSize() : null;
  const width = viewport?.width || 1500;
  const height = viewport?.height || 980;
  const x = Math.max(900, Math.min(width - 120, 1320));
  const y = Math.max(620, Math.min(height - 120, 860));
  await page.mouse.move(x, y).catch(() => {});
  await page.waitForTimeout(120).catch(() => {});
  return { action: 'safe_mouse_park', reason, x, y, ok: true };
}

export async function dismissTransientUi(page, reason = 'dismiss-transient-ui') {
  const parked = await safeMousePark(page, reason);
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(250).catch(() => {});
  return { action: 'dismiss_transient_ui', reason, parked, ok: true };
}

export async function clickAirtableViewInSidebar(page, viewName, options = {}) {
  const xMin = options.xMin ?? 40;
  const xMax = options.xMax ?? 420;
  const yMin = options.yMin ?? 240;
  const iconAvoidWidth = options.iconAvoidWidth ?? 82;

  await dismissTransientUi(page, 'before-click-sidebar-view');

  const picked = await page.evaluate(({ name, xMin, xMax, yMin, iconAvoidWidth }) => {
    const normalize = (s) => String(s || '').replace(/\s+/g, ' ').trim();
    function visible(el) {
      const style = window.getComputedStyle(el);
      const box = el.getBoundingClientRect();
      return style && style.visibility !== 'hidden' && style.display !== 'none' && box.width > 0 && box.height > 0;
    }

    const nodes = Array.from(document.querySelectorAll('button, [role="button"], div, span, a'));
    const candidates = nodes.map((el) => {
      const box = el.getBoundingClientRect();
      return { el, text: normalize(el.innerText || el.textContent), x: box.x, y: box.y, w: box.width, h: box.height };
    }).filter((c) => {
      if (!visible(c.el)) return false;
      if (c.text !== name) return false;
      if (c.x < xMin || c.x > xMax || c.y < yMin || c.w < 20 || c.h < 8) return false;
      return true;
    }).sort((a, b) => a.y - b.y || a.x - b.x || (a.w * a.h) - (b.w * b.h));

    const c = candidates[0];
    if (!c) return null;
    c.el.scrollIntoView({ block: 'center', inline: 'center' });
    const box = c.el.getBoundingClientRect();
    const clickX = Math.round(Math.min(box.right - 8, Math.max(box.left + iconAvoidWidth, box.left + (box.width * 0.55))));
    const clickY = Math.round(box.top + (box.height / 2));
    const target = document.elementFromPoint(clickX, clickY) || c.el;
    target.click();
    return {
      selector: 'geometry:airtable-left-sidebar-view-row',
      text: c.text,
      x: Math.round(box.x),
      y: Math.round(box.y),
      w: Math.round(box.width),
      h: Math.round(box.height),
      click_x: clickX,
      click_y: clickY,
      avoided_left_icon_width: iconAvoidWidth
    };
  }, { name: viewName, xMin, xMax, yMin, iconAvoidWidth });

  await page.waitForTimeout(450).catch(() => {});
  const parked = await safeMousePark(page, 'after-click-sidebar-view-avoid-metadata-tooltip');
  return picked ? { ok: true, ...picked, parked } : { ok: false, selector: 'geometry:airtable-left-sidebar-view-row', text: viewName, parked };
}

export async function clickAirtableToolbarButton(page, kind, options = {}) {
  const label = String(kind || '').toLowerCase();
  const labelRegex = label === 'filter' ? /\bFilter\b|Filter rows/i : /\bSort\b|Sort rows|Sorted by/i;
  const xMin = options.xMin ?? 560;
  const xMax = options.xMax ?? 1450;
  const yMin = options.yMin ?? 75;
  const yMax = options.yMax ?? 165;
  const widthMax = options.widthMax ?? 220;
  const heightMax = options.heightMax ?? 48;

  await dismissTransientUi(page, `before-open-${label}-toolbar-button`);

  const roleNames = label === 'filter'
    ? [/^Filter rows$/i, /^Filter$/i]
    : [/^Sort rows$/i, /^Sort$/i, /^Sorted by/i];

  for (const name of roleNames) {
    const loc = page.getByRole('button', { name });
    const count = await loc.count().catch(() => 0);
    for (let i = 0; i < count; i += 1) {
      const item = loc.nth(i);
      const box = await item.boundingBox().catch(() => null);
      const visible = await item.isVisible().catch(() => false);
      if (!visible || !box) continue;
      if (box.y < yMin || box.y > yMax || box.x < xMin || box.x > xMax || box.width < 8 || box.width > widthMax || box.height < 8 || box.height > heightMax) continue;
      const text = String(await item.innerText().catch(() => '')).replace(/\s+/g, ' ').trim();
      const aria = await item.getAttribute('aria-label').catch(() => '');
      await item.click({ timeout: 3000 });
      await page.waitForTimeout(700).catch(() => {});
      await safeMousePark(page, `after-open-${label}-toolbar-button`);
      return { ok: true, selector: `role-toolbar-button:${label}`, text, aria: aria || '', x: Math.round(box.x), y: Math.round(box.y), w: Math.round(box.width), h: Math.round(box.height) };
    }
  }

  const picked = await page.evaluate(({ source, label, xMin, xMax, yMin, yMax, widthMax, heightMax }) => {
    const re = new RegExp(source, 'i');
    function visible(el) {
      const style = window.getComputedStyle(el);
      const box = el.getBoundingClientRect();
      return style && style.visibility !== 'hidden' && style.display !== 'none' && box.width > 0 && box.height > 0;
    }

    const candidates = Array.from(document.querySelectorAll('button, [role="button"]')).map((el) => {
      const box = el.getBoundingClientRect();
      const text = (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim();
      const aria = el.getAttribute('aria-label') || '';
      return { el, text, aria, x: box.x, y: box.y, w: box.width, h: box.height };
    }).filter((c) => {
      if (!visible(c.el)) return false;
      if (c.y < yMin || c.y > yMax || c.x < xMin || c.x > xMax || c.w < 8 || c.w > widthMax || c.h < 8 || c.h > heightMax) return false;
      if (label === 'filter' && (c.aria === 'Filter rows' || c.text === 'Filter' || c.text.startsWith('Filter'))) return true;
      if (label === 'sort' && (c.aria === 'Sort rows' || c.text === 'Sort' || c.text.startsWith('Sort') || c.text.startsWith('Sorted by'))) return true;
      return re.test(`${c.text} ${c.aria}`);
    }).sort((a, b) => (a.w * a.h) - (b.w * b.h) || a.x - b.x);

    const c = candidates[0];
    if (!c) return null;
    c.el.click();
    return { selector: `geometry:airtable-toolbar-${label}`, text: c.text, aria: c.aria, x: Math.round(c.x), y: Math.round(c.y), w: Math.round(c.w), h: Math.round(c.h) };
  }, { source: labelRegex.source, label, xMin, xMax, yMin, yMax, widthMax, heightMax });

  await page.waitForTimeout(700).catch(() => {});
  await safeMousePark(page, `after-open-${label}-toolbar-button-fallback`);
  return picked ? { ok: true, ...picked } : { ok: false, selector: `geometry:airtable-toolbar-${label}` };
}
