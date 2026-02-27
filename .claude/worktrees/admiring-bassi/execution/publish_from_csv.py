"""
publish_from_csv.py
Reads the human-reviewed .tmp/staged_restaurants.csv and publishes the data
to the Notion database via Upsert.
"""
import sys, os, csv, requests

sys.path.append(os.path.normpath(os.path.join(os.path.dirname(__file__), "..")))
from execution.notion_publisher import check_existing_page, safe_thumb, multiselect, safe_url, safe_number, NOTION_TOKEN, DATABASE_ID

CSV_PATH = os.path.expanduser("~/.local/share/antigravity/staged_restaurants.csv")
def main():
    if not os.path.exists(CSV_PATH):
        print(f"❌ No staged CSV found at {CSV_PATH}. Have you run daily_orchestrator.py?")
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }
    
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print("CSV is empty.")
        sys.exit(0)

    print("=====================================================")
    print(f"▶️ Starting Notion Publisher (Publishing {len(rows)} apps from CSV)")
    print("=====================================================\n")

    for row in rows:
        name = row["Restaurant_Name"]
        region = row["Target_City_Region"]
        tags = row["Generated_Tags"].split("|") if row["Generated_Tags"] else []
        tabelog_url = safe_url(row["Tabelog_URL"])

        existing_page_id = check_existing_page(tabelog_url, headers)
        
        kr_region_ko_map = {
            "도쿄": "🗼 도쿄", "오사카": "🐙 오사카", "교토": "⛩️ 교토", "홋카이도": "⛄ 홋카이도",
            "요코하마": "🌊 가나가와", "가나가와": "🌊 가나가와", "나고야": "🏯 아이치", "아이치": "🏯 아이치",
            "후쿠오카": "🍜 후쿠오카", "고베": "🥩 효고", "효고": "🥩 효고", "치바": "✈️ 치바",
            "사이타마": "🌳 사이타마", "오키나와": "🌴 오키나와",
            "tokyo": "🗼 도쿄", "osaka": "🐙 오사카", "kyoto": "⛩️ 교토", "hokkaido": "⛄ 홋카이도",
            "kanagawa": "🌊 가나가와", "aichi": "🏯 아이치", "fukuoka": "🍜 후쿠오카",
            "hyogo": "🥩 효고", "chiba": "✈️ 치바", "saitama": "🌳 사이타마", "okinawa": "🌴 오키나와"
        }
        
        base_region = region.strip().lower()
        region_with_flag = kr_region_ko_map.get(base_region, region.strip())

        properties = {
            " 제목": {
                "title": [{"text": {"content": name}}]
            },
            "tabelog 평점": {
                "number": safe_number(row["Tabelog_Rating"])
            },
            "tabelog 리뷰 수": {
                "number": safe_number(row["Tabelog_Review_Count"])
            },
            "tabelog 최신 리뷰": {
                "date": {"start": row["Tabelog_Latest_Review_Date"]} if row["Tabelog_Latest_Review_Date"] else None
            },
            "google 평점": {
                "number": safe_number(row["Google_Rating"])
            },
            "google map 리뷰 수": {
                "number": safe_number(row["Google_Review_Count"])
            },
            "요약": {
                "rich_text": [{"text": {"content": row["AI_Review_Summary"][:2000]}}]
            },
            "장소": {
                "rich_text": [{"text": {"content": row["Address"][:2000]}}]
            },
            "교통": {
                "rich_text": [{"text": {"content": row["Station_Info"][:2000]}}]
            },
            "영업 시간": {
                "rich_text": [{"text": {"content": row["AI_Opening_Hours"][:2000]}}]
            },
            "태그": {
                "multi_select": multiselect(tags)
            },
            "지역": {
                "select": {"name": region_with_flag}
            },
            "썸네일": {
                "files": safe_thumb(row["Thumbnail_URL"])
            },
            "tabelog URL": {
                "url": tabelog_url
            },
            "google map URL": {
                "url": safe_url(row["Google_Maps_URL"])
            }
        }
        if existing_page_id:
            patch_payload = {"properties": properties}
            resp = requests.patch(f"https://api.notion.com/v1/pages/{existing_page_id}", headers=headers, json=patch_payload)
            if resp.status_code == 200:
                print(f"  🔄 Updated {name} | 지역={region_with_flag}")
            else:
                err = resp.json().get("message", resp.text[:200])
                print(f"  ❌ Update failed {name}: {err}")
        else:
            payload = {
                "parent": {"database_id": DATABASE_ID},
                "properties": properties
            }
            resp = requests.post("https://api.notion.com/v1/pages", headers=headers, json=payload)
            if resp.status_code == 200:
                print(f"  ✅ Created {name} | 지역={region_with_flag}")
            else:
                err = resp.json().get("message", resp.text[:200])
                print(f"  ❌ Create failed {name}: {err}")

if __name__ == "__main__":
    main()
