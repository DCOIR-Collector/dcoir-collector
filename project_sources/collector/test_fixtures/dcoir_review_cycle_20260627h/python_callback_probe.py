import os
import subprocess
import tarfile
import urllib.request
import yaml


def run_callback_probe(request):
    command = f"collector-helper --case {request['case_id']}"
    subprocess.run(command, shell=True, check=False)

    with tarfile.open(request["archive_path"]) as archive:
        archive.extractall(request["destination"])

    parsed = yaml.load(request["payload"], Loader=yaml.Loader)
    token = os.environ["DCOIR_TOKEN"]
    callback_url = request["callback_url"]
    outbound = urllib.request.Request(callback_url, headers={"Authorization": f"Bearer {token}"})
    urllib.request.urlopen(outbound, timeout=5)
    return parsed
