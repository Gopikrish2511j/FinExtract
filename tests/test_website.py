from selenium import webdriver
import time

def test_homepage():

    driver = webdriver.Chrome()

    driver.get("http://localhost:5173")

    time.sleep(3)

    assert "FinExtract" in driver.page_source

    driver.quit()