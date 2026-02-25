"""
google_maps_lookup.py
Uses Playwright to directly visit maps.google.com, search for each restaurant,
and extract: rating, review count, latest 5 reviews with dates, Maps URL.
"""
import os, re, json, time, asyncio
from urllib.parse import quote as requests_quote
from playwright.async_api import async_playwright

INPUT_PATH  = os.path.expanduser("~/.local/share/antigravity/tabelog_report.json")
OUTPUT_PATH = INPUT_PATH


async def scrape_maps(page, restaurant_name, address=""):
    """Search Google Maps for restaurant, return rating, review count, reviews, URL."""
    result = {"google_rating": 0.0, "google_review_count": 0,
              "google_reviews": [], "google_maps_url": ""}
    try:
        # Search on Google Maps — include address/region to be specific
        # We use a substring of the address or just the name + " Okinawa" if available
        query = f"{restaurant_name} {address[:5]}".strip() 
        search_url = f"https://www.google.com/maps/search/{requests_quote(query)}"
        await page.goto(search_url, wait_until="domcontentloaded", timeout=25000)
        await page.wait_for_timeout(4000) # Wait a bit longer for JS

        # Wait for potential navigation or loading
        await page.wait_for_timeout(3000)
        
        print(f"    [DEBUG] Current URL: {page.url}")
        print(f"    [DEBUG] Page Title: {await page.title()}")
        
        result["google_maps_url"] = page.url

        # Check if we are on a Place page (URL contains /place/ or title has name)
        # Rating selector for Place page: Try multiple common selectors
        # 1. Big font class
        # 2. aria-label="X stars"
        rating_elem = page.locator('div[class*="fontDisplayLarge"], span[class*="fontDisplayLarge"]').first
        rc_count = await rating_elem.count()
        print(f"    [DEBUG] Rating elements found: {rc_count}")
        
        if rc_count > 0:
            try:
                txt = await rating_elem.text_content()
                result["google_rating"] = float(txt.strip().replace(",", "."))
            except:
                pass
        
        if result["google_rating"] == 0.0:
            # Try specific class found in dumps
            # <span class="ceNzKf" role="img" aria-label="4.6 つ星 ">
            specific = page.locator('.ceNzKf[role="img"]').first
            if await specific.count() > 0:
                lbl = await specific.get_attribute("aria-label")
                if lbl:
                    m = re.search(r"([\d\.]+)", lbl)
                    if m:
                        result["google_rating"] = float(m.group(1))

        # Review count selector
        # Try finding element with text matching "X reviews" or "X クチコミ"
        # Often: <button ... aria-label="1,234 reviews">...1,234 reviews...</button>
        # Review count extraction via JS evaluation (more robust)
        try:
            rc_val = await page.evaluate('''() => {
                const bodyText = document.body.innerText;
                const m = bodyText.match(/([0-9,]+)\s*(?:件|reviews|クチコミ)/i);
                if (m) {
                    return parseInt(m[1].replace(/,/g, ''));
                }
                const m2 = bodyText.match(/\(([0-9,]+)\)/); // sometimes (1,234)
                if (m2) {
                    return parseInt(m2[1].replace(/,/g, ''));
                }
                return 0;
            }''')
            if rc_val > 0:
                result["google_review_count"] = rc_val
                print(f"    [DEBUG] Review count found via JS: {rc_val}")
        except Exception as e:
            print(f"    JS Review count error: {e}")

        # Fallback to Google Local Search if Maps page is restricted
        if result["google_review_count"] == 0:
            print("    [DEBUG] Maps review count 0. Trying Local Search fallback...")
            try:
                curr_url = page.url
                fallback_url = f"https://www.google.com/search?q={requests_quote(query)}&tbm=lcl&hl=ko&gl=kr"
                await page.goto(fallback_url, wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(2000)
                rc_val2 = await page.evaluate('''() => {
                    const txt = document.body.innerText;
                    // match patterns like 3.9 ★★★★★ (1,200) or just (1,200) Google 리뷰
                    const m = txt.match(/([0-9\.]+)\s*(?:[★\*]+)?\s*\(([0-9,]+)\)/);
                    if (m) {
                        return parseInt(m[2].replace(/,/g, ''));
                    }
                    const m2 = txt.match(/\(([0-9,]+)\)\s*(?:件|クチコミ|reviews)/i);
                    if (m2) {
                        return parseInt(m2[1].replace(/,/g, ''));
                    }
                    return 0;
                }''')
                if rc_val2 > 0:
                    result["google_review_count"] = rc_val2
                    print(f"    [DEBUG] Review count found via fallback: {rc_val2}")
                # Restore original page to continue fetching review texts if possible
                await page.goto(curr_url, wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(3000)
            except Exception as e:
                print(f"    Fallback error: {e}")

        # Click reviews tab
        # Try strict selectors for the tab button
        review_tab = page.locator('button[role="tab"][aria-label*="クチコミ"], button[role="tab"][aria-label*="Reviews"], div[role="tab"]:has-text("クチコミ")').first
        if await review_tab.count() > 0:
            print("    [DEBUG] Clicking Reviews tab...")
            await review_tab.click()
            await page.wait_for_timeout(2000)

            # Sort by newest
            sort_btn = page.locator('button[aria-label*="並べ替え"], button[aria-label*="Sort"]').first
            if await sort_btn.count() > 0:
                await sort_btn.click()
                await page.wait_for_timeout(800)
                newest = page.locator('li[data-index="2"], [data-value="2"]').first
                if await newest.count() > 0:
                    await newest.click()
                    await page.wait_for_timeout(1500)

            # Wait for reviews to load
            await page.wait_for_timeout(3000)

            # Extract latest 5 reviews using multiple possible selectors
            review_elems = page.locator('.wiI7pd, .MyEned, span[class*="wiI7pd"], div[class*="wiI7pd"]')
            count = min(5, await review_elems.count())
            print(f"    [DEBUG] Review text elements found: {await review_elems.count()}")
            reviews = []
            for i in range(count):
                elem = review_elems.nth(i)
                # Expand "more" if needed
                more_btn = elem.locator('button:has-text("...もっと"), button:has-text("More")').first
                if await more_btn.count() > 0:
                    await more_btn.click()
                    await page.wait_for_timeout(300)

                text = (await elem.text_content() or "").strip()[:300]

                # Date from sibling
                date_str = ""
                parent = elem.locator("..").first
                date_elem = parent.locator('[class*="rsqaWe"]').first
                if await date_elem.count() > 0:
                    raw_d = await date_elem.text_content()
                    # "1 ヶ月前" style → approximate
                    if "週間前" in raw_d or "日前" in raw_d or "時間前" in raw_d:
                        from datetime import datetime
                        date_str = datetime.now().strftime("%Y-%m-%d")
                    elif "ヶ月前" in raw_d:
                        date_str = datetime.now().strftime("%Y-%m")
                    else:
                        m2 = re.search(r"(20\d{2})[年/\-](\d{1,2})", raw_d)
                        if m2:
                            date_str = f"{m2.group(1)}-{m2.group(2).zfill(2)}"

                if text:
                    reviews.append({"date": date_str, "text": text})

            result["google_reviews"] = reviews

    except Exception as e:
        print(f"    Maps error for {restaurant_name}: {e}")
    return result


async def run():
    if not os.path.exists(INPUT_PATH):
        print("tabelog_report.json not found.")
        return

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        restaurants = json.load(f)

    # Redirect Playwright temp files to /tmp to avoid Desktop permission errors
    os.environ["TMPDIR"] = "/tmp"
    pw_tmp = "/tmp/antigravity_playwright"
    os.makedirs(pw_tmp, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled",
                  f"--disk-cache-dir={pw_tmp}/cache"]
        )
        ctx = await browser.new_context(
            locale="ja-JP",
            user_agent=("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"),
            storage_state=None
        )
        page = await ctx.new_page()

        for res in restaurants:
            name = res["name"]
            print(f"  Maps: {name}")
            data = await scrape_maps(page, name, res.get("address", ""))
            res["google_rating"]       = data["google_rating"]
            res["google_review_count"] = data["google_review_count"]
            res["google_reviews"]      = data["google_reviews"]
            res["google_maps_url"]     = data["google_maps_url"]
            print(f"    → 평점={data['google_rating']} | 리뷰={data['google_review_count']}개 | URL={data['google_maps_url'][:50]}")
            await asyncio.sleep(2)

        await browser.close()

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(restaurants, f, ensure_ascii=False, indent=2)
    print(f"\nUpdated {OUTPUT_PATH} with Google Maps data.")


def main():
    asyncio.run(run())

if __name__ == "__main__":
    main()
