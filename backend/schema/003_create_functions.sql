-- PickerWheel PostgreSQL Schema
-- 003_create_functions.sql - Stored procedures for atomic operations
-- Created: January 2026

-- =====================================================
-- FUNCTION: update_timestamp
-- Automatically updates updated_at column
-- =====================================================
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update_timestamp trigger to tables
DROP TRIGGER IF EXISTS update_events_timestamp ON events;
CREATE TRIGGER update_events_timestamp
    BEFORE UPDATE ON events
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

DROP TRIGGER IF EXISTS update_prizes_timestamp ON prizes;
CREATE TRIGGER update_prizes_timestamp
    BEFORE UPDATE ON prizes
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

DROP TRIGGER IF EXISTS update_inventory_timestamp ON prize_inventory;
CREATE TRIGGER update_inventory_timestamp
    BEFORE UPDATE ON prize_inventory
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

DROP TRIGGER IF EXISTS update_daily_stats_timestamp ON daily_stats;
CREATE TRIGGER update_daily_stats_timestamp
    BEFORE UPDATE ON daily_stats
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- =====================================================
-- FUNCTION: consume_prize
-- Atomically decrements inventory and records transaction
-- Returns TRUE if successful, FALSE if out of stock
-- =====================================================
CREATE OR REPLACE FUNCTION consume_prize(
    p_prize_id INTEGER,
    p_event_id INTEGER,
    p_user_identifier VARCHAR(255) DEFAULT NULL,
    p_metadata JSONB DEFAULT '{}'
)
RETURNS TABLE(success BOOLEAN, transaction_id INTEGER, remaining INTEGER) AS $$
DECLARE
    v_remaining INTEGER;
    v_daily_limit INTEGER;
    v_wins_today INTEGER;
    v_transaction_id INTEGER;
    v_today DATE := CURRENT_DATE;
BEGIN
    -- Lock the inventory row for update
    SELECT pi.remaining_quantity, pi.daily_limit
    INTO v_remaining, v_daily_limit
    FROM prize_inventory pi
    WHERE pi.prize_id = p_prize_id
      AND pi.event_id = p_event_id
      AND pi.available_date = v_today
    FOR UPDATE;
    
    -- Check if inventory exists
    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, NULL::INTEGER, 0;
        RETURN;
    END IF;
    
    -- Check remaining quantity
    IF v_remaining <= 0 THEN
        RETURN QUERY SELECT FALSE, NULL::INTEGER, 0;
        RETURN;
    END IF;
    
    -- Check daily limit
    SELECT COUNT(*)
    INTO v_wins_today
    FROM transactions t
    WHERE t.prize_id = p_prize_id
      AND t.transaction_type = 'win'
      AND DATE(t.created_at) = v_today;
    
    IF v_wins_today >= v_daily_limit THEN
        RETURN QUERY SELECT FALSE, NULL::INTEGER, v_remaining;
        RETURN;
    END IF;
    
    -- Decrement inventory
    UPDATE prize_inventory
    SET remaining_quantity = remaining_quantity - 1
    WHERE prize_id = p_prize_id
      AND event_id = p_event_id
      AND available_date = v_today;
    
    -- Record transaction
    INSERT INTO transactions (prize_id, user_identifier, transaction_type, quantity, metadata)
    VALUES (p_prize_id, p_user_identifier, 'win', 1, p_metadata)
    RETURNING id INTO v_transaction_id;
    
    -- Log to audit
    INSERT INTO audit_log (action, entity_type, entity_id, new_value)
    VALUES ('consume', 'prize', p_prize_id, 
            jsonb_build_object('user', p_user_identifier, 'transaction_id', v_transaction_id));
    
    RETURN QUERY SELECT TRUE, v_transaction_id, v_remaining - 1;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- FUNCTION: get_available_prizes
