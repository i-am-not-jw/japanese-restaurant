import requests, sys, os
sys.path.append(os.path.normpath(os.path.join(os.path.dirname(__file__), "..")))
from execution.notion_publisher import NOTION_TOKEN, DATABASE_ID

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}
url = f"https://api.notion.com/v1/databases/{DATABASE_ID}"

res = requests.get(url, headers=headers)
options = res.json().get("properties", {}).get("태그", {}).get("multi_select", {}).get("options", [])

new_options = []
for opt in options:
    name = opt["name"]
    color = "default"
    
    # Filter out junk station tags to bypass the 100 option limit
    if "역" in name or "버스" in name or "도보" in name or "🚇" in name or "🚌" in name or "徒歩" in name:
        continue

    if name in ["🏆 현지인 인증맛집", "💡 숨겨진 맛집", "🦄 0.1% 레전드 맛집"]:
        color = "red"
    elif name in ["카드 가능", "현금만", "간편결제 가능"]:
        color = "gray"
    elif any(x in name for x in ["구", "현", "도", "부", "시", "오사카", "도쿄", "교토", "홋카이도", "가나가와", "나고야", "효고", "오키나와", "사이타마", "치바"]):
        color = "blue"
    else:
        # Default for cuisines
        color = "green"
        
    new_options.append({
        "id": opt["id"],
        "name": name,
        "color": color
    })

payload = {
    "properties": {
        "태그": {
            "multi_select": {
                "options": new_options
            }
        }
    }
}
patch_res = requests.patch(url, headers=headers, json=payload)
if patch_res.status_code == 200:
    print("Tags successfully standardized!")
else:
    print(patch_res.json())
