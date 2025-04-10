import tempfile
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import time

def get_leaderboard_data():
    """
    Uses Selenium and BeautifulSoup to scrape ESPN Golf Leaderboard.
    Returns a list of dictionaries with keys 'player' and 'score'.
    If the page fails to load within the timeout, returns an empty list.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")              # Required on Heroku.
    chrome_options.add_argument("--disable-dev-shm-usage")     # Overcome limited resource problems.
    chrome_options.add_argument("--disable-gpu")             # Often recommended in headless environments.
    
    # Create a unique temporary directory for the user-data-dir
    user_data_dir = tempfile.mkdtemp()
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # Set page load timeout (adjust as needed)
    driver.set_page_load_timeout(120)
    url = "https://www.espn.com/golf/leaderboard"
    
    try:
        driver.get(url)
    except TimeoutException as te:
        print("Page load timed out:", te)
        driver.quit()
        shutil.rmtree(user_data_dir)  # Clean up the temporary directory
        return []  # Fallback: return empty list
    
    # Wait for the table body containing the scores to be present.
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "tbody.Table__TBODY"))
        )
    except TimeoutException as te:
        print("Timeout waiting for table body:", te)
        driver.quit()
        shutil.rmtree(user_data_dir)  # Clean up the temporary directory
        return []
    
    time.sleep(2)  # Extra wait time (if necessary)
    
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    driver.quit()
    shutil.rmtree(user_data_dir)  # Remove the temporary user data directory
    
    leaderboard = []
    # Parse the leaderboard rows using BeautifulSoup.
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
