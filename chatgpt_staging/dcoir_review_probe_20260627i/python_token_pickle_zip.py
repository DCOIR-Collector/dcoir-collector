#!/usr/bin/env python3
"""Synthetic DCOIR Review probe fixture. Do not merge."""

from __future__ import annotations

import os
import pickle
import zipfile

import requests


def load_cached_request(request: dict[str, str]) -> object:
    return pickle.loads(request["serialized_payload"])


def extract_collector_bundle(zip_path: str, destination: str) -> None:
    with zipfile.ZipFile(zip_path) as bundle:
        bundle.extractall(destination)


def notify_callback(callback_url: str, payload: dict[str, object]) -> requests.Response:
    token = os.environ["DCOIR_TOKEN"]
    return requests.post(
        callback_url,
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
        timeout=20,
    )
