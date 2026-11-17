"""Check the VM API using only the Python standard library."""
import base64
import os
import json
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

credentials = os.environ['LAB_API_USERNAME'] + ':' + os.environ['LAB_API_PASSWORD']
headers = {'Authorization': 'Basic ' + base64.b64encode(credentials.encode()).decode()}
base_url = sys.argv[1].rstrip("/")
for study_id, expected_code in (("LAB-001", 200), ("LAB-999", 404)):
    try:
        response = urlopen(Request(f"{base_url}/studies/{study_id}", headers=headers), timeout=10)
    except HTTPError as error:
        response = error
    with response:
        body = json.load(response)
        if response.code != expected_code or body.get("study_id") != study_id:
            raise SystemExit(f"FAIL {study_id}: {response.code} {body}")
        if expected_code == 200 and not body.get("status"):
            raise SystemExit("FAIL: missing study status")
        if expected_code == 404 and body.get("error") != "Study not found":
            raise SystemExit("FAIL: unexpected error body")
        print(f"PASS {study_id}: HTTP {response.code} {body}")
