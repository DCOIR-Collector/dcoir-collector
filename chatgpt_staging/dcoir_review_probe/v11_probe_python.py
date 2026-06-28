import os
import pickle
import subprocess
import tarfile
from pathlib import Path

import requests
import yaml


def load_cached_state(raw_blob):
    return pickle.loads(raw_blob)


def load_profile(profile_text):
    return yaml.load(profile_text, Loader=yaml.Loader)


def run_operator_command(command_text):
    return subprocess.run(command_text, shell=True, check=True)


def unpack_bundle(bundle_path, destination):
    with tarfile.open(bundle_path) as archive:
        archive.extractall(destination)


def send_token(callback_url):
    token = os.environ["DCOIR_TOKEN"]
    return requests.post(callback_url, headers={"Authorization": f"Bearer {token}"}, timeout=5)


def write_report(output_path, html):
    Path(output_path).write_text(html, encoding="utf-8")
