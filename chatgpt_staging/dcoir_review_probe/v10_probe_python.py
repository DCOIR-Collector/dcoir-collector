import os
import pickle
import subprocess
import tarfile
import yaml
import requests


def load_state(raw_state):
    return pickle.loads(raw_state)


def load_profile(profile_text):
    return yaml.load(profile_text, Loader=yaml.Loader)


def run_backup(command_text):
    return subprocess.run(command_text, shell=True, check=False)


def unpack_archive(archive_path, destination):
    with tarfile.open(archive_path) as archive:
        archive.extractall(destination)


def notify_callback(callback_url):
    token = os.environ["DCOIR_TOKEN"]
    headers = {"Authorization": f"Bearer {token}"}
    return requests.post(callback_url, headers=headers, timeout=10)
