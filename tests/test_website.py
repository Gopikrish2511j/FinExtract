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
    # Path to the backend directory
    backend_dir = os.path.join(os.getcwd(), "backend")

    # Start the Flask server in the background
    # We use a dummy secret key and other config for testing if needed
    process = subprocess.Popen(
        ["python", "app.py"],
        cwd=backend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "PORT": "5000"}
    )

    # Wait for the server to start
    time.sleep(5)

    yield "http://localhost:5000"

    # Terminate the server after tests
    if os.name == 'nt':
        process.send_signal(signal.CTRL_C_EVENT)
    else:
        process.terminate()

def test_homepage(app_server):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        driver.get(app_server)

        # Wait for the page to load and animation to play a bit
        time.sleep(5)

        # Check for FinExtract in the page title or source
        assert "FinExtract" in driver.title or "FinExtract" in driver.page_source
        print("✅ Homepage test passed!")
    finally:
        driver.quit()
