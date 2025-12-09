# Changelog

All notable changes to ludolog are documented here.

## [1.2.0] - 2025-06-12

### Added
- BG Stats CSV import and BGG collection XML/JSON import
- Recurring game night scheduler with venue defaults
- HTTP read-only server for collection and recent plays
- Goals tracking (play N times, try new games, win rate targets)
- Stats: most played, win rates, games fitting a time slot
- Plugin hook for custom report formatters

### Changed
- Schema version 3 adds shelves, venues, and recurring nights
- Search ranks by title, designer, and mechanic overlap

### Fixed
- Atomic save on Windows when target file is open elsewhere
- Scoreboard tie-break when multiple players share high score

## [1.1.0] - 2025-03-01

### Added
- Excel export for play history
- Season summaries and timeline view
- Shelf assignment for physical organization

## [1.0.0] - 2024-11-15

Initial release: JSON journal, CLI, CSV import/export, basic reports.
