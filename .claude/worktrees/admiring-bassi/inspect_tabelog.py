import requests
from bs4 import BeautifulSoup
import re

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}
base_url = "https://tabelog.com/okinawa/A4701/A470101/47001979/"
print(f"Fetching detail page: {base_url}")
try:
    resp = requests.get(base_url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")
    
    # Check if we got a valid page
    if "お探しのページ" in soup.title.text:
        print("Detail page returned 404/Not Found title.")
        print(resp.text[:500])
        exit()

    # Find the review list link
    review_link = soup.find("a", href=re.compile(r"dtlrvwlst"))
    target_url = ""
    if review_link:
        target_url = review_link["href"]
        if not target_url.startswith("http"):
            target_url = "https://tabelog.com" + target_url
        print(f"Found review link: {target_url}")
        
        # Now fetch that
        resp = requests.get(target_url, headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
    else:
        print("No review link found on detail page.")
        # Try constructing it
        target_url = base_url.rstrip("/") + "/dtlrvwlst/"
        print(f"Trying constructed URL: {target_url}")
        resp = requests.get(target_url, headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")

    # Find all elements containing "202" (year)
    print(f"Searching for date in {target_url}")
    found = False
    for elem in soup.find_all(string=re.compile(r"202\d")):
        parent = elem.parent
        print(f"Found: '{elem.strip()}'")
        print(f"  Parent Tag: {parent.name}")
        print(f"  Parent Classes: {parent.get('class')}")
        found = True

    if not found:
        print("No date string found.")

except Exception as e:
    print(f"Error: {e}")
