"""
finalize_sync.py
Moves all items from NOTION_STAGING_DB_ID to NOTION_JAPAN_RESTAURANT_DB_ID,
then archives the staging items and triggers map_data_bridge.py.
"""
import os, sys, requests, time
from dotenv import load_dotenv

# Load env from current directory
load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
STAGING_DB_ID = os.getenv("NOTION_STAGING_DB_ID")
MAIN_DB_ID = os.getenv("NOTION_JAPAN_RESTAURANT_DB_ID")

if not STAGING_DB_ID or not MAIN_DB_ID:
    print("❌ Error: Missing NOTION_STAGING_DB_ID or NOTION_JAPAN_RESTAURANT_DB_ID in .env")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

def get_all_staging_items():
    url = f"https://api.notion.com/v1/databases/{STAGING_DB_ID}/query"
    items = []
    has_more = True
    start_cursor = None
    
    while has_more:
        payload = {"page_size": 100}
        if start_cursor:
            payload["start_cursor"] = start_cursor
        
        resp = requests.post(url, headers=HEADERS, json=payload)
        if resp.status_code != 200:
            print(f"❌ Error querying Staging DB: {resp.text}")
            break
            
        data = resp.json()
        items.extend(data.get("results", []))
        has_more = data.get("has_more")
        start_cursor = data.get("next_cursor")
        
    return items

def move_to_main(item):
    """
    Copies properties from a staging item to the main database.
    Since we want to preserve IDs/URLs, we assume 'tabelog URL' is the unique key.
    """
    props = item["properties"]
    
    # Remove properties that cannot be set during creation or are specific to the old page
    # Actually, we can just extract the ones our bridge expects.
    
    # We use Upsert logic: check if exists in Main DB first
    tabelog_url = ""
    target_prop = props.get("tabelog URL", {})
    if target_prop.get("url"):
        tabelog_url = target_prop["url"]
    
    # Check existing in Main
    existing_page_id = None
    if tabelog_url:
        query_url = f"https://api.notion.com/v1/databases/{MAIN_DB_ID}/query"
        filter_payload = {
            "filter": {
                "property": "tabelog URL",
                "url": {"equals": tabelog_url}
            }
        }
        q_resp = requests.post(query_url, headers=HEADERS, json=filter_payload)
        if q_resp.status_code == 200:
            q_results = q_resp.json().get("results", [])
            if q_results:
                existing_page_id = q_results[0]["id"]

    # Filter out read-only properties
    clean_props = {}
    for key, val in props.items():
        # Skip system properties
        if key in ["Created time", "Last edited time"]:
            continue
        # Only keep data properties
        clean_props[key] = val

    if existing_page_id:
        # Patch
        resp = requests.patch(f"https://api.notion.com/v1/pages/{existing_page_id}", headers=HEADERS, json={"properties": clean_props})
        print(f"  🔄 Updated in Main: {existing_page_id}")
    else:
        # Create
        payload = {
            "parent": {"database_id": MAIN_DB_ID},
            "properties": clean_props
        }
        resp = requests.post("https://api.notion.com/v1/pages", headers=HEADERS, json=payload)
        print(f"  ✅ Created in Main")

def delete_staging_item(item_id):
    url = f"https://api.notion.com/v1/pages/{item_id}"
    requests.patch(url, headers=HEADERS, json={"archived": True})

def main():
    print("🚀 Finalizing Sync: Moving data from Staging to Main...")
    items = get_all_staging_items()
    
    if not items:
        print("ℹ️ No items found in Staging Database.")
        return

    # Filter out the 'Notification' page if it exists (usually has '📢' in title)
    data_items = []
    for item in items:
        title_prop = item["properties"].get(" 제목", {}).get("title", [])
        if title_prop:
            title_text = title_prop[0].get("plain_text", "")
            if "📢" in title_text:
                print(f"  🗑️ Removing notification page: {title_text}")
                delete_staging_item(item["id"])
                continue
        data_items.append(item)

    print(f"📦 Found {len(data_items)} data items to sync.")
    
    for i, item in enumerate(data_items):
        try:
            move_to_main(item)
            delete_staging_item(item["id"])
            print(f"  [{i+1}/{len(data_items)}] Processed and cleared from Staging.")
            time.sleep(0.3) # Avoid rate limits
        except Exception as e:
            print(f"  ❌ Failed to process item {item.get('id')}: {e}")

    print("\n🌍 Triggering Web Map update...")
    os.system("python3 execution/map_data_bridge.py")
    
    print("\n✨ All operations complete. Staging DB is clean.")

if __name__ == "__main__":
    main()
