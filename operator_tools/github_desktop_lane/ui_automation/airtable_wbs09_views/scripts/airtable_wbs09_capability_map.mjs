#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const VERSION = '2026-05-10.wbs09-capability-map.4';

function parseArgs(argv) {
  const args = {
    manifest: null,
    outputDir: null,
    schemaJson: null,
    evidenceRoot: null,
    evidenceRootsJson: null,
    baseId: process.env.DCOIR_AIRTABLE_BASE_ID || null,
    noLiveSchema: false,
    requireLiveSchema: false,
    uiEvidenceCollected: false
  };
  for (let i = 2; i < argv.length; i += 1) {
    const a = argv[i];
    const next = () => argv[++i];
    if (a === '--manifest') args.manifest = next();
    else if (a === '--output-dir') args.outputDir = next();
    else if (a === '--schema-json') args.schemaJson = next();
    else if (a === '--evidence-root') args.evidenceRoot = next();
    else if (a === '--evidence-roots-json') args.evidenceRootsJson = next();
    else if (a === '--base-id') args.baseId = next();
    else if (a === '--no-live-schema') args.noLiveSchema = true;
    else if (a === '--require-live-schema') args.requireLiveSchema = true;
    else if (a === '--ui-evidence-collected') args.uiEvidenceCollected = true;
    else throw new Error(`Unknown argument: ${a}`);
  }
  return args;
}

function ensureDir(p) { fs.mkdirSync(p, { recursive: true }); }
function readJson(p) { return JSON.parse(fs.readFileSync(p, 'utf8').replace(/^\uFEFF/, '')); }
function writeJson(p, obj) { fs.writeFileSync(p, JSON.stringify(obj, null, 2), 'utf8'); }
function nowIso() { return new Date().toISOString(); }
function norm(s) { return String(s || '').replace(/\s+/g, ' ').trim(); }
function safeName(s) { return String(s).replace(/[^A-Za-z0-9_.-]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 120) || 'item'; }
function uniq(arr) { return Array.from(new Set(arr.filter(x => x !== null && x !== undefined && String(x).length > 0))); }

function getNestedTables(schema) {
  if (!schema) return [];
  if (Array.isArray(schema.tables)) return schema.tables;
  if (schema.base && Array.isArray(schema.base.tables)) return schema.base.tables;
  if (schema.schema && Array.isArray(schema.schema.tables)) return schema.schema.tables;
  if (schema.raw_schema && Array.isArray(schema.raw_schema.tables)) return schema.raw_schema.tables;
  return [];
}

function fieldKind(type) {
  const t = String(type || '').toLowerCase();
  if (t.includes('date')) return 'date';
  if (t.includes('checkbox') || t === 'boolean') return 'checkbox';
  if (t.includes('single') && t.includes('select')) return 'single_select';
  if (t.includes('multiple') && t.includes('select')) return 'multi_select';
  if (t.includes('number') || t.includes('currency') || t.includes('percent') || t.includes('rating') || t.includes('duration')) return 'number';
  if (t.includes('formula') || t.includes('rollup') || t.includes('lookup') || t.includes('count')) return 'computed';
  return 'text_like';
}

function choicesForField(field) {
  const opt = field?.options || {};
  const choices = opt.choices || opt.selectOptions || [];
  return Array.isArray(choices) ? choices.map(c => c.name || c.value || c.id || String(c)).filter(Boolean) : [];
}

async function fetchLiveAirtableSchema(baseId) {
  const token = process.env.DCOIR_AIRTABLE_TOKEN;
  if (!token || !token.trim()) {
    return { ok: false, reason: 'missing DCOIR_AIRTABLE_TOKEN', schema: null };
  }
  if (!baseId || !baseId.trim()) {
    return { ok: false, reason: 'missing DCOIR_AIRTABLE_BASE_ID or --base-id', schema: null };
  }
  if (typeof fetch !== 'function') {
    return { ok: false, reason: 'node fetch API unavailable', schema: null };
  }
  const url = `https://api.airtable.com/v0/meta/bases/${encodeURIComponent(baseId)}/tables`;
  const res = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  const text = await res.text();
  let body = null;
  try { body = text ? JSON.parse(text) : null; } catch (_) { body = { raw_text: text.slice(0, 500) }; }
  if (!res.ok) {
    return { ok: false, reason: `Airtable metadata API returned HTTP ${res.status}`, status: res.status, body, schema: null };
  }
  return { ok: true, reason: null, schema: body };
}

