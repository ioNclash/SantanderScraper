# main.py
import os
import shutil
import sys
import time
import random
import pandas
import argparse  # <-- Added for modular configuration flags
from santander_scraper import SantanderScraper
from notifier import HomeAssistantNotifier
import config

PROFILE_PATH = "./santander_profile"

def parse_arguments():
    """Parses command-line flags to determine active operational modules."""
    parser = argparse.ArgumentParser(
        description="Santander Bank Scraping Pipeline Orchestrator"
    )
    parser.add_argument(
        "--notify", 
        action="store_true", 
        help="Enable Home Assistant webhook status notifications"
    )
    parser.add_argument(
        "--firefly", 
        action="store_true", 
        help="Enable automated file movement to the Firefly III import directory"
    )
    parser.add_argument(
        "--no-jitter", 
        action="store_true", 
        help="Bypass the random anti-bot execution sleep window"
    )
    return parser.parse_args()

def main():
    args = parse_arguments()
    print("[ORCHESTRATOR] Initializing daily banking data ingest...")
    
    # Check if persistent cookies profile exists
    if not os.path.exists(PROFILE_PATH) or not os.listdir(PROFILE_PATH):
        print("\n" + "!"*60)
        print("[CRITICAL] Santander browser session profile folder is missing or empty!")
        print(f"Path evaluated: {os.path.abspath(PROFILE_PATH)}")
        print("\nTo fix this problem, please run the profile capturer script first:")
        print("    python3 santander_scraper.py")
        print("\nLog completely into your account and complete any Multi-Factor Auth.")
        print("Once the dashboard renders, close the browser window to save your profile.")
        print("!"*60 + "\n")
        sys.exit(1)

    # --- RANDOM JITTER LAYER ---
    if not args.no_jitter:
        delay_seconds = random.randint(0, 3600)
        delay_minutes = round(delay_seconds / 60, 1)
        print(f"[ORCHESTRATOR] Anti-bot Jitter: Sleeping for {delay_minutes} minutes before initiating logon...")
        time.sleep(delay_seconds)
        print("[ORCHESTRATOR] Sleep complete. Commencing secure browser cycle.")
    else:
        print("[ORCHESTRATOR] --no-jitter flag active. Commencing browser cycle immediately.")
    
    # Initialize Home Assistant only if explicitly requested via flag
    notifier = None
    if args.notify:
        print("[ORCHESTRATOR] Home Assistant module: ENABLED")
        notifier = HomeAssistantNotifier(config.HA_WEBHOOK_URL)
    else:
        print("[ORCHESTRATOR] Home Assistant module: DISABLED (Skipping notifications)")

    # Initialize scraper engine
    scraper = SantanderScraper(
        personal_id=config.SANTANDER_PERSONAL_ID, 
        security_number=config.SANTANDER_SECURITY_NUMBER
    )
    
    # Run the automated scraper headlessly
    success, result = scraper.run(debug=False)
    
    if not success:
        print(f"[ORCHESTRATOR] Scraper reported failure: {result}")
        if notifier:
            notifier.send_status("failed", f"Santander scraping failed: {result}")
        sys.exit(1)

    raw_file_path = result
    
    # File handling module logic
    if args.firefly:
        print("[ORCHESTRATOR] Firefly III import module: ENABLED")
        try:
            # Define our new Firefly-compatible CSV destination path
            destination_path = os.path.join(config.FIREFLY_WATCH_DIR, "santander_daily.csv")
            print(f"[ORCHESTRATOR] Converting Excel sheet to Firefly-native CSV layout at: {destination_path}")
            
            import pandas as pd
            # Read the raw .xls file and export it straight as a clean .csv
            df = pd.read_excel(raw_file_path)
            df.to_csv(destination_path, index=False)
            
            if notifier:
                notifier.send_status("success", "Santander file successfully scraped, converted to CSV, and delivered to Firefly III.")
            print("[ORCHESTRATOR] Pipeline completed successfully with Firefly ingestion.")
            
        except Exception as e:
            error_msg = f"Failed to convert and transfer file to Firefly directory: {str(e)}"
            print(f"[ERROR] {error_msg}")
            if notifier:
                notifier.send_status("failed", error_msg)
            sys.exit(1)
    else:
        print("[ORCHESTRATOR] Firefly III import module: DISABLED")
        print(f"[ORCHESTRATOR] File left in local directory payload zone: {raw_file_path}")
        if notifier:
            notifier.send_status("success", f"Santander file successfully scraped locally to {raw_file_path}.")
        print("[ORCHESTRATOR] Pipeline completed successfully (Local only execution).")

if __name__ == "__main__":
    main()