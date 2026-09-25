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
-- Prizes are grouped into two independent classifications:
--   category_id  -> rarity / spin win-odds bucket (1=ultra_rare 15%, 2=rare 35%, 3=common 50%)
--   budget_tier  -> admin-panel price grouping only (budget/mid_budget/high_end), no effect on odds or wheel rendering
INSERT INTO prizes (id, name, category_id, type, emoji, is_active, is_enabled, display_order, budget_tier, description) VALUES
-- High-End Prizes (category_id: 1 / ultra_rare, budget_tier: high_end)
(1, 'Air Cooler', 1, 'single', '❄️', TRUE, TRUE, 1, 'high_end', 'High Performance Air Cooler'),
(2, '32-inch TV', 1, 'single', '📺', TRUE, TRUE, 2, 'high_end', 'Premium 32-inch Smart TV'),
(3, 'Washing Machine', 1, 'single', '🧺', TRUE, TRUE, 3, 'high_end', 'Automatic Washing Machine'),
(4, 'Home Theatre', 1, 'single', '🎭', TRUE, TRUE, 4, 'high_end', 'Home Theatre System'),

-- Mid-Budget Prizes (category_id: 2 / rare, budget_tier: mid_budget)
(5, 'Luggage Bag', 2, 'single', '🧳', TRUE, TRUE, 5, 'mid_budget', 'Travel Luggage Bag'),
(6, 'Govo Buds', 2, 'single', '🎧', TRUE, TRUE, 6, 'mid_budget', 'Govo Wireless Earbuds'),
(7, 'Smart Audio Sunglasses', 2, 'single', '🕶️', TRUE, TRUE, 7, 'mid_budget', 'Smart Audio Sunglasses'),
(8, 'Boult Q5 Bluetooth Speaker', 2, 'single', '🔊', TRUE, TRUE, 8, 'mid_budget', 'Boult Q5 Bluetooth Speaker'),
(9, 'G5 Game + SUP Gaming Handheld', 2, 'single', '🎮', TRUE, TRUE, 9, 'mid_budget', 'G5 Game and SUP Gaming Handheld'),
(10, 'Soundbar', 2, 'single', '📻', TRUE, TRUE, 10, 'mid_budget', 'Soundbar'),

-- Budget Prizes (category_id: 3 / common, budget_tier: budget)
(11, 'Screen Guard + Back Cover', 3, 'single', '📱', TRUE, TRUE, 11, 'budget', 'Mobile Screen Guard and Back Cover'),
(12, 'Wired Earphones', 3, 'single', '🎧', TRUE, TRUE, 12, 'budget', 'Wired Earphones'),
(13, 'Neckband', 3, 'single', '🎶', TRUE, TRUE, 13, 'budget', 'Wireless Neckband'),
(14, 'Power Bank', 3, 'single', '🔋', TRUE, TRUE, 14, 'budget', 'Power Bank'),
(15, 'Smart Watch', 3, 'single', '⌚', TRUE, TRUE, 15, 'budget', 'Smart Watch'),
(16, 'Dinner Set', 3, 'single', '🍽️', TRUE, TRUE, 16, 'budget', 'Complete Dinner Set'),
(17, 'Casserole Set', 3, 'single', '🍲', TRUE, TRUE, 17, 'budget', 'Casserole Set'),
(18, 'Meetha Set', 3, 'single', '🍬', TRUE, TRUE, 18, 'budget', 'Meetha Set'),
(19, 'Laptop Stand', 3, 'single', '💻', TRUE, TRUE, 19, 'budget', 'Laptop Stand'),
(20, 'Massage Gun', 3, 'single', '💆', TRUE, TRUE, 20, 'budget', 'Massage Gun'),
(21, 'Induction Stove', 3, 'single', '🔥', TRUE, TRUE, 21, 'budget', 'Induction Stove'),
(22, '2-in-1 Juicer', 3, 'single', '🥤', TRUE, TRUE, 22, 'budget', '2-in-1 Juicer')
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