function buildSchemaIndex(tables) {
  const byTableName = new Map();
  const byTableId = new Map();
  for (const t of tables || []) {
    const table = {
      id: t.id || t.table_id || t.tableId || null,
      name: t.name || t.table_name || null,
      raw: t,
      fields: [],
      fieldsByName: new Map(),
      fieldsById: new Map(),
      views: Array.isArray(t.views) ? t.views.map(v => ({ id: v.id || v.view_id || null, name: v.name || v.view_name || null, type: v.type || v.view_type || null })) : []
    };
    for (const f of (t.fields || [])) {
      const field = {
        id: f.id || f.field_id || f.fieldId || null,
        name: f.name || f.field_name || null,
        type: f.type || f.field_type || null,
        kind: fieldKind(f.type || f.field_type),
        choices: choicesForField(f),
        raw: f
      };
      table.fields.push(field);
      if (field.name) table.fieldsByName.set(String(field.name).toLowerCase(), field);
      if (field.id) table.fieldsById.set(field.id, field);
    }
    if (table.name) byTableName.set(String(table.name).toLowerCase(), table);
    if (table.id) byTableId.set(table.id, table);
  }
  return { byTableName, byTableId, tables: Array.from(byTableName.values()) };
}

function classifyFilterPrimitive(filter, field) {
  const operator = String(filter.operator || '').toLowerCase();
  const value = filter.value;
  const kind = field?.kind || 'unknown_field';
  if (operator === 'on or before' && String(value).toLowerCase() === 'today') return 'filter.relative_date.on_or_before_today';
  if (kind === 'date') return `filter.date.${operator.replace(/\s+/g, '_')}`;
  if (kind === 'checkbox' && operator === 'is') return `filter.checkbox.is_${String(value).toLowerCase()}`;
  if ((kind === 'single_select' || kind === 'multi_select') && (operator.includes('one of') || operator.includes('any of'))) return `filter.select.multi_value.${operator.replace(/\s+/g, '_')}`;
  if (kind === 'single_select' || kind === 'multi_select') return `filter.select.${operator.replace(/\s+/g, '_')}`;
  if (operator === 'contains') return 'filter.text.contains';
  if (operator.includes('empty')) return `filter.empty.${operator.replace(/\s+/g, '_')}`;
  return `filter.${kind}.${operator.replace(/\s+/g, '_') || 'unknown_operator'}`;
}

function classifySortPrimitive(sort, field) {
  const direction = String(sort.direction || '').toLowerCase() === 'desc' ? 'desc' : 'asc';
  let kind = field?.kind || 'unknown_field';
  if (kind === 'unknown_field' && /date|time|after|before|confirmed|created|updated/i.test(String(sort.field || ''))) kind = 'date';
  return `sort.${kind}.${direction}`;
}

function schemaSupportsFilter(filter, field) {
  if (!field) return { supported: false, reason: 'field not found in schema' };
  const op = String(filter.operator || '').toLowerCase();
  const val = filter.value;
  if (field.kind === 'date' && op === 'on or before') return { supported: true, reason: 'date field supports relative date comparison in Airtable UI' };
  if (field.kind === 'checkbox' && op === 'is') return { supported: ['true','false'].includes(String(val).toLowerCase()), reason: 'checkbox field supports true/false equality' };
  if ((field.kind === 'single_select' || field.kind === 'multi_select') && Array.isArray(val)) {
    const missing = val.filter(v => !field.choices.includes(v));
    return { supported: missing.length === 0, reason: missing.length ? `missing choices: ${missing.join(', ')}` : 'all select choices exist' };
  }
  if (field.kind === 'single_select' || field.kind === 'multi_select') {
    const ok = !val || field.choices.includes(val);
    return { supported: ok, reason: ok ? 'select choice exists or value not required' : `missing choice: ${val}` };
  }
  if (op === 'contains') return { supported: true, reason: 'text-like contains supported by UI for this manifest family' };
  if (op.includes('empty')) return { supported: true, reason: 'empty/not-empty operator does not require value choices' };
  return { supported: true, reason: 'not proven unsupported by schema' };
}

