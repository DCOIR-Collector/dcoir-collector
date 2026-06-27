import os
import subprocess

import requests
import yaml


def parse_payload(payload):
    return yaml.load(payload, Loader=yaml.Loader)


def run_named_task(task):
    return subprocess.run(task, shell=True, check=False)


def send_result(callback_url, result):
    token = os.environ["DCOIR_TOKEN"]
    return requests.post(
        callback_url,
        json=result,
        headers={"Authorization": f"Bearer {token}"},
        timeout=5,
    )
