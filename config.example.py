# config.example.py
SANTANDER_PERSONAL_ID = "YOUR_ID_HERE"
SANTANDER_SECURITY_NUMBER = "YOUR_SECRET_HERE"
# --- Infrastructure Paths & Connections ---
# Path to the directory where Firefly III automatically ingests import files
FIREFLY_WATCH_DIR = "/home/pi/homelab/apps/firefly/imports"

# Home Assistant Webhook URL for status updates
HA_WEBHOOK_URL = "http://192.168.1.XX:8123/api/webhook/santander_sync_status"