function schemaSupportsSort(sort, field) {
  if (!field) return { supported: false, reason: 'field not found in schema' };
  return { supported: true, reason: `schema field kind ${field.kind} can be sorted by Airtable UI` };
}

function requiredControlsForFilter(filter, field) {
  const controls = [`field dropdown: ${filter.field}`, `operator dropdown: ${filter.operator}`];
  const primitive = classifyFilterPrimitive(filter, field);
  if (primitive === 'filter.relative_date.on_or_before_today') controls.push('relative date value dropdown: today');
  else if (filter.value !== undefined && filter.value !== null && String(filter.value).length) controls.push(`value control: ${Array.isArray(filter.value) ? filter.value.join(', ') : filter.value}`);
  return controls;
}

function requiredControlsForSort(sort) {
  return [`sort field dropdown: ${sort.field}`, `sort direction dropdown: ${sort.direction === 'desc' ? 'descending' : 'ascending'}`];
}

function isEvidenceDirectoryName(name) {
  return /^dcoir_wbs09_(view_discovery|view_panel_readback|apply_validation_due_view|apply_sort_direction)_/i.test(String(name || ''));
}

function listJsonFilesUnder(root, limit = 5000) {
  const out = [];
  if (!root || !fs.existsSync(root)) return out;
  const stack = [root];
  while (stack.length && out.length < limit) {
    const dir = stack.pop();
    let entries = [];
    try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch (_) { continue; }
    for (const e of entries) {
      const p = path.join(dir, e.name);
      if (e.isDirectory()) {
        if (/node_modules|\.git/i.test(e.name)) continue;
        stack.push(p);
      } else if (e.isFile() && e.name.toLowerCase().endsWith('.json')) {
        out.push(p);
      }
      if (out.length >= limit) break;
    }
  }
  return out;
}

function readEvidenceRootsJson(filePath) {
  if (!filePath || !fs.existsSync(filePath)) return [];
  const parsed = readJson(filePath);
  if (Array.isArray(parsed)) return parsed;
  if (Array.isArray(parsed.roots)) return parsed.roots;
  if (Array.isArray(parsed.evidence_roots)) return parsed.evidence_roots;
  return [];
}

function discoverEvidenceRoots(evidenceRoot, explicitRoots = []) {
  const roots = [];
  for (const r of explicitRoots || []) {
    if (r && fs.existsSync(r)) roots.push(r);
  }
  if (!evidenceRoot || !fs.existsSync(evidenceRoot)) return roots;

  // First, inspect only first-level DCOIR WBS09 evidence folders. This avoids a
  // large Downloads tree exhausting a generic JSON limit before reaching the
  // relevant evidence folders.
  let entries = [];
  try { entries = fs.readdirSync(evidenceRoot, { withFileTypes: true }); } catch (_) { entries = []; }
  for (const e of entries) {
    if (e.isDirectory() && isEvidenceDirectoryName(e.name)) roots.push(path.join(evidenceRoot, e.name));
  }

  // If the operator points directly at an evidence folder, include it too.
  const base = path.basename(evidenceRoot);
  if (isEvidenceDirectoryName(base)) roots.push(evidenceRoot);

  return uniq(roots.map(r => path.resolve(r)));
}

function inferKindFromPath(p) {
  if (/view_discovery/i.test(p)) return 'view_discovery';
  if (/view_panel_readback|panel_readback/i.test(p)) return 'panel_readback';
  if (/apply_validation_due/i.test(p)) return 'apply_validation_due';
  if (/apply_sort_direction/i.test(p)) return 'apply_sort_direction';
  return 'other';
}

