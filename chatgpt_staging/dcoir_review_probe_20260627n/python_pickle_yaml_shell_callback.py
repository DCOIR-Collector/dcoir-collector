import os
import pickle
import subprocess

import requests
import yaml


def load_yaml(raw_text):
    return yaml.load(raw_text, Loader=yaml.Loader)


def load_pickle(blob):
    return pickle.loads(blob)


def run_command(command):
    return subprocess.run(command, shell=True, check=False)


def post_result(callback_url, payload):
    token = os.environ["DCOIR_TOKEN"]
    headers = {"Authorization": f"Bearer {token}"}
    return requests.post(callback_url, json=payload, headers=headers, timeout=15)
