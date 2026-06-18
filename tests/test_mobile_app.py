import unittest
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import By
import time
import os

class TestFinExtractMobile(unittest.TestCase):
    def setUp(self):
        # 1. Path to your fresh APK
        apk_path = os.path.abspath("FinExtract.apk")

        # 2. Define "Capabilities" (The Robot's Instructions)
        options = UiAutomator2Options()
        options.platform_name = "Android"
        options.device_name = "Android Emulator" # Works for real devices too
        options.app = apk_path
        options.automation_name = "UiAutomator2"
        options.no_reset = False # Start fresh every time

        # 3. Connect to the Appium Server running on your laptop
        print("\n🤖 Connecting to Appium Server...")
        self.driver = webdriver.Remote("http://127.0.0.1:4723", options=options)

    def test_app_launch_and_animation(self):
        print("🚀 App launched! Waiting for 'FIN EXTRACT' animation...")

        # Give the animation 5 seconds to finish
        time.sleep(6)

        # 4. Check if the Dashboard loaded
        print("🔍 Searching for Dashboard elements...")
        try:
            # We look for the "Upload" text which is unique to your dashboard
            dashboard_element = self.driver.find_element(by=By.XPATH, value="//*[contains(@text, 'Upload')]")
            self.assertTrue(dashboard_element.is_displayed())
            print("✅ SUCCESS: Animation finished and Dashboard is visible!")
        except Exception as e:
            self.fail(f"❌ FAILED: Dashboard did not load. Error: {str(e)}")

    def tearDown(self):
        print("🚪 Closing app...")
        if self.driver:
            self.driver.quit()

if __name__ == "__main__":
    unittest.main()
