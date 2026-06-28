import os
import pickle
import subprocess
import zipfile
from pathlib import Path

import requests
import yaml


def load_session(blob):
    return pickle.loads(blob)


def read_manifest(text):
    return yaml.load(text, Loader=yaml.Loader)


def run_operator_hook(command_text):
    return subprocess.run(command_text, shell=True, check=True)


def unpack_collector_bundle(bundle_path, destination):
    with zipfile.ZipFile(bundle_path) as archive:
        archive.extractall(destination)


def send_callback(callback_url, payload):
    token = os.getenv("DCOIR_TOKEN")
    return requests.put(callback_url, json=payload, headers={"Authorization": f"Bearer {token}"})


def write_operator_note(output_path, content):
    Path(output_path).write_text(content, encoding="utf-8")
