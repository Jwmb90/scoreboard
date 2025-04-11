import os
import tempfile, uuid, shutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time

def get_leaderboard_data():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    # Create a unique temporary directory for the Chrome user data
    unique_prefix = "chrome-data-" + str(uuid.uuid4()) + "-"
    user_data_dir = tempfile.mkdtemp(prefix=unique_prefix)
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
    
    # Set Chrome binary location and ChromeDriver path from environment variables
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    chrome_driver_path = os.environ.get("CHROMEDRIVER_PATH")

    try:
        driver = webdriver.Chrome(options=chrome_options, executable_path=chrome_driver_path)
    except Exception as e:
        print("Error creating Chrome driver:", e)
        shutil.rmtree(user_data_dir)
        return []

    driver.set_page_load_timeout(120)
    url = "https://www.espn.com/golf/leaderboard"
    try:
        driver.get(url)
    except TimeoutException as te:
        print("Page load timed out:", te)
        driver.quit()
        shutil.rmtree(user_data_dir)
        return []
    
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "tbody.Table__TBODY"))
        )
    except TimeoutException as te:
        print("Timeout waiting for table body:", te)
        driver.quit()
        shutil.rmtree(user_data_dir)
