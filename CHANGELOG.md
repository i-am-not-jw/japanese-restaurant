# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2026-02-27

### Added
- **Automated CSV Review**: Added `--auto` mode in `publish_from_csv.py` to detect remaining Japanese text before uploading.
- **Tag Color Standardization**: Implemented automatic Notion tag color synchronization by category (Badges, Cuisine, Location, Payment).
- **Orchestrator Integration**: `daily_orchestrator.py` now automatically attempts to publish data if it passes the Japanese detection check.
- **Webhook Status Page**: Added a simple auto-closing success page for browser-triggered webhooks.

### Improved
- **Path Handling**: Updated all scripts to use relative paths or unified `/tmp` storage for better portability after directory renaming.
- **AI Rescue Logic**: Enhanced Gemini fallbacks for railway line translation and station info cleaning.

### Fixed
- **Environment Issues**: Corrected virtual environment dependencies for `flask` and `python-dotenv`.
- **Notion API Limits**: Optimized tag sync logic to respect Notion's 100-option limit for multi-select properties.

## [1.0.0] - 2026-02-15
- Initial release of the Japan Restaurant Scraper pipeline.
- Cross-platform validation between Tabelog and Google Maps.
- AI-driven review summarization and translation.
- Basic Notion database publishing.
