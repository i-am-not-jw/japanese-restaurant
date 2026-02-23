"""
export_to_csv.py
Reads /tmp/antigravity_tmp/tabelog_report.json, processes the AI summarization
and translation, and appends the final clean data to .tmp/staged_restaurants.csv 
for human review.
"""
import sys, os, json, csv
from datetime import datetime

# Add parent directory to path to import notion_publisher helpers
sys.path.append(os.path.normpath(os.path.join(os.path.dirname(__file__), "..")))
from execution.notion_publisher import gemini_summarize, translate_hours, build_tags, safe_number

CSV_PATH = "/tmp/antigravity_tmp/staged_restaurants.csv"
JSON_PATH = "/tmp/antigravity_tmp/tabelog_report.json"

HEADERS = [
    "Target_City_Region",
    "Restaurant_Name",
    "Tabelog_Rating",
    "Google_Rating",
    "Generated_Tags",
    "AI_Review_Summary",
    "AI_Opening_Hours",
    "Station_Info",
    "Tabelog_Review_Count",
    "Google_Review_Count",
    "Tabelog_Latest_Review_Date",
    "Address",
    "Tabelog_URL",
    "Google_Maps_URL",
    "Thumbnail_URL"
]

def main():
    if not os.path.exists(JSON_PATH):
        print(f"  [CSV Export] No JSON data found at {JSON_PATH}. Skipping.")
        sys.exit(0)

    # Make sure .tmp/ exists
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)

    file_exists = os.path.exists(CSV_PATH)
    
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not data:
        print("  [CSV Export] JSON is empty. Skipping.")
        sys.exit(0)

    print(f"  📝 Staging {len(data)} restaurants to CSV...")

    with open(CSV_PATH, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(HEADERS)

        for item in data:
            name = item.get("name", "N/A")
            
            # Use `build_tags` logic from notion_publisher to pre-calculate tags
            tags = build_tags(item)
            if tags is None:
                print(f"    ⏭️ Skipping {name} (기준 평점 미달)")
                continue
                
            print(f"    [AI] Summarizing reviews and translating hours for {name}...")
            
            summary = gemini_summarize(
                item.get("tabelog_reviews", []),
                item.get("google_reviews", []),
                name
            )
            
            hours = translate_hours(item.get("opening_hours") or "")
            
            row = [
                item.get("region", ""),
                name,
                safe_number(item.get("tabelog_score")),
                safe_number(item.get("google_rating")),
                "|".join(tags),  # Pipe-separated for CSV safety
                summary,
                hours,
                item.get("station_info", ""),
                safe_number(item.get("tabelog_review_count")),
                safe_number(item.get("google_review_count")),
                item.get("tabelog_latest_date", ""),
                item.get("address", ""),
                item.get("tabelog_url", ""),
                item.get("google_maps_url", ""),
                item.get("thumbnail", "")
            ]
            writer.writerow(row)
            
if __name__ == "__main__":
    main()
