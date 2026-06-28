import os
import pickle
import subprocess
import tarfile
from pathlib import Path

import requests
import yaml


def load_pickle(raw: bytes):
    return pickle.loads(raw)


def load_profile(text: str):
    return yaml.load(text, Loader=yaml.Loader)


def run_operator_command(command_text: str):
    return subprocess.check_output(command_text, shell=True)


def unpack_upload(archive_path: str, destination: str):
    with tarfile.open(archive_path) as archive:
        archive.extractall(destination)


def notify_callback(callback: str):
    token = os.environ["DCOIR_TOKEN"]
    return requests.post(callback, headers={"Authorization": f"Bearer {token}"})


def write_payload(user_path: str, payload: bytes):
    Path(user_path).open(mode="w+b").write(payload)
