# 🏗️ PickerWheel Contest - System Architecture Plan
## Database-Backed 2-Month Event with Smart Backend Logic

### 📋 **Project Overview**

**Objective**: Create a robust, database-backed contest system that handles a 2-month event with intelligent prize distribution while maintaining a seamless user experience.

**Key Principle**: Backend handles all complexity, frontend remains simple and user-friendly.

---

## 🎯 **Core Requirements**

### **User Experience Requirements:**
1. **Seamless UX** - Users should feel all items are always available
2. **No date/quantity messages** - Backend handles availability logic silently
3. **Even wheel slices** - All 22 prizes always visible on wheel
4. **Smooth animations** - Reuse existing celebration and animation systems
5. **Mobile-first design** - Maintain responsive design from existing system

### **Backend Logic Requirements:**
1. **Date-based availability** - Items only winnable on their scheduled dates
2. **Quantity management** - Respect daily/weekly/monthly limits
3. **Intelligent fallback** - If selected prize unavailable, select alternative
4. **Persistent tracking** - 2-month event data retention
5. **Admin controls** - Inventory management and statistics

---

## 🏗️ **System Architecture**

### **3-Tier Architecture:**

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   Web Frontend  │  │  Admin Panel    │  │  Mobile PWA │ │
│  │   (React/JS)    │  │   (React/JS)    │  │   (PWA)     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     API LAYER                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              RESTful API (Flask/FastAPI)                │ │
│  │  • Prize Management    • Spin Logic                     │ │
│  │  • User Sessions       • Statistics                     │ │
│  │  • Admin Operations    • Health Checks                  │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    BUSINESS LOGIC LAYER                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ Prize Manager   │  │ Inventory Mgr   │  │ Stats Mgr   │ │
│  │ • Availability  │  │ • Quantities    │  │ • Analytics │ │
│  │ • Selection     │  │ • Replenishment │  │ • Reporting │ │
│  │ • Validation    │  │ • Scheduling    │  │ • Tracking  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     DATA LAYER                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                SQLite Database                          │ │
│  │  • Events        • Prizes         • Inventory          │ │
│  │  • Users         • Wins           • Statistics         │ │
│  │  • Sessions      • Logs           • Configurations     │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎨 **Asset Reuse Strategy**

### **Existing Assets to Reuse:**

#### **Visual Assets:**
- ✅ `myt-mobiles-logo.png` - Company logo
- ✅ `style.css` - Base styling and animations
- ✅ Celebration animations and effects
- ✅ Wheel design and segment styling
- ✅ Modal designs and transitions

#### **Audio Assets:**
- ✅ `win-sound.mp3` - Victory sound
- ✅ `rare-win-sound.mp3` - Special win sound  
- ✅ `spin-sound.mp3` - Wheel spinning sound
- ✅ `audio-generator.js` - Fallback audio system

#### **Code Components:**
- ✅ `CelebrationManager` - Visual effects system
- ✅ Wheel animation logic
- ✅ Modal system
- ✅ PWA configuration (`manifest.json`, `sw.js`)
- ✅ Mobile-responsive CSS

#### **Configuration:**
- ✅ Prize categories and weights
- ✅ Color schemes and themes
- ✅ Admin password system

---

## 🎡 **Smart Wheel Logic**

### **Frontend Wheel Display:**
```javascript
// Always show all 22 prizes on wheel
const wheelPrizes = [
  // Ultra Rare (6 items)
  { id: 1, name: "Smart TV 32 inches", category: "ultra_rare", emoji: "📺" },
  { id: 2, name: "Silver Coin", category: "ultra_rare", emoji: "🪙" },
  // ... all 22 prizes always visible
];

// Wheel segments = 360° / 22 = 16.36° per segment
const segmentAngle = 360 / wheelPrizes.length;
```

### **Backend Selection Logic:**
```python
def intelligent_prize_selection(user_id, date):
    """
    Smart prize selection with fallback logic
    """
    # 1. Get all prizes (for wheel display)
    all_prizes = get_all_prizes()
    
    # 2. Get actually available prizes (backend logic)
    available_today = get_available_prizes_for_date(date)
    
    # 3. User spins - wheel shows landing on any prize
    selected_prize_id = simulate_wheel_spin(all_prizes)
    
    # 4. Backend validation
    if is_prize_available(selected_prize_id, date):
        return award_prize(selected_prize_id, user_id)
    else:
        # 5. Intelligent fallback - award similar category prize
        return award_fallback_prize(selected_prize_id, available_today, user_id)
```

