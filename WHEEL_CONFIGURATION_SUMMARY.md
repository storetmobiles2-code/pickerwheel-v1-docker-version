# 🎡 PickerWheel Configuration Summary

**Generated:** October 14, 2025  
**Configuration File:** `itemlist_dates.txt`  
**CSV Files:** 22 daily files (Oct 15 - Nov 5, 2025)

---

## ✅ Validation Results

- **Total Items:** 22
- **Unique Items:** 22
- **Duplicates:** 0 ✅
- **Common Items:** 1 (available every day)
- **Rare Items:** 21 (date-specific)

---

## 📊 All Unique Items (Alphabetically)

1. Air Cooler
2. Boat Smartwatch
3. Boult 60W Soundbar
4. Defy Buds + Screen Guard
5. Dinner Set
6. Free Pouch and Screen Guard
7. Gas Stove
8. Intex Home Theatre
9. Jio Tab
10. Luggage Bag
11. Mi Smart Speaker
12. Mixer Grinder
13. Power Bank + Neckband
14. Pressure Cooker
15. Refrigerator
16. Silver Coin
17. Skull Candy Earphones + Selfie Stick
18. Smart TV 32 Inches
19. Washing Machine
20. Zebronics Astra BT Speaker
21. Zebronics BT Astra Speaker (common item)
22. Zebronics Home Theatre

---

## 🎯 Common Items (Available Every Day)

| Item | Category | Quantity | Daily Limit | Emoji |
|------|----------|----------|-------------|-------|
| zebronics bt astra speaker | Common | 15 | 2 | 🔊 |

**This item appears on the wheel EVERY day from Oct 15 - Nov 5**

---

## 🌟 Rare Items Schedule (One Special Prize Per Day)

Each day features ONE special rare item along with the common item:

| Date | Rare Item | Quantity | Daily Limit | Emoji |
|------|-----------|----------|-------------|-------|
| **Oct 15** | *(none - only common item)* | - | - | - |
| **Oct 16** | BOAT SMARTWATCH | 3 | 1 | ⌚ |
| **Oct 17** | DEFY BUDS + SCREEN GUARD | 3 | 1 | 🎧 |
| **Oct 18** | POWER BANK + NECKBAND | 5 | 1 | 🔋 |
| **Oct 19** | DINNER SET | 3 | 1 | 🍽️ |
| **Oct 20** | JIO TAB | 2 | 1 | 📱 |
| **Oct 21** | INTEX HOME THEATRE | 2 | 1 | 🎭 |
| **Oct 22** | ZEBRONICS HOME THEATRE | 2 | 1 | 🎭 |
| **Oct 23** | MI SMART SPEAKER | 2 | 1 | 🔊 |
| **Oct 24** | ZEBRONICS ASTRA BT SPEAKER | 3 | 1 | 🔊 |
| **Oct 25** | SMART TV 32 INCHES | 1 | 1 | 📺 |
| **Oct 26** | LUGGAGE BAG | 3 | 1 | 🧳 |
| **Oct 27** | SILVER COIN | 2 | 1 | 🪙 |
| **Oct 28** | REFRIGERATOR | 1 | 1 | 🧊 |
| **Oct 29** | WASHING MACHINE | 1 | 1 | 🧺 |
| **Oct 30** | AIR COOLER | 2 | 1 | ❄️ |
| **Oct 31** | BOULT 60W SOUNDBAR | 2 | 1 | 🔊 |
| **Nov 1** | PRESSURE COOKER | 3 | 1 | 🍳 |
| **Nov 2** | GAS STOVE | 2 | 1 | 🔥 |
| **Nov 3** | MIXER GRINDER | 3 | 1 | 🥤 |
| **Nov 4** | FREE POUCH AND SCREEN GUARD | 3 | 1 | 📱 |
| **Nov 5** | SKULL CANDY EARPHONES + SELIE STICK | 3 | 1 | 🎧 |

---

## 🎡 What Users Will See on the Wheel

### Today (Oct 15, 2025)
The wheel will show:
1. **zebronics bt astra speaker** (Common) 🔊

### Oct 16, 2025
The wheel will show:
1. **zebronics bt astra speaker** (Common) 🔊
2. **BOAT SMARTWATCH** (Rare) ⌚

### Oct 25, 2025 (Example)
The wheel will show:
1. **zebronics bt astra speaker** (Common) 🔊
2. **SMART TV 32 INCHES** (Rare) 📺

---

## 📁 Generated Files

### Daily CSV Files
All CSV files have been generated in `daily_csvs/`:
- ✅ prizes_2025-10-15.csv (1 item)
- ✅ prizes_2025-10-16.csv (2 items)
- ✅ prizes_2025-10-17.csv (2 items)
- ... (continues through Nov 5)

### Old Files Cleaned Up
- Removed 24 old CSV files from September - October 14

---

## ⚙️ Configuration Details

### Item Categories
- **Common:** Available every day, higher quantity, higher daily limit
- **Rare:** Available on specific dates only, limited quantity, limit 1 per day

### Quantity Levels
- **Ultra Rare (TV, Refrigerator, Washing Machine):** 1 item
- **Rare Electronics:** 2 items
- **Standard Rare:** 3 items
- **Popular Rare:** 5 items
- **Common:** 15 items

### Daily Limits
- **Rare Items:** 1 win per day
- **Common Items:** 2 wins per day

---

## 🔧 Scripts Used

1. **validate_and_update_prizes.py** - Validates itemlist, checks duplicates, generates CSVs
2. **Backend API** - Loads daily CSVs to serve prizes to the wheel

---

## 📝 Notes

1. **No Duplicates:** All items are unique - no overlap between common and rare
2. **One Common Item:** Only the zebronics bt astra speaker is available every day
3. **Daily Rotation:** Each day from Oct 16 onwards features one special rare item
4. **Database:** Database uses a different schema (category_id instead of category column), so CSV-based approach is recommended

---

## 🚀 Next Steps

If you want to add more common items (items available every day), update `itemlist_dates.txt`:
- Add items to the "# Common Items" section
- Set `Available Dates` to `*` for daily availability
- Run `python3 scripts/validate_and_update_prizes.py` to regenerate CSVs

If you want to adjust rare item dates:
- Update the specific date in the `Available Dates` column
- Run the validation script again

---

**Status:** ✅ Ready for deployment

