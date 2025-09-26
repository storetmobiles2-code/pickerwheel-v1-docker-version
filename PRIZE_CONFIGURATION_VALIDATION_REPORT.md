# Prize Configuration Validation Report
**Generated:** September 26, 2025 at 08:13 UTC

## Overview
This report validates prize configurations across three systems:
1. `itemlist_dates_v2.txt` (master configuration)
2. Daily CSV files in `daily_csvs/` directory
3. SQLite database (`pickerwheel_contest.db`)

## 1. Overall Statistics
- Total dates in CSVs: 40
- Total dates in Database: 40
- Total items in v2 config: 21

## 2. Item Availability by Date

| Date | Items in CSV | Items in DB | Match? |
|------|--------------|-------------|--------|
| 2025-09-21 | 6 | 6 | ✅ |
| 2025-09-22 | 8 | 8 | ✅ |
| 2025-09-23 | 10 | 10 | ✅ |
| 2025-09-24 | 7 | 7 | ✅ |
| 2025-09-25 | 6 | 6 | ✅ |
| 2025-09-26 | 6 | 6 | ✅ |
| 2025-09-27 | 6 | 6 | ✅ |
| 2025-09-28 | 7 | 7 | ✅ |
| 2025-09-29 | 8 | 8 | ✅ |
| 2025-09-30 | 7 | 7 | ✅ |
| 2025-10-01 | 10 | 10 | ✅ |
| 2025-10-02 | 13 | 13 | ✅ |
| 2025-10-03 | 6 | 6 | ✅ |
| 2025-10-04 | 7 | 7 | ✅ |
| 2025-10-05 | 6 | 6 | ✅ |
| 2025-10-06 | 6 | 6 | ✅ |
| 2025-10-07 | 7 | 7 | ✅ |
| 2025-10-08 | 6 | 6 | ✅ |
| 2025-10-09 | 6 | 6 | ✅ |
| 2025-10-10 | 6 | 6 | ✅ |
| 2025-10-11 | 6 | 6 | ✅ |
| 2025-10-12 | 6 | 6 | ✅ |
| 2025-10-13 | 6 | 6 | ✅ |
| 2025-10-14 | 7 | 7 | ✅ |
| 2025-10-15 | 6 | 6 | ✅ |
| 2025-10-16 | 6 | 6 | ✅ |
| 2025-10-17 | 6 | 6 | ✅ |
| 2025-10-18 | 8 | 8 | ✅ |
| 2025-10-19 | 8 | 8 | ✅ |
| 2025-10-20 | 11 | 11 | ✅ |
| 2025-10-21 | 13 | 13 | ✅ |
| 2025-10-22 | 8 | 8 | ✅ |
| 2025-10-23 | 7 | 7 | ✅ |
| 2025-10-24 | 6 | 6 | ✅ |
| 2025-10-25 | 6 | 6 | ✅ |
| 2025-10-26 | 6 | 6 | ✅ |
| 2025-10-27 | 6 | 6 | ✅ |
| 2025-10-28 | 7 | 7 | ✅ |
| 2025-10-29 | 6 | 6 | ✅ |
| 2025-10-30 | 6 | 6 | ✅ |

## 3. Special Items Distribution

| Item | Expected Dates | CSV Dates | DB Dates | Match? |
|------|----------------|------------|-----------|--------|
| washing machine | 2025-09-28, 2025-10-20 | 2025-09-28, 2025-10-20 | 2025-09-28, 2025-10-20 | ✅ |
| Budget Smartphone | 2025-09-23 | 2025-09-23 | 2025-09-23 | ✅ |
| Smart Tv 32 inches | 2025-10-20 | 2025-10-20 | 2025-10-20 | ✅ |
| silver coin | 2025-09-22, 2025-10-01, 2025-10-21 | 2025-09-22, 2025-10-01, 2025-10-21 | 2025-09-22, 2025-10-01, 2025-10-21 | ✅ |
| refrigerator | 2025-10-02 | 2025-10-02 | 2025-10-02 | ✅ |
| aircooler | 2025-10-01, 2025-10-21 | 2025-10-01, 2025-10-21 | 2025-10-01, 2025-10-21 | ✅ |
| Mi smart speaker | 2025-09-23 | 2025-09-23 | 2025-09-23 | ✅ |
| intex home theatre | 2025-09-23 | 2025-09-23 | 2025-09-23 | ✅ |

## 4. Common Items Verification

| Item | Config | CSV | DB | Match? |
|------|---------|-----|----|----|
| smartwatch + mini cooler | * | 40 days | 40 days | ✅ |
| power bank + neckband | * | 40 days | 40 days | ✅ |
| luggage bags | * | 40 days | 40 days | ✅ |
| Free pouch and screen guard | * | 40 days | 40 days | ✅ |
| Dinner Set | * | 40 days | 40 days | ✅ |
| Earbuds and G.Speaker | * | 40 days | 40 days | ✅ |

## Key Findings

### Notable Dates:
- **Sep 23:** 10 items (includes MI smart speaker, Intex home theatre, Budget Smartphone)
- **Oct 02:** 13 items
- **Oct 20:** 11 items (includes washing machine)
- **Oct 21:** 13 items

### Key Item Verification:
1. **MI smart speaker:** Available only on Sep 23 ✓
2. **Intex home theatre:** Available only on Sep 23 ✓
3. **Budget Smartphone:** Available only on Sep 23 ✓
4. **Washing Machine:** Available on Sep 28 and Oct 20 ✓

## Conclusion
The validation confirms that all prize configurations are correctly synchronized across all three systems. Each item appears on its designated dates with the correct properties (category, quantity, daily limit, and emoji). No discrepancies were found between the master configuration, CSV files, and database records.
