-- =====================================================
-- GUARANTEED WIN ATOMICITY FIX
-- Fixes: a guaranteed win was marked 'triggered' via a separate,
-- already-committed statement BEFORE the prize inventory/daily-limit
-- consumption was attempted. When consumption then failed (prize already
-- won out / daily limit reached), the guaranteed win stayed permanently
-- spent with no matching transaction, desyncing the admin's Guaranteed
-- Win, Prize Win, and Daily Quantity panels.
--
-- Fix: fold guaranteed-win validation and completion into the same
-- consume_prize() call that decrements inventory, so both succeed or
-- both fail together.
-- =====================================================

CREATE OR REPLACE FUNCTION consume_prize(
    p_prize_id INTEGER,
    p_event_id INTEGER,
    p_user_identifier VARCHAR(255) DEFAULT NULL,
    p_metadata JSONB DEFAULT '{}',
    p_guaranteed_win_id INTEGER DEFAULT NULL
)
RETURNS TABLE(success BOOLEAN, transaction_id INTEGER, remaining INTEGER) AS $$
DECLARE
    v_remaining INTEGER;
    v_daily_limit INTEGER;
    v_wins_today INTEGER;
    v_transaction_id INTEGER;
    v_today DATE := CURRENT_DATE;
    v_gw_found BOOLEAN;
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

    -- If fulfilling a guaranteed win, lock and validate it BEFORE mutating
    -- inventory, so a stale/already-used/cancelled win aborts cleanly
    -- instead of being marked triggered with nothing consumed.
    IF p_guaranteed_win_id IS NOT NULL THEN
        SELECT TRUE INTO v_gw_found
        FROM guaranteed_wins gw
        WHERE gw.id = p_guaranteed_win_id
          AND gw.status = 'pending'
          AND (gw.max_triggers IS NULL OR gw.triggered_count < gw.max_triggers)
          AND (gw.expires_at IS NULL OR gw.expires_at > NOW())
        FOR UPDATE;

        IF NOT FOUND THEN
            RETURN QUERY SELECT FALSE, NULL::INTEGER, v_remaining;
            RETURN;
        END IF;
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

    -- Only now mark the guaranteed win as triggered - same transaction as
    -- the inventory decrement above, so a rollback of one rolls back both.
    IF p_guaranteed_win_id IS NOT NULL THEN
        UPDATE guaranteed_wins
        SET triggered_count = triggered_count + 1,
            triggered_at = CURRENT_TIMESTAMP,
            triggered_by_user = p_user_identifier,
            status = CASE
                WHEN max_triggers IS NOT NULL AND triggered_count + 1 >= max_triggers
                THEN 'triggered'
                ELSE 'pending'
            END,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = p_guaranteed_win_id;
    END IF;

    RETURN QUERY SELECT TRUE, v_transaction_id, v_remaining - 1;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION consume_prize(INTEGER, INTEGER, VARCHAR, JSONB, INTEGER) IS
    'Atomically consumes prize inventory and, when p_guaranteed_win_id is set, atomically completes that guaranteed win in the same transaction.';
