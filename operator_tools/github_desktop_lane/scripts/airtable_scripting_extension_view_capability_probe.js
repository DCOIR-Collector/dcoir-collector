/******************************************************************************
DCOIR WBS09 Airtable Scripting Extension capability probe

Purpose: no-mutation probe to check whether Airtable Scripting Extension exposes
native view creation methods in the current runtime. Expected result for current
Airtable scripting environments: no supported create-view method.

Paste into Airtable Scripting Extension and run. It does not create, update, or
delete anything.
******************************************************************************/
const table = base.tables[0];
const result = {
  timestamp: new Date().toISOString(),
  table_name: table ? table.name : null,
  has_createViewAsync_on_table: table ? typeof table.createViewAsync === 'function' : false,
  has_createViewAsync_on_base: typeof base.createViewAsync === 'function',
  has_createGridViewAsync_on_table: table ? typeof table.createGridViewAsync === 'function' : false,
  available_table_method_names_sample: table ? Object.getOwnPropertyNames(Object.getPrototypeOf(table)).filter(n => n.toLowerCase().includes('view')).sort() : []
};
output.markdown('```json\n' + JSON.stringify(result, null, 2) + '\n```');
