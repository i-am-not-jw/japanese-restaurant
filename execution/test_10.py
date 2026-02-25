import os, subprocess, csv, sys, random

TARGET_CITIES = [
    "tokyo", "kanagawa", "osaka", "aichi",
    "hokkaido", "fukuoka", "hyogo", "kyoto",
    "saitama", "chiba", "okinawa"
]
TIER_2_CITIES = [
    "hiroshima", "shizuoka", "kagoshima", "kagawa", 
    "kumamoto", "miyagi", "nagano", "ishikawa", "hakodate"
]
ALL_CITIES = TARGET_CITIES + TIER_2_CITIES

CITIES = random.sample(ALL_CITIES, 10)
CSV_PATH = "/tmp/antigravity_tmp/staged_restaurants.csv"

# Clear staging area
if os.path.exists(CSV_PATH):
    os.remove(CSV_PATH)

print(f"Randomly selected 10 cities: {', '.join(CITIES)}")

for city in CITIES:
    print(f"Fetching 5 from {city}...")
    subprocess.run(["python3", "execution/tabelog_lookup.py", city, "5"])
    subprocess.run(["python3", "execution/google_maps_lookup.py"])
    subprocess.run(["python3", "execution/export_to_csv.py"])
    
if os.path.exists(CSV_PATH):
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        lines = list(csv.reader(f))
    
    if len(lines) > 1:
        print(f"Gathered {len(lines)-1} valid items. Publishing.")
        subprocess.run(["python3", "execution/publish_from_csv.py"])
        sys.exit(0)

print("Failed to gather any items across tested cities.")
