import requests, sys, os
sys.path.append(os.path.normpath(os.path.join(os.path.dirname(__file__), "..")))
from execution.notion_publisher import NOTION_TOKEN, DATABASE_ID

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}
url = f"https://api.notion.com/v1/databases/{DATABASE_ID}"

payload = {
    "properties": {
        "교통": {
            "rich_text": {}
        }
    }
}
patch_res = requests.patch(url, headers=headers, json=payload)
if patch_res.status_code == 200:
    print("Column '교통' successfully added!")
else:
    print(patch_res.json())
