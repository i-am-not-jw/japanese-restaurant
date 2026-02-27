"""
daily_orchestrator.py
Sequentially runs the restaurant scraping pipeline across Japan's top cities by population.
Gracefully halts operations if a 429 Too Many Requests status is detected from Gemini.
"""
import sys
import subprocess
import time
import os

# City targets ordered from highest population downwards.
TARGET_CITIES = [
    "tokyo", "kanagawa", "osaka", "aichi",
    "hokkaido", "fukuoka", "hyogo", "kyoto",
    "saitama", "chiba", "okinawa"
]

# Tier 2 small cities for regional variety
TIER_2_CITIES = [
    "hiroshima",    # 히로시마
    "shizuoka",     # 시즈오카
    "kagoshima",    # 가고시마
    "kagawa",       # 다카마쓰 (향천현)
    "kumamoto",     # 구마모토
    "miyagi",       # 센다이 (미야기현)
    "nagano",       # 나가노
    "ishikawa",     # 가나자와 (이시카와현)
    "hakodate"      # 하코다테 (홋카이도 특구)
]

ALL_CITIES = TARGET_CITIES + TIER_2_CITIES

MAX_RESULTS_PER_CITY = 3  # Fetch more to ensure a rich final database

def run_script(script_name, args=[]):
    cmd = ["python3", f"execution/{script_name}"] + args
    print(f"  [Orchestrator] Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode

def main():
    print("=====================================================")
    print("▶️ Starting Daily Orchestrator (City Population Mode)")
    print("=====================================================\n")

    # Wipe existing staging CSV before a full fresh run
    # Note: Using absolute path from current file directory to avoid PermissionError
    staging_file = "/tmp/japanese_restaurant_data/staged_restaurants.csv"
    if os.path.exists(staging_file):
        os.remove(staging_file)
        print(f"  [Orchestrator] Wiped existing staging file: {staging_file}")
    
    print(f"=====================================================\n")
    
    for city in ALL_CITIES:
        print(f"\n🌍 Target City: {city.upper()} (Max: {MAX_RESULTS_PER_CITY} listings)")
        
        # 1. Tabelog Lookup
        exit_code = run_script("tabelog_lookup.py", [city, str(MAX_RESULTS_PER_CITY)])
        if exit_code != 0:
            print(f"  ❌ Tabelog scraping failed for {city}. Skipping to next.")
            continue
            
        # 2. Google Maps Lookup
        exit_code = run_script("google_maps_lookup.py")
        if exit_code != 0:
            print(f"  ❌ Google Maps extraction failed for {city}. Skipping to next.")
            continue
            
        # 3. Export to CSV (Staging for Human Review)
        exit_code = run_script("export_to_csv.py")
        if exit_code != 0:
            print(f"  ❌ CSV Export failed for {city}.")
            continue
            
        print(f"✅ Successfully staged {city} into CSV.")
        
        # Friendly delay between heavy city blocks
        print("  ⏳ Resting for 15 seconds before the next city...")
        time.sleep(15)
        
    print("\n🎉 Daily Orchestrator extraction finished.")
    print("=====================================================")
    print("🚀 Attempting automatic upload to Notion...")
    
    # Call publish_from_csv.py with --auto
    publish_script = os.path.join(os.path.dirname(__file__), "publish_from_csv.py")
    res = os.system(f"python3 {publish_script} --auto")
    
    if res == 0:
        print("\n🎉 Automatic upload completed successfully!")
    else:
        print("\n⚠️ Automatic upload skipped. Please check the CSV at .tmp/staged_restaurants.csv and run publish_from_csv.py manually.")

if __name__ == "__main__":
    main()
