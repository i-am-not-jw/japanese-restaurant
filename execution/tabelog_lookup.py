import sys
import os
import json
import requests
from bs4 import BeautifulSoup
import re

def lookup_tabelog(restaurant_name):
    """Searches and extracts info from Tabelog for a given restaurant name."""
    print(f"Looking up {restaurant_name} on Tabelog...")
    search_url = f"https://tabelog.com/rst/rstsearch/?sa=&sk={restaurant_name}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the first result item
        rst_item = soup.select_one(".list-rst")
        if not rst_item:
            return None
            
        name_elem = rst_item.select_one(".list-rst__rst-name-target")
        score_elem = rst_item.select_one(".list-rst__rating-val")
        price_elems = rst_item.select(".list-rst__budget-val")
        
        name = name_elem.text.strip() if name_elem else restaurant_name
        score = float(score_elem.text.strip()) if score_elem and score_elem.text.strip() != "-" else 0.0
        
        night_price = ""
        day_price = ""
        if len(price_elems) >= 2:
            night_price = price_elems[0].text.strip()
            day_price = price_elems[1].text.strip()
            
        return {
            "name": name,
            "score": score,
            "night_price": night_price,
            "day_price": day_price,
            "url": name_elem['href'] if name_elem else search_url
        }
    except Exception as e:
        print(f"Error looking up {restaurant_name}: {e}")
        return None

def main():
    input_path = os.path.join(os.getcwd(), ".tmp", "sns_results.json")
    if not os.path.exists(input_path):
        print("Input file not found. Running search first?")
        return
        
    with open(input_path, "r", encoding="utf-8") as f:
        sns_data = json.load(f)
        
    # Heuristic: Find potential names in search result titles
    raw_titles = []
    for platform in sns_data:
        raw_titles.extend(sns_data[platform])
        
    # Extract names (this is a simplified logic, ideally would use NLP)
    unique_candidates = set()
    for title in raw_titles:
        # Example: "Restaurant Name | Tabelog" or just the first few words
        # Removing common suffixes
        clean_name = re.split(r' \| | - |: ', title)[0].strip()
        if len(clean_name) > 1:
            unique_candidates.add(clean_name)
        
    report = []
    for candidate in list(unique_candidates)[:10]: # Limit for demo
        details = lookup_tabelog(candidate)
        if details and details['score'] >= 3.0: # Lowered threshold slightly for variety
            report.append(details)
            
    report_path = os.path.join(os.getcwd(), ".tmp", "tabelog_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=4)
        
    print(f"Tabelog report saved to {report_path}")

if __name__ == "__main__":
    main()
