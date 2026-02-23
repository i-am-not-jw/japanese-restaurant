"""
notion_publisher.py
Publishes restaurant data to Notion with:
  - Gemini AI-powered review summary (Tabelog 5 + Google Maps 5)
  - Separate tabelog URL and google map URL properties
  - Korean tags (location + cuisine)
  - Gallery-friendly: 지역 select, 썸네일 files property
"""
import os, re, json, requests, sys
from datetime import datetime

# ── Credentials ──────────────────────────────────────────────────────────────
def load_env():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.normpath(os.path.join(script_dir, "..", ".env"))
    if os.path.exists(env_path):
        try:
            with open(env_path, "r") as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        k, v = line.strip().split("=", 1)
                        os.environ.setdefault(k, v)
        except PermissionError:
            pass

load_env()
NOTION_TOKEN  = os.getenv("NOTION_TOKEN")  or "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"
DATABASE_ID   = os.getenv("NOTION_JAPAN_RESTAURANT_DB_ID") or "307deb1120c1800f914fcc99c25dc0f8"
GEMINI_KEY    = os.getenv("GEMINI_API_KEY") or "AIzaSyDgxh1klUXODqhlIStnhU51yheeu3xxewg"

# ── Gemini AI summary ─────────────────────────────────────────────────────────
def gemini_summarize(tabelog_reviews, google_reviews, restaurant_name):
    """
    Send up to 5 Tabelog reviews + 5 Google Maps reviews to Gemini,
    get a concise Korean summary paragraph.
    """
    all_texts = []
    for r in tabelog_reviews[:5]:
        if r.get("text"):
            all_texts.append(f"[타베로그] {r['text']}")
    for r in google_reviews[:5]:
        if r.get("text"):
            all_texts.append(f"[구글 맵] {r['text']}")

    if not all_texts:
        return ""

    combined = "\n\n".join(all_texts)
    prompt = (
        f"다음은 일본 식당 「{restaurant_name}」의 최신 리뷰들입니다.\n\n"
        f"{combined}\n\n"
        "위 리뷰들을 바탕으로 이 식당의 특징, 인기 메뉴, 분위기, "
        "장단점을 한국어로 3~4문장으로 간결하게 요약해 주세요."
    )
    url_pro = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        resp2 = requests.post(url_pro, json=payload, timeout=20)
        if resp2.status_code == 200:
            return resp2.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        elif resp2.status_code == 429:
            print(f"    [RATELIMIT] Gemini Flash-latest 429 Too Many Requests -> Exiting")
            sys.exit(429)
        print(f"    Gemini latest error: {resp2.status_code} {resp2.reason}")
        return f"요약 실패 (에러 {resp.status_code})"
    except Exception as e:
        print(f"    Gemini API call error: {e}")
        # Fallback: plain concatenation
        return " | ".join(t[:100] for t in all_texts[:3])

def translate_hours(hours_jp):
    if not hours_jp:
        return ""
        
    prompt = (
        f"다음은 일본 식당의 영업시간 안내 표기입니다:\n\n{hours_jp}\n\n"
        "이 내용을 자연스러운 한국어로 번역하되, 절대로 줄글이나 문장형으로 길게 명시하지 마세요. "
        "오직 아래와 같은 '간결한 불릿 포인트(•)' 형식으로 요일, 시간, 휴무일 정보만 명확하게 요약하여 출력해주세요.\n\n"
        "출력 양식 예시:\n"
        "• 평일: 11:50~15:00 / 17:00~23:00\n"
        "• 주말 및 공휴일: 17:00~23:00\n"
        "• 라스트 오더: 요리 22:00, 음료 22:30\n"
        "• 휴무일: 부정기 휴무\n\n"
        "위 예시처럼 핵심 시간과 휴무일 정보만 한눈에 들어오게 정리해 주세요."
    )
    url_pro = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        resp2 = requests.post(url_pro, json=payload, timeout=20)
        if resp2.status_code == 200:
            return resp2.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        elif resp2.status_code == 429:
            print(f"    [RATELIMIT] Gemini Flash-latest 429 Too Many Requests (Hours) -> Exiting")
            sys.exit(429)
    except SystemExit:
        raise
    except Exception as e:
        pass
    return hours_jp # Fallback to original

