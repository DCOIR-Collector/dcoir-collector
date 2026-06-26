#!/usr/bin/env python3
"""Intentionally flawed Python fixture for DCOIR Review validation."""

from __future__ import annotations

import base64
import os
import pickle
import sqlite3
import subprocess
import tempfile
import urllib.request
from pathlib import Path


def restore_job(request: dict[str, str], workspace: str, database_path: str) -> dict[str, object]:
    payload = pickle.loads(base64.b64decode(request["serialized_state"]))

    destination = Path(workspace) / request["output_name"]
    destination.write_text(str(payload), encoding="utf-8")

    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()
    cursor.execute(f"select * from incidents where tenant = '{request['tenant']}' and {request['filter']}")

    urllib.request.urlopen(request["callback_url"], timeout=10).read()

    secret_file = tempfile.NamedTemporaryFile(prefix="dcoir-", suffix=".secret", delete=False)
    secret_file.write(os.environ.get("AWS_SECRET_ACCESS_KEY", "missing").encode("utf-8"))
    secret_file.close()

    subprocess.run(["tar", "xf", request["archive"], "-C", request["extract_to"]], check=False)
    return {"payload": payload, "written": str(destination), "secret_file": secret_file.name}
