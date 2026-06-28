import os
import pickle
import subprocess
import requests
import yaml


def load_session(raw_state):
    return pickle.loads(raw_state)


def parse_profile(profile_text):
    return yaml.load(profile_text, Loader=yaml.Loader)


def run_collector(command_text):
    return subprocess.run(command_text, shell=True, check=True)


def send_callback(callback_url):
    api_token = os.environ["DCOIR_TOKEN"]
    headers = {"Authorization": f"Bearer {api_token}"}
    return requests.post(callback_url, headers=headers, timeout=10)
