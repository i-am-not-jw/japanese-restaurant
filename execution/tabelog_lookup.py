"""
tabelog_lookup.py
Primary source: Tabelog trending restaurants.
Collects: name, score, address, thumbnail, tabelog_url,
          latest 5 review texts + dates, total review count,
          cuisine (for tags), region (for gallery grouping).
Filters Korean cuisine. Saves to tabelog_report.json.
"""
import os, re, json, time, random, requests
from bs4 import BeautifulSoup
from datetime import datetime

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"),
    "Accept-Language": "ja-JP,ja;q=0.9",
}

KOREAN_EXCLUDE = ["韓国", "コリアン", "キムチ", "チゲ", "ビビンバ",
                  "サムギョプサル", "チャンジャ", "冷麺", "Korean"]

REGION_MAP = {
    "tokyo": "도쿄", "osaka": "오사카", "kyoto": "교토",
    "fukuoka": "후쿠오카", "sapporo": "삿포로", "hokkaido": "홋카이도",
    "kanagawa": "가나가와", "aichi": "나고야", "hyogo": "고베",
    "okinawa": "오키나와",
}

def is_korean(text):
    return any(k in text for k in KOREAN_EXCLUDE)

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

        result["reviews"] = reviews
        result["latest_review_date"] = latest_date
        result["opening_hours"] = hours
        result["payment_tags"] = payment_tags

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
                "region":              REGION_MAP.get(region, "도쿄"),
                # filled by subsequent scripts:
                "google_rating":       0.0,
                "google_review_count": 0,
                "google_reviews":      [],   # [{date, text}]
                "google_maps_url":     "",
            })
        return results
    except Exception as e:
        print(f"Tabelog error: {e}")
        return []


def main():
    os.makedirs("/tmp/antigravity_tmp", exist_ok=True)
    # User requested Nagoya (using aichi hub) and 5 results
    restaurants = scrape_tabelog_trending(region="aichi", max_results=5)
    out = "/tmp/antigravity_tmp/tabelog_report.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(restaurants, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(restaurants)} restaurants → {out}")
    for r in restaurants:
        print(f"  {r['name']} | 평점={r['tabelog_score']} | 리뷰={r['tabelog_review_count']}개 | 최신={r['tabelog_latest_date']}")

if __name__ == "__main__":
    main()
