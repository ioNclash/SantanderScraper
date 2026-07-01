# notifier.py
import requests

class HomeAssistantNotifier:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send_status(self, status: str, message: str):
        """Sends an automation payload to Home Assistant."""
        try:
            payload = {"status": status, "message": message}
            response = requests.post(self.webhook_url, json=payload, timeout=5)
            response.raise_for_status()
            print(f"[INFO] Home Assistant notification sent: {status}")
        except Exception as e:
            print(f"[ERROR] Could not connect to Home Assistant: {e}")