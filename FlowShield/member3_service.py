import requests

MEMBER3_BASE_URL = "http://172.16.135.25:8000"


def get_worker_risk(worker_id: str):
    url = f"{MEMBER3_BASE_URL}/workers/{worker_id}/risk"

    response = requests.get(url, timeout=10)

    if response.status_code == 200:
        return response.json()

    if response.status_code == 404:
        return None

    response.raise_for_status()