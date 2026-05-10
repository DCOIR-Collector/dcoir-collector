#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const TOOL_VERSION = '2026-05-10.wbs09-primitive-coverage-audit.1';

function parseArgs(argv) {
  const parsed = { manifest: null, outputDir: null };
  for (let i = 2; i < argv.length; i += 1) {
    const a = argv[i];
    const next = () => argv[++i];
    if (a === '--manifest') parsed.manifest = next();
    else if (a === '--output-dir') parsed.outputDir = next();
    else throw new Error(`Unknown argument: ${a}`);
  }
  if (!parsed.manifest) throw new Error('--manifest is required');
  if (!parsed.outputDir) throw new Error('--output-dir is required');
  return parsed;
}

function readJson(p) { return JSON.parse(fs.readFileSync(p, 'utf8')); }
function ensureDir(p) { fs.mkdirSync(p, { recursive: true }); }
function writeJson(p, obj) { fs.writeFileSync(p, JSON.stringify(obj, null, 2) + '\n', 'utf8'); }
function writeText(p, s) { fs.writeFileSync(p, s, 'utf8'); }

function valueKind(value) {
  if (value === null || value === undefined) return 'null';
  if (Array.isArray(value)) return 'list';
  if (value === 'today') return 'relative_date_today';
  if (typeof value === 'boolean') return 'boolean';
  return typeof value;
}

function primitiveForFilter(filter) {
  const op = String(filter.operator ?? '').toLowerCase();
  const kind = valueKind(filter.value);
  const field = String(filter.field ?? '');
  if (op === 'on or before' && kind === 'relative_date_today') return 'filter.relative_date.on_or_before_today';
  if (op === '=' && kind === 'boolean') return 'filter.checkbox.equals_boolean';
  if (op === '=' && kind === 'string') return 'filter.single_value.equals_string';
  if (op === 'is one of' && kind === 'list') return 'filter.multi_value.is_one_of';
  if (op === 'is not empty' && kind === 'null') return 'filter.emptyness.is_not_empty';
  if (op === 'contains' && kind === 'string') return 'filter.text.contains';
  return `filter.unsupported.${op || 'unknown'}.${kind}${field ? `.${field}` : ''}`;
}

function primitiveForSort(sort, index, total) {
  if (index === 0 && total === 1) return 'sort.single_existing_or_create_row';
  if (index === 0 && total > 1) return 'sort.multi_row.first_row';
  if (index > 0) return 'sort.multi_row.additional_row';
  return 'sort.unknown';
}

const SUPPORT = {
  'readback.panel_rows': { status: 'active', evidence: 'DCOIR-AIRTABLE-WBS09-VIEW-PANEL-READBACK / commit 2beb3e7' },
  'discovery.panel_rows_and_options': { status: 'active', evidence: 'DCOIR-AIRTABLE-WBS09-VIEW-DISCOVERY / commit 950cb3c' },
  'sort.direction.existing_row': { status: 'active_guarded', evidence: 'DCOIR-AIRTABLE-WBS09-APPLY-SORT-DIRECTION / commit 950cb3c' },
  'sort.multi_row.additional_row': { status: 'not_ready', evidence: '2026-05-10 failed at second sort insertion; needs isolated primitive' },
  'filter.relative_date.on_or_before_today': { status: 'not_ready', evidence: '2026-05-10 failed at relative-date value dropdown targeting; needs isolated primitive' },
  'filter.checkbox.equals_boolean': { status: 'not_ready', evidence: '2026-05-10 failed at checkbox value handling before manual correction; needs isolated primitive' },
  'filter.multi_value.is_one_of': { status: 'not_ready', evidence: 'requires multi-select option discovery and exact option selection; no promoted action primitive yet' },
  'filter.single_value.equals_string': { status: 'partial_prior_success', evidence: 'inline text contains/equals paths had earlier bounded success, but not promoted as generic primitive' },
  'filter.text.contains': { status: 'partial_prior_success', evidence: 'draft29 contains retry passed, but not promoted as generic primitive' },
  'filter.emptyness.is_not_empty': { status: 'not_ready', evidence: 'requires explicit empty/not-empty operator primitive and verification' },
  'view.create': { status: 'draft_limited', evidence: 'older WBS09 creation paths had bounded success; broad create/configure not promoted' },
  'view.configure_general': { status: 'not_ready', evidence: 'requires primitive composition and action planner after individual primitives pass' }
};

const args = parseArgs(process.argv);
const manifest = readJson(args.manifest);
ensureDir(args.outputDir);

const views = Array.isArray(manifest.views) ? manifest.views : [];
const filterOperators = new Map();
const filterValueKinds = new Map();
const filterPrimitiveCounts = new Map();
const sortPrimitiveCounts = new Map();
const sortDirectionCounts = new Map();
const filterFieldCounts = new Map();
const tableCounts = new Map();
const multiSortViews = [];
const multiFilterViews = [];
const viewRows = [];

function inc(map, key, amount = 1) { map.set(key, (map.get(key) ?? 0) + amount); }
function sortedObject(map) { return Object.fromEntries([...map.entries()].sort((a, b) => String(a[0]).localeCompare(String(b[0])))); }

