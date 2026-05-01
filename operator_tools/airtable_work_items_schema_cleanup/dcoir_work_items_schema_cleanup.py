#!/usr/bin/env python3
"""DCOIR Work Items schema cleanup helper.

Local operator tool for the AFRICOM_SOC_IR / DCOIR Airtable Work Items table.
Reads Airtable token from DCOIR_AIRTABLE_TOKEN or AIRTABLE_TOKEN.
Writes reports to DCOIR_DOWNLOADS_DIR when set, otherwise ./out.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

API = "https://api.airtable.com/v0"
META = "https://api.airtable.com/v0/meta"
DEFAULT_BASE_ID = "appM4KSwnVf3G3OTK"
DEFAULT_TABLE_ID = "tblgsQAVWvh8K7gIR"
TABLE_NAME = "Work Items"
PRIMARY_FIELD_ID = "fld62VxHtbRTZhPdX"
PRIMARY_FIELD_NAME = "Work Item"
ITEM_ID_FIELD_ID = "fldTneAArfh5yJOXi"

FIELD_IDS = {
    "Work Item": "fld62VxHtbRTZhPdX",
    "Item ID": "fldTneAArfh5yJOXi",
    "Repo Path or Skill": "fldZ922sf04D4WbvE",
    "GitHub Link": "fldfq7rvP6vA0AAGF",
    "Evidence / Notes": "fldZ966uvUvaZ77dS",
    "Blocker": "fldTlQrbx8uJ9mvrQ",
    "Next Action": "fld28gLP0rXdRQNdq",
    "Due Date": "fldTUAhmt9LWwjBAt",
    "Active": "fldlF2k4ImBt4NkHc",
    "Queue Control": "fldy67yDzHiwu7Cfq",
    "Queue Rank": "fld3vWpcC6OfYEber",
    "Resume First": "fldwbZAHBQFfGMlBv",
    "Supersedes Item IDs": "fld5cJr4T7mxs7TIn",
    "Superseded By Item ID": "fldQNXeZTpxeib1kJ",
    "Priority Rationale": "fldcsf5ymFwePtkVj",
    "Decision Source": "fldSRxMPHr9jHEjsn",
    "Last Confirmed Text": "fldUVyj1B7LhRIFAI",
    "created_at": "fld9Dw9YYk8DjOden",
    "updated_at": "fldD1rwuVsNketueT",
    "review_after": "flddEfCAHEQLwD0n7",
    "canonical_parent_plan_id": "fldbZhaIrAX2cbHrE",
    "source_table": "fldunDrubjhN0zchO",
    "source_record_id": "fldBO42BHGdbibmCN",
    "Area": "fldd0urjdszMBR1LU",
    "Work Type": "fldGa1GseWf6ro78L",
    "Status": "fldvGbvwTx84mxtwO",
    "Priority": "fld4XJowALSopxpnV",
    "Branch State": "fldTFpFZ4vQ8RXRWu",
    "Authority Scope": "fldQ5YKb9EuM8nqph",
    "GitHub Promotion Need": "fldATbftmJ4UQ8Flk",
    "retention_class": "fldX9vydvQqreL4cF",
    "canonical_item_type": "fld58RqZOYyXAeTbe",
    "pipeline_stage": "fldYmzraKwmpUVhcL",
    "retirement_action": "fldEBKJkv1tx9H22s",
    "Owner": "flds3pqDPg3riy0UM",
}

# Fields the operator approved for retirement by reversible prefix first.
FIELDS_TO_PREFIX_DELETE = [
    "Next Action",
    "Branch State",
    "pipeline_stage",
    "canonical_item_type",
    "retirement_action",
    "Owner",
    "Active",
    "Resume First",
    "Queue Control",
    "GitHub Link",
    "Due Date",
    "Blocker",
    "Decision Source",
    "Priority Rationale",
    "Supersedes Item IDs",
    "Superseded By Item ID",
    "source_table",
    "source_record_id",
    "review_after",
    "Last Confirmed Text",
]

KEEP_VISIBLE_FIELDS = [
    "Queue Rank",
    "Status",
    "Work Item",
    "Item ID",
    "canonical_parent_plan_id",
    "Area",
    "Priority",
    "Work Type",
    "Repo Path or Skill",
    "Evidence / Notes",
    "created_at",
    "updated_at",
]

CANONICAL_SELECTS = {
    "Status": ["todo", "active", "blocked", "waiting", "done", "dropped"],
    "Area": ["collector", "gemini", "github", "airtable", "skills", "docs", "validation", "packaging", "workflow", "governance", "other"],
    "Work Type": ["task", "bug", "enhancement", "decision", "validation"],
    "Priority": ["critical", "high", "medium", "low"],
}

SELECT_FIELD_IDS = {
    "Status": FIELD_IDS["Status"],
    "Area": FIELD_IDS["Area"],
    "Work Type": FIELD_IDS["Work Type"],
    "Priority": FIELD_IDS["Priority"],
}

STATUS_MAP = {
    "backlog": "todo",
    "planned": "todo",
    "queued": "todo",
    "todo": "todo",
    "in_progress": "active",
    "validating": "active",
    "ready_for_validation": "active",
    "ready_to_push": "active",
    "active": "active",
    "waiting_on_operator": "waiting",
    "waiting": "waiting",
    "blocked": "blocked",
    "failed": "blocked",
    "passed": "done",
    "completed": "done",
    "done": "done",
    "dropped": "dropped",
}
AREA_MAP = {
    "git_hub": "github",
    "documentation": "docs",
    "drive": "other",
    "prompt_pack": "gemini",
    "collector": "collector",
    "gemini": "gemini",
    "github": "github",
    "airtable": "airtable",
    "skills": "skills",
    "docs": "docs",
    "validation": "validation",
    "packaging": "packaging",
    "workflow": "workflow",
    "governance": "governance",
    "other": "other",
}
WORK_TYPE_MAP = {
    "task": "task",
    "implementation": "task",
    "planning": "task",
    "planning_execution": "task",
    "docs": "task",
    "publish": "task",
    "design": "task",
    "restore": "task",
    "follow_up": "task",
    "release": "task",
    "verify": "validation",
    "validation": "validation",
    "troubleshooting": "bug",
    "investigation": "bug",
    "bug": "bug",
    "skill_ux": "enhancement",
    "enhancement": "enhancement",
    "decision": "decision",
}
VALUE_MAPS = {
    "Status": STATUS_MAP,
    "Area": AREA_MAP,
    "Work Type": WORK_TYPE_MAP,
}

# Options that should be removed after records are moved away from them.
OPTIONS_TO_DELETE = {
    "Status": sorted(set(STATUS_MAP.keys()) - set(CANONICAL_SELECTS["Status"])),
    "Area": sorted(set(AREA_MAP.keys()) - set(CANONICAL_SELECTS["Area"])),
    "Work Type": sorted(set(WORK_TYPE_MAP.keys()) - set(CANONICAL_SELECTS["Work Type"])),
}

DELETE_FIELD_CONFIRM = "DELETE_FIELDS"
DELETE_OPTION_CONFIRM = "DELETE_OPTIONS"

class AirtableError(RuntimeError):
    pass

class Airtable:
    def __init__(self, token: str, verbose: bool = False) -> None:
        self.token = token
        self.verbose = verbose

    def request(self, method: str, url: str, body: Any | None = None) -> Any:
        data = None if body is None else json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", "Bearer " + self.token)
        req.add_header("Content-Type", "application/json")
        for attempt in range(6):
            try:
                if self.verbose:
                    print(f"{method} {url}")
                with urllib.request.urlopen(req, timeout=90) as resp:
                    raw = resp.read().decode("utf-8", "replace")
                    return {} if not raw else json.loads(raw)
            except urllib.error.HTTPError as exc:
                raw = exc.read().decode("utf-8", "replace")
                if exc.code == 429 and attempt < 5:
                    time.sleep(2 + attempt)
                    continue
                raise AirtableError(f"{method} {url} failed HTTP {exc.code}: {raw}") from exc

    def schema(self, base_id: str) -> Dict[str, Any]:
        return self.request("GET", f"{META}/bases/{base_id}/tables")

    def update_field(self, base_id: str, table_id: str, field_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.request("PATCH", f"{META}/bases/{base_id}/tables/{table_id}/fields/{field_id}", payload)

    def delete_field_attempt(self, base_id: str, table_id: str, field_id: str) -> Dict[str, Any]:
        return self.request("DELETE", f"{META}/bases/{base_id}/tables/{table_id}/fields/{field_id}")

    def list_records(self, base_id: str, table_id: str, fields: List[str] | None = None) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        offset = None
        while True:
            params: List[Tuple[str, str]] = [("pageSize", "100")]
            if offset:
                params.append(("offset", offset))
            if fields:
                for f in fields:
                    params.append(("fields[]", f))
            qs = urllib.parse.urlencode(params)
            url = f"{API}/{base_id}/{urllib.parse.quote(table_id, safe='')}?{qs}"
            data = self.request("GET", url)
            records.extend(data.get("records", []))
            offset = data.get("offset")
            if not offset:
                return records

    def update_records(self, base_id: str, table_id: str, records: List[Dict[str, Any]], typecast: bool = False) -> Dict[str, Any]:
        out: List[Dict[str, Any]] = []
        for i in range(0, len(records), 10):
            body = {"records": records[i:i+10]}
            if typecast:
                body["typecast"] = True
            url = f"{API}/{base_id}/{urllib.parse.quote(table_id, safe='')}"
            data = self.request("PATCH", url, body)
            out.extend(data.get("records", []))
        return {"records": out}

    def create_records(self, base_id: str, table_id: str, records: List[Dict[str, Any]], typecast: bool = False) -> Dict[str, Any]:
        out: List[Dict[str, Any]] = []
        for i in range(0, len(records), 10):
            body = {"records": records[i:i+10]}
            if typecast:
                body["typecast"] = True
            url = f"{API}/{base_id}/{urllib.parse.quote(table_id, safe='')}"
            data = self.request("POST", url, body)
            out.extend(data.get("records", []))
        return {"records": out}

    def delete_records(self, base_id: str, table_id: str, record_ids: List[str]) -> Dict[str, Any]:
        out: List[Dict[str, Any]] = []
        for i in range(0, len(record_ids), 10):
            qs = urllib.parse.urlencode([("records[]", rid) for rid in record_ids[i:i+10]])
            url = f"{API}/{base_id}/{urllib.parse.quote(table_id, safe='')}?{qs}"
            data = self.request("DELETE", url)
            out.extend(data.get("records", []))
        return {"records": out}

def utc_stamp() -> str:
    return dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

def out_dir() -> Path:
    p = os.environ.get("DCOIR_DOWNLOADS_DIR")
    if p:
        d = Path(p)
    else:
        d = Path(__file__).resolve().parent / "out"
    d.mkdir(parents=True, exist_ok=True)
    return d

def get_token() -> str:
    token = os.environ.get("DCOIR_AIRTABLE_TOKEN") or os.environ.get("AIRTABLE_TOKEN")
    if not token:
        raise SystemExit("Missing token. Set DCOIR_AIRTABLE_TOKEN or AIRTABLE_TOKEN.")
    return token

def field_name_by_id(schema: Dict[str, Any], table_id: str) -> Dict[str, str]:
    for table in schema.get("tables", []):
        if table.get("id") == table_id:
            return {f["id"]: f.get("name", "") for f in table.get("fields", [])}
    return {}

def fields_by_name(schema: Dict[str, Any], table_id: str) -> Dict[str, Dict[str, Any]]:
    for table in schema.get("tables", []):
        if table.get("id") == table_id:
            return {f.get("name", ""): f for f in table.get("fields", [])}
    return {}

def fields_by_id(schema: Dict[str, Any], table_id: str) -> Dict[str, Dict[str, Any]]:
    for table in schema.get("tables", []):
        if table.get("id") == table_id:
            return {f.get("id", ""): f for f in table.get("fields", [])}
    return {}

def table_exists(schema: Dict[str, Any], table_id: str) -> bool:
    return any(t.get("id") == table_id for t in schema.get("tables", []))

def select_choices(schema: Dict[str, Any], table_id: str, field_id: str) -> List[Dict[str, Any]]:
    fld = fields_by_id(schema, table_id).get(field_id, {})
    return fld.get("options", {}).get("choices", []) or fld.get("config", {}).get("choices", []) or []

def choice_names(schema: Dict[str, Any], table_id: str, field_id: str) -> List[str]:
    return [c.get("name", "") for c in select_choices(schema, table_id, field_id)]

def current_value(fields: Dict[str, Any], field_name: str, field_id: str) -> Any:
    if field_name in fields:
        return fields[field_name]
    if field_id in fields:
        return fields[field_id]
    return None

def normalize_one_value(value: Any, mapping: Dict[str, str]) -> Any:
    if value is None or value == "":
        return value
    if isinstance(value, str):
        return mapping.get(value, value)
    if isinstance(value, dict) and "name" in value:
        return mapping.get(value["name"], value["name"])
    return value

def build_record_updates(records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    updates: List[Dict[str, Any]] = []
    counts: Dict[str, int] = {}
    for rec in records:
        fields = rec.get("fields", {})
        changed: Dict[str, Any] = {}
        for field_name, mapping in VALUE_MAPS.items():
            fid = FIELD_IDS[field_name]
            old = current_value(fields, field_name, fid)
            new = normalize_one_value(old, mapping)
            if new != old and new is not None:
                changed[field_name] = new
                key = f"{field_name}: {old} -> {new}"
                counts[key] = counts.get(key, 0) + 1
        if changed:
            updates.append({"id": rec["id"], "fields": changed})
    return updates, counts

def fields_to_prefix(schema: Dict[str, Any], table_id: str) -> List[Dict[str, Any]]:
    by_name = fields_by_name(schema, table_id)
    targets: List[Dict[str, Any]] = []
    for name in FIELDS_TO_PREFIX_DELETE:
        prefixed = "DELETE - " + name
        if prefixed in by_name:
            targets.append({"field": by_name[prefixed], "old_name": prefixed, "new_name": prefixed, "already_prefixed": True})
        elif name in by_name:
            targets.append({"field": by_name[name], "old_name": name, "new_name": prefixed, "already_prefixed": False})
    return targets

def create_missing_options_via_scratch(at: Airtable, base_id: str, table_id: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    existing = {field: set(choice_names(schema, table_id, fid)) for field, fid in SELECT_FIELD_IDS.items()}
    missing = {field: [v for v in wanted if v not in existing.get(field, set())]
               for field, wanted in CANONICAL_SELECTS.items()}
    missing = {field: vals for field, vals in missing.items() if vals}
    if not missing:
        return {"missing_options": {}, "scratch_record_created": False, "scratch_record_deleted": False}

    fields: Dict[str, Any] = {
        PRIMARY_FIELD_NAME: "TEMP - DCOIR option creation scratch - safe to delete",
        "Item ID": "TEMP-DCOIR-OPTION-CREATION-SCRATCH",
    }
    for field, vals in missing.items():
        fields[field] = vals[0]

    created = at.create_records(base_id, table_id, [{"fields": fields}], typecast=True)
    created_ids = [r["id"] for r in created.get("records", [])]
    deleted = at.delete_records(base_id, table_id, created_ids) if created_ids else {"records": []}
    return {
        "missing_options": missing,
        "scratch_record_created": bool(created_ids),
        "scratch_record_ids": created_ids,
        "scratch_record_deleted": len(deleted.get("records", [])) == len(created_ids),
    }

def option_usage(records: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    usage: Dict[str, Dict[str, int]] = {field: {} for field in OPTIONS_TO_DELETE}
    for rec in records:
        fs = rec.get("fields", {})
        for field, options in OPTIONS_TO_DELETE.items():
            fid = FIELD_IDS[field]
            val = current_value(fs, field, fid)
            if isinstance(val, dict) and "name" in val:
                val = val["name"]
            if isinstance(val, str) and val in options:
                usage[field][val] = usage[field].get(val, 0) + 1
    return usage

def generate_option_delete_script(schema: Dict[str, Any], table_id: str, records: List[Dict[str, Any]], output: Path) -> Dict[str, Any]:
    usage = option_usage(records)
    blocked = {field: vals for field, vals in usage.items() if vals}
    lines = []
    lines.append("// DCOIR Work Items select-option cleanup")
    lines.append("// Paste into Airtable Scripting Extension inside the DCOIR base.")
    lines.append("// Run only after Python verify says obsolete option usage is zero.")
    lines.append("// This script updates field options; it does not change record values.")
    lines.append("")
    lines.append(f"let table = base.getTable('{TABLE_NAME}');")
    lines.append("let changes = [")
    for field, obsolete in OPTIONS_TO_DELETE.items():
        if blocked.get(field):
            continue
        choices = select_choices(schema, table_id, FIELD_IDS[field])
        keep = [c for c in choices if c.get("name") not in obsolete]
        js_choices = []
        for c in keep:
            item = {"name": c.get("name")}
            if c.get("color"):
                item["color"] = c.get("color")
            js_choices.append(item)
        lines.append("  {")
        lines.append(f"    fieldName: '{field}',")
        lines.append(f"    remove: {json.dumps(obsolete)},")
        lines.append(f"    choices: {json.dumps(js_choices)}")
        lines.append("  },")
    lines.append("];" )
    lines.append("")
    lines.append("for (let change of changes) {")
    lines.append("  let field = table.getField(change.fieldName);")
    lines.append("  output.text(`Updating ${change.fieldName}; removing: ${change.remove.join(', ')}`);")
    lines.append("  await field.updateOptionsAsync({ choices: change.choices });")
    lines.append("}")
    lines.append("output.markdown('**DCOIR option cleanup complete.**');")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"script_path": str(output), "blocked_by_usage": blocked}

def attempt_api_option_delete(at: Airtable, base_id: str, table_id: str, schema: Dict[str, Any], records: List[Dict[str, Any]]) -> Dict[str, Any]:
    usage = option_usage(records)
    results = []
    for field, obsolete in OPTIONS_TO_DELETE.items():
        if usage.get(field):
            results.append({"field": field, "status": "skipped", "reason": "obsolete values still used", "usage": usage[field]})
            continue
        field_id = FIELD_IDS[field]
        choices = select_choices(schema, table_id, field_id)
        keep = []
        for c in choices:
            if c.get("name") not in obsolete:
                item = {"name": c.get("name")}
                if c.get("color"):
                    item["color"] = c.get("color")
                keep.append(item)
        body = {"options": {"choices": keep}, "enableSelectFieldChoiceDeletion": True}
        try:
            at.update_field(base_id, table_id, field_id, body)
            results.append({"field": field, "status": "attempted_success", "removed": obsolete})
        except Exception as exc:
            results.append({"field": field, "status": "failed_expected_for_web_api", "error": str(exc), "removed": obsolete})
    return {"results": results}

def attempt_field_delete(at: Airtable, base_id: str, table_id: str, schema: Dict[str, Any], explicit_ids: List[str], delete_prefixed: bool) -> Dict[str, Any]:
    by_id = fields_by_id(schema, table_id)
    targets: List[Tuple[str, str]] = []
    if explicit_ids:
        for fid in explicit_ids:
            name = by_id.get(fid, {}).get("name", "")
            targets.append((fid, name))
    if delete_prefixed:
        for fid, fld in by_id.items():
            name = fld.get("name", "")
            if name.startswith("DELETE - "):
                targets.append((fid, name))
    seen = set()
    unique_targets = []
    for fid, name in targets:
        if fid not in seen:
            seen.add(fid)
            unique_targets.append((fid, name))
    results = []
    for fid, name in unique_targets:
        if not name.startswith("DELETE - "):
            results.append({"field_id": fid, "field_name": name, "status": "skipped", "reason": "field is not prefixed DELETE -"})
            continue
        try:
            at.delete_field_attempt(base_id, table_id, fid)
            results.append({"field_id": fid, "field_name": name, "status": "attempted_success"})
        except Exception as exc:
            results.append({"field_id": fid, "field_name": name, "status": "failed_expected_for_web_api", "error": str(exc)})
    return {"targets": [{"field_id": fid, "field_name": name} for fid, name in unique_targets], "results": results}

def write_report(mode: str, report: Dict[str, Any]) -> Path:
    d = out_dir()
    stamp = utc_stamp()
    jp = d / f"work_items_schema_cleanup_{mode}_{stamp}.json"
    mp = d / f"work_items_schema_cleanup_{mode}_{stamp}.md"
    report["timestamp_utc"] = dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    jp.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    lines = []
    lines.append(f"# Work Items schema cleanup - {mode}\n\n")
    lines.append(f"Timestamp UTC: `{report['timestamp_utc']}`\n\n")
    for key in ("summary", "actions", "warnings", "manual_followup"):
        if key in report:
            lines.append(f"## {key.replace('_', ' ').title()}\n\n")
            val = report[key]
            if isinstance(val, list):
                for item in val[:200]:
                    lines.append(f"- `{json.dumps(item, sort_keys=True)}`\n")
            else:
                lines.append("```json\n" + json.dumps(val, indent=2, sort_keys=True) + "\n```\n")
            lines.append("\n")
    mp.write_text("".join(lines), encoding="utf-8")
    print(f"Wrote JSON report: {jp}")
    print(f"Wrote Markdown report: {mp}")
    return jp

def run_self_test() -> int:
    assert STATUS_MAP["completed"] == "done"
    assert STATUS_MAP["ready_to_push"] == "active"
    assert AREA_MAP["git_hub"] == "github"
    assert WORK_TYPE_MAP["verify"] == "validation"
    assert "Next Action" in FIELDS_TO_PREFIX_DELETE
    assert "Status" in CANONICAL_SELECTS
    print("PASS: self-test checks passed")
    return 0

def build_common_report(schema: Dict[str, Any], table_id: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
    updates, counts = build_record_updates(records)
    prefix_targets = fields_to_prefix(schema, table_id)
    current_select_options = {field: choice_names(schema, table_id, fid) for field, fid in SELECT_FIELD_IDS.items()}
    missing_options = {field: [v for v in vals if v not in current_select_options.get(field, [])]
                       for field, vals in CANONICAL_SELECTS.items()}
    missing_options = {k: v for k, v in missing_options.items() if v}
    usage = option_usage(records)
    return {
        "summary": {
            "table": TABLE_NAME,
            "record_count": len(records),
            "records_needing_value_normalization": len(updates),
            "fields_to_prefix_delete": len(prefix_targets),
            "missing_canonical_select_options": missing_options,
            "obsolete_option_usage": usage,
            "keep_visible_fields": KEEP_VISIBLE_FIELDS,
            "canonical_status_options": CANONICAL_SELECTS["Status"],
        },
        "value_change_counts": counts,
        "field_prefix_targets": [
            {"field_id": t["field"].get("id"), "old_name": t["old_name"], "new_name": t["new_name"], "already_prefixed": t["already_prefixed"]}
            for t in prefix_targets
        ],
        "manual_followup": {
            "recommended_defaults": {
                "Status": "todo",
                "Priority": "medium",
                "Area": "other",
                "Work Type": "task",
            },
            "default_note": "Airtable field defaults are usually set in the UI. This tool reports recommended defaults but does not set defaults by API.",
            "final_manual_delete_after_verify": ["Delete fields prefixed DELETE - if API field deletion attempt is unsupported", "Delete obsolete select options in UI or run generated Scripting Extension code"],
        },
    }

def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DCOIR Work Items Airtable schema cleanup helper")
    parser.add_argument("--mode", required=True, choices=[
        "self-test",
        "dry-run",
        "apply-options",
        "apply-safe",
        "verify",
        "generate-option-delete-script",
        "attempt-api-option-delete",
        "attempt-field-delete",
    ])
    parser.add_argument("--base-id", default=os.environ.get("DCOIR_AIRTABLE_BASE_ID", DEFAULT_BASE_ID))
    parser.add_argument("--table-id", default=os.environ.get("DCOIR_AIRTABLE_WORK_ITEMS_TABLE_ID", DEFAULT_TABLE_ID))
    parser.add_argument("--confirm-field-delete", default="")
    parser.add_argument("--confirm-option-delete", default="")
    parser.add_argument("--delete-prefixed-fields", action="store_true")
    parser.add_argument("--field-id", action="append", default=[])
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    if args.mode == "self-test":
        return run_self_test()

    token = get_token()
    at = Airtable(token, verbose=args.verbose)
    schema = at.schema(args.base_id)
    if not table_exists(schema, args.table_id):
        raise SystemExit(f"Table ID not found in schema: {args.table_id}")
    records = at.list_records(args.base_id, args.table_id, fields=[
        "Work Item", "Item ID", "Status", "Area", "Work Type", "Priority"
    ])

    report = build_common_report(schema, args.table_id, records)
    report["mode"] = args.mode
    report["base_id"] = args.base_id
    report["table_id"] = args.table_id
    report["warnings"] = []
    report["actions"] = []

    if args.mode == "dry-run":
        report["actions"].append("No Airtable changes made.")

    elif args.mode == "apply-options":
        result = create_missing_options_via_scratch(at, args.base_id, args.table_id, schema)
        report["actions"].append({"created_missing_options_via_scratch_record": result})

    elif args.mode == "apply-safe":
        updates, counts = build_record_updates(records)
        if updates:
            at.update_records(args.base_id, args.table_id, updates, typecast=True)
        report["actions"].append({"normalized_records": len(updates), "value_change_counts": counts})
        prefix_targets = fields_to_prefix(schema, args.table_id)
        renamed = []
        for target in prefix_targets:
            if target["already_prefixed"]:
                continue
            field_id = target["field"]["id"]
            old_name = target["old_name"]
            new_name = target["new_name"]
            desc = f"Pending deletion. Retired during DCOIR Work Items simplification. Previous field name: {old_name}."
            at.update_field(args.base_id, args.table_id, field_id, {"name": new_name, "description": desc})
            renamed.append({"field_id": field_id, "old_name": old_name, "new_name": new_name})
        report["actions"].append({"prefixed_fields_for_manual_delete": renamed})

    elif args.mode == "verify":
        updates, counts = build_record_updates(records)
        usage = option_usage(records)
        unprefixed = [t for t in fields_to_prefix(schema, args.table_id) if not t["already_prefixed"]]
        report["actions"].append({"records_still_needing_normalization": len(updates), "remaining_value_change_counts": counts})
        report["actions"].append({"obsolete_option_usage": usage})
        report["actions"].append({"retirement_fields_not_yet_prefixed": [t["old_name"] for t in unprefixed]})
        if len(updates) == 0 and not any(usage.values()):
            print("PASS: Work Items values are normalized and obsolete options are unused.")
        else:
            print("WARN: Work Items cleanup is not fully verified yet. See report.")

    elif args.mode == "generate-option-delete-script":
        out = out_dir() / f"work_items_option_delete_scripting_extension_{utc_stamp()}.js"
        result = generate_option_delete_script(schema, args.table_id, records, out)
        report["actions"].append({"generated_airtable_scripting_extension_code": result})

    elif args.mode == "attempt-api-option-delete":
        if args.confirm_option_delete != DELETE_OPTION_CONFIRM:
            raise SystemExit(f"Refusing option deletion attempt. Add --confirm-option-delete {DELETE_OPTION_CONFIRM}")
        result = attempt_api_option_delete(at, args.base_id, args.table_id, schema, records)
        report["actions"].append({"experimental_api_option_delete_attempt": result})
        report["warnings"].append("Airtable Web API is expected to reject direct select-option deletion. Use generated Scripting Extension fallback if this fails.")

    elif args.mode == "attempt-field-delete":
        if args.confirm_field_delete != DELETE_FIELD_CONFIRM:
            raise SystemExit(f"Refusing field deletion attempt. Add --confirm-field-delete {DELETE_FIELD_CONFIRM}")
        if not args.delete_prefixed_fields and not args.field_id:
            raise SystemExit("Refusing field deletion attempt. Provide --delete-prefixed-fields or one or more --field-id values.")
        result = attempt_field_delete(at, args.base_id, args.table_id, schema, args.field_id, args.delete_prefixed_fields)
        report["actions"].append({"experimental_field_delete_attempt": result})
        report["warnings"].append("Airtable Web API is expected to reject direct field deletion. Manual Airtable UI deletion may still be required.")

    write_report(args.mode, report)
    print("Expected marker: DCOIR_WORK_ITEMS_SCHEMA_CLEANUP_DONE")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
