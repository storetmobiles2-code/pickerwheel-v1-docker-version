# 🔧 Validation Scripts - Usage Guide

## Primary Scripts

### 1. **validate_and_update_prizes.py** ✅ RECOMMENDED
**Purpose:** Complete validation, CSV generation, and database update

**What it does:**
- ✅ Parses `itemlist_dates.txt`
- ✅ Checks for duplicate items
- ✅ Shows unique item count (after deduplication)
- ✅ Generates all daily CSV files
- ✅ Updates database
- ✅ Cleans up old CSV files

**Usage:**
```bash
python3 scripts/validate_and_update_prizes.py
```

**When to use:**
- After editing `itemlist_dates.txt`
- When updating prize lists
- To regenerate all CSVs and database
- For complete system validation

---

### 2. **verify_admin_data.py**
**Purpose:** Quick verification of current system state

**What it does:**
- ✅ Checks itemlist configuration
- ✅ Verifies CSV files exist
- ✅ Checks database status
- ✅ Shows deduplication info
- ✅ Provides admin panel access info

**Usage:**
```bash
python3 scripts/verify_admin_data.py
```

**When to use:**
- To verify system status
- Before starting the application
- After updates to check everything is synced
- For quick health checks

---

## Understanding the Numbers

### Total Items vs Unique Items

**Example from current configuration:**
```
itemlist_dates.txt:
- 9 common items
- 21 rare items
- Total: 30 items

Dual-availability items (appear in both):
- 8 items (e.g., "Boat smartwatch" as common AND rare)

After deduplication:
- Unique items: 22
- Wheel displays: 22 segments
```

### Why Deduplication?

Some items appear in **both** common and rare categories:
- **Common:** Available for win every day
- **Rare:** Special bonus on specific dates

The wheel shows each item **only once** (deduplicated) but the backend controls when they can be won based on the date.

---

## System Architecture

```
itemlist_dates.txt (30 items)
         ↓
   CSV Generation
         ↓
daily_csvs/*.csv (30 items each)
         ↓
Backend API /api/prizes/wheel-display
         ↓
  Deduplication Logic
         ↓
Frontend Wheel (22 unique segments)
```

---

## File Locations

- **Config:** `/itemlist_dates.txt`
- **CSVs:** `/daily_csvs/prizes_YYYY-MM-DD.csv`
- **Database:** `/backend/pickerwheel_contest.db`
- **Scripts:** `/scripts/`

---

## Deprecated Scripts

### ❌ update_csvs_from_v2.py
**Status:** DEPRECATED  
**Replaced by:** `validate_and_update_prizes.py`

This script is kept for backward compatibility but should not be used for new updates.

---

## Quick Commands

**Full update after editing itemlist_dates.txt:**
```bash
python3 scripts/validate_and_update_prizes.py
```

**Quick verification:**
```bash
python3 scripts/verify_admin_data.py
```

**Check specific CSV file:**
```bash
head daily_csvs/prizes_2025-10-15.csv
```

**Count items in CSV:**
```bash
wc -l daily_csvs/prizes_2025-10-15.csv
```

---

## Troubleshooting

### Issue: Wheel shows duplicates
**Solution:** Backend deduplication is automatic. If you see duplicates, check browser console for errors.

### Issue: Database not updating
**Solution:** Run `validate_and_update_prizes.py` which clears and rebuilds the database.

### Issue: CSV files missing
**Solution:** Run `validate_and_update_prizes.py` to regenerate all CSV files.

### Issue: Wrong item count
**Solution:** 
1. Check `itemlist_dates.txt` for correct items
2. Run `validate_and_update_prizes.py`
3. Verify with `verify_admin_data.py`

---

## Expected Output

**After running validate_and_update_prizes.py:**
```
✅ Total items in config: 30 (9 common + 21 rare)
✅ Unique items (deduplicated): 22
✅ Dual-availability items: 8
✅ CSV files: 22 files with 30 items each
✅ Wheel display: 22 unique segments
✅ Database updated with 30 prizes

📌 Backend automatically deduplicates 30 → 22 for wheel display
```

This is **normal and correct** - the system is designed to handle dual-availability items automatically.

---

**Last Updated:** October 15, 2025


