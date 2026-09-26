-- =====================================================
-- FIX: a disabled prize could still be awarded
--
-- get_available_prizes() (used by POST /api/pre-spin) correctly excludes
-- is_enabled = FALSE prizes from selection. But the wheel animation takes
-- several seconds between /pre-spin (which picks the prize) and /spin
-- (which calls consume_prize() to actually award it) - and consume_prize()
-- never re-checked is_enabled, only remaining_quantity and daily_limit.
--
-- If an admin disabled a prize (or, since the budget-tier master toggle,
-- an entire tier of prizes at once) during that window, /spin still
-- awarded it: consume_prize() had no reason to refuse. Same gap let a
-- pending guaranteed win bypass is_enabled entirely, since
-- select_winning_prize()'s guaranteed-win branch never checked it either
-- - both paths go through this one function to actually consume the
-- prize, so fixing it here closes both at once.
--
-- Fix: lock and check prizes.is_enabled alongside the existing inventory
-- checks, before decrementing anything. A disabled prize now fails the
-- same way an out-of-stock one already did (fails clean, no transaction
-- recorded) instead of being silently awarded.
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
    v_is_enabled BOOLEAN;
BEGIN
    -- Lock the prize row too (not just inventory), so a concurrent
    -- disable-tier/disable-prize UPDATE either commits before this
    -- transaction sees it or waits behind this transaction's lock -
    -- either way, no window where a spin reads "enabled" but a
    -- since-committed disable never gets checked.
    SELECT p.is_enabled INTO v_is_enabled
    FROM prizes p
    WHERE p.id = p_prize_id
    FOR UPDATE;

    IF NOT FOUND OR NOT v_is_enabled THEN
        RETURN QUERY SELECT FALSE, NULL::INTEGER, 0;
        RETURN;
    END IF;

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
    'Atomically consumes prize inventory (checking is_enabled, stock, and daily limit) and, when p_guaranteed_win_id is set, atomically completes that guaranteed win in the same transaction.';
