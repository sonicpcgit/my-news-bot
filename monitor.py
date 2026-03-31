import feedparser
import requests
import os

# --- CONFIGURATION ---
# This looks for keywords ONLY on stocktitan.net
RSS_URL = 'https://news.google.com/rss/search?q=allintext:("phase 3" OR "partnership" OR "FDA") site:stocktitan.net'
# Replace the end of this URL with your unique topic name from the ntfy app
NTFY_URL = "https://ntfy.sh/stock_titan_alerts_777" 
DB_FILE = "seen_articles.txt"

def send_alert(title, link):
    """Sends a high-priority push notification"""
    try:
        requests.post(NTFY_URL, 
                      data=link.encode('utf-8'),
                      headers={
                          "Title": title.encode('utf-8'),
                          "Click": link,
                          "Priority": "high",
                          "Tags": "chart_with_upwards_trend,pill"
                      })
        print(f"Alert Sent: {title}")
    except Exception as e:
        print(f"Error: {e}")

def run_monitor():
    # Create database file if it doesn't exist
    if not os.path.exists(DB_FILE):
        open(DB_FILE, "w").close()
    
    with open(DB_FILE, "r") as f:
        seen_ids = set(f.read().splitlines())

    # Fetch and parse the Google News RSS feed
    feed = feedparser.parse(RSS_URL)
    new_ids = []

    for entry in feed.entries:
        # Check if we have notified for this article before
        if entry.id not in seen_ids:
            send_alert(entry.title, entry.link)
            new_ids.append(entry.id)
            # Limit to 5 alerts per run to prevent spam
            if len(new_ids) >= 5: break 

    # Save the new IDs so we don't alert twice
    with open(DB_FILE, "a") as f:
        for eid in new_ids:
            f.write(eid + "\n")

if __name__ == "__main__":
    run_monitor()