function viewKeyFromReport(j) {
  if (j?.target?.view_key) return j.target.view_key;
  if (j?.target?.table_name && j?.target?.view_name) return `${j.target.table_name}::${j.target.view_name}`;
  if (j?.table_name && j?.view_name) return `${j.table_name}::${j.view_name}`;
  if (Array.isArray(j?.results) && j.results.length === 1) {
    const r = j.results[0];
    if (r?.target?.view_key) return r.target.view_key;
    if (r?.target?.table_name && r?.target?.view_name) return `${r.target.table_name}::${r.target.view_name}`;
    if (r?.table_name && r?.view_name) return `${r.table_name}::${r.view_name}`;
  }
  return null;
}

function missingFromReport(j) {
  const out = [];
  if (Array.isArray(j?.missing)) out.push(...j.missing);
  if (Array.isArray(j?.results)) {
    for (const r of j.results) if (Array.isArray(r?.missing)) out.push(...r.missing);
  }
  return out;
}

function addSignal(result, primitiveId, signal) {
  result.primitive_ui_signals[primitiveId] ||= [];
  result.primitive_ui_signals[primitiveId].push(signal);
}

function scanEvidence(evidenceRoot, explicitRoots = []) {
  const result = {
    root: evidenceRoot || null,
    evidence_roots_scanned: [],
    scanned_json_count: 0,
    reports: [],
    by_view_key: {},
    primitive_ui_signals: {}
  };

  const roots = discoverEvidenceRoots(evidenceRoot, explicitRoots);
  result.evidence_roots_scanned = roots;
  const files = [];
  for (const r of roots) files.push(...listJsonFilesUnder(r, 5000));

  for (const p of uniq(files)) {
    let j;
    try { j = readJson(p); } catch (_) { continue; }
    result.scanned_json_count += 1;
    const viewKey = viewKeyFromReport(j);
    const kind = j.kind || inferKindFromPath(p);
    const status = j.status || null;
    const missing = missingFromReport(j);
    result.reports.push({ path: p, kind, status, view_key: viewKey });
    if (viewKey) {
      result.by_view_key[viewKey] ||= { reports: [], statuses: [], missing: [], observed_text_signals: [] };
      result.by_view_key[viewKey].reports.push({ path: p, kind, status });
      if (status) result.by_view_key[viewKey].statuses.push(status);
      result.by_view_key[viewKey].missing.push(...missing);
    }

    const text = JSON.stringify(j).toLowerCase();
    const signalBase = { path: p, view_key: viewKey, status };

    if (text.includes('on or before') && text.includes('today')) {
      addSignal(result, 'filter.relative_date.on_or_before_today', { ...signalBase, signal: 'on or before today observed in evidence JSON' });
    }
    if (text.includes('exact date') && text.includes('enter a date')) {
      addSignal(result, 'filter.relative_date.exact_date_empty', { ...signalBase, signal: 'exact date empty/default state observed in evidence JSON' });
    }
    if (text.includes('earliest -> latest') || text.includes('ascending')) {
      addSignal(result, 'sort.date.asc', { ...signalBase, signal: 'ascending date sort option/state observed in evidence JSON' });
    }
    if (text.includes('z -> a') || text.includes('descending')) {
      addSignal(result, 'sort.text_like.desc', { ...signalBase, signal: 'descending sort option/state observed in evidence JSON' });
      addSignal(result, 'sort.date.desc', { ...signalBase, signal: 'descending sort option/state observed in evidence JSON' });
    }
    if (text.includes('a -> z') || text.includes('earliest -> latest') || text.includes('1 -> 9')) {
      addSignal(result, 'sort.text_like.asc', { ...signalBase, signal: 'ascending sort option/state observed in evidence JSON' });
      addSignal(result, 'sort.single_select.asc', { ...signalBase, signal: 'ascending sort option/state observed in evidence JSON' });
      addSignal(result, 'sort.number.asc', { ...signalBase, signal: 'ascending sort option/state observed in evidence JSON' });
    }
    if (text.includes('active') && text.includes('is') && text.includes('filter')) {
      addSignal(result, 'filter.select.=', { ...signalBase, signal: 'single-select equality UI signal observed in evidence JSON' });
    }
    if (text.includes('true') && text.includes('false') && text.includes('checkbox')) {
      addSignal(result, 'filter.checkbox.=', { ...signalBase, signal: 'checkbox true/false UI signal observed in evidence JSON' });
    }
  }
  return result;
}

