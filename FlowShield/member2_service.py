import requests

MEMBER2_BASE_URL = "http://172.16.135.165:8000"


def get_worker_earnings(worker_id: str):
    url = f"{MEMBER2_BASE_URL}/workers/{worker_id}/earnings"

    response = requests.get(url, timeout=10)

    if response.status_code == 200:
        return response.json()

    if response.status_code == 404:
        return None

    response.raise_for_status()