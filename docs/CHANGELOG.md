# PickerWheel Contest v4 - Changelog

## September 22, 2025 - Major Update

### Fixed Issues

#### 1. Daily Limit Enforcement
- Fixed issue with rare and ultra-rare items exceeding daily limits
- Moved win record insertion after daily limit check in `finalize_prize` method
- Added proper filtering in `get_available_prizes` to exclude prizes that have reached their daily limits
- Added fallback mechanism in prize selection algorithm

#### 2. Prize Selection Algorithm
- Simplified algorithm to use category-based weighting
- Added proper error handling to prevent crashes
- Removed complex distribution calculations that were causing errors
- Increased chance of rare and ultra-rare items to ensure fair distribution
- Boosted weighting for rare items (5x) and ultra-rare items (8x)
- Increased selection probability for rare and ultra-rare items to 50%

#### 3. Wheel Positioning Logic
- Fixed critical issue with hardcoded sector calculation (23 segments)
- Updated to use dynamic prize count instead of hardcoded value
- Ensures wheel lands on correct prize when number of prizes changes

#### 4. CSV Format and Handling
- Simplified CSV format to include only essential fields
- Updated CSV parsing logic to handle the simplified format
- Ensured database and CSV stay in sync

#### 5. Error Handling
- Added proper error handling in the stats endpoint
- Fixed the per_day_limit column issue in the database schema
- Added graceful fallbacks for missing tables or columns

### New Features

#### 1. Admin Testing Tools
- Added `force_prize_id` parameter to the admin test-spin endpoint
- Created comprehensive test scripts for verifying daily limits
- Added test_prize_distribution.py for analyzing prize distribution

#### 2. System Management
- Created robust start and stop scripts
- Added backup functionality
- Organized scripts into logical directories

### Code Cleanup
- Removed duplicate and backup files
- Organized scripts into admin and utils directories
- Updated documentation to reflect changes

## September 21, 2025 - Initial Release

### Features
- Database-backed 2-month event system (Sep 21 - Nov 21, 2025)
- Smart backend logic that handles all complexity
- Server-authoritative wheel positioning
- Prize availability based on CSV configuration
- Admin panel for system management
