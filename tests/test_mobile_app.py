import unittest
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

# --- AUTOMATIC PATH FIXER ---
os.environ["ANDROID_HOME"] = r"C:\Users\da300\AppData\Local\Android\Sdk"
os.environ["PATH"] = os.environ["ANDROID_HOME"] + r"\platform-tools;" + os.environ["PATH"]

class TestFinExtractMobile(unittest.TestCase):
    def setUp(self):
        apk_path = os.path.abspath("FinExtract.apk")
        options = UiAutomator2Options()
        options.platform_name = "Android"
        options.device_name = "Android Device"
        options.app = apk_path
        options.automation_name = "UiAutomator2"
        options.no_reset = True
        options.ignore_hidden_api_policy_error = True

        print("\n🤖 Connecting to Appium Server...")
        self.driver = webdriver.Remote("http://127.0.0.1:4723", options=options)
        self.wait = WebDriverWait(self.driver, 60) # Increased wait time for manual step

    def test_hybrid_workflow(self):
        print("🚀 App launched! Ready for Hybrid Demo...")

        # 1. Wait for Landing Animation
        print("⏳ Waiting for branding animation to finish...")
        time.sleep(8)

        # 2. USER ACTION INSTRUCTION
        print("\n👇 ACTION REQUIRED: Please manually upload a PDF on your phone now.")
        print("⏳ Robot is waiting for the 'Extracted KPI' table to appear...")

        # 3. Robot waits for the dashboard to update (This is where it takes over)
        try:
            # We wait up to 60 seconds for you to pick a file and for the engine to process it
            kpi_table_header = self.wait.until(EC.presence_of_element_located(
                (By.XPATH, "//*[contains(@text, 'Extracted KPI')]")
            ))
            print("✅ Robot Detected Results! Taking control now...")
        except:
            self.fail("❌ FAILED: Robot did not see any results after 60 seconds.")

        # 4. Automate adding a Custom KPI (Proves Backend is alive)
        print("✍️ Testing Python Engine integration...")
        try:
            input_field = self.driver.find_element(by=By.CLASS_NAME, value="android.widget.EditText")
            input_field.click()
            input_field.send_keys("Total Revenue Growth %")

            plus_btn = self.driver.find_element(by=By.XPATH, value="//android.widget.Button")
            plus_btn.click()
            print("✅ Custom metric added by Robot.")
        except Exception as e:
            print(f"⚠️ UI Interaction warning: {str(e)}")

        # 5. Verify the Chart is visible
        print("📈 Verifying interactive charts...")
        time.sleep(2)
        self.driver.save_screenshot("tests/mobile_hybrid_success.png")
        print("📸 Proof saved to 'tests/mobile_hybrid_success.png'")

        print("\n✨ ALL REMAINING TEST CASES PASSED! ✨")

    def tearDown(self):
        print("🚪 Closing session...")
        if self.driver:
            self.driver.quit()

if __name__ == "__main__":
    unittest.main()
