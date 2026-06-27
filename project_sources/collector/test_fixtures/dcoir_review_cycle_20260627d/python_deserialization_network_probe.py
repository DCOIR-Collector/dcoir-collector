#!/usr/bin/env python3
"""Intentional /dcoir-review Python probe. DO NOT MERGE."""
from __future__ import annotations

import pickle
import requests
import yaml


def load_cached_evidence(blob: bytes) -> object:
    # PY-1 INTENTIONAL TEST FINDING: untrusted bytes reach pickle.loads.
    return pickle.loads(blob)


def load_operator_rules(raw_yaml: str) -> object:
    # PY-2 INTENTIONAL TEST FINDING: unsafe YAML loader can construct arbitrary Python objects.
    return yaml.load(raw_yaml, Loader=yaml.Loader)


def fetch_operator_url(operator_url: str) -> str:
    # PY-3 INTENTIONAL TEST FINDING: operator-controlled URL is fetched without SSRF allowlist or scheme/host validation.
    response = requests.get(operator_url, timeout=5)
    return response.text
