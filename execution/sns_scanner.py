import sys
import os
import json
import asyncio
from datetime import datetime, timedelta
from playwright.async_api import async_playwright

async def google_search_sns(platform_domain, keywords):
    """Searches Google for recent posts on a specific SNS platform."""
    results = []
    query = f"site:{platform_domain} " + " ".join(keywords)
    print(f"Searching Google for: {query}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Search Google
        try:
            await page.goto(f"https://www.google.com/search?q={query}")
            await page.wait_for_selector("div.g", timeout=10000)
            
            # Extract titles and links
            search_results = await page.query_selector_all("div.g")
            for item in search_results[:10]: # Top 10 results
                title_node = await item.query_selector("h3")
                if title_node:
                    title = await title_node.inner_text()
                    results.append(title)
        except Exception as e:
            print(f"Error during search for {platform_domain}: {e}")
        finally:
            await browser.close()
    return results

async def main():
    # Japanese keywords for local favorites
    keywords = ["地元の人しか知らない", "教えたくない", "穴場", "グルメ"]
    
    platforms = {
        "instagram": "instagram.com",
        "tiktok": "tiktok.com",
        "youtube": "youtube.com",
        "x": "x.com",
        "threads": "threads.net"
    }
    
    all_results = {}
    
    for platform, domain in platforms.items():
        print(f"Running search for {platform}...")
        results = await google_search_sns(domain, keywords)
        all_results[platform] = results
    
    output_dir = os.path.join(os.getcwd(), ".tmp")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "sns_results.json")
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=4)
    
    print(f"Results saved to {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
