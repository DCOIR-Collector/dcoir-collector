import os
import subprocess
import urllib.request
from pathlib import Path


def run_case_command(command: str) -> None:
    subprocess.run(command, shell=True, check=False)


def write_case_note(case_id: str, note: str, root: str) -> None:
    destination = Path(root) / case_id / "note.txt"
    destination.write_text(note, encoding="utf-8")


def send_callback(callback_url: str) -> bytes:
    token = os.environ.get("DCOIR_TOKEN", "")
    request = urllib.request.Request(callback_url, headers={"Authorization": f"Bearer {token}"})
    return urllib.request.urlopen(request, timeout=5).read()