function supportStatus(primitiveId, schemaOk, evidenceSignals) {
  const uiSignals = evidenceSignals[primitiveId] || [];
  const observed = uiSignals.length > 0;
  let applySupported = false;
  let status = 'needs_apply_hardening';
  if (primitiveId === 'sort.text_like.desc') {
    applySupported = true;
    status = 'guarded_apply_supported_existing_row_only';
  } else if (primitiveId.startsWith('sort.')) {
    status = observed ? 'ui_observed_apply_not_generalized' : 'schema_supported_ui_evidence_needed';
  } else if (primitiveId === 'filter.relative_date.on_or_before_today') {
    status = observed ? 'ui_observed_apply_not_ready' : 'schema_supported_ui_evidence_needed';
  } else if (schemaOk) {
    status = observed ? 'ui_observed_apply_not_ready' : 'schema_supported_ui_evidence_needed';
  } else {
    status = 'schema_gap_or_unknown';
  }
  return { ui_discovery_supported: observed, apply_supported: applySupported, status };
}

function markdownSummary(map) {
  const lines = [];
  lines.push(`# WBS09 Airtable Capability Map`);
  lines.push('');
  lines.push(`Generated: ${map.generated_utc}`);
  lines.push(`Tool version: ${map.tool_version}`);
  lines.push('');
  lines.push(`Views analyzed: ${map.summary.view_count}`);
  lines.push(`Tables in manifest: ${map.summary.manifest_table_count}`);
  lines.push(`Schema source: ${map.schema.source_status}`);
  lines.push(`Evidence JSON scanned: ${map.evidence.scanned_json_count}`);
  lines.push('');
  lines.push('## Primitive summary');
  lines.push('');
  lines.push('| Primitive | Manifest uses | Schema support | UI support | Apply support | Status |');
  lines.push('|---|---:|---|---|---|---|');
  for (const p of map.primitives) {
    lines.push(`| ${p.primitive_id} | ${p.manifest_use_count} | ${p.schema_supported ? 'yes' : 'no'} | ${p.ui_discovery_supported ? 'yes' : 'no'} | ${p.apply_supported ? 'yes' : 'no'} | ${p.status} |`);
  }
  lines.push('');
  lines.push('## Recommended next actions');
  lines.push('');
  for (const a of map.recommendations) lines.push(`- ${a}`);
  lines.push('');
  return lines.join('\n');
}

