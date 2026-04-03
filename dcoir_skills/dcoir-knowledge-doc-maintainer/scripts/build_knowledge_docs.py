#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path
from typing import Any, Dict, Iterable, List


def escape_cell(value: Any) -> str:
    text = str(value).replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("|", "\\|")
    return " ".join(part.strip() for part in text.splitlines() if part.strip())


def emit_table(headers: List[str], rows: Iterable[Iterable[Any]]) -> List[str]:
    out = [
        "| " + " | ".join(escape_cell(h) for h in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(escape_cell(v) for v in row) + " |")
    return out


def normalize_paragraph(text: str) -> str:
    return text.rstrip()


def build_doc_text(doc_data: Dict[str, Any]) -> str:
    filename = doc_data["filename"]
    if not filename.endswith(".md.txt"):
        raise ValueError(f"Knowledge doc filename must end with .md.txt: {filename}")

    lines: List[str] = []
    lines.append(f"# {doc_data['title']}")
    lines.append("")

    subtitle = doc_data.get("subtitle", "AFRICOM_SOC_IR / DCOIR supporting knowledge document")
    lines.append(f"_{subtitle}_")
    lines.append("")

    if doc_data.get("summary"):
        lines.append(f"**Summary:** {normalize_paragraph(doc_data['summary'])}")
        lines.append("")

    lines.append("## Source basis")
    lines.append("")
    source_rows = [
        ["Project sources", "; ".join(doc_data.get("project_sources", [])) or "None listed"],
        ["Official external sources", "; ".join(doc_data.get("external_sources", [])) or "Not required for this page"],
    ]
    if doc_data.get("notes"):
        source_rows.append(["Scope note", doc_data["notes"]])
    lines.extend(emit_table(["Source class", "Authoritative basis"], source_rows))
    lines.append("")

    for section in doc_data.get("sections", []):
        lines.append(f"## {section['heading']}")
        lines.append("")
        for para in section.get("paragraphs", []):
            lines.append(normalize_paragraph(para))
            lines.append("")
        for bullet in section.get("bullets", []):
            lines.append(f"- {normalize_paragraph(bullet)}")
        if section.get("bullets"):
            lines.append("")
        table_data = section.get("table")
        if table_data:
            lines.extend(emit_table(table_data["headers"], table_data["rows"]))
            lines.append("")
        for code_block in section.get("code_blocks", []):
            language = code_block.get("language", "")
            lines.append(f"```{language}".rstrip())
            lines.extend(code_block.get("lines", []))
            lines.append("```")
            lines.append("")

    lines.append("> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--spec-json', required=True)
    ap.add_argument('--output-dir', required=True)
    ap.add_argument('--zip-path', required=True)
    args = ap.parse_args()

    spec = json.loads(Path(args.spec_json).read_text(encoding='utf-8'))
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    produced: List[Path] = []
    for doc_data in spec['documents']:
        out_path = out_dir / doc_data['filename']
        out_path.write_text(build_doc_text(doc_data), encoding='utf-8')
        produced.append(out_path)

    zip_path = Path(args.zip_path)
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for path in produced:
            zf.write(path, arcname=path.name)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
