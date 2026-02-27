# Routine Collection SOP (Standard Operating Procedure)

## Goal
Automate the discovery and data curation of top trending Japanese restaurants across major cities into a Notion database, ensuring 100% data quality via a staged human-review loop and AI fallback translations.

## The 2-Step Orchestration Process
The collection pipeline is split into a "Staging" step and a "Publishing" step. 
This prevents compounding errors (like bad AI translations or missing APIs) from polluting the live Notion database.

### Step 1: Extraction & Staging
**Command:** `python3 execution/daily_orchestrator.py`
**What it does:**
1. Sequences through 8 major Japanese cities (Tokyo, Kanagawa, Osaka, Aichi, Hokkaido, Fukuoka, Hyogo, Kyoto).
2. Scrapes `tabelog_lookup.py` to get trending restaurants, addresses, ratings, and un-translated Japanese station info.
3. Translates Japanese station info deterministically using a local dictionary (`custom_stations_ko.json`) and the Wikipedia API. As a final fallback layer, it calls the Gemini API to rescue completely untranslatable station strings, completely avoiding manual user translations.
4. Curates review counts and backup ratings via `google_maps_lookup.py`.
5. Uses Gemini to translate operating hours and summarize restaurant reviews.
6. Dumps the fully translated and enriched data payload into `.tmp/staged_restaurants.csv`.

### Step 2: Human Review & Publishing
**Command:** `python3 execution/publish_from_csv.py`
**What it does:**
1. The AI Assistant/Orchestrator pauses and notifies the user to inspect the `staged_restaurants.csv` file in their spreadsheet software.
2. The user glances at the CSV for 10 seconds to verify that tags, AI summaries, and translated station names look correct without needing to manually copy/paste Japanese text.
3. The user replies "approved" or manually triggers the publish command.
4. `publish_from_csv.py` pulls the rows from the CSV, matches them with the Notion API payload architecture, and Upserts (creates or updates based on the unique Tabelog URL) the items directly into the Notion Database.

## Error Handling & Rate Limits
- **Gemini API Limits (HTTP 429)**: The scripts (`tabelog_lookup` and `export_to_csv`) are programmed to gracefully exit `sys.exit(429)` if Gemini's Free Tier limits are reached.
- **Missing Wikipedia Translations**: Found inside `tabelog_lookup.py`, logged as `[WARNING]`, translated by Gemini, and recorded into the cache. Users can permanently map these to strings in `custom_stations_ko.json` if needed.
