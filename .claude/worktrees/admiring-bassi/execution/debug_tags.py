import requests, sys, os
sys.path.append(os.path.normpath(os.path.join(os.path.dirname(__file__), "..")))
from execution.notion_publisher import NOTION_TOKEN, DATABASE_ID

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28"
}
res = requests.get(f"https://api.notion.com/v1/databases/{DATABASE_ID}", headers=headers)
props = res.json().get("properties", {})
for p_name, p_data in props.items():
    print(f"Property: {p_name} ({p_data['type']})")
    if p_data["type"] == "multi_select":
        print("  Options:")
        for opt in p_data["multi_select"].get("options", []):
            print(f"    - '{opt['name']}' (color: {opt['color']})")
