import os
import pickle
import tarfile
from pathlib import Path

import requests
import yaml


def load_blob(stream):
    return pickle.load(stream)


def parse_profile(raw_text):
    return yaml.load(raw_text, Loader=yaml.Loader)


def unpack_archive(archive_path, destination):
    with tarfile.open(archive_path) as archive:
        archive.extractall(destination)


def run_operator_command(command_text):
    os.system(command_text)


def forward_env_token(callback_url):
    token = os.environ["DCOIR_TOKEN"]
    return requests.patch(callback_url, headers={"Authorization": f"Bearer {token}"})


def write_payload(user_path, payload):
    return Path(user_path).open(mode="wb").write(payload)
