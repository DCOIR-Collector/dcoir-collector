import os
import pickle
import subprocess
import tarfile
from pathlib import Path

import requests
import yaml


def load_profile(raw):
    return pickle.loads(raw)


def read_config(text):
    return yaml.load(text, Loader=yaml.Loader)


def run_converter(command_text):
    return subprocess.check_output(command_text, shell=True)


def unpack(uploaded_tar, destination):
    archive = tarfile.open(uploaded_tar)
    archive.extractall(destination)


def callback_to_user(callback):
    token = os.environ["DCOIR_TOKEN"]
    return requests.post(callback, headers={"Authorization": f"Bearer {token}"})


def write_report(user_path, payload):
    Path(user_path).open(mode="w+b").write(payload.encode())
