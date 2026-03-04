
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

    def get_time(prop_name):
        prop = props.get(prop_name)
        if not prop: return None
        # created_time and last_edited_time are direct strings in their respective fields
        t = prop.get("created_time") or prop.get("last_edited_time")
        if t:
            # Format: 2024-03-02T07:36:00.000Z -> 2024-03-02
            return t.split("T")[0]
        return None

    name = get_title()
    address = get_plain_text("장소")
    google_url = get_url("google map URL")
    
    place_id = extract_place_id(google_url)
    
    def clean_tags(tag_list):
        """Unifies redundant tags like '발/다이닝바', '바(Bar)', etc."""
        # Tag Mapping/Unification and Region Translation
        mapping = {
            "발/다이닝바": "다이닝 바",
            "다이닝바": "다이닝 바",
            "바(Bar)": "바(Bar)",
            "발": "다이닝 바",
            "중앙구": "주오구",
            "북구": "기타구",
            "서구": "니시구",
            "남구": "미나미구",
            "동구": "히가시구",
            "중구": "나카구",
            "신주쿠": "신주쿠구"
        }
        
        if not tag_list: return []
        
        cleaned = []
        for t in tag_list:
            # Check for direct mapping or substrings
            new_tag = mapping.get(t, t)
            cleaned.append(new_tag)
            
        # Deduplicate while preserving order (using dict as ordered set)
        return list(dict.fromkeys(cleaned))

    # Icon mapping
    tags = clean_tags(get_multi_select("태그"))
    icon_type = "restaurant"
    tags_lower = [t.lower() for t in tags]
    if any(k in tags_lower for k in ["이자카야", "izakaya", "술집", "맥주", "야키토리", "다이닝 바", "바(bar)"]):
        icon_type = "izakaya"
    elif any(k in tags_lower for k in ["카페", "cafe", "디저트", "커피"]):
        icon_type = "cafe"

    # Get coordinates
    lat, lng = extract_coords_from_url(google_url)
    if lat is None:
        print(f"   🔍 Geocoding via Nominatim for: {name}")
    region_map = {
        "중앙구": "주오구",
        "북구": "기타구",
        "서구": "니시구",
        "남구": "미나미구",
        "동구": "히가시구",
        "중구": "나카구",
        "신주쿠": "신주쿠구"
    }
    raw_region = get_select("지역")
    processed_region = raw_region
    if raw_region:
        for k, v in region_map.items():
            if k in raw_region:
                processed_region = raw_region.replace(k, v)
                break

    return {
        "id": page.get("id"),
        "place_id": place_id,
        "icon_type": icon_type,
        "name": name,
        "address": address,
        "lat": lat,
        "lng": lng,
        "tabelog_rating": get_number("tabelog 평점"),
        "google_rating": get_number("google 점수") if "google 점수" in props else get_number("google 평점"),
        "tags": tags,
        "summary": get_plain_text("요약").replace("\n", " ").replace("\r", ""), # CRITICAL: No unescaped newlines
        "station": get_plain_text("교통"),
        "region": processed_region,
        "thumbnail": get_thumbnail(),
        "google_url": google_url,
        "tabelog_url": get_url("tabelog URL"),
        "created_at": get_time("생성 일시"),
        "updated_at": get_time("최종 편집 일시")
    }

def save_csv(restaurants, output_path):
    """Saves a list of restaurants to a CSV file optimized for Google My Maps."""
    if not restaurants: return
    keys = ["Name", "Address", "Latitude", "Longitude", "Rating_Tabelog", "Rating_Google", "Tags", "Summary", "Station", "Region", "Thumbnail", "Google_URL", "Tabelog_URL", "Created_At", "Updated_At"]
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for r in restaurants:
            writer.writerow({
                "Name": r["name"], "Address": r["address"], "Latitude": r["lat"], "Longitude": r["lng"],
                "Rating_Tabelog": r["tabelog_rating"], "Rating_Google": r["google_rating"],
                "Tags": ", ".join(r["tags"]), "Summary": r["summary"], "Station": r["station"],
                "Region": r["region"], "Thumbnail": r["thumbnail"],
                "Google_URL": r["google_url"], "Tabelog_URL": r["tabelog_url"],
                "Created_At": r["created_at"], "Updated_At": r["updated_at"]
            })

def inject_to_html(restaurants, html_path):
    """Injects restaurant data directly into the index.html file to bypass CORS."""
    if not os.path.exists(html_path):
        print(f"⚠️  HTML file not found: {html_path}")
        return

    print(f"💉 Injecting {len(restaurants)} items into {os.path.basename(html_path)}...")
    
    # Use json.dumps with ensure_ascii=False and no extra formatting for safer injection
    json_data = json.dumps(restaurants, ensure_ascii=False)
    
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Regex to find the window.RESTAURANT_DATA assignment block
    # Matches window.RESTAURANT_DATA = [ ... ];
    pattern = r'window\.RESTAURANT_DATA\s*=\s*\[.*?\];'
    
    # We need to be careful with the replacement string formatting
    replacement = f"window.RESTAURANT_DATA = {json_data};"
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"✅ Injection complete.")

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

    # 4. Inject into index.html
    html_path = os.path.join(base_dir, "web_map", "index.html")
    inject_to_html(processed, html_path)
    
    print(f"🌟 Full CSV export saved to {all_csv_path}")

if __name__ == "__main__":
    main()
