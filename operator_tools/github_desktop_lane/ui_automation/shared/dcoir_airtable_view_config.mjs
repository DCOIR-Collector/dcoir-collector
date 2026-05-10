// DCOIR Airtable view configuration primitives
// Version: 2026-05-09.draft28-multi-filter-support

export const SUPPORTED_FILTER_OPERATORS = Object.freeze([
  'is one of',
  '=',
  'is not empty',
  'contains',
  'on or before'
]);

export const SUPPORTED_SORT_DIRECTIONS = Object.freeze(['asc', 'desc']);

export function normalizeFilterValues(filter) {
  if (!filter) return [];
  if (Array.isArray(filter.value)) return filter.value;
  if (filter.value === null || filter.value === undefined) return [];
  return [filter.value];
}

export function filterRequiresValue(filter) {
  return filter && filter.operator !== 'is not empty';
}

export function getFilterOperatorLabel(operator) {
  const op = String(operator || '').trim();
  if (op === '=') return 'is';
  if (op === 'is one of') return 'is any of';
  if (op === 'is not empty') return 'is not empty';
  if (op === 'contains') return 'contains';
  if (op === 'on or before') return 'is on or before';
  throw new Error(`Unsupported filter operator for Airtable UI mapping: ${op}`);
}

export function validateViewConfigContract(view, options = {}) {
  const filters = Array.isArray(view.filters) ? view.filters : [];
  const sorts = Array.isArray(view.sorts) ? view.sorts : [];
  const maxFilters = Number.isInteger(options.maxFilters) ? options.maxFilters : 2;
  const maxSorts = Number.isInteger(options.maxSorts) ? options.maxSorts : 5;

  if (filters.length > maxFilters) {
    throw new Error(`This draft supports at most ${maxFilters} filter condition(s); ${view.view_key || view.view_name} has ${filters.length}.`);
  }
  if (sorts.length > maxSorts) {
    throw new Error(`This draft supports at most ${maxSorts} sort condition(s); ${view.view_key || view.view_name} has ${sorts.length}.`);
  }

  for (const filter of filters) {
    if (!filter.field) throw new Error('Filter is missing field name.');
    if (!SUPPORTED_FILTER_OPERATORS.includes(filter.operator)) {
      throw new Error(`Unsupported filter operator for one-view smoke: ${filter.operator}`);
    }
    const values = normalizeFilterValues(filter);
    if (filterRequiresValue(filter) && values.length < 1) {
      throw new Error('Single-filter smoke target requires at least one filter value.');
    }
  }

  for (const sort of sorts) {
    if (!sort.field) throw new Error('Sort is missing field name.');
    if (!SUPPORTED_SORT_DIRECTIONS.includes(sort.direction)) {
      throw new Error(`Unsupported sort direction: ${sort.direction}`);
    }
  }

  return { filters, sorts };
}

export function summarizeViewConfig(view) {
  const filters = Array.isArray(view.filters) ? view.filters : [];
  const sorts = Array.isArray(view.sorts) ? view.sorts : [];
  return {
    table_name: view.table_name,
    view_name: view.view_name,
    filter_count: filters.length,
    filter_operators: filters.map((f) => f.operator),
    sort_count: sorts.length,
    sort_fields: sorts.map((s) => s.field)
  };
}
