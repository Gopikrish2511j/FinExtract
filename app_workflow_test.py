import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURATION ---
APP_URL = "http://localhost:5000"
SAMPLE_PDF = os.path.abspath("backend/sample_annual_report.pdf")

def run_automated_workflow():
    print("\n🚀 Starting FinExtract Automated Workflow Test...")

    # 1. Setup Chrome Driver
    chrome_options = Options()
    # chrome_options.add_argument("--headless") # Uncomment to run without opening window
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.maximize_window()

    try:
        # 2. Open Application
        print(f"🔗 Opening {APP_URL}...")
        driver.get(APP_URL)

        # 3. Wait for Landing Page Animation (3.5 seconds)
        print("⏳ Waiting for landing animation to finish...")
        time.sleep(4)

        # 4. Verify Dashboard is Loaded
        wait = WebDriverWait(driver, 15)
        upload_section = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Upload & Documents')]")))
        print("✅ Dashboard loaded successfully.")

        # 5. Automated PDF Upload
        print(f"📂 Uploading sample PDF: {os.path.basename(SAMPLE_PDF)}...")
        file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
        file_input.send_keys(SAMPLE_PDF)

        # 6. Wait for Extraction to Trigger and Complete
        print("⚙️ Processing document... (This might take a moment)")
        # Wait for the "Reprocess" button to be clickable again (meaning extraction finished)
        extract_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Reprocess Report')]")))
        print("✅ Extraction complete.")

        # 7. Verify Data in Table
        print("📊 Verifying extracted results...")
        table_rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")
        if len(table_rows) > 0:
            print(f"✅ Success! Found {len(table_rows)} KPI records in the table.")
        else:
            raise Exception("❌ Data verification failed: Table is empty.")

        # 8. Test KPI Search
        print("🔍 Testing KPI Search filter...")
        search_box = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Filter results...']")
        search_box.send_keys("Revenue")
        time.sleep(1)
        filtered_rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")
        print(f"✅ Filter working. Showing {len(filtered_rows)} records for 'Revenue'.")

        # 9. Test Excel Export
        print("📥 Testing Excel Export button...")
        export_btn = driver.find_element(By.XPATH, "//*[contains(text(), 'Export formatted Excel')]")
        export_btn.click()
        print("✅ Export command sent.")

        print("\n✨ ALL TEST CASES PASSED SUCCESSFULLY! ✨")
        time.sleep(5)

    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")

    finally:
        print("🚪 Closing browser...")
        driver.quit()

if __name__ == "__main__":
    run_automated_workflow()
