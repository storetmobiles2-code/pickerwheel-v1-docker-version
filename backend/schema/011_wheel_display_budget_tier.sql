-- =====================================================
-- ADD budget_tier TO get_wheel_display_prizes()
--
-- The customer wheel page's debug console logging (frontend/wheel.js)
-- printed "category"/"Category:" labels using pc.name (rare/ultra_rare/
-- common) because that was the only grouping value the wheel-display
-- API sent it - budget_tier was never selected here. Admin-facing PRs
-- already deprecated category as a concept anyone sees; this closes the
-- last gap by making budget_tier available client-side too, so the
-- debug logs can say "budget tier" and mean it, instead of relabeling
-- text while still printing a category value underneath.
--
-- Postgres can't add a column to a function's RETURNS TABLE via
-- CREATE OR REPLACE - the signature has to be dropped first.
-- =====================================================

DROP FUNCTION IF EXISTS get_wheel_display_prizes(INTEGER, DATE);

CREATE FUNCTION get_wheel_display_prizes(
    p_event_id INTEGER,
    p_date DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE(
    prize_id INTEGER,
    name VARCHAR(255),
    category_name VARCHAR(50),
    category_display VARCHAR(100),
    budget_tier VARCHAR(20),
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
        p.budget_tier,
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
