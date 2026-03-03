import csv
import os

path = '/tmp/japanese_restaurant_data/staged_restaurants.csv'
out_path = '/tmp/japanese_restaurant_data/staged_restaurants_fixed.csv'

regions = [
    '도쿄', '오사카', '교토', '홋카이도', '가나가와', '아이치', '후쿠오카', '효고', '치바', '사이타마', '오키나와', 
    '히로시마', '시즈오카', '가고시마', '가가와', '구마모토', '미야기', '나가노', '이시카와', '하코다테'
]

def fix_csv():
    if not os.path.exists(path):
        print("Source CSV not found.")
        return

    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    header = lines[0].strip()
    data_lines = lines[1:]

    records = []
    current_record = ""

    for line in data_lines:
        # Check if line starts a new record
        is_start = any(line.startswith(r + ',') for r in regions)
        
        if is_start:
            if current_record:
                records.append(current_record.strip())
            current_record = line
        else:
            current_record += line
            
    if current_record:
        records.append(current_record.strip())

    print(f"Detected {len(records)} records from {len(lines)} lines.")

    # Now parse and re-write using csv.writer to ensure proper quoting
    with open(out_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header.split(','))
        
        for rec in records:
            # We need to split the record into exactly 15 fields.
            # However, since the internal content might have commas and mismatched quotes, 
            # we will try a greedy approach:
            # 1. Target_City_Region (Known)
            # 2. Restaurant_Name
            # 3. Tabelog_Rating
            # 4. Google_Rating
            # 5. Generated_Tags
            # --- The problematic part starts here ---
            # 6. AI_Review_Summary
            # 7. AI_Opening_Hours
            # ... and the rest (Station_Info, counts, date, Address, URLs, etc.)
            
            # Since splitting correctly is hard without a parser, we'll use a simpler trick:
            # Most trailing fields are URLs or numbers or short strings.
            # Let's just try to parse it with csv.reader on the single multi-line string.
            
            try:
                parsed = list(csv.reader([rec]))[0]
                if len(parsed) >= 15:
                    writer.writerow(parsed[:15])
                else:
                    # Fallback for failed parsing: split by commas but handle quotes manually
                    print(f"  [WARN] Parsing failed or incomplete for: {rec[:50]}...")
                    writer.writerow([rec]) # Fallback as 1 field
            except Exception as e:
                 print(f"  [ERROR] {e}")

    # Replace original with fixed
    os.rename(out_path, path)
    print(f"Successfully fixed CSV: {path}")

if __name__ == "__main__":
    fix_csv()
