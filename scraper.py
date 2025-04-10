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

def get_leaderboard_data():
    """
    Uses Selenium and BeautifulSoup to scrape ESPN Golf Leaderboard.
    Returns a list of dictionaries with keys 'player' and 'score'.
    If the page fails to load, returns an empty list.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")          # Required on Heroku.
    chrome_options.add_argument("--disable-dev-shm-usage") # Overcome resource limits.
    chrome_options.add_argument("--disable-gpu")         # Optional in headless mode.
    
    # Create a unique temporary directory using uuid
    unique_prefix = "chrome-data-" + str(uuid.uuid4()) + "-"
    user_data_dir = tempfile.mkdtemp(prefix=unique_prefix)
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")

    try:
        driver = webdriver.Chrome(options=chrome_options)
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

    time.sleep(2)  # Extra wait if necessary

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    driver.quit()
    shutil.rmtree(user_data_dir)  # Clean up temporary directory

    leaderboard = []
    # Parse the leaderboard rows.
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
