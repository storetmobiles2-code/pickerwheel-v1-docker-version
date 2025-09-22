-- PickerWheel Contest Database Schema
-- 2-Month Event Management System
-- Created: September 21, 2025

-- Event Configuration Table
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'paused', 'ended')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Prize Categories Table
CREATE TABLE IF NOT EXISTS prize_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    weight INTEGER DEFAULT 10,
    color TEXT DEFAULT '#4ECDC4',
    text_color TEXT DEFAULT '#FFFFFF',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Prizes Table
CREATE TABLE IF NOT EXISTS prizes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category_id INTEGER NOT NULL,
    type TEXT DEFAULT 'single' CHECK (type IN ('single', 'combo')),
    emoji TEXT DEFAULT '🎁',
    icon_path TEXT,
    description TEXT,
    value DECIMAL(10,2) DEFAULT 0.00,
    is_premium BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES prize_categories(id)
);

-- Combo Items Table (for combo prizes)
CREATE TABLE IF NOT EXISTS combo_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prize_id INTEGER NOT NULL,
    item_name TEXT NOT NULL,
    item_emoji TEXT DEFAULT '🎁',
    item_icon_path TEXT,
    sort_order INTEGER DEFAULT 0,
    FOREIGN KEY (prize_id) REFERENCES prizes(id) ON DELETE CASCADE
);

-- Prize Inventory Table (tracks quantities per date)
CREATE TABLE IF NOT EXISTS prize_inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prize_id INTEGER NOT NULL,
    event_id INTEGER NOT NULL,
    available_date DATE NOT NULL,
    initial_quantity INTEGER NOT NULL DEFAULT 0,
    remaining_quantity INTEGER NOT NULL DEFAULT 0,
    is_unlimited BOOLEAN DEFAULT FALSE,
    per_day_limit INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (prize_id) REFERENCES prizes(id),
    FOREIGN KEY (event_id) REFERENCES events(id),
    UNIQUE(prize_id, event_id, available_date)
);

-- Prize Wins Table (tracks all wins)
CREATE TABLE IF NOT EXISTS prize_wins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prize_id INTEGER NOT NULL,
    event_id INTEGER NOT NULL,
    user_identifier TEXT, -- IP, session, or user ID
    win_date DATE NOT NULL,
    win_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verification_code TEXT UNIQUE,
    is_verified BOOLEAN DEFAULT FALSE,
    notes TEXT,
    FOREIGN KEY (prize_id) REFERENCES prizes(id),
    FOREIGN KEY (event_id) REFERENCES events(id)
);

-- Daily Statistics Table
CREATE TABLE IF NOT EXISTS daily_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    stat_date DATE NOT NULL,
    total_spins INTEGER DEFAULT 0,
    total_wins INTEGER DEFAULT 0,
    unique_users INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES events(id),
    UNIQUE(event_id, stat_date)
);

-- User Sessions Table (optional - for tracking users)
CREATE TABLE IF NOT EXISTS user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    first_visit TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_spins INTEGER DEFAULT 0,
    total_wins INTEGER DEFAULT 0
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_prize_inventory_date ON prize_inventory(available_date);
CREATE INDEX IF NOT EXISTS idx_prize_inventory_prize ON prize_inventory(prize_id);
CREATE INDEX IF NOT EXISTS idx_prize_wins_date ON prize_wins(win_date);
CREATE INDEX IF NOT EXISTS idx_prize_wins_prize ON prize_wins(prize_id);
CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_stats(stat_date);

-- Insert default event
INSERT OR IGNORE INTO events (id, name, start_date, end_date, status) VALUES 
(1, 'myT MOBILES Spin & Win Contest', '2025-09-21', '2025-11-21', 'active');

