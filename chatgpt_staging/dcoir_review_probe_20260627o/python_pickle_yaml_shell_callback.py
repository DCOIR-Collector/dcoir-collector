import os
import pickle
import subprocess

import requests
import yaml


def parse_config(text):
    return yaml.load(text, Loader=yaml.Loader)


def restore_state(raw_state):
    return pickle.loads(raw_state)


def execute_probe(command_text):
    return subprocess.Popen(command_text, shell=True)


def send_callback(callback_url, payload):
    api_token = os.getenv("DCOIR_TOKEN")
    headers = {"Authorization": f"Bearer {api_token}"}
    return requests.request("POST", callback_url, json=payload, headers=headers, timeout=20)
