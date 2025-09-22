# PickerWheel Contest System v4 - Complete Documentation

## System Overview
The PickerWheel Contest v4 is a server-authoritative spin-to-win contest system designed for myT MOBILES. It features a database-backed 2-month event system running from September 21 to November 21, 2025, with smart backend logic that handles prize availability and distribution.

### Key Architecture Principles
1. **Frontend Simplicity**: All 22 prizes always visible on wheel, no availability messages
2. **Backend Intelligence**: Smart prize selection with fallback logic
3. **Asset Reuse**: Migrated existing logos, sounds, animations, celebration effects
4. **Even Wheel Slices**: 360°/22 = 16.36° per segment, always consistent
5. **Persistent Storage**: SQLite database with proper 2-month event tracking

### Prize Categories
- **Ultra Rare (6)**: Smart TV, Silver Coin, Refrigerator, Washing Machine, Air Cooler, Soundbar
- **Rare (8)**: Dinner Set, Jio Tab, Home Theatres, Speaker, Gas Stove, Mixer, Mobile
- **Common (8)**: 5 combo items + 3 singles (unlimited availability)

## System Architecture

### Backend Components
- **Flask API**: RESTful API for prize selection and management
- **SQLite Database**: Persistent storage for prizes, inventory, and user spins
- **CSV Configuration**: Prize definitions with availability dates and quantities
- **Server-Authoritative Logic**: Backend decides prize outcomes

### Frontend Components
- **Responsive UI**: Works on mobile and desktop devices
- **Interactive Wheel**: Animated spinning wheel with dynamic prize segments
- **Admin Interface**: Dashboard for monitoring and management
- **Database Manager**: Interface for database operations and CSV management

### Security Features
- **Admin Authentication**: Password-protected admin access
- **HMAC Signatures**: Prevents tampering with spin results
- **Idempotency Keys**: Prevents duplicate prize claims
- **TTL Reservations**: Time-limited prize reservations

## Key System Features

### Server-Authoritative Prize Selection
The backend determines which prize a user will win before the wheel is spun. The frontend wheel animation is synchronized to land on the predetermined prize, ensuring fairness and preventing client-side manipulation.

### Dynamic Prize Availability
Prizes are configured with:
- Total quantity limits
- Daily quantity limits
- Specific available dates

The system enforces these limits while maintaining a seamless user experience.

### Prize Weighting System
- Common items: 1x weight (baseline)
- Rare items: 5x weight (5 times more likely than baseline)
- Ultra-rare items: 8x weight (8 times more likely than baseline)

### Fallback Logic
If a selected prize is unavailable (out of stock or daily limit reached), the system will:
1. Try another prize in the same category
2. Fall back to a prize in a lower category
3. Always ensure the user wins something

### Admin Tools
- **Statistics Dashboard**: Real-time contest statistics
- **Inventory Management**: Monitor and replenish prize inventory
- **Database Manager**: Manage database operations and CSV configuration
- **System Verifier**: Comprehensive system verification tool

## Technical Implementation

### Database Schema
- **prizes**: Prize definitions and metadata
- **prize_inventory**: Daily prize availability and quantities
- **prize_wins**: Record of all prize wins
- **prize_reservations**: Temporary prize reservations

### API Endpoints
- **/api/prizes/available**: Get available prizes for today
- **/api/prizes/wheel-display**: Get all prizes for wheel display
- **/api/spin/reserve**: Reserve a prize before spinning
- **/api/spin/claim**: Claim a reserved prize
- **/api/admin/...**: Various admin endpoints

### CSV Configuration
The system uses a CSV file to define prizes with the following columns:
- Item/Combo Name: Name of the prize
- Category: common, rare, or ultra_rare
- Total Quantity: Total available quantity
- Daily Limit: Maximum wins per day
- Available Dates: Specific dates or date ranges when available

## System Verification
The system includes a comprehensive verification tool that checks:
1. Database Connection
2. Prize Availability
3. CSV Configuration
4. Inventory Status
5. Daily Limits
6. Server-Authoritative Wheel
7. Dynamic Prize Count

## Maintenance and Troubleshooting

### Common Operations
- **Start Server**: `./scripts/start-server.sh`
- **Stop Server**: `./scripts/stop-server.sh`
- **Reset Database**: Use Database Manager interface
- **Update CSV**: Use CSV editor in Database Manager

### Troubleshooting
- **Prize Availability Issues**: Check CSV configuration and inventory
- **Wheel Animation Issues**: Verify wheel.js version and browser compatibility
- **Database Errors**: Use Database Manager to check database integrity

## Security Considerations
- Admin password should be changed from default "myTAdmin2025"
- CSV configuration should be backed up regularly
- Database should be backed up daily during the contest period
