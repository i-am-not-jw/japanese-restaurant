"""
tabelog_lookup.py
Primary source: Tabelog trending restaurants.
Collects: name, score, address, thumbnail, tabelog_url,
          latest 5 review texts + dates, total review count,
          cuisine (for tags), region (for gallery grouping).
Filters Korean cuisine. Saves to tabelog_report.json.
"""
import os, re, json, time, random, requests, sys
from bs4 import BeautifulSoup
from datetime import datetime

# Load Environment Variables for Gemini
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
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyDgxh1klUXODqhlIStnhU51yheeu3xxewg"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)",
    "Accept-Language": "ja-JP,ja;q=0.9",
}
# Load custom station dictionary to prevent unnecessary API calls and missing fallbacks
STATION_CACHE = {}
_custom_dict_path = os.path.join(os.path.dirname(__file__), "custom_stations_ko.json")
if os.path.exists(_custom_dict_path):
    try:
        with open(_custom_dict_path, "r", encoding="utf-8") as _f:
            STATION_CACHE = json.load(_f)
    except:
        pass

KOREAN_EXCLUDE = ["韓国", "コリアン", "キムチ", "チゲ", "ビビンバ",
                  "サムギョプサル", "チャンジャ", "冷麺", "Korean"]

REGION_MAP = {
    "tokyo": "도쿄", "osaka": "오사카", "kyoto": "교토",
    "fukuoka": "후쿠오카", "sapporo": "삿포로", "hokkaido": "홋카이도",
    "kanagawa": "가나가와", "aichi": "나고야", "hyogo": "고베",
    "okinawa": "오키나와", "saitama": "사이타마", "chiba": "치바",
    "hiroshima": "히로시마", "kagoshima": "가고시마", "shizuoka": "시즈오카",
    "kumamoto": "구마모토", "kagawa": "가가와", "miyagi": "미야기",
    "nagano": "나가노", "ishikawa": "이시카와", "hakodate": "하코다테"
}

def is_korean(text):
    return any(k in text for k in KOREAN_EXCLUDE)

def get_korean_station_name(japanese_station_name):
    raw_name = japanese_station_name.replace("駅", "").replace("JR", "").replace("地下鉄", "").replace("各線", "").strip()
    if not raw_name:
        return ""
    if raw_name in STATION_CACHE:
        return STATION_CACHE[raw_name]
        
    search_term = f"{raw_name}駅"
    url = "https://ja.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "prop": "langlinks",
        "lllang": "ko",
        "titles": search_term,
        "format": "json"
    }
    
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            pages = data.get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                if int(page_id) > 0 and "langlinks" in page_data:
                    ko_title = page_data["langlinks"][0]["*"]
                    # Extract pure name without '역' to store in cache, we append it later
                    pure = ko_title.replace("역", "")
                    STATION_CACHE[raw_name] = pure
                    return ko_title
    except requests.exceptions.Timeout:
        print(f"    [TIMEOUT] Wikipedia API timeout for {search_term} — AI fallback 진행")
    except Exception as e:
        print(f"    [WARN] Wikipedia API error for {search_term}: {e}")
        
    # AI Fallback: Use Gemini to forcefully translate edge-case station names
    if GEMINI_KEY:
        print(f"    [AI RESCUE] Invoking Gemini for untranslated station: {raw_name}")
        prompt = (
            f"일본의 기차역/지하철역 이름 '{raw_name}'을(를) 한국어 발음대로 번역해주세요. "
            "출력은 역 이름 뒷부분의 '역'을 제외한 순수 역 이름만 출력해야 합니다. "
            "(예: 우메다, 신주쿠, 오도리, 시부야 등). 일절 다른 부연 설명을 덧붙이지 마세요."
        )
        url_pro = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            resp2 = requests.post(url_pro, json=payload, timeout=10)
            if resp2.status_code == 200:
                ai_pure_name = resp2.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                ai_pure_name = ai_pure_name.replace("역", "").strip()
                if ai_pure_name:
                    STATION_CACHE[raw_name] = ai_pure_name
                    print(f"      -> AI Translated: {ai_pure_name}")
                    return f"{ai_pure_name}역"
            elif resp2.status_code == 429:
                print(f"    [RATELIMIT] Gemini Flash-latest 429 Too Many Requests -> Exiting")
                sys.exit(429)
        except requests.exceptions.Timeout:
            print(f"      -> AI Rescue Timeout — 재시도 중...")
            try:
                resp2 = requests.post(url_pro, json=payload, timeout=10)
                if resp2.status_code == 200:
                    ai_pure_name = resp2.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    ai_pure_name = ai_pure_name.replace("역", "").strip()
                    if ai_pure_name:
                        STATION_CACHE[raw_name] = ai_pure_name
                        print(f"      -> AI Translated (retry): {ai_pure_name}")
                        return f"{ai_pure_name}역"
            except Exception:
                pass
            print(f"      -> AI Rescue 최종 실패 — 원본 유지: {raw_name}")
        except SystemExit:
            raise
        except Exception as e:
            print(f"      -> AI Rescue Failed: {e}")

    # Final Fallback: Warning log so user can add it to JSON manually later
    print(f"    [WARNING] 미번역 역 감지됨 (Wikipedia & AI 실패): {raw_name}")
    STATION_CACHE[raw_name] = raw_name
    return f"{raw_name}역"

