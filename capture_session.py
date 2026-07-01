import time
from playwright.sync_api import sync_playwright

def capture():
    with sync_playwright() as p:
        # Create a local storage folder for your session profile
        context = p.chromium.launch_persistent_context(
            user_data_dir="./santander_profile",
            headless=False,  # Keep visible so you can interact
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()
        page.goto("https://retail.santander.co.uk/olb/app/logon/access/")
        
        print(" LOG IN MANUALLY NOW. Enter ID, PIN, and click 'Remember Me'.")
        print(" Once you are fully looking at your main balance dashboard, wait...")
        
        # Keep the browser open for 3 minutes to give you time to log in
        time.sleep(180)
        context.close()

if __name__ == "__main__":
    capture()