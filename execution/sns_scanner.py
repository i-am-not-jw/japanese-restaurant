"""
sns_scanner.py
Restaurant-centric: for each restaurant already found on Tabelog,
searches for SNS posts mentioning that restaurant and collects:
  - Platform name
  - Post URL
  - Snippet text
  - Post date
"""
import os
import re
import json
import time
import random
import requests
from datetime import datetime
from urllib.parse import quote

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja-JP,ja;q=0.9",
}

PLATFORMS = {
    "인스타그램":  "instagram.com",
    "틱톡":        "tiktok.com",
    "유튜브":      "youtube.com",
    "X":           "x.com",
    "스레드":      "threads.net",
}


def parse_date(text):
    """Extract YYYY-MM-DD from a snippet or date hint."""
    if re.search(r"\d+[時日週ヶ月年]前", text):
        return datetime.now().strftime("%Y-%m-%d")
    m = re.search(r"(20\d{2})[年/-](\d{1,2})[月/-](\d{1,2})", text)
    if m:
        return f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}"
    return ""


def google_site_search(restaurant_name, domain, time_range="m"):
    """Search `site:domain restaurant_name` on Google, return top results."""
    query = f'site:{domain} "{restaurant_name}"'
    url = f"https://www.google.com/search?q={quote(query)}&tbs=qdr:{time_range}&hl=ja&num=5"
    results = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        text = resp.text

        titles = re.findall(r"<h3[^>]*>(.*?)</h3>", text, re.S)
        snippets = re.findall(r'class="[^"]*VwiC3b[^"]*"[^>]*>(.*?)</span>', text, re.S)
        hrefs = re.findall(r'<a href="(https?://[^"&]+)"', text)
        dates_raw = re.findall(r'<span[^>]*class="[^"]*MUxGbd[^"]*"[^>]*>(.*?)</span>', text, re.S)

        clean = lambda s: re.sub(r"<[^>]+>", "", s).strip()

        for i, title in enumerate(titles[:5]):
            t = clean(title)
            s = clean(snippets[i]) if i < len(snippets) else ""
            d = clean(dates_raw[i]) if i < len(dates_raw) else ""
            link = hrefs[i] if i < len(hrefs) else ""

            if not t or not link:
                continue

            post_date = parse_date(d + " " + s)
            results.append({
                "snippet": s[:300],
                "url": link,
                "post_date": post_date,
            })
    except Exception as e:
        print(f"    Search error ({domain}): {e}")
    return results


def find_sns_posts(restaurant_name):
    """For a given restaurant, search all platforms and return structured posts."""
    all_posts = []  # [{platform, url, snippet, post_date}]
    for platform_label, domain in PLATFORMS.items():
        results = google_site_search(restaurant_name, domain, time_range="m")
        for r in results:
            all_posts.append({
                "platform": platform_label,
                "url": r["url"],
                "snippet": r["snippet"],
                "post_date": r["post_date"],
            })
            print(f"      [{platform_label}] {r['url'][:60]}")
        time.sleep(random.uniform(0.5, 1.0))
    return all_posts


def main():
    input_path = "/tmp/antigravity_tmp/tabelog_report.json"
    if not os.path.exists(input_path):
        print("tabelog_report.json not found. Run tabelog_lookup.py first.")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        restaurants = json.load(f)

    for res in restaurants:
        name = res["name"]
        print(f"\nSearching SNS for: {name}")
        posts = find_sns_posts(name)
        res["sns_posts"] = posts

        # Use earliest confirmed post_date
        dates = [p["post_date"] for p in posts if p.get("post_date") and len(p["post_date"]) == 10]
        if dates:
            res["post_date"] = sorted(dates)[0]

        print(f"  → {len(posts)} SNS posts found, earliest: {res.get('post_date', 'N/A')}")

    with open(input_path, "w", encoding="utf-8") as f:
        json.dump(restaurants, f, ensure_ascii=False, indent=2)

    print(f"\nUpdated {input_path} with SNS data.")


if __name__ == "__main__":
    main()
