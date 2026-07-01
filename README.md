# Santander UK to Firefly III Automation Pipeline

An automated open-source banking pipeline designed to log into Santander UK Online Banking safely, extract recent transaction ledgers as an Excel worksheet, and route them to a local Firefly III data ingestion folder. 

This project uses **Playwright** for dynamic browser interaction and includes smart anti-bot countermeasures, such as randomized operational execution windows (jitter).

---

## 🛠️ System Architecture & Workflow

1. **Orchestrator (`main.py`)**: Manages flags, evaluates persistent session cookies, and handles file transfer.
2. **Scraper Core (`santander_scraper.py`)**: Launches a persistent Chromium context to bypass recurring multi-factor challenges using real cookie profiles.
3. **Session Capturer**: A standalone tool to cleanly generate your initial authorization tokens via a one-time visual login.
4. **Notifier (`notifier.py`)**: Relays real-time pipeline status payloads straight to a Home Assistant automation webhook.

---

## 🚀 Getting Started

### 1. Prerequisites
Ensure your host machine has Python 3.10+ and the required browser binaries installed:

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Configuration Setup
Create a localized environment file. Do **not** commit this file to public version control.

```bash
cp config.example.py config.py
```

Open `config.py` and populate your credentials and infrastructure endpoints:

```python
SANTANDER_PERSONAL_ID = "YourID"
SANTANDER_SECURITY_NUMBER = "YourSecurityNumber"
FIREFLY_WATCH_DIR = "/home/nicholas/homelab/apps/firefly/imports"
HA_WEBHOOK_URL = "http://192.168.1.XX:8123/api/webhook/santander_sync"
```

### 3. Capturing Your Persistent Session Profile
To allow the script to run headlessly without getting blocked by Multi-Factor Authentication (MFA/OTP) every day, you must capture an initial authorized browser profile.

Run the scraper file directly to trigger the **interactive visual session window**:

```bash
python3 santander_scraper.py
```

* A visible Chromium window will open.
* Manually complete your Santander ID, Security Number, and any OTP/mobile notification verification steps.
* Once you safely reach the main banking accounts dashboard (`MyAccounts`), **manually close the browser window**. 

Your authentication cookies are now securely baked into `./santander_profile/` for future headless operations.

---

## ⚙️ Execution and Command-Line Flags

The pipeline is completely modular. By default, running `main.py` performs a local-only scrape without interacting with external network applications. Use flags to activate specific integrations:

| Flag | Functional Purpose |
| :--- | :--- |
| `--notify` | Enables status updates via your Home Assistant webhook URL. |
| `--firefly` | Automatically shifts the downloaded sheet to your Firefly III watch directory. |
| `--no-jitter` | Bypasses the 1-hour anti-bot randomized sleep window (ideal for manual testing). |

### Examples:

**Run a complete production pipeline (Cron Mode):**
```bash
python3 main.py --firefly --notify
```

**Run an immediate manual test locally without waiting or sending alerts:**
```bash
python3 main.py --no-jitter
```

---

## 🕒 Automation (Crontab Integration)

To make the ingestion completely hands-off, map the script to a system daemon scheduler like `cron`. It is highly recommended to fire the script at the *beginning* of an hour window; the script's internal jitter algorithm will automatically sleep for a random duration up to 60 minutes to prevent uniform access patterns.

Open your local user crontab configuration:

```bash
crontab -e
```

Append the execution mapping (e.g., triggering a random login sequence between 06:00 AM and 07:00 AM daily):

```text
0 6 * * * /usr/bin/python3 /home/nicholas/Documents/Projects/SantanderScraper/main.py --firefly --notify >> /home/nicholas/Documents/Projects/SantanderScraper/cron.log 2>&1
```

---

## ⚠️ Disclaimer
This is an unofficial, community-made utility developed strictly for private personal finance management and budgeting purposes. This software is not affiliated with, authorized, or endorsed by Santander Bank UK. Automated scraping of banking interfaces can violate specific regional Terms of Service. Use responsibly.