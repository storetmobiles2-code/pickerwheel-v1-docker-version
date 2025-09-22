# PickerWheel Contest - Business Rules & Logic

## 🎯 Prize Categories & Rules

### **Ultra Rare Items**
- ✅ **Limited Availability**: Only on specific dates (never "*")
- ✅ **Very Low Quantity**: Maximum 2 items per date
- ✅ **One Per User Per Day**: User can win max 1 rare/ultra-rare per day
- ✅ **Exhaust & Done**: When inventory is consumed, no more available
- ✅ **Examples**: Smart TV, Refrigerator, Silver Coin

### **Rare Items**
- ✅ **Limited Availability**: Only on specific dates (never "*")
- ✅ **Low Quantity**: Maximum 5 items per date
- ✅ **One Per User Per Day**: User can win max 1 rare/ultra-rare per day
- ✅ **Exhaust & Done**: When inventory is consumed, no more available
- ✅ **Examples**: Gas Stove, Mixer Grinder, Jio Tab

### **Common Items**
- ✅ **Always Available**: Can use "*" for all contest dates
- ✅ **Higher Quantity**: 5-15 items per date (unlimited)
- ✅ **Multiple Per User**: No daily limits
- ✅ **Unlimited Restocking**: Can be replenished anytime
- ✅ **Examples**: Power Bank + Neckband, Bluetooth Speaker

## 🔒 User Restrictions

### **Daily Limits**
- **Rare/Ultra-Rare**: Maximum 1 per user per day (combined)
- **Common**: No limits

### **Fallback Logic**
1. User spins wheel → lands on Ultra Rare item
2. System checks: Has user won rare/ultra-rare today?
3. If YES → Automatically fallback to Common items only
4. If NO → Check inventory availability
5. If available → Award the prize
6. If not available → Fallback to similar category

## 🗄️ Database Schema (Current)

### **Tables Used**
```sql
prize_categories (id, name, display_name, weight)
├── 1: ultra_rare
├── 2: rare  
└── 3: common

prizes (id, name, category_id, type, emoji, weight, description)
├── Links to prize_categories via category_id

prize_inventory (prize_id, event_id, available_date, initial_quantity, remaining_quantity)
├── Tracks quantities per date per prize

prize_wins (prize_id, user_identifier, win_date, win_timestamp)
├── Records all wins for tracking limits
```

## 🎮 Admin Interface Rules

### **Smart Category Auto-Adjustment**
The system automatically adjusts categories based on quantity and availability:

**Auto-Adjustment Logic:**
- **"*" (Always Available)** → Automatically becomes `Common`
- **Limited Dates + Quantity ≤2** → Automatically becomes `Ultra Rare`
- **Limited Dates + Quantity 3-5** → Automatically becomes `Rare`
- **Limited Dates + Quantity >5** → Automatically becomes `Common`

### **Real-Time Suggestions**
- **Live Preview**: Shows suggested category as you type
- **Smart Hints**: Explains why a category is suggested
- **Auto-Update**: Form updates category automatically when needed

### **Prize Creation Validation**
- **Ultra Rare**: 
  - Cannot use "*" for availability
  - Max 2 quantity per date
  - Must specify exact dates
  
- **Rare**:
  - Cannot use "*" for availability  
  - Max 5 quantity per date
  - Must specify exact dates
  
- **Common**:
  - Can use "*" for always available
  - 5-15 recommended quantity per date
  - No date restrictions

### **Business Logic Enforcement**
- **Frontend**: Real-time suggestions and auto-adjustment
- **Backend**: Double-validation with auto-correction
- **Clear Messages**: Explains all adjustments and validations

## 🎲 Probability System

### **Category Weights** (from database)
- **Ultra Rare**: Weight 5 (lowest probability)
- **Rare**: Weight 25 (medium probability)  
- **Common**: Weight 70 (highest probability)

### **Smart Selection**
- Recently won prizes get reduced weight
- Prevents same prize winning repeatedly
- Maintains fairness across all users

## 📊 Example Prize Setup

### **Ultra Rare Prize**
```json
{
  "name": "Smart TV 32 inches",
  "category": "ultra_rare",
  "availability_dates": ["2025-09-25", "2025-10-15", "2025-11-05"],
  "quantity_per_date": 1,
  "weight": 5
}
```

### **Common Prize**
```json
{
  "name": "Power Bank + Neckband", 
  "category": "common",
  "availability_dates": ["*"],
  "quantity_per_date": 10,
  "weight": 70
}
```

## 🚀 Implementation Status

✅ **Database Schema**: Working with existing complex schema
✅ **Business Rules**: Enforced in frontend and backend
✅ **User Limits**: 1 rare/ultra-rare per user per day
✅ **Inventory Tracking**: Per-date quantity management
✅ **Admin Validation**: Rules enforced in prize manager
✅ **Fallback Logic**: Smart prize selection with limits
✅ **Category Mapping**: Proper database integration

This system ensures fair distribution of rare items while maintaining excitement and preventing abuse.
