
import os
import json
import requests
import re
import time
import sys
import csv

# Add parent dir to path to import from execution
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from execution.notion_publisher import NOTION_TOKEN, DATABASE_ID

NOTION_API_URL = "https://api.notion.com/v1"
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def get_all_restaurants():
    """Fetches all restaurant entries from the Notion database."""
    restaurants = []
    has_more = True
    start_cursor = None

    print(f"📡 Querying Notion database: {DATABASE_ID}")
    
    while has_more:
        payload = {"page_size": 100}
        if start_cursor:
            payload["start_cursor"] = start_cursor

        response = requests.post(f"{NOTION_API_URL}/databases/{DATABASE_ID}/query", json=payload, headers=HEADERS)
        if response.status_code != 200:
            print(f"❌ Failed to query Notion: {response.status_code} {response.text}")
            break

        data = response.json()
        results = data.get("results", [])
        restaurants.extend(results)
        
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")
        print(f"   Collected {len(restaurants)} items...")

    return restaurants

def extract_place_id(url):
    """Attempt to extract Place ID from a Google Maps URL."""
    if not url:
        return None
    # Look for /place/ChI.../ or ?q=place_id:ChI...
    match_place = re.search(r'/place/([^/]+)/', url)
    if match_place:
        return match_place.group(1)
    
    match_qid = re.search(r'place_id:([^&]+)', url)
    if match_qid:
        return match_qid.group(1)
        
    return None

def extract_coords_from_url(url):
    """Attempt to extract lat/lng from a Google Maps URL."""
    if not url:
        return None, None
        
    # Pattern for !3d35.6585805!4d139.7454329 (typical in CID/Share URLs)
    match_3d = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', url)
    if match_3d:
        return float(match_3d.group(1)), float(match_3d.group(2))
        
    # Pattern for @35.6585805,139.7454329
    match_at = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
    if match_at:
        return float(match_at.group(1)), float(match_at.group(2))

    return None, None

def geocode_address(address):
    """Fallback: Geocode address using Nominatim (free)."""
    if not address:
        return None, None
    
    # Try to make it more specific for Japan if not already
    search_query = address
    if "Japan" not in address and "일본" not in address:
        search_query += ", Japan"
        
    try:
        # Nominatim requires a User-Agent
        headers = {"User-Agent": "JapaneseRestaurantMapTracker/1.0"}
        url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(search_query)}&format=json&limit=1"
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200 and resp.json():
            first = resp.json()[0]
            return float(first["lat"]), float(first["lon"])
    except Exception as e:
        print(f"   ⚠️ Geocoding error for {address}: {e}")
    
    return None, None

def simplify_restaurant(page):
    """Extracts relevant fields and simplifies for the web map."""
    props = page.get("properties", {})
    
    def get_plain_text(prop_name):
        prop = props.get(prop_name)
        if not prop: return ""
        rich_text = prop.get("rich_text", [])
        return "".join([t.get("plain_text", "") for t in rich_text]) if rich_text else ""

    def get_title():
        prop = props.get(" 제목")
        if not prop: return "Unknown"
        title_list = prop.get("title", [])
        return "".join([t.get("plain_text", "") for t in title_list]) if title_list else "Unknown"

    def get_number(prop_name):
        prop = props.get(prop_name)
        return prop.get("number") if prop else None

    def get_url(prop_name):
        prop = props.get(prop_name)
        return prop.get("url") if prop else None

    def get_multi_select(prop_name):
        prop = props.get(prop_name)
        if prop and prop.get("multi_select"):
            return [o.get("name") for o in prop["multi_select"]]
        return []

    def get_select(prop_name):
        prop = props.get(prop_name)
        if prop and prop.get("select"):
            return prop["select"].get("name")
        return None

    def get_thumbnail():
        files = props.get("썸네일", {}).get("files", [])
        if files:
            # Handle both internal Notion files and external URLs
            f = files[0]
            return f.get("external", {}).get("url") or f.get("file", {}).get("url")
        return None

    name = get_title()
    address = get_plain_text("장소")
    google_url = get_url("google map URL")
    
    place_id = extract_place_id(google_url)
    tags = get_multi_select("태그")
    
    # Simple icon mapping based on tags
    icon_type = "default"
    tags_lower = [t.lower() for t in tags]
    if any(k in tags_lower for k in ["라멘", "ramen", "면"]):
        icon_type = "ramen"
    elif any(k in tags_lower for k in ["스시", "sushi", "초밥", "회"]):
        icon_type = "sushi"
    elif any(k in tags_lower for k in ["카페", "cafe", "디저트", "커피"]):
        icon_type = "cafe"
    elif any(k in tags_lower for k in ["이자카야", "izakaya", "술집", "맥주", "야키토리"]):
        icon_type = "izakaya"

    # Get coordinates
    lat, lng = extract_coords_from_url(google_url)
    if lat is None:
        print(f"   🔍 Geocoding via Nominatim for: {name}")
    return {
        "id": page.get("id"),
        "place_id": place_id,
        "icon_type": icon_type,
        "name": name,
        "address": address,
        "lat": lat,
        "lng": lng,
        "tabelog_rating": get_number("tabelog 평점"),
        "google_rating": get_number("google 평점"),
        "tags": get_multi_select("태그"),
        "summary": get_plain_text("요약"),
        "station": get_plain_text("교통"),
        "region": get_select("지역"),
        "thumbnail": get_thumbnail(),
        "google_url": google_url,
        "tabelog_url": get_url("tabelog URL")
    }

