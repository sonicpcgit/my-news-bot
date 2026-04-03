import feedparser
import requests
import urllib.parse
import os

# --- 1. CONFIGURATION (Edit Keywords Here) ---
# Type your keywords naturally. No need for %20 or %22 here!
KEYWORDS = 'intitle:("phase 3" OR "FDA") site:stocktitan.net/news when:24h'

# Words to ignore (prevents Pizza/Crypto/Gaming false positives)
BLOCKLIST = ["pizza", "restaurant", "burger", "gaming", "crypto", "bitcoin", "litigation"]

# Your ntfy.sh topic URL
NTFY_URL = "https://ntfy.sh/stock_titan_alerts_jlc_888" 

# --- 2. URL CONSTRUCTION ---
# This encodes the KEYWORDS string into a safe URL format
encoded_query = urllib.parse.quote(KEYWORDS)
RSS_URL = f"https://news.google.com/rss/search?q={encoded_query}"

# --- 3. LOAD PREVIOUSLY SEEN ARTICLES ---
DB_FILE = "seen_articles.txt"
if not os.path.exists(DB_FILE):
    open(DB_FILE, 'w').close()

with open(DB_FILE, 'r') as f:
    seen_ids = set(line.strip() for line in f)

# --- 4. FETCH AND FILTER THE FEED ---
feed = feedparser.parse(RSS_URL)
new_ids = []

print(f"Checking feed: {RSS_URL}")

for entry in feed.entries:
    # Get the title in lowercase for easier checking
    title_lower = entry.title.lower()
    
    # Check the BLOCKLIST
    if any(word in title_lower for word in BLOCKLIST):
        print(f"Skipping (Blocklisted): {entry.title}")
        continue
    
    # Check if we have seen this ID before
    if entry.id not in seen_ids:
        print(f"New Article Found: {entry.title}")
        
        # Send to ntfy.sh
        try:
            requests.post(NTFY_URL,
                data=entry.title.encode('utf-8'),
                headers={
                    "Title": "Biotech Catalyst Alert",
                    "Click": entry.link,
                    "Priority": "high"
                }
            )
            new_ids.append(entry.id)
        except Exception as e:
            print(f"Error sending notification: {e}")

    # Safety limit: don't send more than 10 alerts in one run
    if len(new_ids) >= 10:
        break

# --- 5. SAVE NEW SEEN ARTICLES ---
if new_ids:
    with open(DB_FILE, 'a') as f:
        for article_id in new_ids:
            f.write(article_id + "\n")
    print(f"Saved {len(new_ids)} new articles to memory.")
else:
    print("No new matches found.")
    
