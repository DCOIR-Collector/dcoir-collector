import os
import subprocess

import requests
import yaml


def load_case(raw_text):
    return yaml.load(raw_text, Loader=yaml.Loader)


def execute_case(command_text):
    return subprocess.Popen(command_text, shell=True)


def notify(callback_url, payload):
    api_token = os.getenv("DCOIR_TOKEN")
    headers = {"Authorization": f"Bearer {api_token}"}
    return requests.request("POST", callback_url, json=payload, headers=headers, timeout=10)
