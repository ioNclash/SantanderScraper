# santander_scraper.py
import os
import time
from playwright.sync_api import sync_playwright

class SantanderScraper:
    def __init__(self, personal_id: str, security_number: str, output_dir: str = "./tmp"):
        self.personal_id = personal_id
        self.security_number = security_number
        self.output_dir = output_dir
        self.profile_dir = "./santander_profile"
        self.target_url = "https://retail.santander.co.uk/olb/app/logon/access/"
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def _execute_extraction_workflow(self, page) -> str:
        """Executes the explicit 9-step Santander interface interaction model."""
        print("[INFO] Step 1: Login verification status checked.")

        # Step 2: View transactions (Click the link located in the informationBar sidebar)
        print("[INFO] Step 2: Selecting view transactions from the navigation panel...")
        page.locator("#informationBar").get_by_text("View transactions", exact=False).click()
        page.wait_for_load_state("networkidle")

        # Step 3: Click Download Transactions
        print("[INFO] Step 3: Launching the transactional download interface pane...")
        page.get_by_text("Download transactions", exact=False).click()
        page.wait_for_load_state("networkidle")

        # Step 4: Click Format Dropdown (Initial placeholder text reads 'Please choose')
        print("[INFO] Step 4: Opening format selection drop-down component...")
        dropdown = page.get_by_role("combobox", name="Please choose", exact=False)
        if not dropdown.is_visible():
            dropdown = page.locator("select:has-text('Please choose')")
        dropdown.click()

        # Step 5: Select Microsoft Excel (XLS)
        print("[INFO] Step 5: Committing download format choice to Microsoft Excel (XLS)...")
        dropdown.select_option(label="Microsoft Excel (XLS)")
        page.wait_for_load_state("domcontentloaded")

        # Step 6: Wait for dates field to appear (Targeting the exact form container)
        print("[INFO] Step 6: Polling browser DOM state for download form to render...")
        page.wait_for_selector("form#downloadTransaction, span.radioGroup", state="visible", timeout=15000)

        # Step 7: Select 'Since last download' radio choice
        print("[INFO] Step 7: Configuring export boundaries to 'Since last download' delta scope...")
        radio_target = page.locator("span.radioGroup").get_by_text("Since last download", exact=False)
        radio_target.wait_for(state="visible", timeout=5000)
        radio_target.click()

        # Step 8: Click download and resolve the asynchronous system stream transfer
        print("[INFO] Step 8: Initializing transactional file generation download event...")
        with page.expect_download() as download_info:
            page.get_by_role("button", name="Download", exact=False).click()
        download = download_info.value

        target_file = os.path.abspath(os.path.join(self.output_dir, "raw_santander.xls"))
        download.save_as(target_file)
        print(f"[INFO] File stream write complete to workspace: {target_file}")

        # Step 9: Log off safely using the logoff link ID
        print("[INFO] Step 9: Terminating secure application session via explicit log off action...")
        page.locator("#logoff").click()
        page.wait_for_load_state("networkidle")

        return target_file

    def run(self, debug: bool = False) -> tuple[bool, str]:
        """Executes the automated browser pipeline lifecycle."""
        with sync_playwright() as p:
            print(f"[INFO] Initializing browser engine. Headless={not debug}")
            context = p.chromium.launch_persistent_context(
                user_data_dir=self.profile_dir,
                headless=not debug,
                slow_mo=1500 if debug else 0
            )
            page = context.new_page()

            try:
                print("[INFO] Routing browser context straight to Santander login portal...")
                page.goto(self.target_url)
                page.wait_for_load_state("networkidle")

                if "MyAccounts" not in page.url:
                    print("[INFO] Profile session unauthenticated. Executing credentials injection...")
                    page.fill("input[name='personalId'], input#personalId, input[type='text']", self.personal_id)
                    page.fill("input[type='password'], input#securityNumber", self.security_number)
                    page.get_by_role("button", name="Log on", exact=True).click()
                    
                print("[INFO] Waiting for visual dashboard UI components to render...")
                page.wait_for_selector("text=View transactions", state="visible", timeout=30000)

                print("[INFO] Access authorization verified. Executing core extraction workflow...")
                downloaded_file_path = self._execute_extraction_workflow(page)
                return True, downloaded_file_path

            except Exception as err:
                error_msg = f"Extraction operational pipeline failure: {str(err)}"
                print(f"[ERROR] {error_msg}")
                return False, error_msg
            finally:
                context.close()


class SessionCapturer:
    """Class designed to visually launch the browser to save authorization tokens."""
    def __init__(self, profile_dir: str = "./santander_profile"):
        self.profile_dir = profile_dir
        self.target_url = "https://retail.santander.co.uk/olb/app/logon/access/"

    def capture(self):
        print(f"\n=== LAUNCHING CAPTURE SESSION ===")
        print(f"[INFO] Profile directory target: {self.profile_dir}")
        print("[INFO] The browser will open. Please completely log in, perform OTP checks,")
        print("[INFO] and reach your dashboard. Close the browser window manually when done.\n")
        
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=self.profile_dir,
                headless=False  # Must be visible to interact
            )
            page = context.new_page()
            page.goto(self.target_url)

            # Keep the context open until the user manually exits the browser window
            while True:
                try:
                    if page.is_closed():
                        break
                    time.sleep(1)
                except Exception:
                    break
            
            context.close()
        print("[SUCCESS] Browser session successfully synchronized and stored.")


if __name__ == "__main__":
    # If a user fires santander_scraper.py directly, run the session capturer tool
    capturer = SessionCapturer()
    capturer.capture()