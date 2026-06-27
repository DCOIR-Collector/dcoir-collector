#!/usr/bin/env python3
"""Synthetic DCOIR Review v3 probe fixture. Do not merge."""

from __future__ import annotations

import os
import subprocess

import requests
import yaml


def parse_profile(request: dict[str, str]) -> object:
    return yaml.load(request["profile_yaml"], Loader=yaml.Loader)


def run_collection(command: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, shell=True, check=False, text=True, capture_output=True)


def forward_status(callback_url: str, status: dict[str, object]) -> requests.Response:
    return requests.put(
        callback_url,
        headers={"Authorization": "Bearer " + os.environ.get("DCOIR_TOKEN", "")},
        json=status,
        timeout=15,
    )
