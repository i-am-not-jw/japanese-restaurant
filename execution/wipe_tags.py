import requests, sys, os
sys.path.append(os.path.normpath(os.path.join(os.path.dirname(__file__), "..")))
from execution.notion_publisher import NOTION_TOKEN, DATABASE_ID, CUISINE_KO, LOCATION_KO

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}
url = f"https://api.notion.com/v1/databases/{DATABASE_ID}"

# Step 1: Wipe property
res1 = requests.patch(url, headers=headers, json={"properties": {"태그": None}})

# Step 2: Build master option list
options = []
def add_opt(name, color):
    if not any(o["name"] == name for o in options):
        options.append({"name": name, "color": color})

add_opt("🏆 현지인 인증맛집", "red")
add_opt("💡 숨겨진 맛집", "red")
add_opt("🦄 0.1% 레전드 맛집", "red")
add_opt("카드 가능", "gray")
add_opt("현금만", "gray")
add_opt("간편결제 가능", "gray")

for name in LOCATION_KO.values():
    add_opt(name, "blue")

for name in CUISINE_KO.values():
    add_opt(name, "green")

# Add a few extra locations that might not be in the direct map but are known
# No longer adding prefectures manually since LOCATION_KO uses city level

# Step 3: Recreate with full options defined (Chunked to bypass 100 limit)
import time

chunk_size = 99
success_count = 0

for i in range(0, len(options), chunk_size):
    chunk = options[i:i+chunk_size]
    payload = {
        "properties": {
            "태그": {
                "multi_select": {
                    "options": chunk
                }
            }
        }
    }
    res2 = requests.patch(url, headers=headers, json=payload)
    if res2.status_code == 200:
        success_count += len(chunk)
    else:
        print(f"Failed to append chunk {i}: {res2.text}")
    time.sleep(1) # Be gentle with Notion rate limit

print(f"Successfully rebuilt '태그' property with {success_count} hardcoded color options!")