-- Insert prize categories
INSERT OR IGNORE INTO prize_categories (id, name, display_name, weight, color, text_color) VALUES 
(1, 'ultra_rare', 'Ultra Rare', 5, '#FFD700', '#000000'),
(2, 'rare', 'Rare', 25, '#FF6B6B', '#FFFFFF'),
(3, 'common', 'Common', 70, '#4ECDC4', '#FFFFFF');

-- Insert prizes with latest combo list
INSERT OR IGNORE INTO prizes (id, name, category_id, type, emoji, is_premium, description) VALUES 
-- Ultra Rare Prizes (6 items)
(1, 'Smart TV 32 inches', 1, 'single', '📺', TRUE, 'Premium 32-inch Smart TV'),
(2, 'Silver Coin', 1, 'single', '🪙', TRUE, 'Collectible Silver Coin'),
(3, 'Refrigerator', 1, 'single', '🧊', TRUE, 'Energy Efficient Refrigerator'),
(4, 'Washing Machine', 1, 'single', '🧺', TRUE, 'Automatic Washing Machine'),
(5, 'Air Cooler', 1, 'single', '❄️', TRUE, 'High Performance Air Cooler'),
(6, 'Boult 60W Soundbar', 1, 'single', '🔊', TRUE, 'Premium 60W Soundbar'),

-- Rare Prizes (8 items)
(7, 'Dinner Set', 2, 'single', '🍽️', FALSE, 'Complete Dinner Set'),
(8, 'Jio Tab', 2, 'single', '📱', FALSE, 'Jio Tablet Device'),
(9, 'Intex Home Theatre', 2, 'single', '🎭', FALSE, 'Intex Home Theatre System'),
(10, 'Zebronics Home Theatre', 2, 'single', '🎪', FALSE, 'Zebronics Home Theatre System'),
(11, 'Mi Smart Speaker', 2, 'single', '🔈', FALSE, 'Mi Smart Speaker'),
(12, 'Gas Stove', 2, 'single', '🔥', FALSE, 'Multi-burner Gas Stove'),
(13, 'Mixer Grinder', 2, 'single', '🥤', FALSE, 'High Speed Mixer Grinder'),
(14, 'Low Cost Mobile', 2, 'single', '📞', FALSE, 'Budget Smartphone'),

-- Common Prizes (8 items - 5 combos + 3 singles)
(15, 'Smartwatch + Mini Cooler', 3, 'combo', '⌚', FALSE, 'Smartwatch and Mini Cooler Combo'),
(16, 'Defy Buds + Google Speaker', 3, 'combo', '🎧', FALSE, 'Wireless Earbuds and Smart Speaker'),
(17, 'Power Bank + Neckband', 3, 'combo', '🔋', FALSE, 'Power Bank and Wireless Neckband'),
(18, 'Zebronics Astra BT Speaker', 3, 'single', '📻', FALSE, 'Bluetooth Speaker'),
(19, 'Luggage Bags', 3, 'single', '🧳', FALSE, 'Travel Luggage Set'),
(20, 'Pressure Cooker', 3, 'single', '🍲', FALSE, 'Stainless Steel Pressure Cooker'),
(21, 'Free Pouch and Screen Guard', 3, 'combo', '📱', FALSE, 'Mobile Accessories Combo'),
(22, 'Trimmer + Skullcandy Earphones', 3, 'combo', '✂️', FALSE, 'Grooming and Audio Combo');

-- Insert combo items
INSERT OR IGNORE INTO combo_items (prize_id, item_name, item_emoji, sort_order) VALUES 
-- Smartwatch + Mini Cooler (ID: 15)
(15, 'Smartwatch', '⌚', 1),
(15, 'Mini Cooler', '❄️', 2),

-- Defy Buds + Google Speaker (ID: 16)
(16, 'Defy Wireless Buds', '🎧', 1),
(16, 'Google Smart Speaker', '🔈', 2),

-- Power Bank + Neckband (ID: 17)
(17, 'Power Bank 10000mAh', '🔋', 1),
(17, 'Wireless Neckband', '🎵', 2),