for (const view of views) {
  const tableName = view.table_name;
  const viewName = view.view_name;
  const filters = Array.isArray(view.filters) ? view.filters : [];
  const sorts = Array.isArray(view.sorts) ? view.sorts : [];
  inc(tableCounts, tableName);
  if (filters.length > 1) multiFilterViews.push({ table_name: tableName, view_name: viewName, filters });
  if (sorts.length > 1) multiSortViews.push({ table_name: tableName, view_name: viewName, sorts });

  const filterPrimitives = [];
  for (const filter of filters) {
    const primitive = primitiveForFilter(filter);
    filterPrimitives.push(primitive);
    inc(filterOperators, filter.operator ?? '');
    inc(filterValueKinds, valueKind(filter.value));
    inc(filterPrimitiveCounts, primitive);
    inc(filterFieldCounts, filter.field ?? '');
  }

  const sortPrimitives = [];
  sorts.forEach((sort, index) => {
    const primitive = primitiveForSort(sort, index, sorts.length);
    sortPrimitives.push(primitive);
    inc(sortPrimitiveCounts, primitive);
    inc(sortDirectionCounts, sort.direction ?? '');
  });

  viewRows.push({
    table_name: tableName,
    view_name: viewName,
    filter_count: filters.length,
    sort_count: sorts.length,
    filter_primitives: filterPrimitives,
    sort_primitives: sortPrimitives,
    filters,
    sorts
  });
}

const requiredPrimitiveSet = new Set();
for (const k of filterPrimitiveCounts.keys()) requiredPrimitiveSet.add(k);
for (const k of sortPrimitiveCounts.keys()) requiredPrimitiveSet.add(k);
requiredPrimitiveSet.add('readback.panel_rows');
requiredPrimitiveSet.add('discovery.panel_rows_and_options');
requiredPrimitiveSet.add('sort.direction.existing_row');
requiredPrimitiveSet.add('view.create');
requiredPrimitiveSet.add('view.configure_general');

const primitiveReadiness = [...requiredPrimitiveSet].sort().map((primitive) => {
  const support = SUPPORT[primitive] ?? { status: 'unknown_not_ready', evidence: 'not mapped by this audit tool' };
  return {
    primitive,
    manifest_count: (filterPrimitiveCounts.get(primitive) ?? 0) + (sortPrimitiveCounts.get(primitive) ?? 0),
    status: support.status,
    evidence: support.evidence
  };
});

const notReady = primitiveReadiness.filter((x) => !['active', 'active_guarded'].includes(x.status));
const recommendedNext = [
  {
    rank: 1,
    primitive: 'filter.relative_date.on_or_before_today',
    reason: 'High manifest frequency and known failed action primitive; 13 views use review_after-style relative today filters.'
  },
  {
    rank: 2,
    primitive: 'filter.checkbox.equals_boolean',
    reason: 'Known failed action primitive and low-risk boolean control if isolated; needed for active/delete-oriented views.'
  },
  {
    rank: 3,
    primitive: 'sort.multi_row.additional_row',
    reason: 'Only 4 views need second sort rows, but prior failure blocked Work Items and must be solved before broad configure.'
  }
];

const report = {
  timestamp_utc: new Date().toISOString(),
  tool_version: TOOL_VERSION,
  manifest_path: path.resolve(args.manifest),
  manifest_schema: manifest.schema ?? null,
  view_count: views.length,
  table_count: tableCounts.size,
  summary: {
    filter_operator_counts: sortedObject(filterOperators),
    filter_value_kind_counts: sortedObject(filterValueKinds),
    filter_primitive_counts: sortedObject(filterPrimitiveCounts),
    sort_primitive_counts: sortedObject(sortPrimitiveCounts),
    sort_direction_counts: sortedObject(sortDirectionCounts),
    multi_filter_view_count: multiFilterViews.length,
    multi_sort_view_count: multiSortViews.length,
    not_ready_primitive_count: notReady.length
  },
  primitive_readiness: primitiveReadiness,
  recommended_next_primitives: recommendedNext,
  multi_sort_views: multiSortViews,
  multi_filter_views: multiFilterViews,
  view_rows: viewRows
};

const jsonPath = path.join(args.outputDir, 'wbs09_primitive_coverage_audit.json');
writeJson(jsonPath, report);

const lines = [];
lines.push('# WBS09 Primitive Coverage Audit');
lines.push('');
lines.push(`- Tool version: ${TOOL_VERSION}`);
lines.push(`- Manifest views: ${views.length}`);
lines.push(`- Tables: ${tableCounts.size}`);
lines.push(`- Multi-filter views: ${multiFilterViews.length}`);
lines.push(`- Multi-sort views: ${multiSortViews.length}`);
lines.push('');
lines.push('## Filter operators');
for (const [k, v] of [...filterOperators.entries()].sort()) lines.push(`- ${k}: ${v}`);
lines.push('');
lines.push('## Primitive readiness');
for (const r of primitiveReadiness) lines.push(`- ${r.primitive}: ${r.status} (manifest_count=${r.manifest_count})`);
lines.push('');
lines.push('## Recommended next primitives');
for (const r of recommendedNext) lines.push(`${r.rank}. ${r.primitive}: ${r.reason}`);
lines.push('');
lines.push('## Multi-sort views');
for (const v of multiSortViews) lines.push(`- ${v.table_name} / ${v.view_name}: ${v.sorts.map(s => `${s.field} ${s.direction}`).join('; ')}`);
lines.push('');
lines.push('## Multi-filter views');
for (const v of multiFilterViews) lines.push(`- ${v.table_name} / ${v.view_name}: ${v.filters.map(f => `${f.field} ${f.operator} ${JSON.stringify(f.value)}`).join('; ')}`);
lines.push('');
writeText(path.join(args.outputDir, 'wbs09_primitive_coverage_audit.md'), lines.join('\n'));

console.log(JSON.stringify({ status: 'success', tool_version: TOOL_VERSION, output_dir: args.outputDir, report_path: jsonPath, not_ready_primitive_count: notReady.length }, null, 2));
