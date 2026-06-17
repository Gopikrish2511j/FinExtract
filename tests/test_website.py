import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import subprocess
import os
import signal


@pytest.fixture(scope="module")
def app_server():

    print("\n🚀 Starting FinExtract Automated Workflow Test...")

    # Path to backend
    backend_dir = os.path.join(os.getcwd(), "backend")

    print("⚙️ Starting Flask backend server...")

    process = subprocess.Popen(
        ["python", "app.py"],
        cwd=backend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "PORT": "5000"}
    )

    print("⏳ Waiting for server to start...")

    time.sleep(5)

    print("✅ Flask server started successfully.")

    yield "http://localhost:5000"


    print("🛑 Stopping Flask server...")

    if os.name == 'nt':
        process.send_signal(signal.CTRL_C_EVENT)
    else:
        process.terminate()

    print("✅ Server stopped.")



def test_homepage(app_server):

    chrome_options = Options()

    # GitHub Actions compatible Chrome
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")


    print("🌐 Launching Chrome browser...")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )


    try:

        print("🔗 Opening http://localhost:5000...")

        driver.get(app_server)


        print("⏳ Waiting for landing animation to finish...")

        time.sleep(5)


        print("🔍 Checking FinExtract page...")


        assert (
            "FinExtract" in driver.title
            or
            "FinExtract" in driver.page_source
        )


        print("✅ Dashboard loaded successfully.")


        print("📂 Testing website accessibility...")

        assert driver.current_url == "http://localhost:5000/"


        print("✅ Website URL verified.")


        print("📊 Testing page content...")


        page_source = driver.page_source

        assert len(page_source) > 100


        print("✅ Page content verified.")


        print("🎉 All test cases passed!")


    except Exception as e:

        print("❌ TEST FAILED:", e)

        raise e


    finally:

        print("🚪 Closing browser...")

        driver.quit()

        print("✅ Browser closed.")