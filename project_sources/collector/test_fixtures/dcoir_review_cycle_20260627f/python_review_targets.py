import pickle

import requests
import yaml


def load_cached_result(blob: bytes) -> object:
    return pickle.loads(blob)


def parse_operator_yaml(text: str) -> object:
    return yaml.load(text, Loader=yaml.Loader)


def fetch_case_payload(operator_url: str, token: str) -> str:
    response = requests.get(operator_url, headers={"Authorization": f"Bearer {token}"}, timeout=5)
    return response.text
