import csv
import os
import json

CSV_PATH = "/tmp/japanese_restaurant_data/staged_restaurants.csv"

def check_integrity():
    if not os.path.exists(CSV_PATH):
        return {"error": "CSV file not found"}

    integrity_report = {
        "total_count": 0,
        "missing_google_rating": 0,
        "missing_google_reviews": 0,
        "missing_thumbnails": 0,
        "missing_details": []
    }

    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            integrity_report["total_count"] += 1
            issues = []
            
            # Check Google Rating
            g_rating = row.get("Google_Rating", "").strip()
            if not g_rating or g_rating == "0" or g_rating == "0.0":
                integrity_report["missing_google_rating"] += 1
                issues.append("Google Rating Missing")
            
            # Check Google Reviews
            g_reviews = row.get("Google_Review_Count", "").strip()
            if not g_reviews or g_reviews == "0":
                integrity_report["missing_google_reviews"] += 1
                issues.append("Google Reviews Missing")
                
            # Check Thumbnail
            thumb = row.get("Thumbnail_URL", "").strip()
            if not thumb or thumb == "N/A":
                integrity_report["missing_thumbnails"] += 1
                issues.append("Thumbnail Missing")
            
            if issues:
                integrity_report["missing_details"].append({
                    "name": row.get("Restaurant_Name", "Unknown"),
                    "city": row.get("Target_City_Region", "Unknown"),
                    "issues": issues,
                    "tabelog_url": row.get("Tabelog_URL", "")
                })

    return integrity_report

if __name__ == "__main__":
    report = check_integrity()
    print(json.dumps(report, indent=2, ensure_ascii=False))