---

## 🗄️ **Database Schema Design**

### **Core Tables:**

#### **1. Events Table**
```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    start_date DATE NOT NULL,        -- 2025-09-21
    end_date DATE NOT NULL,          -- 2025-11-21
    status TEXT DEFAULT 'active'
);
```

#### **2. Prizes Table**
```sql
CREATE TABLE prizes (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,          -- ultra_rare, rare, common
    type TEXT DEFAULT 'single',      -- single, combo
    emoji TEXT,
    icon_path TEXT,
    weight INTEGER DEFAULT 10,
    is_premium BOOLEAN DEFAULT FALSE,
    display_order INTEGER
);
```

#### **3. Prize Inventory (Smart Availability)**
```sql
CREATE TABLE prize_inventory (
    id INTEGER PRIMARY KEY,
    prize_id INTEGER,
    event_id INTEGER,
    available_date DATE,
    max_quantity INTEGER,
    remaining_quantity INTEGER,
    is_unlimited BOOLEAN DEFAULT FALSE,
    availability_type TEXT           -- daily, weekly, monthly, special
);
```

#### **4. Prize Wins (Tracking)**
```sql
CREATE TABLE prize_wins (
    id INTEGER PRIMARY KEY,
    prize_id INTEGER,
    user_id TEXT,
    win_date DATE,
    win_timestamp TIMESTAMP,
    verification_code TEXT,
    ip_address TEXT
);
```

---

## 🎯 **Smart Backend Logic**

### **Prize Availability Engine:**

#### **1. Availability Rules:**
```python
AVAILABILITY_RULES = {
    'ultra_rare': {
        'smart_tv': {'dates': ['2025-09-25', '2025-10-15', '2025-11-05'], 'qty': 1},
        'silver_coin': {'frequency': 'weekly', 'qty': 2},
        'refrigerator': {'frequency': 'monthly', 'qty': 1},
        # ...
    },
    'rare': {
        'default': {'frequency': 'daily', 'qty': 2, 'skip_sunday': True}
    },
    'common': {
        'default': {'unlimited': True}
    }
}
```

#### **2. Intelligent Fallback System:**
```python
def get_fallback_prize(original_prize, available_prizes):
    """
    If user lands on unavailable prize, award similar category prize
    """
    # Priority 1: Same category
    same_category = filter_by_category(available_prizes, original_prize.category)
    if same_category:
        return weighted_random_select(same_category)
    
    # Priority 2: Lower category (always give something)
    if original_prize.category == 'ultra_rare':
        return get_rare_or_common_prize(available_prizes)
    elif original_prize.category == 'rare':
        return get_common_prize(available_prizes)
    
    # Priority 3: Any available prize
    return weighted_random_select(available_prizes)
```

---

## 🎨 **Frontend Architecture**

### **Component Structure:**
```
src/
├── components/
│   ├── Wheel/
│   │   ├── WheelComponent.js      # Main wheel display
│   │   ├── WheelSegment.js        # Individual segments
│   │   └── SpinButton.js          # Center spin button
│   ├── Prize/
│   │   ├── PrizeModal.js          # Win announcement
│   │   ├── ComboDisplay.js        # Multi-item prizes
│   │   └── PrizeCard.js           # Individual prize display
│   ├── Effects/
│   │   ├── CelebrationManager.js  # Reused from existing
│   │   ├── Confetti.js            # Particle effects
│   │   └── SoundManager.js        # Audio system
│   └── Admin/
│       ├── AdminPanel.js          # Management interface
│       ├── InventoryView.js       # Stock management
│       └── StatsView.js           # Analytics
├── services/
│   ├── ApiService.js              # Backend communication
│   ├── WheelService.js            # Wheel logic
│   └── StorageService.js          # Local storage
├── assets/                        # Reused assets
│   ├── images/
│   ├── sounds/
│   └── styles/
└── utils/
    ├── constants.js
    ├── helpers.js
    └── validators.js
```

---

## 🔄 **User Flow Design**

### **Seamless User Experience:**

#### **1. User Visits Page:**
```
User loads page → Frontend shows all 22 prizes on wheel → User sees "everything available"
```

#### **2. User Spins Wheel:**
```
User clicks SPIN → Wheel animates → Lands on any prize → Backend validates availability
```

