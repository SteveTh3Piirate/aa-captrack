import requests

def send_discord_webhook(url, payload):
    if not url:
        return False

    try:
        response = requests.post(url, json=payload, timeout=5)
        return response.status_code in (200, 204)
    except Exception:
        return False
