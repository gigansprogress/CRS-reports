import os
import requests
from atproto import Client, client_utils

# --- CONFIGURATION ---
# These pull from your GitHub Secrets for safety
BSKY_HANDLE = os.environ.get('BSKY_HANDLE')
BSKY_PASSWORD = os.environ.get('BSKY_PASSWORD')
MEMORY_FILE = "posted_links.txt"

def get_latest_crs_reports():
    """Fetches the 5 most recent reports from EveryCRSReport JSON API."""
    url = "https://www.everycrsreport.com/reports.json"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        reports = []
        for report in data[:5]:
            reports.append({
                "title": report['title'],
                "link": f"https://www.everycrsreport.com/reports/{report['id']}.html",
                "summary": report.get('summary', 'New CRS Report Available')
            })
        return reports
    except Exception as e:
        print(f"Error fetching reports: {e}")
        return []

def filter_new_reports(reports):
    """Checks the memory file to see which reports are actually new."""
    if not os.path.exists(MEMORY_FILE):
        return reports

    with open(MEMORY_FILE, "r") as f:
        posted_links = f.read().splitlines()
    
    return [r for r in reports if r['link'] not in posted_links]

def post_to_bluesky(report):
    """Formats and sends the post to Bluesky using facets for links."""
    client = Client()
    client.login(BSKY_HANDLE, BSKY_PASSWORD)
    
    # Bluesky has a 300 char limit. We trim title/summary to fit.
    title = (report['title'][:100] + '...') if len(report['title']) > 100 else report['title']
    summary = (report['summary'][:120] + '...') if len(report['summary']) > 120 else report['summary']
    
    text_builder = client_utils.TextBuilder()
    text_builder.text(f"🏛️ New CRS Report:\n{title}\n\n")
    text_builder.text(f"{summary}\n\n")
    text_builder.link("View Full Report", report['link'])
    
    client.send_post(text_builder)
    print(f"Successfully posted: {title}")

def mark_as_posted(link):
    """Saves the link to the memory file."""
    with open(MEMORY_FILE, "a") as f:
        f.write(link + "\n")

if __name__ == "__main__":
    print("Checking for new CRS reports...")
    all_latest = get_latest_crs_reports()
    new_reports = filter_new_reports(all_latest)

    if not new_reports:
        print("No new reports found.")
    else:
        for report in new_reports:
            post_to_bluesky(report)
            mark_as_posted(report['link'])