#### **3. Backend Processing:**
```
If available: Award selected prize
If unavailable: Award fallback prize (same category preferred)
User never knows about availability logic
```

#### **4. Prize Announcement:**
```
Show celebration → Display won prize → Generate verification code → Update statistics
```

---

## 📱 **API Design**

### **Public Endpoints:**
```
GET  /api/prizes              # Get all prizes (for wheel display)
POST /api/spin                # Spin wheel and win prize
GET  /api/stats               # Public statistics
GET  /api/health              # System health
```

### **Admin Endpoints:**
```
GET  /api/admin/inventory     # View inventory status
POST /api/admin/replenish     # Add inventory
GET  /api/admin/wins          # View all wins
GET  /api/admin/analytics     # Detailed analytics
```

### **Smart Spin API:**
```python
@app.route('/api/spin', methods=['POST'])
def smart_spin():
    """
    Intelligent spin with fallback logic
    """
    user_id = get_user_id(request)
    
    # 1. Simulate wheel spin (frontend shows this result)
    wheel_result = simulate_wheel_physics()
    selected_prize_id = wheel_result['prize_id']
    
    # 2. Backend validation and smart selection
    actual_prize = intelligent_prize_selection(selected_prize_id, user_id)
    
    # 3. Return result (user sees smooth experience)
    return {
        'success': True,
        'prize': actual_prize,
        'wheel_result': wheel_result,  # For animation
        'celebration_level': get_celebration_level(actual_prize)
    }
```

---

## 🎨 **UI/UX Design Principles**

### **Clean & Intuitive:**
1. **Single Action** - One big SPIN button
2. **Visual Feedback** - Clear animations and sounds
3. **Instant Gratification** - Immediate prize announcement
4. **No Complexity** - Hide all backend logic from user
5. **Mobile First** - Touch-friendly design

### **Reused Design Elements:**
- ✅ Futuristic gradient backgrounds
- ✅ Neon glow effects
- ✅ Smooth wheel animations
- ✅ Celebration particle systems
- ✅ Professional modal designs
- ✅ Responsive grid layouts

---

## 🔧 **Development Phases**

### **Phase 1: Foundation (Week 1)**
- ✅ Database schema setup
- ✅ Basic API structure
- ✅ Asset migration
- ✅ Core wheel component

### **Phase 2: Smart Logic (Week 2)**
- ✅ Intelligent prize selection
- ✅ Availability engine
- ✅ Fallback system
- ✅ Admin interface

### **Phase 3: Integration (Week 3)**
- ✅ Frontend-backend integration
- ✅ Animation system
- ✅ Testing and debugging
- ✅ Performance optimization

### **Phase 4: Production (Week 4)**
- ✅ Security hardening
- ✅ Monitoring setup
- ✅ Documentation
- ✅ Deployment

---

## 🚀 **Deployment Strategy**

### **Infrastructure:**
- **Database**: SQLite (development) → PostgreSQL (production)
- **Backend**: Python Flask with Gunicorn
- **Frontend**: Static files with CDN
- **Hosting**: Cloud platform (AWS/GCP/Azure)

### **Monitoring:**
- **Health Checks**: API endpoint monitoring
- **Analytics**: Prize distribution tracking
- **Alerts**: Inventory low warnings
- **Logs**: Comprehensive audit trail

---

## 🎯 **Success Metrics**

### **User Experience:**
- **Spin Success Rate**: >99% successful spins
- **Load Time**: <2 seconds initial load
- **Mobile Performance**: 60fps animations
- **User Retention**: Engagement tracking

### **Business Logic:**
- **Prize Distribution**: Matches planned schedule
- **Inventory Accuracy**: Real-time tracking
- **Admin Efficiency**: Easy management
- **Data Integrity**: Zero data loss

---

## 🔐 **Security & Compliance**

### **Security Measures:**
- **Input Validation**: All API inputs sanitized
- **Rate Limiting**: Prevent abuse
- **Admin Authentication**: Secure admin access
- **Data Encryption**: Sensitive data protection
- **Audit Logging**: Complete activity trail

### **Privacy:**
- **Minimal Data**: Only necessary user data
- **Anonymous Sessions**: No personal info required
- **Data Retention**: Configurable cleanup
- **GDPR Compliance**: Privacy by design

---

This architecture ensures a seamless user experience while maintaining robust backend logic for the 2-month event. The system is designed to be scalable, maintainable, and user-friendly while reusing all valuable existing assets.

**Ready to implement this architecture?** 🚀
