import requests, sys, os
sys.path.append(os.path.normpath(os.path.join(os.path.dirname(__file__), "..")))
from execution.notion_publisher import NOTION_TOKEN, DATABASE_ID, CUISINE_KO, LOCATION_KO

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# The definitive list of allowed tags
ALLOWED_TAGS = set([
    "🏆 현지인 인증맛집", "💡 숨겨진 맛집", "🦄 0.1% 레전드 맛집",
    "카드 가능", "현금만", "간편결제 가능",
    "가나가와현", "아이치현", "효고현", "사이타마현", "치바현", "후쿠오카현",
    "도쿄도", "오사카부", "교토부", "홋카이도", "오키나와현"
])

for loc in LOCATION_KO.values():
    ALLOWED_TAGS.add(loc)
    
for cui in CUISINE_KO.values():
    ALLOWED_TAGS.add(cui)

def get_all_pages():
    pages = []
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    has_more = True
    next_cursor = None
    
    while has_more:
        payload = {}
        if next_cursor:
            payload["start_cursor"] = next_cursor
        res = requests.post(url, headers=headers, json=payload).json()
        
        pages.extend(res.get("results", []))
        has_more = res.get("has_more", False)
        next_cursor = res.get("next_cursor")
        
    return pages

print(f"Total allowed tags: {len(ALLOWED_TAGS)}")
pages = get_all_pages()
print(f"Found {len(pages)} pages in the database.")

for page in pages:
    page_id = page["id"]
    props = page["properties"]
    
    # Get Title
    title_obj = props.get(" 제목", {}).get("title", [])
    title = title_obj[0]["plain_text"] if title_obj else "Unknown"
    
    # Get Tags
    tags_prop = props.get("태그", {}).get("multi_select", [])
    current_tags = [t["name"] for t in tags_prop]
    
    # Filter
    new_tags = [t for t in current_tags if t in ALLOWED_TAGS]
    
    if len(new_tags) != len(current_tags):
        removed = set(current_tags) - set(new_tags)
        print(f"Cleaning [{title}] - Removing: {removed}")
        
        patch_payload = {
            "properties": {
                "태그": {
                    "multi_select": [{"name": nt} for nt in new_tags]
                }
            }
        }
        res = requests.patch(f"https://api.notion.com/v1/pages/{page_id}", headers=headers, json=patch_payload)
        if res.status_code != 200:
            print(f"  ❌ Failed to update {title}: {res.json()}")
    else:
        print(f"[{title}] is already clean.")

print("Done cleaning legacy tags from pages.")
