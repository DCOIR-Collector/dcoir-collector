import json
import os
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List

import dlt
import requests
from dlt.destinations import postgres

try:
    import psycopg2
    from psycopg2 import sql
except Exception:
    psycopg2 = None
    sql = None

BASE_ID = os.environ["DCOIR_AIRTABLE_BASE_ID"]
AIRTABLE_TOKEN = os.environ["DCOIR_AIRTABLE_TOKEN"]
POSTGRES_URL = os.environ["DCOIR_SUPABASE_POSTGRES_URL"]
OUT_REPORT = os.environ.get("DCOIR_DLT_REPORT_PATH", "dlt_airtable_to_supabase_report.json")
OUT_MD = os.environ.get("DCOIR_DLT_MD_PATH", "dlt_airtable_to_supabase_report.md")
DATASET_NAME = os.environ.get("DCOIR_DLT_DATASET_NAME", "airtable_import")
PIPELINE_NAME = os.environ.get("DCOIR_DLT_PIPELINE_NAME", "dcoir_airtable_to_supabase")
HEADERS = {"Authorization": f"Bearer {AIRTABLE_TOKEN}"}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def safe_name(table_name: str, table_id: str) -> str:
    name = re.sub(r"[^A-Za-z0-9_]+", "_", table_name).strip("_").lower()
    if not name:
        name = "airtable_table"
    if re.match(r"^[0-9]", name):
        name = "t_" + name
    return f"{name}_{table_id[-6:].lower()}"


def airtable_get(url: str) -> Dict[str, Any]:
    r = requests.get(url, headers=HEADERS, timeout=90)
    if not r.ok:
        raise RuntimeError(f"Airtable GET failed {r.status_code}: {r.text[:2000]}")
    return r.json()


def get_airtable_schema() -> List[Dict[str, Any]]:
    data = airtable_get(f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables")
    return list(data.get("tables", []))


def iter_records(table_id: str, table_name: str) -> Iterable[Dict[str, Any]]:
    encoded = requests.utils.quote(table_id, safe="")
    url = f"https://api.airtable.com/v0/{BASE_ID}/{encoded}"
    while url:
        data = airtable_get(url)
        for rec in data.get("records", []):
            row = {
                "airtable_record_id": rec.get("id"),
                "airtable_created_time": rec.get("createdTime"),
                "_airtable_table_id": table_id,
                "_airtable_table_name": table_name,
            }
            row.update(rec.get("fields") or {})
            yield row
        offset = data.get("offset")
        if offset:
            url = f"https://api.airtable.com/v0/{BASE_ID}/{encoded}?offset={requests.utils.quote(str(offset), safe='')}"
        else:
            url = None


def make_resource(table: Dict[str, Any]):
    table_id = table["id"]
    table_name = table["name"]
    resource_name = safe_name(table_name, table_id)

    @dlt.resource(name=resource_name, write_disposition="replace")
    def resource():
        yield from iter_records(table_id, table_name)

    resource.table_info = {
        "table_id": table_id,
        "table_name": table_name,
        "resource_name": resource_name,
        "field_count": len(table.get("fields", [])),
        "view_count": len(table.get("views", [])),
    }
    return resource


def fetch_table_counts() -> List[Dict[str, Any]]:
    if psycopg2 is None:
        return []
    rows: List[Dict[str, Any]] = []
    with psycopg2.connect(POSTGRES_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "select table_name from information_schema.tables where table_schema = %s and table_type = 'BASE TABLE' order by table_name",
                (DATASET_NAME,),
            )
            table_names = [r[0] for r in cur.fetchall()]
            for table_name in table_names:
                cur.execute(sql.SQL("select count(*) from {}.{}").format(sql.Identifier(DATASET_NAME), sql.Identifier(table_name)))
                rows.append({"table_schema": DATASET_NAME, "table_name": table_name, "row_count": int(cur.fetchone()[0])})
    return rows


def write_reports(report: Dict[str, Any]) -> None:
    with open(OUT_REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    lines = [
        "# dlt Airtable to Supabase import report",
        "",
        f"- result: {report.get('result')}",
        f"- pipeline_name: {PIPELINE_NAME}",
        f"- dataset_name: {DATASET_NAME}",
        f"- airtable_table_count: {report.get('airtable_table_count')}",
        f"- supabase_table_count: {report.get('supabase_table_count')}",
        "",
        "## Supabase table counts",
        "| table | rows |",
        "|---|---:|",
    ]
    for row in report.get("supabase_table_counts", []):
        lines.append(f"| {row['table_name']} | {row['row_count']} |")
    lines += ["", "## Airtable resource inventory", "| Airtable table | table_id | dlt resource | fields | views |", "|---|---|---|---:|---:|"]
    for row in report.get("resource_inventory", []):
        lines.append(f"| {row['table_name']} | {row['table_id']} | {row['resource_name']} | {row['field_count']} | {row['view_count']} |")
    if report.get("error"):
        lines += ["", "## Error", f"- {report.get('error_type')}: {report.get('error')}"]
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main() -> int:
    started = utc_now()
    tables = get_airtable_schema()
    resources = [make_resource(t) for t in tables]
    inventory = [r.table_info for r in resources]
    pipeline = dlt.pipeline(
        pipeline_name=PIPELINE_NAME,
        destination=postgres(credentials=POSTGRES_URL),
        dataset_name=DATASET_NAME,
    )
    load_info = pipeline.run([r() for r in resources], write_disposition="replace")
    counts = fetch_table_counts()
    report = {
        "generated_utc": utc_now(),
        "started_utc": started,
        "result": "success",
        "pipeline_name": PIPELINE_NAME,
        "dataset_name": DATASET_NAME,
        "airtable_base_id": BASE_ID,
        "airtable_table_count": len(tables),
        "resource_inventory": inventory,
        "supabase_table_count": len(counts),
        "supabase_table_counts": counts,
        "load_info_str": str(load_info),
    }
    write_reports(report)
    print("DLT_AIRTABLE_TO_SUPABASE_RESULT=success")
    print(f"DLT_DATASET_NAME={DATASET_NAME}")
    print(f"AIRTABLE_TABLE_COUNT={len(tables)}")
    print(f"SUPABASE_TABLE_COUNT={len(counts)}")
    for row in counts:
        print(f"SUPABASE_TABLE={row['table_name']}; rows={row['row_count']}")
    print(f"REPORT_JSON={OUT_REPORT}")
    print(f"REPORT_MD={OUT_MD}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        report = {
            "generated_utc": utc_now(),
            "result": "failure",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "dataset_name": DATASET_NAME,
        }
        write_reports(report)
        print("DLT_AIRTABLE_TO_SUPABASE_RESULT=failure", file=sys.stderr)
        print(f"ERROR_TYPE={type(exc).__name__}", file=sys.stderr)
        print(f"ERROR={exc}", file=sys.stderr)
        raise
