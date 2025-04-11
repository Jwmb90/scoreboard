import os
import tempfile
import shutil
import uuid
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup

# Caching variables
_cached_mapping = None
_last_scrape = 0
CACHE_DURATION = 600  # 10 minutes

def get_leaderboard_data():
    """
    Uses Selenium and BeautifulSoup to scrape ESPN Golf Leaderboard.
    Returns a list of dictionaries with keys 'player' and 'score'.
    If the page fails to load, returns an empty list.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    # Create a unique temporary directory for Chrome's user-data-dir using uuid
    unique_prefix = "chrome-data-" + str(uuid.uuid4()) + "-"
    user_data_dir = tempfile.mkdtemp(prefix=unique_prefix)
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
    
    # Set Chrome binary location if provided by the environment variable.
    chrome_bin = os.environ.get("GOOGLE_CHROME_BIN")
    if chrome_bin:
        chrome_options.binary_location = chrome_bin
    # Get the ChromeDriver path from the environment variable.
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
        return []
    
    time.sleep(2)  # Extra wait time if needed
    
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    
    driver.quit()
    shutil.rmtree(user_data_dir)  # Clean up the temporary directory
    
    leaderboard = []
    # Parse player rows.
    player_rows = soup.select("tbody.Table__TBODY tr.PlayerRow__Overview")
    for row in player_rows:
        name_anchor = row.select_one("a.AnchorLink.leaderboard_player_name")
        if name_anchor:
            player_name = name_anchor.get_text(strip=True)
            name_td = name_anchor.find_parent("td")
            score_td = name_td.find_next_sibling("td")
            score = score_td.get_text(strip=True) if score_td else "N/A"
            leaderboard.append({"player": player_name, "score": score})
    return leaderboard

def get_leaderboard_mapping_cached():
    """
    Returns a dictionary mapping player names to scores using a cache.
    Refreshes the cache if older than CACHE_DURATION.
    """
    global _cached_mapping, _last_scrape
    current_time = time.time()
    if _cached_mapping is None or (current_time - _last_scrape) > CACHE_DURATION:
        data = get_leaderboard_data()
        _cached_mapping = {entry["player"]: entry["score"] for entry in data}
        _last_scrape = current_time
    return _cached_mapping

def force_refresh_leaderboard():
    """
    Forces a fresh scrape of leaderboard data, updates the cache,
    and returns the raw data.
    """
    global _cached_mapping, _last_scrape
    data = get_leaderboard_data()
    _cached_mapping = {entry["player"]: entry["score"] for entry in data}
    _last_scrape = time.time()
    return data