# ── Translation tables ────────────────────────────────────────────────────────
LOCATION_KO = {
    "千代田区": "치요다구", "中央区": "주오구", "港区": "미나토구",
    "新宿区": "신주쿠구", "文京区": "분쿄구", "台東区": "다이토구",
    "墨田区": "스미다구", "江東区": "고토구", "品川区": "시나가와구",
    "目黒区": "메구로구", "大田区": "오타구", "世田谷区": "세타가야구",
    "渋谷区": "시부야구", "中野区": "나카노구", "杉並区": "스기나미구",
    "豊島区": "도시마구", "北区": "기타구", "荒川区": "아라카와구",
    "板橋区": "이타바시구", "練馬区": "네리마구", "足立区": "아다치구",
    "葛飾区": "가쓰시카구", "江戸川区": "에도가와구",
    "立川市": "다치카와", "町田市": "마치다",
    "横浜市": "요코하마", "川崎市": "가와사키", "鎌倉市": "가마쿠라",
    "大阪市": "오사카", "堺市": "사카이",
    "京都市": "교토", 
    "札幌市": "삿포로", "函館市": "하코다테", "小樽市": "오타루",
    "名古屋市": "나고야",
    "神戸市": "고베", "姫路市": "히메지",
    "福岡市": "후쿠오카", "北九州市": "기타큐슈",
    "さいたま市": "사이타마", "川越市": "가와고에",
    "千葉市": "치바", "船橋市": "후나바시",
    "那覇市": "나하", "石垣市": "이시가키", "宮古島市": "미야코지마",
    
    # Tier 2 Small Cities Extension
    "広島市": "히로시마",
    "静岡市": "시즈오카",
    "鹿児島市": "가고시마",
    "高松市": "다카마쓰",
    "熊本市": "구마모토",
    "仙台市": "센다이",
    "長野市": "나가노",
    "金沢市": "가나자와"
}

CUISINE_KO = {
    "居酒屋": "이자카야", "和食": "일식", "寿司": "스시(초밥)", "鮨": "스시(초밥)",
    "ラーメン": "라멘", "焼肉": "야키니쿠", "焼き鳥": "야키토리",
    "天ぷら": "텐동/튀김", "蕎麦": "소바", "うどん": "우동",
    "イタリアン": "이탈리안", "フレンチ": "프렌치", "中華料理": "중식",
    "ベトナム料理": "베트남 요리", "タイ料理": "태국 요리",
    "ハンバーガー": "수제버거", "カフェ": "카페", "バー": "바(Bar)",
    "バル": "발/다이닝바", "ビストロ": "비스트로",
    "海鮮": "해산물", "鍋": "나베", "串焼き": "꼬치구이",
    "しゃぶしゃぶ": "샤브샤브", "鉄板焼き": "철판구이", "ステーキ": "스테이크",
    "ハンバーグ": "함박스테이크", "とんかつ": "돈카츠", "牛丼": "규동(덮밥)",
    "お好み焼き": "오코노미야키", "たこ焼き": "타코야키", "もつ鍋": "모츠나베(곱창전골)",
    "すき焼き": "스키야키", "カレー": "카레", "うなぎ": "장어(우나기)",
    "馬肉料理": "말고기 요리", "ジンギスカン": "징기스칸",
    "小籠包": "샤오롱바오", "ダイニングバー": "다이닝바",
    "郷土料理": "향토 요리", "沖縄料理": "오키나와 요리", "韓国料理": "한국 요리",
    "レストラン": "레스토랑", "スイーツ": "디저트", "パン": "베이커리"
}

def build_tags(restaurant):
    rating_tags = []
    cuisine_tags = []
    location_tags = []
    payment_tags = []

    addr = restaurant.get("address", "")
    cuisine = restaurant.get("cuisine_raw", "")

    # Group location tags
    for jp, ko in LOCATION_KO.items():
        if jp in addr and ko not in location_tags:
            location_tags.append(ko)
    
    # Group cuisine tags
    for jp, ko in CUISINE_KO.items():
        if jp in cuisine and ko not in cuisine_tags:
            cuisine_tags.append(ko)

    # Group payment tags
    for pt in restaurant.get("payment_tags", []):
        if pt not in payment_tags:
            payment_tags.append(pt)

    # Add Rating Tags
    tabelog_score = restaurant.get("tabelog_score", 0.0)
    google_rating = restaurant.get("google_rating", 0.0)
    google_review_count = restaurant.get("google_review_count", 0)
    tabelog_latest_date = restaurant.get("tabelog_latest_date", "")

    from datetime import datetime
    has_recent_review = False
    try:
        if tabelog_latest_date:
            latest_dt = datetime.strptime(tabelog_latest_date, "%Y-%m")
            delta = datetime.now() - latest_dt
            if delta.days <= 60:
                has_recent_review = True
    except:
        pass

    if tabelog_score >= 4.0:
        rating_tags.append("🦄 0.1% 레전드 맛집")
    elif 3.50 <= tabelog_score < 4.0:
        rating_tags.append("🏆 현지인 인증맛집")
    elif 3.20 <= tabelog_score < 3.50:
        if google_rating >= 4.2 and google_review_count >= 50 and has_recent_review:
            rating_tags.append("💡 숨겨진 맛집")

    # Filter out if it doesn't meet the minimum rating requirement
    if not rating_tags:
        return None

    # Tag Ordering: Rating -> Cuisine (Menu) -> Region (Location) -> Card (Payment)
    return rating_tags + cuisine_tags + location_tags + payment_tags

