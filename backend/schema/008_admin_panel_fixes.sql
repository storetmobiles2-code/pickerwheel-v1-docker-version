-- =====================================================
-- ADMIN PANEL BUG FIXES
-- See ADMIN_PANEL_BUGS.md and the guaranteed-win kanban board for context.
-- =====================================================

-- -----------------------------------------------------
-- Fix: an unfulfillable pending guaranteed win permanently blocked the
-- spin queue.
--
-- get_pending_guaranteed_win() always returned the single
-- highest-priority/oldest pending row with no check that its prize could
-- actually be won today. Combined with the 007 atomicity fix (which
-- correctly leaves an unfulfillable win 'pending' instead of corrupting
-- it), a guaranteed win whose prize sold out would permanently occupy the
-- "next spin" slot for every customer and every other guaranteed win,
-- since nothing ever skipped past it.
--
-- Fix: only consider a pending win a candidate if its prize currently has
-- remaining inventory and hasn't hit its daily limit for today. An
-- unfulfillable win stays 'pending' (visible to the admin to reassign or
-- cancel) but no longer blocks anyone else.
-- -----------------------------------------------------
CREATE OR REPLACE FUNCTION get_pending_guaranteed_win(
    p_user_identifier VARCHAR DEFAULT NULL,
    p_event_id INTEGER DEFAULT 1
)
RETURNS TABLE(
    win_id INTEGER,
    prize_id INTEGER,
    prize_name VARCHAR,
    prize_emoji VARCHAR,
    reason VARCHAR,
    is_next_spin BOOLEAN,
    triggered_count INTEGER,
    max_triggers INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        gw.id AS win_id,
        gw.prize_id,
        p.name AS prize_name,
        p.emoji AS prize_emoji,
        gw.reason,
        (gw.scheduled_at IS NULL) AS is_next_spin,
        gw.triggered_count,
        gw.max_triggers
    FROM guaranteed_wins gw
    JOIN prizes p ON gw.prize_id = p.id
    WHERE gw.status = 'pending'
      AND (
          -- Next spin wins (no schedule)
          gw.scheduled_at IS NULL
          OR
          -- Scheduled wins that are due
          gw.scheduled_at <= NOW()
      )
      AND (
          -- No target specified OR matches the user
          gw.target_identifier IS NULL
          OR gw.target_identifier = p_user_identifier
      )
      AND (
          -- Check max_triggers limit (NULL means unlimited, default 1)
          gw.max_triggers IS NULL
          OR gw.triggered_count < gw.max_triggers
      )
      AND (
          -- Check expiry date
          gw.expires_at IS NULL
          OR gw.expires_at > NOW()
      )
      AND EXISTS (
          -- The prize must actually be winnable today, or this candidate
          -- is skipped instead of jamming the queue for everyone
          SELECT 1
          FROM prize_inventory pi
          WHERE pi.prize_id = gw.prize_id
            AND pi.event_id = p_event_id
            AND pi.available_date = CURRENT_DATE
            AND pi.remaining_quantity > 0
            AND pi.daily_limit > COALESCE((
                SELECT COUNT(*)
                FROM transactions t
                WHERE t.prize_id = gw.prize_id
                  AND t.transaction_type = 'win'
                  AND DATE(t.created_at) = CURRENT_DATE
            ), 0)
      )
    ORDER BY
        gw.priority DESC,
        CASE WHEN gw.scheduled_at IS NULL THEN 0 ELSE 1 END,  -- Next spin first
        gw.created_at ASC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- -----------------------------------------------------
-- Fix: special-event type mismatch between admin UI and DB constraint.
-- admin.html's event-type dropdown offers "National Holiday" and
-- "Custom Event", which the original CHECK constraint rejected, causing
-- a raw DB error on create instead of a usable result.
-- -----------------------------------------------------
ALTER TABLE special_events DROP CONSTRAINT IF EXISTS special_events_event_type_check;
ALTER TABLE special_events ADD CONSTRAINT special_events_event_type_check
    CHECK (event_type IN ('promotion', 'festival', 'flash_sale', 'special', 'national_holiday', 'custom'));

COMMENT ON COLUMN special_events.event_type IS 'Type of event: promotion, festival, flash_sale, special, national_holiday, custom';
