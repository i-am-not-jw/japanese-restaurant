# Technical Design: Japan Restaurant Discovery Workflow

This document details the strategy for collecting data from restricted SNS platforms.

## 1. Social Media Data Collection Strategy

| Platform | Difficulty | Strategy |
| :--- | :--- | :--- |
| **Instagram** | High | Use Google Search with `site:instagram.com` + Japanese keywords to find recent public posts. |
| **TikTok** | High | Use `site:tiktok.com` search or specific "Trending restaurants in [City]" keyword aggregation. |
| **X (Twitter)** | Medium | Use `site:x.com` search filtered by "last 7 days" or Search APIs if available. |
| **Threads** | Medium | Use `site:threads.net` search. |
| **YouTube** | Low | Use YouTube Data API or `site:youtube.com` search for "Vlog" or "Gourmet" titles. |

### Keyword Engineering (Japanese)
To find "locals' favorites", we avoid "Must eat in Tokyo" (tourist keywords).
- `地元の人しか知らない` (Only locals know)
- `観光客がいない` (No tourists)
- `教えたくない` (Don't want to tell anyone - common Japanese expression for gems)

## 2. Tabelog Cross-Reference Schema
Once a restaurant name is identified:
1. Search Google for `[Restaurant Name] tabelog`.
2. Extract the URL.
3. Fetch:
    - **Score**: Target > 3.5.
    - **Review Count**: > 100 for reliability.
    - **Demographics**: Check if reviews are mostly in Japanese.

## 3. Weekly Automation (Scheduling)
GitHub Actions를 사용하며 두 워크플로우 모두 수동 트리거로만 실행된다.

- **collect workflow** (`.github/workflows/collect.yml`): 수집 파이프라인 실행 → `data/staged_restaurants.csv` 커밋
- **publish workflow** (`.github/workflows/publish.yml`): 수동 트리거 — human review 완료 후 실행하여 Notion에 업로드

## 4. Dependencies
- `python3`
- `playwright` (for browser automation)
- `beautifulsoup4`
- `python-dotenv`
