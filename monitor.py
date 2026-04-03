import feedparser
import requests
import urllib.parse
import os

# --- 1. CONFIGURATION (Edit Keywords & Filters Here) ---
# The keywords Google uses to find articles initially
SEARCH_QUERY = 'intitle:("phase 3" OR "FDA") site:stocktitan.net/news when:24h'

# The "Double-Check" list: The title MUST contain one of these to pass
MUST_CONTAIN = ["phase 3", "fda"]

# The "Bouncer" list: If these are in the title, skip it immediately
BLOCKLIST = ["pizza", "restaurant", "burger", "gaming", "crypto", "bitcoin", "litigation", "pineapple"]

# Your ntfy.sh topic URL
NTFY_URL = "https://ntfy.sh/stock_titan_alerts_jlc_888" 

# --- 2. URL CONSTRUCTION ---
encoded_query = urllib.parse.quote(SEARCH_QUERY)
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

print(f"Checking feed for: {SEARCH_QUERY}")

for entry in feed.entries:
    title_lower = entry.title.lower()
    
    # FILTER A: The "Double-Check" (Must have biotech keywords in the actual title)
    if not any(key in title_lower for key in MUST_CONTAIN):
        print(f"Skipping (Sidebar match only): {entry.title}")
        continue

    # FILTER B: The Blocklist (Removes known junk)
    if any(word in title_lower for word in BLOCKLIST):
        print(f"Skipping (Blocklisted): {entry.title}")
        continue
    
    # FILTER C: The ID Check (Don't alert twice)
    if entry.id not in seen_ids:
        print(f"Verified New Article: {entry.title}")
        
        # Send to ntfy.sh
        try:
            requests.post(NTFY_URL,
                data=entry.title.encode('utf-8'),
                headers={
                    "Title": entry.title,
                    "Click": entry.link,
                    "Priority": "high",
                    "Tags": "dna,pill"
                }
            )
            new_ids.append(entry.id)
        except Exception as e:
            print(f"Error sending notification: {e}")

    # Safety limit: max 10 alerts per 15-minute run
    if len(new_ids) >= 10:
        break

# --- 5. SAVE NEW SEEN ARTICLES ---
if new_ids:
    with open(DB_FILE, 'a') as f:
        for article_id in new_ids:
            f.write(article_id + "\n")
    print(f"Saved {len(new_ids)} new articles to memory.")
else:
    print("No new verified matches found.")
    
