import os
import requests
import re
import time
import sys

# Add parent directory to path to import variables
sys.path.append(os.path.normpath(os.path.join(os.path.dirname(__file__), "..")))
from execution.notion_publisher import NOTION_TOKEN, DATABASE_ID, GEMINI_KEY

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def contains_japanese(text):
    # Regex to match Hiragana, Katakana, and Kanji
    return bool(re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', text))

def translate_with_gemini(text):
    prompt = f"""일본 음식점의 교통/대중교통 안내 구문 '{text}'을(를) 자연스러운 한국어로 단답형으로 번역하세요. 
규칙: 
1. 식당 주인이 자유롭게 적은 문장이므로 버스 정류장, 버스 회사/노선명, 랜드마크 등이 섞여 있을 수 있습니다. 문맥을 파악해서 자연스럽게 번역하세요.
2. '차로 OO분(차로 OO분, 車でOO分)'이나 '택시로' 같은 정보는 무조건 삭제하세요.
3. 고유명사나 회사명(예: 호쿠테쓰 가나자와 버스) 뒤에 억지로 '정류장'을 붙이지 마세요. 정류장(停留所)이라는 뜻이 원문에 있을 때만 붙이세요.
4. 부연설명 없이 결과만 한 줄로 출력하세요."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_KEY}"
    try:
        resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        if resp.status_code == 200:
            return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"Gemini Exception: {e}")
    return text

def main():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    has_more = True
    next_cursor = None
    count = 0
    updated = 0

    while has_more:
        payload = {}
        if next_cursor:
            payload["start_cursor"] = next_cursor
        
        res = requests.post(url, headers=HEADERS, json=payload)
        data = res.json()
        
        for item in data.get("results", []):
            count += 1
            page_id = item["id"]
            props = item["properties"]
            
            # Get Title
            title_prop = props.get("제목", {}).get("title", [])
            title = title_prop[0]["text"]["content"] if title_prop else "Unknown"

            # Check '교통'
            traffic_prop = props.get("교통", {}).get("rich_text", [])
            if traffic_prop:
                traffic_text = "".join(t["text"]["content"] for t in traffic_prop)
                if contains_japanese(traffic_text) or "차로" in traffic_text or "버스 주변" in traffic_text or "가나자와 버스 정류장" in traffic_text or "가타마치 버스 정류장" in traffic_text:
                    print(f"[{count}] {title} - Requires bus re-translation: {traffic_text}")
                    korean_text = translate_with_gemini(traffic_text)
                    print(f"  -> Translating to: {korean_text}")
                    
                    if korean_text != traffic_text:
                        # Ensure emoji is present if it was there
                        if traffic_text.startswith("🚌") and not korean_text.startswith("🚌"):
                            korean_text = "🚌 " + korean_text.replace("🚌", "").strip()
                        elif traffic_text.startswith("🚇") and not korean_text.startswith("🚇"):
                            korean_text = "🚇 " + korean_text.replace("🚇", "").strip()

                        # Update Notion
                        patch_url = f"https://api.notion.com/v1/pages/{page_id}"
                        patch_payload = {
                            "properties": {
                                "교통": {
                                    "rich_text": [{"text": {"content": korean_text}}]
                                }
                            }
                        }
                        patch_res = requests.patch(patch_url, headers=HEADERS, json=patch_payload)
                        if patch_res.status_code == 200:
                            print("  -> Successfully updated.")
                            updated += 1
                        else:
                            print("  -> Failed to update.")
                else:
                    print(f"[{count}] {title} - OK (Korean): {traffic_text}")
                    
        has_more = data.get("has_more")
        next_cursor = data.get("next_cursor")
        
    print(f"\nChecked {count} entries. Updated {updated} items.")

if __name__ == '__main__':
    main()