# ── Notion helpers ────────────────────────────────────────────────────────────
def safe_url(url):
    return str(url) if url and str(url).startswith("http") else None

def safe_number(val):
    try:
        f = float(val)
        return f if f > 0 else None
    except:
        return None

def check_existing_page(tabelog_url, headers):
    if not tabelog_url:
        return None
    query_payload = {
        "filter": {
            "property": "tabelog URL",
            "url": {
                "equals": tabelog_url
            }
        }
    }
    try:
        resp = requests.post(f"https://api.notion.com/v1/databases/{DATABASE_ID}/query", headers=headers, json=query_payload)
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            if results:
                return results[0]["id"]
    except Exception as e:
        print(f"  [ERROR] Check existing page failed: {e}")
    return None

def safe_thumb(url):
    if url and str(url).startswith("http") and "data:image" not in str(url):
        return [{"name": "썸네일", "external": {"url": str(url)}}]
    return []

def multiselect(items):
    return [{"name": str(s)[:100]} for s in items if s]


def publish_one(item, headers):
    name = item.get("name", "N/A")
    tags   = build_tags(item)

    if tags is None:
        print(f"  ⏭️ Skipping {name} (기준 평점 미달)")
        return

    # AI summary
    print(f"    Gemini 요약 중...")
    summary = gemini_summarize(
        item.get("tabelog_reviews", []),
        item.get("google_reviews", []),
        name
    )
    region = item.get("region", "도쿄")
    latest = item.get("tabelog_latest_date", "")

    tabelog_url = safe_url(item.get("tabelog_url", ""))
    existing_page_id = check_existing_page(tabelog_url, headers)

    properties = {
        " 제목": {
            "title": [{"text": {"content": name}}]
        },
        "tabelog 평점": {
            "number": safe_number(item.get("tabelog_score"))
        },
        "tabelog 리뷰 수": {
            "number": safe_number(item.get("tabelog_review_count"))
        },
        "tabelog 최신 리뷰": {
            "date": {"start": latest} if latest else None
        },
        "google 평점": {
            "number": safe_number(item.get("google_rating"))
        },
        "google map 리뷰 수": {
            "number": safe_number(item.get("google_review_count"))
        },
        "요약": {
            "rich_text": [{"text": {"content": summary[:2000]}}]
        },
        "장소": {
            "rich_text": [{"text": {"content": (item.get("address") or "")[:2000]}}]
        },
        "영업 시간": {
            "rich_text": [{"text": {"content": translate_hours(item.get("opening_hours") or "")[:2000]}}]
        },
        "태그": {
            "multi_select": multiselect(tags)
        },
        "지역": {
            "select": {"name": region}
        },
        "썸네일": {
            "files": safe_thumb(item.get("thumbnail", ""))
        },
        "tabelog URL": {
            "url": tabelog_url
        },
        "google map URL": {
            "url": safe_url(item.get("google_maps_url", ""))
        },
    }

    if existing_page_id:
        resp = requests.patch(f"https://api.notion.com/v1/pages/{existing_page_id}", headers=headers, json={"properties": properties})
        if resp.status_code == 200:
            print(f"  🔄 Updated {name} | 지역={region} | 태그={tags[:3]}")
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
            print(f"  ✅ Created {name} | 지역={region} | 태그={tags[:3]}")
        else:
            err = resp.json().get("message", resp.text[:200])
            print(f"  ❌ Create failed {name}: {err}")


def main():
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }
    path = "/tmp/antigravity_tmp/tabelog_report.json"
    if not os.path.exists(path):
        print("No data found. Run tabelog_lookup.py first.")
        return
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Publishing {len(data)} restaurants...")
    for item in data:
        publish_one(item, headers)

if __name__ == "__main__":
    main()
