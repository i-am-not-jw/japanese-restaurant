# Changelog

All notable changes to this project will be documented in this file.

## [1.2.0] - 2026-03-02

### Added
- **Dropdown-based Filtering**: Refactored the web map filter system into hierarchical dropdowns (Region > Sub-region) for better organization.
- **Regional CSV Export**: Added automatic partitioning of restaurant data into regional CSVs (Tokyo, Osaka, etc.) in the `exports/` folder.
- **Improved UI**: Implemented teardrop markers (32px) and glassmorphism styling for a more premium, modern aesthetic.

### Improved
- **Data Purity**: Switched back to pure Japanese naming for restaurants to preserve original Tabelog brand identity.
- **Responsive Layout**: Optimized the filter bar and info panel for better accessibility across different screen sizes.

### Fixed
- **Name Corruption**: Identified and removed aggressive normalization logic that caused Japanese/Korean character merging (e.g., `は야부사`).
- **UI Overlap**: Disabled default Google Maps UI controls to prevent interference with the custom glassmorphism overlay.

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
