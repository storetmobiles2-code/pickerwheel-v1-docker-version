-- =====================================================
-- BACKFILL: align category_id with budget_tier
--
-- The admin panel no longer lets anyone set category_id independently -
-- it's derived from budget_tier (see BUDGET_TIER_TO_CATEGORY_ID in
-- backend/app/models/prize.py: high_end->1/ultra_rare, mid_budget->2/rare,
-- budget->3/common). Existing rows created before this change may have a
-- category_id that doesn't match that mapping (e.g. a prize created via
-- direct API/test call with an arbitrary category_id + budget_tier pair).
-- One-time realignment so the invariant holds for all pre-existing data,
-- not just prizes created after this migration.
-- =====================================================

UPDATE prizes
SET category_id = CASE budget_tier
    WHEN 'high_end' THEN 1
    WHEN 'mid_budget' THEN 2
    ELSE 3
END
WHERE category_id != CASE budget_tier
    WHEN 'high_end' THEN 1
    WHEN 'mid_budget' THEN 2
    ELSE 3
END;
