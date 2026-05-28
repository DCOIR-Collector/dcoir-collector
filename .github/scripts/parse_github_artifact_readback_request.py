#!/usr/bin/env python3
import argparse
import json
import pathlib
import re
import sys

SCHEMA = "dcoir.chatgpt_staging.github_artifact_readback_request.v1"
SAFE_REQUEST_ID = re.compile(r"[A-Za-z0-9._-]+")
NUMERIC = re.compile(r"[0-9]+")


def clean(payload: dict[str, object], name: str) -> str:
    value = str(payload.get(name, "")).strip()
    if "\n" in value or "\r" in value:
        raise SystemExit(f"{name} must not contain newlines")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("request_path")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    path = pathlib.Path(args.request_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != SCHEMA:
        raise SystemExit(f"artifact readback request schema must be {SCHEMA}")

    request_id = clean(payload, "request_id")
    source_run_id = clean(payload, "source_run_id")
    artifact_name = clean(payload, "artifact_name")
    artifact_id = clean(payload, "artifact_id")
    artifact_subpath = clean(payload, "artifact_subpath")

    if not request_id:
        raise SystemExit("request_id field is required in the request JSON")
    if not source_run_id:
        raise SystemExit("source_run_id field is required in the request JSON")
    if not SAFE_REQUEST_ID.fullmatch(request_id):
        raise SystemExit(f"Unsafe request_id: {request_id!r}")
    if not NUMERIC.fullmatch(source_run_id):
        raise SystemExit("source_run_id must be numeric")
    if not artifact_name and not artifact_id:
        raise SystemExit("artifact_name or artifact_id is required")
    if artifact_id and not NUMERIC.fullmatch(artifact_id):
        raise SystemExit("artifact_id must be numeric when provided")
    if artifact_subpath:
        pure = pathlib.PurePosixPath(artifact_subpath)
        if artifact_subpath.startswith("/") or ".." in pure.parts:
            raise SystemExit("artifact_subpath must be relative and must not contain parent traversal")

    output_path = pathlib.Path(args.output)
    with output_path.open("a", encoding="utf-8") as fh:
        fh.write(f"request_path={path.as_posix()}\n")
        fh.write(f"source_run_id={source_run_id}\n")
        fh.write(f"artifact_name={artifact_name}\n")
        fh.write(f"artifact_id={artifact_id}\n")
        fh.write(f"request_id={request_id}\n")
        fh.write(f"artifact_subpath={artifact_subpath}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
