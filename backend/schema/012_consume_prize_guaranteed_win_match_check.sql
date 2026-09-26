-- =====================================================
-- FIX: a tampered /api/spin request could mismatch prize_id and
-- guaranteed_win_id
--
-- consume_prize() validates a submitted guaranteed_win_id's status,
-- max_triggers, and expiry - and separately validates the submitted
-- prize_id's is_enabled/stock/daily_limit - but never checks that
-- guaranteed_wins.prize_id actually equals p_prize_id. A caller could
-- submit an unrelated prize_id alongside a real, currently-pending
-- guaranteed_win_id for a DIFFERENT prize: the submitted prize's
-- inventory gets consumed while the mismatched guaranteed win is marked
-- triggered - a data-integrity/free-prize exploit, independent of the
-- is_enabled fix in 009 (which closed a different gap in this same
-- function).
--
-- trigger_guaranteed_win_now (backend/app/routes/admin.py) is unaffected -
-- it derives prize_id from the win itself server-side and never trusts a
-- client-supplied pair. Only the public /api/spin path (which trusts
-- both prize_id and guaranteed_win_id from the client, per the pre-spin/
-- spin flow) was exposed.
--
-- Fix: require gw.prize_id = p_prize_id in the same guaranteed-win
-- validation this function already does.
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
    SELECT p.is_enabled INTO v_is_enabled
    FROM prizes p
    WHERE p.id = p_prize_id
    FOR UPDATE;

    IF NOT FOUND OR NOT v_is_enabled THEN
        RETURN QUERY SELECT FALSE, NULL::INTEGER, 0;
        RETURN;
    END IF;

    SELECT pi.remaining_quantity, pi.daily_limit
    INTO v_remaining, v_daily_limit
    FROM prize_inventory pi
    WHERE pi.prize_id = p_prize_id
      AND pi.event_id = p_event_id
      AND pi.available_date = v_today
    FOR UPDATE;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, NULL::INTEGER, 0;
        RETURN;
    END IF;

    IF v_remaining <= 0 THEN
        RETURN QUERY SELECT FALSE, NULL::INTEGER, 0;
        RETURN;
    END IF;

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
    -- inventory - now including that it's actually FOR this prize, not
    -- just any pending win the client happened to reference.
    IF p_guaranteed_win_id IS NOT NULL THEN
        SELECT TRUE INTO v_gw_found
        FROM guaranteed_wins gw
        WHERE gw.id = p_guaranteed_win_id
          AND gw.prize_id = p_prize_id
          AND gw.status = 'pending'
          AND (gw.max_triggers IS NULL OR gw.triggered_count < gw.max_triggers)
          AND (gw.expires_at IS NULL OR gw.expires_at > NOW())
        FOR UPDATE;

        IF NOT FOUND THEN
            RETURN QUERY SELECT FALSE, NULL::INTEGER, v_remaining;
            RETURN;
        END IF;
    END IF;

    UPDATE prize_inventory
    SET remaining_quantity = remaining_quantity - 1
    WHERE prize_id = p_prize_id
      AND event_id = p_event_id
      AND available_date = v_today;

    INSERT INTO transactions (prize_id, user_identifier, transaction_type, quantity, metadata)
    VALUES (p_prize_id, p_user_identifier, 'win', 1, p_metadata)
    RETURNING id INTO v_transaction_id;

    INSERT INTO audit_log (action, entity_type, entity_id, new_value)
    VALUES ('consume', 'prize', p_prize_id,
            jsonb_build_object('user', p_user_identifier, 'transaction_id', v_transaction_id));

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
    'Atomically consumes prize inventory (checking is_enabled, stock, and daily limit) and, when p_guaranteed_win_id is set, atomically completes that guaranteed win in the same transaction - only if the win is actually for the submitted prize_id.';
