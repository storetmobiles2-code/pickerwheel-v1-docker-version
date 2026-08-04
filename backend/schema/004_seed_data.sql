-- PickerWheel PostgreSQL Schema
-- 004_seed_data.sql - Initial prize data
-- Created: January 2026

-- =====================================================
-- INSERT DEFAULT EVENT
-- =====================================================
INSERT INTO events (id, name, start_date, end_date, status) VALUES 
(1, 'myT MOBILES Spin & Win Contest', '2025-09-21', '2026-03-21', 'active')
ON CONFLICT (id) DO NOTHING;

-- Reset sequence
SELECT setval('events_id_seq', (SELECT MAX(id) FROM events));

-- =====================================================
-- INSERT PRIZE CATEGORIES
-- =====================================================
INSERT INTO prize_categories (id, name, display_name, weight, color, text_color) VALUES 
(1, 'ultra_rare', 'Ultra Rare', 5, '#FFD700', '#000000'),
(2, 'rare', 'Rare', 25, '#FF6B6B', '#FFFFFF'),
(3, 'common', 'Common', 70, '#4ECDC4', '#FFFFFF')
ON CONFLICT (id) DO NOTHING;

-- Reset sequence
SELECT setval('prize_categories_id_seq', (SELECT MAX(id) FROM prize_categories));

-- =====================================================
-- INSERT PRIZES
-- =====================================================
INSERT INTO prizes (id, name, category_id, type, emoji, is_active, is_enabled, display_order, description) VALUES 
-- Ultra Rare Prizes (category_id: 1)
(1, 'Smart TV 32 inches', 1, 'single', '📺', TRUE, TRUE, 1, 'Premium 32-inch Smart TV'),
(2, 'Silver Coin', 1, 'single', '🪙', TRUE, TRUE, 2, 'Collectible Silver Coin'),
(3, 'Refrigerator', 1, 'single', '🧊', TRUE, TRUE, 3, 'Energy Efficient Refrigerator'),
(4, 'Washing Machine', 1, 'single', '🧺', TRUE, TRUE, 4, 'Automatic Washing Machine'),
(5, 'Air Cooler', 1, 'single', '❄️', TRUE, TRUE, 5, 'High Performance Air Cooler'),
(6, 'Boult 60W Soundbar', 1, 'single', '🔊', TRUE, TRUE, 6, 'Premium 60W Soundbar'),

-- Rare Prizes (category_id: 2)
(7, 'Dinner Set', 2, 'single', '🍽️', TRUE, TRUE, 7, 'Complete Dinner Set'),
(8, 'Jio Tab', 2, 'single', '📱', TRUE, TRUE, 8, 'Jio Tablet Device'),
(9, 'Intex Home Theatre', 2, 'single', '🎭', TRUE, TRUE, 9, 'Intex Home Theatre System'),
(10, 'Zebronics Home Theatre', 2, 'single', '🎪', TRUE, TRUE, 10, 'Zebronics Home Theatre System'),
(11, 'Mi Smart Speaker', 2, 'single', '🔈', TRUE, TRUE, 11, 'Mi Smart Speaker'),
(12, 'Gas Stove', 2, 'single', '🔥', TRUE, TRUE, 12, 'Multi-burner Gas Stove'),
(13, 'Mixer Grinder', 2, 'single', '🥤', TRUE, TRUE, 13, 'High Speed Mixer Grinder'),
(14, 'Low Cost Mobile', 2, 'single', '📞', TRUE, TRUE, 14, 'Budget Smartphone'),

-- Common Prizes (category_id: 3)
(15, 'Smartwatch + Mini Cooler', 3, 'combo', '⌚', TRUE, TRUE, 15, 'Smartwatch and Mini Cooler Combo'),
(16, 'Defy Buds + Google Speaker', 3, 'combo', '🎧', TRUE, TRUE, 16, 'Wireless Earbuds and Smart Speaker'),
(17, 'Power Bank + Neckband', 3, 'combo', '🔋', TRUE, TRUE, 17, 'Power Bank and Wireless Neckband'),
(18, 'Zebronics Astra BT Speaker', 3, 'single', '📻', TRUE, TRUE, 18, 'Bluetooth Speaker'),
(19, 'Luggage Bags', 3, 'single', '🧳', TRUE, TRUE, 19, 'Travel Luggage Set'),
(20, 'Pressure Cooker', 3, 'single', '🍲', TRUE, TRUE, 20, 'Stainless Steel Pressure Cooker'),
(21, 'Free Pouch and Screen Guard', 3, 'combo', '📱', TRUE, TRUE, 21, 'Mobile Accessories Combo'),
(22, 'Trimmer + Skullcandy Earphones', 3, 'combo', '✂️', TRUE, TRUE, 22, 'Grooming and Audio Combo')
ON CONFLICT (id) DO NOTHING;

-- Reset sequence
SELECT setval('prizes_id_seq', (SELECT MAX(id) FROM prizes));

-- =====================================================
-- INSERT INITIAL INVENTORY (for today and next 30 days)
-- =====================================================
DO $$
DECLARE
    v_date DATE;
    v_prize RECORD;
BEGIN
    -- Loop through next 30 days
    FOR v_date IN SELECT generate_series(CURRENT_DATE, CURRENT_DATE + INTERVAL '30 days', '1 day')::DATE
    LOOP
        -- Insert inventory for each prize
        FOR v_prize IN SELECT id, category_id FROM prizes WHERE is_active = TRUE
        LOOP
            INSERT INTO prize_inventory (prize_id, event_id, available_date, initial_quantity, remaining_quantity, daily_limit)
            VALUES (
                v_prize.id,
                1,  -- event_id
                v_date,
                CASE 
                    WHEN v_prize.category_id = 1 THEN 2   -- Ultra rare: 2 per day
                    WHEN v_prize.category_id = 2 THEN 5   -- Rare: 5 per day
                    ELSE 10                               -- Common: 10 per day
                END,
                CASE 
                    WHEN v_prize.category_id = 1 THEN 2
                    WHEN v_prize.category_id = 2 THEN 5
                    ELSE 10
                END,
                CASE 
                    WHEN v_prize.category_id = 1 THEN 1   -- Ultra rare: 1 win per day max
                    WHEN v_prize.category_id = 2 THEN 2   -- Rare: 2 wins per day max
                    ELSE 5                                -- Common: 5 wins per day max
                END
            )
            ON CONFLICT (prize_id, event_id, available_date) DO NOTHING;
        END LOOP;
    END LOOP;
END $$;

-- =====================================================
-- INSERT DEFAULT DAILY STATS
-- =====================================================
INSERT INTO daily_stats (event_id, stat_date, total_spins, total_wins, unique_users)
VALUES (1, CURRENT_DATE, 0, 0, 0)
ON CONFLICT (event_id, stat_date) DO NOTHING;