-- Returns prizes that can be won (enabled + has inventory)
-- =====================================================
CREATE OR REPLACE FUNCTION get_available_prizes(
    p_event_id INTEGER,
    p_date DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE(
    prize_id INTEGER,
    name VARCHAR(255),
    category_name VARCHAR(50),
    category_display VARCHAR(100),
    emoji VARCHAR(10),
    remaining_quantity INTEGER,
    daily_limit INTEGER,
    wins_today BIGINT,
    weight INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id AS prize_id,
        p.name,
        pc.name AS category_name,
        pc.display_name AS category_display,
        p.emoji,
        pi.remaining_quantity,
        pi.daily_limit,
        COALESCE(tw.wins_today, 0) AS wins_today,
        pc.weight
    FROM prizes p
    JOIN prize_categories pc ON p.category_id = pc.id
    JOIN prize_inventory pi ON p.id = pi.prize_id AND pi.event_id = p_event_id AND pi.available_date = p_date
    LEFT JOIN (
        SELECT t.prize_id, COUNT(*) AS wins_today
        FROM transactions t
        WHERE t.transaction_type = 'win'
          AND DATE(t.created_at) = p_date
        GROUP BY t.prize_id
    ) tw ON p.id = tw.prize_id
    WHERE p.is_active = TRUE
      AND p.is_enabled = TRUE  -- Only enabled prizes can be won
      AND pi.remaining_quantity > 0
      AND COALESCE(tw.wins_today, 0) < pi.daily_limit
    ORDER BY pc.weight ASC, p.display_order ASC;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- FUNCTION: get_wheel_display_prizes
-- Returns ALL active prizes for wheel display (including disabled)
-- =====================================================
CREATE OR REPLACE FUNCTION get_wheel_display_prizes(
    p_event_id INTEGER,
    p_date DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE(
    prize_id INTEGER,
    name VARCHAR(255),
    category_name VARCHAR(50),
    category_display VARCHAR(100),
    emoji VARCHAR(10),
    is_enabled BOOLEAN,
    remaining_quantity INTEGER,
    display_order INTEGER,
    color VARCHAR(20),
    text_color VARCHAR(20)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id AS prize_id,
        p.name,
        pc.name AS category_name,
        pc.display_name AS category_display,
        p.emoji,
        p.is_enabled,
        COALESCE(pi.remaining_quantity, 0) AS remaining_quantity,
        p.display_order,
        pc.color,
        pc.text_color
    FROM prizes p
    JOIN prize_categories pc ON p.category_id = pc.id
    LEFT JOIN prize_inventory pi ON p.id = pi.prize_id AND pi.event_id = p_event_id AND pi.available_date = p_date
    WHERE p.is_active = TRUE  -- Show all active prizes, even if disabled
    ORDER BY p.display_order ASC, p.id ASC;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- FUNCTION: add_prize
-- Adds a new prize and logs to audit
-- =====================================================
CREATE OR REPLACE FUNCTION add_prize(
    p_name VARCHAR(255),
    p_category_id INTEGER,
    p_emoji VARCHAR(10) DEFAULT '🎁',
    p_description TEXT DEFAULT NULL,
    p_display_order INTEGER DEFAULT 0
)
RETURNS INTEGER AS $$
DECLARE
    v_prize_id INTEGER;
BEGIN
    INSERT INTO prizes (name, category_id, emoji, description, display_order, is_active, is_enabled)
    VALUES (p_name, p_category_id, p_emoji, p_description, p_display_order, TRUE, TRUE)
    RETURNING id INTO v_prize_id;
    
    -- Log to audit
    INSERT INTO audit_log (action, entity_type, entity_id, new_value, performed_by)
    VALUES ('create', 'prize', v_prize_id, 
            jsonb_build_object('name', p_name, 'category_id', p_category_id, 'emoji', p_emoji),
            'admin');
    
    RETURN v_prize_id;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- FUNCTION: toggle_prize_enabled
-- Toggles the is_enabled flag for a prize
-- =====================================================
CREATE OR REPLACE FUNCTION toggle_prize_enabled(
    p_prize_id INTEGER,
    p_enabled BOOLEAN
)
RETURNS BOOLEAN AS $$
DECLARE
    v_old_enabled BOOLEAN;
BEGIN
    SELECT is_enabled INTO v_old_enabled FROM prizes WHERE id = p_prize_id;
    
    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;
    
    UPDATE prizes SET is_enabled = p_enabled WHERE id = p_prize_id;
    
    -- Log to audit
    INSERT INTO audit_log (action, entity_type, entity_id, old_value, new_value, performed_by)
    VALUES ('toggle_enabled', 'prize', p_prize_id, 
            jsonb_build_object('is_enabled', v_old_enabled),
            jsonb_build_object('is_enabled', p_enabled),
            'admin');
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- FUNCTION: delete_prize
-- Soft deletes a prize by setting is_active = FALSE
-- =====================================================
CREATE OR REPLACE FUNCTION delete_prize(p_prize_id INTEGER)
RETURNS BOOLEAN AS $$
DECLARE
    v_name VARCHAR(255);
BEGIN
    SELECT name INTO v_name FROM prizes WHERE id = p_prize_id;
    
    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;
    
    UPDATE prizes SET is_active = FALSE WHERE id = p_prize_id;
    
    -- Log to audit
    INSERT INTO audit_log (action, entity_type, entity_id, old_value, performed_by)
    VALUES ('delete', 'prize', p_prize_id, 
            jsonb_build_object('name', v_name),
            'admin');
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- FUNCTION: get_daily_stats
-- Returns statistics for a specific date
-- =====================================================
CREATE OR REPLACE FUNCTION get_daily_stats(
    p_event_id INTEGER,
    p_date DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE(
    total_spins BIGINT,
    total_wins BIGINT,
    unique_users BIGINT,
    wins_by_category JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*) AS total_spins,
        COUNT(*) FILTER (WHERE t.transaction_type = 'win') AS total_wins,
        COUNT(DISTINCT t.user_identifier) AS unique_users,
        COALESCE(
            jsonb_object_agg(
                COALESCE(pc.name, 'unknown'),
                category_wins.win_count
            ) FILTER (WHERE pc.name IS NOT NULL),
            '{}'::jsonb
        ) AS wins_by_category
    FROM transactions t
    LEFT JOIN prizes p ON t.prize_id = p.id
    LEFT JOIN prize_categories pc ON p.category_id = pc.id
    LEFT JOIN (
        SELECT p2.category_id, COUNT(*) AS win_count
        FROM transactions t2
        JOIN prizes p2 ON t2.prize_id = p2.id
        WHERE t2.transaction_type = 'win'
          AND DATE(t2.created_at) = p_date
        GROUP BY p2.category_id
    ) category_wins ON pc.id = category_wins.category_id
    WHERE DATE(t.created_at) = p_date;
END;
$$ LANGUAGE plpgsql;