-- Free Pouch and Screen Guard (ID: 21)
(21, 'Mobile Pouch', '👝', 1),
(21, 'Screen Guard', '🛡️', 2),

-- Trimmer + Skullcandy Earphones (ID: 22)
(22, 'Hair Trimmer', '✂️', 1),
(22, 'Skullcandy Earphones', '🎧', 2);

-- Insert inventory for 2-month period (September 21 - November 21, 2025)
-- Ultra Rare items - limited quantities on specific dates
INSERT OR IGNORE INTO prize_inventory (prize_id, event_id, available_date, initial_quantity, remaining_quantity) VALUES 
-- Smart TV - available on specific dates
(1, 1, '2025-09-25', 1, 1),
(1, 1, '2025-10-15', 1, 1),
(1, 1, '2025-11-05', 1, 1),

-- Silver Coin - weekly availability
(2, 1, '2025-09-28', 2, 2),
(2, 1, '2025-10-05', 2, 2),
(2, 1, '2025-10-12', 2, 2),
(2, 1, '2025-10-19', 2, 2),
(2, 1, '2025-10-26', 2, 2),
(2, 1, '2025-11-02', 2, 2),
(2, 1, '2025-11-09', 2, 2),
(2, 1, '2025-11-16', 2, 2),

-- Refrigerator - monthly
(3, 1, '2025-10-01', 1, 1),
(3, 1, '2025-11-01', 1, 1),

-- Washing Machine - monthly
(4, 1, '2025-10-10', 1, 1),
(4, 1, '2025-11-10', 1, 1),

-- Air Cooler - bi-weekly
(5, 1, '2025-09-30', 1, 1),
(5, 1, '2025-10-14', 1, 1),
(5, 1, '2025-10-28', 1, 1),
(5, 1, '2025-11-11', 1, 1),

-- Boult Soundbar - weekly
(6, 1, '2025-09-22', 1, 1),
(6, 1, '2025-09-29', 1, 1),
(6, 1, '2025-10-06', 1, 1),
(6, 1, '2025-10-13', 1, 1),
(6, 1, '2025-10-20', 1, 1),
(6, 1, '2025-10-27', 1, 1),
(6, 1, '2025-11-03', 1, 1),
(6, 1, '2025-11-10', 1, 1),
(6, 1, '2025-11-17', 1, 1);

-- Rare items - moderate quantities, available most days
-- (We'll generate these programmatically in the backend)

-- Common items - unlimited availability
-- (These will be marked as unlimited in the backend)

-- Create triggers to update timestamps
CREATE TRIGGER IF NOT EXISTS update_events_timestamp 
    AFTER UPDATE ON events
    BEGIN
        UPDATE events SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_prizes_timestamp 
    AFTER UPDATE ON prizes
    BEGIN
        UPDATE prizes SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_inventory_timestamp 
    AFTER UPDATE ON prize_inventory
    BEGIN
        UPDATE prize_inventory SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- Create view for available prizes
CREATE VIEW IF NOT EXISTS available_prizes_today AS
SELECT 
    p.id,
    p.name,
    p.type,
    p.emoji,
    p.is_premium,
    pc.name as category,
    pc.display_name as category_display,
    pc.weight,
    pc.color,
    pc.text_color,
    pi.remaining_quantity,
    pi.is_unlimited,
    CASE 
        WHEN pi.is_unlimited = 1 THEN 999
        ELSE pi.remaining_quantity 
    END as effective_quantity
FROM prizes p
JOIN prize_categories pc ON p.category_id = pc.id
LEFT JOIN prize_inventory pi ON p.id = pi.prize_id 
    AND pi.event_id = 1 
    AND pi.available_date = DATE('now')
WHERE p.is_active = 1 
    AND (pi.remaining_quantity > 0 OR pi.is_unlimited = 1 OR pi.id IS NULL)
ORDER BY pc.weight ASC, p.name;