def save_csv(restaurants, output_path):
    """Saves a list of restaurants to a CSV file optimized for Google My Maps."""
    if not restaurants:
        return
    
    keys = ["Name", "Address", "Latitude", "Longitude", "Rating_Tabelog", "Rating_Google", "Tags", "Summary", "Station", "Region", "Thumbnail", "Google_URL", "Tabelog_URL"]
    
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for r in restaurants:
            writer.writerow({
                "Name": r["name"],
                "Address": r["address"],
                "Latitude": r["lat"],
                "Longitude": r["lng"],
                "Rating_Tabelog": r["tabelog_rating"],
                "Rating_Google": r["google_rating"],
                "Tags": ", ".join(r["tags"]),
                "Summary": r["summary"],
                "Station": r["station"],
                "Region": r["region"],
                "Thumbnail": r["thumbnail"],
                "Google_URL": r["google_url"],
                "Tabelog_URL": r["tabelog_url"]
            })

def main():
    print("🚀 Starting Map Data Bridge (Notion -> JSON & CSV)")
    
    raw_restaurants = get_all_restaurants()
    if not raw_restaurants:
        print("📭 No restaurants found in Notion.")
        return

    processed = []
    print(f"⚙️ Processing {len(raw_restaurants)} restaurants...")
    
    for i, page in enumerate(raw_restaurants):
        res = simplify_restaurant(page)
        if res["lat"] and res["lng"]:
            processed.append(res)
        else:
            print(f"   ⚠️ Skipping {res['name']}: Could not find coordinates.")
            
    # Define output directories
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    web_data_dir = os.path.join(base_dir, "web_map", "data")
    export_dir = os.path.join(base_dir, "exports")
    
    os.makedirs(web_data_dir, exist_ok=True)
    os.makedirs(export_dir, exist_ok=True)
    
    # 1. Save Web JSON
    json_path = os.path.join(web_data_dir, "restaurants.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(processed, f, ensure_ascii=False, indent=2)
    print(f"✅ Web JSON saved to {json_path}")
    
    # 2. Save Regional CSVs (for Monetization)
    regions = {}
    for r in processed:
        reg = r["region"] or "Other"
        # Clean region name for filename
        reg_clean = re.sub(r'[^\w\s-]', '', reg).strip().replace(' ', '_')
        if reg_clean not in regions:
            regions[reg_clean] = []
        regions[reg_clean].append(r)
        
    for reg_name, items in regions.items():
        csv_path = os.path.join(export_dir, f"restaurants_{reg_name}.csv")
        save_csv(items, csv_path)
        print(f"📦 Exported {len(items)} items to {csv_path} ({reg_name})")

    # 3. Save All-in-one CSV
    all_csv_path = os.path.join(export_dir, "restaurants_all.csv")
    save_csv(processed, all_csv_path)
    print(f"🌟 Full CSV export saved to {all_csv_path}")

if __name__ == "__main__":
    main()
