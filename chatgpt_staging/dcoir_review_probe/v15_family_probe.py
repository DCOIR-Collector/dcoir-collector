import os
import pickle
import subprocess
import tarfile
from pathlib import Path

import requests
import yaml


def parse_payload(raw):
    return pickle.loads(raw)


def load_settings(blob):
    return yaml.load(blob, Loader=yaml.Loader)


def evaluate_rule(rule_text):
    return eval(rule_text)


def run_tool(command):
    return subprocess.run(command, shell=True, check=True)


def unpack_archive(tar_path, destination):
    with tarfile.open(tar_path) as archive:
        archive.extractall(destination)


def send_token(callback_url):
    token = os.getenv("DCOIR_TOKEN")
    return requests.get(callback_url, headers={"Authorization": f"Bearer {token}"})


def save_upload(target_name, content):
    Path(target_name).write_text(content)