def extract_detail(url):
    """Fetch address, thumbnail, latest 5 reviews + dates, total review count."""
    result = {"address": "", "thumbnail": "", "reviews": [], "review_count": 0, "latest_review_date": ""}
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        soup = BeautifulSoup(resp.text, "html.parser")

        # Thumbnail
        og = soup.find("meta", property="og:image")
        if og and str(og.get("content", "")).startswith("http"):
            result["thumbnail"] = og["content"]

        # Address
        addr_elem = soup.select_one("[class*=address]")
        if addr_elem:
            raw = addr_elem.get_text(strip=True)
            raw = re.sub(r"(大きな地図を見る|周辺のお店|Googleマップ|地図を見る|コピー).*$", "", raw).strip()
            result["address"] = raw[:150]

        # Total review count from the detail page
        count_elem = soup.select_one(".c-page-count__num")
        if count_elem:
            try:
                result["review_count"] = int(re.sub(r"[^\d]", "", count_elem.get_text()))
            except:
                pass
        if not result["review_count"]:
            # Try pattern like "77件" in the page
            m = re.search(r"(\d+)件", soup.get_text())
            if m:
                result["review_count"] = int(m.group(1))

        # Find review list link dynamically
        review_url = ""
        # Try finding the "See all reviews" link usually in the header or sidebar
        # Often: <a class="mainnavi" href="...">口コミ</a> or <a href="..."><strong>77</strong>件</a>
        rv_link = soup.find("a", href=re.compile(r"dtlrvwlst"))
        if rv_link:
             href = rv_link["href"]
             if not href.startswith("http"):
                 href = "https://tabelog.com" + href
             review_url = href # Use directly to avoid 404 from bad query params
        else:
             print("    [DEBUG] No review link found. Dumping candidates:")
             candidates = [a.get('href') for a in soup.find_all('a') if a.get('href') and 'dtlrvwlst' in a.get('href')]
             print(f"    {candidates}")
        
        if not review_url:
             # Fallback to construction (legacy)
             base_url = url.split("?")[0].rstrip("/")
             review_url = f"{base_url}/dtlrvwlst/?srt=1"

        try:
            print(f"    Fetching reviews from: {review_url}")
            rv = requests.get(review_url, headers=HEADERS, timeout=12)
            if rv.status_code != 200:
                print(f"    [DEBUG] Review fetch status: {rv.status_code}")
            rv_soup = BeautifulSoup(rv.text, "html.parser")
            all_items = rv_soup.select(".rvw-item")
            print(f"    [DEBUG] Found {len(all_items)} review items")
            # Filter out pickup/owner items
            # Filter out pickup/owner items
            review_items = [i for i in all_items
                            if "rstdtl-rvw-pickup" not in " ".join(i.get("class", []))][:5]
        except requests.exceptions.Timeout:
            print(f"    [TIMEOUT] Review fetch timeout — 리뷰 없이 진행")
            review_items = []
        except Exception as e:
            print(f"    Review fetch error: {e}")
            review_items = []

        reviews = []
        latest_date = ""
        for item in review_items:
            # Date extraction: search in full text of the item
            date_str = ""
            item_text = item.get_text(separator=" ", strip=True)
            # Look for 20XX/YY or 20XX年YY月 pattern near "訪問"
            # Try specific "YYYY/MM訪問" first
            m = re.search(r"(20\d{2})/(\d{1,2})[^0-9]*訪問", item_text)
            if not m:
                m = re.search(r"(20\d{2})年(\d{1,2})月", item_text)
            
            if m:
                date_str = f"{m.group(1)}-{m.group(2).zfill(2)}"

            if date_str:
                if not latest_date or date_str > latest_date:
                    latest_date = date_str
            # Text
            body = item.select_one(".rvw-item__rvw-comment") or item.select_one(".rvw-item__review-contents") or item
            if body:
                text = body.get_text(separator=" ", strip=True)
                # Remove "Read more" buttons
                text = re.sub(r"もっと見る|写真をもっと見る", "", text).strip()
                if text:
                    reviews.append({"date": date_str, "text": text[:300]})
        # Extract Info Table (Opening Hours, Card, etc.)
        hours = ""
        station_info = ""
        payment_tags = []
        
        table = soup.select_one(".rstinfo-table")
        if not table:
             print("    [DEBUG] Table .rstinfo-table NOT found on detail page")
             # Try fallback
             table = soup.find("table")
        
        if table:
            # print("    [DEBUG] Table found")
            rows = table.select("tr")
            for row in rows:
                th = row.select_one("th")
                td = row.select_one("td")
                if not th or not td:
                    continue
                
                header = th.get_text(strip=True)
                content = td.get_text(separator="\n", strip=True)
                # print(f"    [DEBUG] Header: {header}") 
                
                if "営業時間" in header:
                    # Clean up: remove "COVID" warnings etc if simple headers
                    h = content[:500] # Limit length
                    trans_map = {
                        "月": "월", "火": "화", "水": "수", "木": "목", "金": "금", "土": "토", "日": "일",
                        "祝日": "공휴일", "祝前日": "공휴일 전날", "祝後日": "공휴일 다음날", "祝": "공휴일",
                        "定休日": "정기휴일", "休日": "휴일", "休": "휴무", "曜日": "요일",
                        "・": ", ", "、": ", ", "：": ":", "～": "~", "L.O.": "라스트오더 ", "L.O": "라스트오더 "
                    }
                    for jp, ko in trans_map.items():
                        h = h.replace(jp, ko)
                    hours = h
                elif "カード" in header or "支払" in header:
                    if "カード可" in content or ("カード" in content and "不可" not in content):
                        if "카드 가능" not in payment_tags: payment_tags.append("카드 가능")
                    elif "不可" in content or "現金" in content:
                        if "현금만" not in payment_tags: payment_tags.append("현금만")
                    
                    if "電子マネー可" in content or "電子マネー" in content and "不可" not in content:
                        if "간편결제 가능" not in payment_tags: payment_tags.append("간편결제 가능")
                elif "電子マネー" in header:
                    if "可" in content:
                        if "간편결제 가능" not in payment_tags: payment_tags.append("간편결제 가능")
                elif "交通手段" in header:
                    # Clean newlines and spaces to make searching easier
                    s = re.sub(r"\s+", " ", content)
                    
                    # Case 4: Bus stop
                    if "バス" in s or "停留所" in s or "バス停" in s:
                        cache_key = f"bus_{s[:50]}"
                        if cache_key in STATION_CACHE:
                            station_info = f"🚌 {STATION_CACHE[cache_key]}"
                        elif GEMINI_KEY:
                            print(f"    [AI] Translating full bus access info: {s}")
                            prompt = f"""일본 음식점의 교통/대중교통 안내 구문 '{s}'을(를) 자연스러운 한국어로 단답형으로 번역하세요. 
규칙: 
1. 식당 주인이 자유롭게 적은 문장이므로 버스 정류장, 버스 회사/노선명, 랜드마크 등이 섞여 있을 수 있습니다. 문맥을 파악해서 자연스럽게 번역하세요.
2. 단순히 '버스' 문자가 있다고 해서 무조건 끝에 '정류장'을 붙이지 마세요. (예: 버스 회사 이름이면 그냥 표기)
3. '차로 OO분(車でOO分)'이나 '택시로 OO분' 같은 소요 시간 정보는 무조건 삭제하고 출력하세요.
4. 한자 뜻풀이가 아닌 고유명사 발음대로 표기하세요. (예: 北鉄金沢バス -> 호쿠테쓰 가나자와 버스).
5. 부연설명 없이 깔끔하게 한 줄로 최적화된 결과만 출력하세요."""
                            url_pro = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_KEY}"
                            try:
                                resp2 = requests.post(url_pro, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
                                if resp2.status_code == 200:
                                    ai_bus = resp2.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                                    if ai_bus:
                                        STATION_CACHE[cache_key] = ai_bus
                                        station_info = f"🚌 {ai_bus}"
                                        print(f"      -> Bus Translated: {ai_bus}")
                                else:
                                    station_info = f"🚌 {s}"
                            except requests.exceptions.Timeout:
                                print(f"      -> Bus Translation Timeout — 재시도 중...")
                                try:
                                    resp2 = requests.post(url_pro, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
                                    if resp2.status_code == 200:
                                        ai_bus = resp2.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                                        if ai_bus:
                                            STATION_CACHE[cache_key] = ai_bus
                                            station_info = f"🚌 {ai_bus}"
                                            print(f"      -> Bus Translated (retry): {ai_bus}")
                                        else:
                                            station_info = f"🚌 {s}"
                                    else:
                                        station_info = f"🚌 {s}"
                                except Exception:
                                    print(f"      -> Bus Translation 최종 실패 — 원본 유지")
                                    station_info = f"🚌 {s}"
                            except Exception:
                                station_info = f"🚌 {s}"
                        else:
                            station_info = f"🚌 {s}"
                        continue
                            
                    # Extract station name and distance metrics anywhere in the text
                    # Look for [StationName]駅 から [xx]m or 徒歩[xx]分
                    # Example target: "西川越駅から665m" or "渋谷駅から徒歩5分"
                    station_m = re.search(r"([^\s「」『』\[\]【】\(\)（）｢｣<>・]+)駅(?:.*?)(徒歩(\d+)分|(\d+)m)", s)
                    if not station_m:
                        # Fallback: maybe just "XXX駅" exists
                        station_m = re.search(r"([^\s「」『』\[\]【】\(\)（）｢｣<>・]+?)駅", s)
                        
                    if station_m:
                        raw_jp_full = station_m.group(1).strip()
                        prefix = ""
                        raw_jp = raw_jp_full
                        
                        # 1. Extract and preserve Line names
                        line_match = re.search(r"^([^線]+線)\s*(.*)", raw_jp)
                        if line_match:
                            prefix += line_match.group(1) + " "
                            raw_jp = line_match.group(2)
                        
                        # 2. Extract and preserve Company names
                        comp_match = re.search(r"^(JR|京王|小田急|都営|メトロ|地下鉄|近鉄|名鉄|阪急|京阪|市営|名市交)\s*(.*)", raw_jp)
                        if comp_match:
                            prefix += comp_match.group(1) + " "
                            raw_jp = comp_match.group(2)
                            
                        ko_station = get_korean_station_name(raw_jp)
                        if not ko_station.endswith("역"):
                            ko_station = f"{ko_station}역"
                        
                        ko_prefix = prefix.strip()
                        if ko_prefix:
                            cache_key = f"prefix_{ko_prefix}"
                            if cache_key in STATION_CACHE:
                                ko_prefix = STATION_CACHE[cache_key]
                            elif GEMINI_KEY:
                                print(f"    [AI] Translating railway line: {ko_prefix}")
                                prompt = f"일본의 철도 노선명 또는 회사명 '{ko_prefix}'을(를) 한국어 발음대로 번역하세요. (예: 地下鉄七隈線 -> 지하철 나나쿠마선, JR -> JR, 京阪本線 -> 게이한 본선). 한자 뜻 번역이 아니라 발음대로 적고, '선'이나 '지하철' 같은 단어만 한국어로 바꾸세요. 딱 번역 결과만 출력하세요."
                                url_pro = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_KEY}"
                                try:
                                    resp2 = requests.post(url_pro, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=10)
                                    if resp2.status_code == 200:
                                        ai_prefix = resp2.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                                        if ai_prefix:
                                            STATION_CACHE[cache_key] = ai_prefix
                                            ko_prefix = ai_prefix
                                            print(f"      -> Prefix Translated: {ai_prefix}")
                                except requests.exceptions.Timeout:
                                    print(f"      -> Rail Line Translation Timeout — 원본 유지: {ko_prefix}")
                                except Exception as e:
                                    pass

                        # Clean up prefix deterministically
                        ko_prefix = ko_prefix.replace("지하철 ", "").replace("지하철", "").replace("地下鉄", "")
                        ko_prefix = ko_prefix.replace("・", "").strip()
                        
                        # Reattach the translated prefix!
                        ko_station_full = f"{ko_prefix} {ko_station}".strip()
                            
                        # See if we captured walking time or distance
                        if len(station_m.groups()) >= 3 and station_m.group(3):
                            station_info = f"🚇 {ko_station_full}에서 도보 {station_m.group(3)}분"
                        elif len(station_m.groups()) >= 4 and station_m.group(4):
                            station_info = f"🚇 {ko_station_full}에서 {station_m.group(4)}m"
                        else:
                            station_info = f"🚇 {ko_station_full}"

        result["reviews"] = reviews
        result["latest_review_date"] = latest_date
        result["opening_hours"] = hours
        result["payment_tags"] = payment_tags
        result["station_info"] = station_info

    except Exception as e:
        print(f"    Detail error: {e}")
    return result


def scrape_tabelog_trending(region="tokyo", max_results=5):
    url = f"https://tabelog.com/{region}/rstLst/?SrtT=trend"
    print(f"Tabelog trending [{region}]: {url}")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select(".list-rst__wrap")
        print(f"  {len(items)} candidates")

        results = []
        for item in items:
            if len(results) >= max_results:
                break

            name_elem = item.select_one(".list-rst__rst-name-target")
            score_elem = item.select_one(".c-rating__val")
            area_elem  = item.select_one(".list-rst__area-genre")
            if not name_elem:
                continue

            name      = name_elem.text.strip()
            area_text = area_elem.text.strip() if area_elem else ""
            cuisine   = area_text.split("/", 1)[1].strip() if "/" in area_text else ""

            if is_korean(name + cuisine):
                print(f"  ⛔ Korean skip: {name}")
                continue

            link = name_elem.get("href", "")
            if link and not link.startswith("http"):
                link = "https://tabelog.com" + link

            score = 0.0
            try:
                score = float(score_elem.text.strip()) if score_elem else 0.0
            except:
                pass

            print(f"  [{len(results)+1}/{max_results}] {name}")
            detail = extract_detail(link) if link else {}
            time.sleep(random.uniform(0.6, 1.2))

            results.append({
                "name":                name,
                "tabelog_score":       score,
                "cuisine_raw":         cuisine,
                "tabelog_url":         link,
                "thumbnail":           detail.get("thumbnail", ""),
                "address":             detail.get("address", ""),
                "tabelog_reviews":     detail.get("reviews", []),      # [{date, text}]
                "tabelog_review_count": detail.get("review_count", 0),
                "tabelog_latest_date": detail.get("latest_review_date", ""),
                "opening_hours":       detail.get("opening_hours", ""),
                "payment_tags":        detail.get("payment_tags", []),
                "station_info":        detail.get("station_info", ""),
                "region":              REGION_MAP.get(region, "도쿄"),
                # filled by subsequent scripts:
                "google_rating":       0.0,
                "google_review_count": 0,
                "google_reviews":      [],   # [{date, text}]
                "google_maps_url":     "",
            })
        return results
    except requests.exceptions.Timeout:
        print(f"[TIMEOUT] Tabelog trending page timeout [{region}] — 빈 결과 반환")
        return []
    except Exception as e:
        print(f"Tabelog error: {e}")
        return []


def main():
    import sys
    region = sys.argv[1] if len(sys.argv) > 1 else "tokyo"
    max_results = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    data_dir = os.path.expanduser("~/.local/share/antigravity")
    os.makedirs(data_dir, exist_ok=True)
    restaurants = scrape_tabelog_trending(region=region, max_results=max_results)
    out = os.path.join(data_dir, "tabelog_report.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(restaurants, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(restaurants)} restaurants → {out}")
    for r in restaurants:
        print(f"  {r['name']} | 평점={r['tabelog_score']} | 리뷰={r['tabelog_review_count']}개 | 최신={r['tabelog_latest_date']}")

if __name__ == "__main__":
    main()
