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
        """Executes the 9-step Santander statement download workflow."""
        print("[INFO] Step 1: Login verified.")

        print("[INFO] Step 2: Navigating to 'View transactions'...")
        page.locator("#informationBar").get_by_text("View transactions", exact=False).click()
        page.wait_for_load_state("networkidle")

        print("[INFO] Step 3: Opening transaction download pane...")
        page.get_by_text("Download transactions", exact=False).click()
        page.wait_for_load_state("networkidle")

        print("[INFO] Step 4: Interacting with format dropdown...")
        dropdown = page.get_by_role("combobox", name="Please choose", exact=False)
        if not dropdown.is_visible():
            dropdown = page.locator("select:has-text('Please choose')")
        dropdown.click()

        print("[INFO] Step 5: Selecting Microsoft Excel (XLS) format...")
        dropdown.select_option(label="Microsoft Excel (XLS)")
        page.wait_for_load_state("domcontentloaded")

        print("[INFO] Step 6: Waiting for download form elements to load...")
        page.wait_for_selector("form#downloadTransaction, span.radioGroup", state="visible", timeout=15000)

        print("[INFO] Step 7: Selecting 'Since last download' option...")
        # Fixed: Using direct global text targeting to bypass layout wrapper changes
        radio_target = page.get_by_text("Since last download", exact=False)
        radio_target.wait_for(state="visible", timeout=5000)
        radio_target.click()

        print("[INFO] Step 8: Triggering file download stream...")
        with page.expect_download() as download_info:
            page.get_by_role("button", name="Download", exact=False).click()
        download = download_info.value

        target_file = os.path.abspath(os.path.join(self.output_dir, "raw_santander.xls"))
        download.save_as(target_file)
        print(f"[INFO] File saved successfully: {target_file}")

        print("[INFO] Step 9: Logging off cleanly...")
        page.locator("#logoff").click()
        page.wait_for_load_state("networkidle")

        return target_file

    def run(self, debug: bool = False) -> tuple[bool, str]:
        """Manages the lifecycle of the browser execution thread."""
        with sync_playwright() as p:
            print(f"[INFO] Launching browser engine (Headless={not debug})")
            context = p.chromium.launch_persistent_context(
                user_data_dir=self.profile_dir,
                headless=not debug,
                slow_mo=1500 if debug else 0
            )
            page = context.new_page()

            try:
                print("[INFO] Navigating to Santander login portal...")
                page.goto(self.target_url)
                page.wait_for_load_state("networkidle")

                if "MyAccounts" not in page.url:
                    print("[INFO] Session unauthenticated. Injecting credentials...")
                    page.fill("input[name='personalId'], input#personalId, input[type='text']", self.personal_id)
                    page.fill("input[type='password'], input#securityNumber", self.security_number)
                    page.get_by_role("button", name="Log on", exact=True).click()
                    
                print("[INFO] Waiting for dashboard components to render...")
                page.wait_for_selector("text=View transactions", state="visible", timeout=30000)

                print("[INFO] Authentication confirmed. Starting extraction pipeline...")
                downloaded_file_path = self._execute_extraction_workflow(page)
                return True, downloaded_file_path

            except Exception as err:
                error_msg = f"Extraction pipeline failure: {str(err)}"
                print(f"[ERROR] {error_msg}")
                return False, error_msg
            finally:
                context.close()


class SessionCapturer:
    """Launches a visible browser window to save cookies and MFA tokens."""
    def __init__(self, profile_dir: str = "./santander_profile"):
        self.profile_dir = profile_dir
        self.target_url = "https://retail.santander.co.uk/olb/app/logon/access/"

    def capture(self):
        print(f"\n=== LAUNCHING CAPTURE SESSION ===")
        print(f"[INFO] Target Profile: {self.profile_dir}")
        print("[INFO] Complete authentication manually. Close the browser window when finished.\n")
        
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=self.profile_dir,
                headless=False
            )
            page = context.new_page()
            page.goto(self.target_url)

            while True:
                try:
                    if page.is_closed():
                        break
                    time.sleep(1)
                except Exception:
                    break
            
            context.close()
        print("[SUCCESS] Session tokens updated and stored successfully.")


if __name__ == "__main__":
    capturer = SessionCapturer()
    capturer.capture()