async function main() {
  const args = parseArgs(process.argv);
  if (!args.manifest) throw new Error('Missing --manifest');
  if (!args.outputDir) throw new Error('Missing --output-dir');
  ensureDir(args.outputDir);
  const manifest = readJson(args.manifest);
  const views = Array.isArray(manifest.views) ? manifest.views : [];
  const manifestTables = Array.isArray(manifest.tables) ? manifest.tables : [];

  let schemaSource = { source_status: 'none', warnings: [] };
  let schema = null;
  if (args.schemaJson) {
    schema = readJson(args.schemaJson);
    schemaSource = { source_status: 'schema-json', schema_json: args.schemaJson, warnings: [] };
  }
  if (!args.noLiveSchema) {
    const live = await fetchLiveAirtableSchema(args.baseId || manifest.base_id);
    if (live.ok) {
      schema = live.schema;
      schemaSource = { source_status: 'live-airtable-metadata-api', base_id: args.baseId || manifest.base_id, warnings: [] };
      writeJson(path.join(args.outputDir, 'airtable_schema_live_metadata.json'), schema);
    } else {
      schemaSource.warnings ||= [];
      schemaSource.warnings.push(`Live schema unavailable: ${live.reason}`);
      if (args.requireLiveSchema) throw new Error(`Live schema required but unavailable: ${live.reason}`);
    }
  }
  const schemaTables = getNestedTables(schema);
  const schemaIndex = buildSchemaIndex(schemaTables);
  const explicitEvidenceRoots = readEvidenceRootsJson(args.evidenceRootsJson);
  const evidence = scanEvidence(args.evidenceRoot, explicitEvidenceRoots);
  const primitiveMap = new Map();
  const viewAnalyses = [];

  function addPrimitive(entry) {
    const key = entry.primitive_id;
    if (!primitiveMap.has(key)) {
      primitiveMap.set(key, {
        primitive_id: key,
        category: entry.category,
        manifest_use_count: 0,
        schema_supported_count: 0,
        schema_gap_count: 0,
        example_views: [],
        required_controls: new Set(),
        schema_notes: [],
        ui_signals: []
      });
    }
    const p = primitiveMap.get(key);
    p.manifest_use_count += 1;
    if (entry.schema_supported) p.schema_supported_count += 1;
    else p.schema_gap_count += 1;
    if (p.example_views.length < 8) p.example_views.push(entry.view_key);
    for (const c of entry.required_controls || []) p.required_controls.add(c);
    if (entry.schema_reason) p.schema_notes.push(entry.schema_reason);
  }

  for (const view of views) {
    const table = schemaIndex.byTableName.get(String(view.table_name || '').toLowerCase()) || schemaIndex.byTableId.get(view.table_id);
    const viewEvidence = evidence.by_view_key[view.view_key] || null;
    const analysis = {
      view_key: view.view_key,
      table_name: view.table_name,
      view_name: view.view_name,
      table_id_manifest: view.table_id || null,
      table_id_schema: table?.id || null,
      table_schema_found: Boolean(table),
      view_name_seen_in_schema: Boolean(table?.views?.some(v => String(v.name || '').toLowerCase() === String(view.view_name || '').toLowerCase())),
      filters: [],
      sorts: [],
      evidence_summary: viewEvidence ? { statuses: uniq(viewEvidence.statuses), missing: uniq(viewEvidence.missing).slice(0, 20), report_count: viewEvidence.reports.length } : null
    };
    for (const filter of (view.filters || [])) {
      const field = table?.fieldsByName.get(String(filter.field || '').toLowerCase()) || null;
      const primitiveId = classifyFilterPrimitive(filter, field);
      const schemaSupport = schemaSupportsFilter(filter, field);
      const controls = requiredControlsForFilter(filter, field);
      analysis.filters.push({
        field: filter.field,
        operator: filter.operator,
        value: filter.value,
        field_id: field?.id || null,
        field_type: field?.type || null,
        field_kind: field?.kind || null,
        primitive_id: primitiveId,
        schema_supported: schemaSupport.supported,
        schema_reason: schemaSupport.reason,
        required_controls: controls
      });
      addPrimitive({ primitive_id: primitiveId, category: 'filter', view_key: view.view_key, schema_supported: schemaSupport.supported, schema_reason: schemaSupport.reason, required_controls: controls });
    }
    for (const sort of (view.sorts || [])) {
      const field = table?.fieldsByName.get(String(sort.field || '').toLowerCase()) || null;
      const primitiveId = classifySortPrimitive(sort, field);
      const schemaSupport = schemaSupportsSort(sort, field);
      const controls = requiredControlsForSort(sort);
      analysis.sorts.push({
        field: sort.field,
        direction: sort.direction,
        field_id: field?.id || null,
        field_type: field?.type || null,
        field_kind: field?.kind || null,
        primitive_id: primitiveId,
        schema_supported: schemaSupport.supported,
        schema_reason: schemaSupport.reason,
        required_controls: controls
      });
      addPrimitive({ primitive_id: primitiveId, category: 'sort', view_key: view.view_key, schema_supported: schemaSupport.supported, schema_reason: schemaSupport.reason, required_controls: controls });
    }
    viewAnalyses.push(analysis);
  }

  const primitives = Array.from(primitiveMap.values()).map(p => {
    const schemaSupported = p.schema_supported_count > 0 && p.schema_gap_count === 0;
    const support = supportStatus(p.primitive_id, schemaSupported, evidence.primitive_ui_signals);
    const uiSignals = evidence.primitive_ui_signals[p.primitive_id] || [];
    return {
      primitive_id: p.primitive_id,
      category: p.category,
      manifest_use_count: p.manifest_use_count,
      schema_supported: schemaSupported,
      schema_supported_count: p.schema_supported_count,
      schema_gap_count: p.schema_gap_count,
      ui_discovery_supported: support.ui_discovery_supported,
      apply_supported: support.apply_supported,
      status: support.status,
      example_views: p.example_views,
      known_ui_signal_count: uiSignals.length,
      known_ui_sample_views: uniq(uiSignals.map(s => s.view_key)).slice(0, 8),
      required_controls: Array.from(p.required_controls).slice(0, 30),
      schema_notes: uniq(p.schema_notes).slice(0, 10)
    };
  }).sort((a, b) => b.manifest_use_count - a.manifest_use_count || a.primitive_id.localeCompare(b.primitive_id));

  const recommendations = [];
  const rel = primitives.find(p => p.primitive_id === 'filter.relative_date.on_or_before_today');
  if (rel) {
    recommendations.push(`Build or harden apply primitive ${rel.primitive_id}; schema=${rel.schema_supported}, ui=${rel.ui_discovery_supported}, apply=${rel.apply_supported}, uses=${rel.manifest_use_count}.`);
  }
  recommendations.push('Keep browser actions gated by this map: schema-supported plus UI option evidence before mutation.');
  recommendations.push('Do not promote validation-due apply until after-click and independent panel readback both prove review_after on or before today.');

  const map = {
    generated_utc: nowIso(),
    tool_version: VERSION,
    safety: {
      read_only: true,
      airtable_api_mutation: false,
      browser_used: Boolean(args.uiEvidenceCollected),
      secret_values_logged: false
    },
    inputs: {
      manifest_path: args.manifest,
      evidence_root: args.evidenceRoot || null,
      evidence_roots_json: args.evidenceRootsJson || null,
      schema_json: args.schemaJson || null,
      collect_ui_evidence: Boolean(args.uiEvidenceCollected),
      base_id_source: args.baseId ? 'provided-or-env' : 'manifest-or-unavailable'
    },
    schema: {
      ...schemaSource,
      table_count: schemaTables.length,
      note: 'The live metadata/API schema is used only for table/field ids, field types, select choices, and view names. It is not used as proof of saved native view filter/sort panel configuration.'
    },
    evidence,
    summary: {
      view_count: views.length,
      manifest_table_count: manifestTables.length,
      schema_table_count: schemaTables.length,
      primitive_count: primitives.length,
      unsupported_or_gap_primitives: primitives.filter(p => !p.schema_supported || p.status.includes('needed') || p.status.includes('gap')).map(p => p.primitive_id)
    },
    primitives,
    views: viewAnalyses,
    recommendations
  };

  const mapPath = path.join(args.outputDir, 'wbs09_airtable_capability_map.generated.json');
  const summaryPath = path.join(args.outputDir, 'wbs09_airtable_capability_map_summary.md');
  writeJson(mapPath, map);
  fs.writeFileSync(summaryPath, markdownSummary(map), 'utf8');
  const repoManifestPath = path.join(path.dirname(args.manifest), 'wbs09_airtable_capability_map.generated.json');
  writeJson(repoManifestPath, map);
  writeJson(path.join(args.outputDir, 'capability_map_run_context.json'), {
    generated_utc: map.generated_utc,
    tool_version: VERSION,
    output_dir: args.outputDir,
    map_path: mapPath,
    repo_generated_manifest_path: repoManifestPath,
    status: 'success'
  });
  console.log(JSON.stringify({ status: 'success', tool_version: VERSION, output_dir: args.outputDir, map_path: mapPath, repo_generated_manifest_path: repoManifestPath, primitive_count: primitives.length }, null, 2));
}

main().catch(err => {
  console.error(err && err.stack ? err.stack : String(err));
  process.exit(1);
});
