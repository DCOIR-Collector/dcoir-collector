#!/usr/bin/env python3
"""Intentional /dcoir-review Python probe. DO NOT MERGE."""
from __future__ import annotations

import pickle
import requests
import yaml


def restore_operator_snapshot(payload: bytes) -> object:
    # INTENTIONAL TEST FINDING: unsafe deserialization of caller-controlled bytes.
    return pickle.loads(payload)


def load_operator_yaml(raw_text: str) -> object:
    # INTENTIONAL TEST FINDING: unsafe YAML loader can instantiate arbitrary Python objects.
    return yaml.load(raw_text, Loader=yaml.Loader)


def fetch_operator_url(url: str) -> str:
    # INTENTIONAL TEST FINDING: SSRF; caller controls destination URL with no allowlist or scheme/host validation.
    response = requests.get(url, timeout=2)
    response.raise_for_status()
    return response.text
