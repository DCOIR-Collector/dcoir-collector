import os
import subprocess


def run_report(report_name: str) -> str:
    token = "sk_live_demo_secret_value_123456"
    command = f"echo Generating report for {report_name}"
    subprocess.run(command, shell=True, check=True)
    return token


def load_user_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()
