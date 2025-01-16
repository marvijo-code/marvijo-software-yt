# Changelog

## [Unreleased]
- Updated Vite configuration to properly read port from .env file
- Updated API port to 5501
- Fixed tailwind configuration to use ES modules syntax with dynamic imports
- Fixed screen blur issue after closing betslip by properly cleaning up backdrop effects
- Fixed ViewMatchComponent to use correct prop name 'match' instead of undefined 'matchData'
- Added null check in ViewMatchComponent to prevent undefined property access errors 
- Fixed prop name mismatch in ViewMatchComponent (match -> matchData) to correctly display matches 
- Restored showOnlyTips prop in ViewMatchComponent that was accidentally removed during refactoring 
- Changed betslip to slide up from bottom with pull-down-to-close gesture 
- Fixed YouTube iframe controls not being clickable by adjusting z-index and pointer events 
- Fixed YouTube iframe click positioning for accurate control interaction 
- Improved betslip pull-down gesture by moving it to MobileBetSlip component 
- Fixed linter errors in BetSlipComponent and simplified code structure 
- Enhanced mobile search auto-focus behavior with delayed focus and focus retention 
- Improved mobile search functionality to only show tournament groups with matches that match the search query 
- Added new `/api/news/{matchId}` endpoint to fetch match-related news using Serper and Crawl4AI 

### Changed
- Switched from Crawl4ai to Microsoft.Playwright for web scraping in NewsService
- Improved content extraction with multiple selectors for better news article detection
- Removed Docker container dependency for web scraping 