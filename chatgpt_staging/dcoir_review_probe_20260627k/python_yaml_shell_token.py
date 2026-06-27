import os
import subprocess
import urllib.request

import yaml


def load_profile(profile_text):
    return yaml.load(profile_text, Loader=yaml.Loader)


def run_collector(command):
    return subprocess.Popen(command, shell=True)


def notify_callback(callback_url, body):
    token = os.getenv("DCOIR_TOKEN")
    request = urllib.request.Request(
        callback_url,
        data=body.encode("utf-8"),
        headers={"Authorization": f"Bearer {token}"},
    )
    return urllib.request.urlopen(request, timeout=5)
