# SOP: Japan Local Restaurant Discovery

## Goal
Identify restaurants in Japan that are currently popular among locals (not just tourists) and have high quality ratings.

## Frequency
Every Monday at 00:00.

## Inputs
- SNS Platforms: Instagram, Threads, TikTok, YouTube, X (Twitter)
- Target Regions: Tokyo, Osaka, Kyoto (Expandable)
- Search Period: Last 7 days

## Workflow Steps

### 1. Social Media Scanning
- Use `execution/sns_scanner.py` to search for trending hashtags and keywords in Japanese.
- **Keywords**:
    - `東京 グルメ` (Tokyo Gourmet)
    - `地元の人に人気` (Popular with locals)
    - `穴場スポット` (Hidden gems)
    - `リピ確定` (Definitely visiting again)
- **Output**: A list of restaurant names or locations mentioned frequently.

### 2. Frequency Filtering
- Aggregate results and identify restaurants mentioned more than 3 times across all platforms.

### 3. Tabelog Cross-reference
- Use `execution/tabelog_lookup.py` for each candidate restaurant.
- **Requirement**: Tabelog score >= 3.5.
- **Avoid**: Restaurants with generic names or those located inside major tourist landmarks unless the review text explicitly mentions local popularity.

### 4. Report Generation
- Create a summary report in `.tmp/report_<DATE>.md`.
- Include: Restaurant Name, SNS Mentions, Tabelog Score, Budget, Map Link.

## Edge Cases
- **No results**: If no restaurants meet the threshold, expand search keywords to include specific cuisines (e.g., `寿司`, `焼肉`).
- **Tabelog block**: If Tabelog blocks automated lookup, fallback to manual checking notification.
