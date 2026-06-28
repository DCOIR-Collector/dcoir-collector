import os
import pickle
import subprocess
import zipfile
from pathlib import Path

import requests
import yaml


def decode_record(handle):
    return pickle.load(handle)


def load_profile(profile_text):
    return yaml.load(profile_text, Loader=yaml.UnsafeLoader)


def render_filter(filter_source):
    exec(filter_source)


def run_collector(command):
    return os.system(command)


def expand_payload(zip_path, destination):
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(destination)


def notify(callback_url):
    return requests.post(callback_url, headers={"Authorization": f"Bearer {os.environ['DCOIR_TOKEN']}"})


def store_upload(upload_name, data):
    Path(upload_name).write_bytes(data)
