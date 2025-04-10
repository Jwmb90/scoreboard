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
    If page elements do not load in time or an error occurs, returns an empty list.
    """
    print("Starting Chrome driver...")
    chrome_options = Options()
    # Uncomment the next line to run headless (comment it out for debugging)
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--log-level=3")
    driver = webdriver.Chrome(options=chrome_options)
    
    print("Setting page load timeout...")
    driver.set_page_load_timeout(120)
    url = "https://www.espn.com/golf/leaderboard"
    
    try:
        print("Opening URL:", url)
        driver.get(url)
    except TimeoutException as te:
        print("Page load timed out:", te)
        driver.quit()
        return []
    except Exception as e:
        print("Error during driver.get:", e)
        driver.quit()
        return []
    
    try:
        print("Waiting for table body with CSS selector 'tbody.Table__TBODY'...")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "tbody.Table__TBODY"))
        )
    except TimeoutException as te:
        print("Timeout waiting for table body:", te)
        driver.quit()
        return []
    except Exception as e:
        print("Error during waiting for table body:", e)
        driver.quit()
        return []
    
    print("Extra sleep to allow page elements to settle...")
    time.sleep(2)
    
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    print("Page source obtained. Quitting driver...")
    driver.quit()

    leaderboard = []
    print("Searching for player rows using selector 'tbody.Table__TBODY tr.PlayerRow__Overview'...")
    player_rows = soup.select("tbody.Table__TBODY tr.PlayerRow__Overview")
    for row in player_rows:
        name_anchor = row.select_one("a.AnchorLink.leaderboard_player_name")
        if name_anchor:
            player_name = name_anchor.get_text(strip=True)
            name_td = name_anchor.find_parent("td")
            score_td = name_td.find_next_sibling("td")
            score = score_td.get_text(strip=True) if score_td else "N/A"
            leaderboard.append({"player": player_name, "score": score})
    print("Scraping complete. Found", len(leaderboard), "players.")
    return leaderboard

# Simple caching mechanism
_cached_mapping = None
_last_scrape = 0
CACHE_DURATION = 600  # 10 minutes

def get_leaderboard_mapping_cached():
    global _cached_mapping, _last_scrape
    current_time = time.time()
    if _cached_mapping is None or (current_time - _last_scrape) > CACHE_DURATION:
        print("Cache expired or empty; scraping new data...")
        data = get_leaderboard_data()
        _cached_mapping = {entry["player"]: entry["score"] for entry in data}
        _last_scrape = current_time
    else:
        print("Using cached leaderboard data.")
    return _cached_mapping

def force_refresh_leaderboard():
    """
    Forces a new scrape of the leaderboard data, updates the cache,
    and returns the fresh data.
    """
    global _cached_mapping, _last_scrape
    print("Force refreshing leaderboard data...")
    data = get_leaderboard_data()  # Always perform a fresh scrape
    _cached_mapping = {entry["player"]: entry["score"] for entry in data}
    _last_scrape = time.time()
    return data
