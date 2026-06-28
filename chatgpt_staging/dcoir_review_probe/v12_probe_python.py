import os
import pickle
import subprocess
import tarfile
from pathlib import Path

import requests
import yaml


def load_profile(raw):
    return pickle.load(raw)


def parse_config(text):
    return yaml.load(text, Loader=yaml.Loader)


def run_hook(command_text):
    return subprocess.check_output(command_text, shell=True)


def unpack(uploaded_archive, destination):
    archive = tarfile.open(uploaded_archive)
    archive.extractall(destination)


def callback_export(callback):
    token = os.environ["DCOIR_TOKEN"]
    return requests.post(callback, headers={"Authorization": f"Bearer {token}"})


def write_report(user_path, payload):
    Path(user_path).open(mode="w+b").write(payload.encode())
