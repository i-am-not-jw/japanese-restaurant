import os, subprocess, csv, sys

CITIES = ["kagawa", "hiroshima", "shizuoka", "kumamoto", "kagoshima"]
CSV_PATH = "/tmp/antigravity_tmp/staged_restaurants.csv"

# Clear staging area
if os.path.exists(CSV_PATH):
    os.remove(CSV_PATH)

for city in CITIES:
    print(f"Fetching 50 from {city}...")
    subprocess.run(["python3", "execution/tabelog_lookup.py", city, "50"])
    subprocess.run(["python3", "execution/google_maps_lookup.py"])
    subprocess.run(["python3", "execution/export_to_csv.py"])
    
    # Check CSV length
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            lines = list(csv.reader(f))
        
        if len(lines) > 10: # >10 means at least header + 10 rows
            # Truncate to exactly 11 lines
            print(f"Gathered {len(lines)-1} items. Truncating to exactly 10 and publishing.")
            with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(lines[:11])
            subprocess.run(["python3", "execution/publish_from_csv.py"])
            sys.exit(0)

print("Failed to gather 10 items across tested cities.")
