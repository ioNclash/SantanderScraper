#!/usr/bin/env python3
import os
import sys
import argparse
import config

def parse_arguments():
    parser = argparse.ArgumentParser(description="Santander Automated Ingestion Orchestrator")
    parser.add_argument("--firefly", action="store_true", help="Convert payload to CSV and deliver to Firefly III watch directory")
    parser.add_argument("--no-jitter", action="store_true", help="Bypass random anti-bot startup delays")
    parser.add_argument("--notify", action="store_true", help="Send pipeline execution status to Home Assistant")
    return parser.parse_args()

def main():
    print("[ORCHESTRATOR] Initializing daily banking data ingest...")
    args = parse_arguments()

    if args.no_jitter:
        print("[ORCHESTRATOR] --no-jitter flag active. Commencing browser cycle immediately.")
    else:
        import random
        import time
        jitter = random.randint(1, 900)
        print(f"[ORCHESTRATOR] Anti-bot jitter active. Sleeping execution loop for {jitter} seconds...")
        time.sleep(jitter)

    notifier = None
    if args.notify:
        try:
            from notifier import Notifier
            notifier = Notifier()
            print("[ORCHESTRATOR] Home Assistant notification module: ACTIVE")
        except Exception as e:
            print(f"[WARN] Failed to load notification subsystem: {str(e)}")

    try:
        from santander_scraper import SantanderScraper
        
        scraper = SantanderScraper(
            personal_id=config.SANTANDER_PERSONAL_ID,
            security_number=config.SANTANDER_SECURITY_NUMBER
        )
        
        success, raw_file_path = scraper.run(debug=False)
        
        if not success:
            raise Exception(raw_file_path)
            
    except Exception as err:
        error_msg = f"Browser orchestration routine encountered a critical crash: {str(err)}"
        print(f"[ERROR] {error_msg}")
        if notifier:
            notifier.send_status("failed", error_msg)
        sys.exit(1)

    if args.firefly:
        print("[ORCHESTRATOR] Firefly III import module: ENABLED")
        try:
            import pandas as pd
            
            destination_path = os.path.join(config.FIREFLY_WATCH_DIR, "santander_daily.csv")
            print(f"[ORCHESTRATOR] Parsing Santander pseudo-Excel HTML layout from: {raw_file_path}")
            
            tables = pd.read_html(raw_file_path)
            df = tables[0]
            
            header_idx = df[df.astype(str).apply(lambda x: x.str.contains('Description', case=False)).any(axis=1)].index[0]
            
            df.columns = df.iloc[header_idx]
            df = df.iloc[header_idx + 1:].copy()
            
            df = df.dropna(subset=['Date', 'Description'], how='all')
            df = df.loc[:, df.columns.notna()]
            df.columns = df.columns.str.strip()
            
            df.to_csv(destination_path, index=False)
            print(f"[ORCHESTRATOR] Conversion complete! File delivered to: {destination_path}")
            
            if notifier:
                notifier.send_status("success", "Santander file successfully scraped, converted to CSV, and delivered to Firefly III.")
            print("[ORCHESTRATOR] Pipeline completed successfully with Firefly ingestion.")
            
        except Exception as e:
            error_msg = f"Failed to parse and transfer file to Firefly directory: {str(e)}"
            print(f"[ERROR] {error_msg}")
            if notifier:
                notifier.send_status("failed", error_msg)
            sys.exit(1)
            
    else:
        print(f"[ORCHESTRATOR] Processing finished. Standalone output retained at: {raw_file_path}")

if __name__ == "__main__":
    main()