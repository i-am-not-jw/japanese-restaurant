import os, requests, json

def load_env():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.normpath(os.path.join(script_dir, "..", ".env"))
    if os.path.exists(env_path):
        try:
            with open(env_path, "r") as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        k, v = line.strip().split("=", 1)
                        os.environ.setdefault(k, v)
        except PermissionError:
            pass

load_env()
NOTION_TOKEN  = os.getenv("NOTION_TOKEN") or "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"
DATABASE_ID   = os.getenv("NOTION_JAPAN_RESTAURANT_DB_ID") or "307deb1120c1800f914fcc99c25dc0f8"

if not NOTION_TOKEN or not DATABASE_ID:
    print("Error: Missing credentials")
    exit(1)

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

def get_all_pages():
    results = []
    has_more = True
    cursor = None
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    
    while has_more:
        payload = {"page_size": 100}
        if cursor:
            payload["start_cursor"] = cursor
            
        resp = requests.post(url, headers=HEADERS, json=payload)
        if resp.status_code != 200:
            print(f"Error querying db: {resp.text}")
            break
            
        data = resp.json()
        results.extend(data.get("results", []))
        has_more = data.get("has_more", False)
        cursor = data.get("next_cursor")
        
    return results

def archive_page(page_id):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    resp = requests.patch(url, headers=HEADERS, json={"archived": True})
    if resp.status_code == 200:
        print(f"Archived {page_id}")
    else:
        print(f"Failed to archive {page_id}: {resp.text}")

def main():
    print(f"Target Database: {DATABASE_ID}")
    pages = get_all_pages()
    print(f"Found {len(pages)} pages. Deleting...")
    
    for p in pages:
        archive_page(p["id"])
    
    print("Done.")

if __name__ == "__main__":
    main()
