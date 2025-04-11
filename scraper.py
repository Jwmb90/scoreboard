import time
import requests
from bs4 import BeautifulSoup

# Caching variables
_cached_mapping = None
_last_scrape = 0
CACHE_DURATION = 600  # 10 minutes

def get_leaderboard_data():
    """
    Uses requests and BeautifulSoup to fetch and parse the ESPN Golf Leaderboard.
    Returns a list of dictionaries with keys 'player' and 'score'.
    If an error occurs, returns an empty list.
    """
    url = "https://www.espn.com/golf/leaderboard"
    
    # Set headers to mimic a regular browser
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/135.0.0.0 Safari/537.36"
        )
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print("Error fetching data with requests:", e)
        return []
    
    html = response.text
    soup = BeautifulSoup(html, "html.parser")
    
    leaderboard = []
    # Adjust these selectors based on ESPN's current HTML structure.
    player_rows = soup.select("tbody.Table__TBODY tr.PlayerRow__Overview")
    for row in player_rows:
        name_anchor = row.select_one("a.AnchorLink.leaderboard_player_name")
        if name_anchor:
            player_name = name_anchor.get_text(strip=True)
            # We assume the score is in the next <td> following the player's <td>
            name_td = name_anchor.find_parent("td")
            score_td = name_td.find_next_sibling("td")
            score = score_td.get_text(strip=True) if score_td else "N/A"
            leaderboard.append({"player": player_name, "score": score})
    
    return leaderboard

def get_leaderboard_mapping_cached():
    """
    Returns a dictionary mapping player names to scores using a cache.
    Refreshes the cache if it is older than CACHE_DURATION.
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
