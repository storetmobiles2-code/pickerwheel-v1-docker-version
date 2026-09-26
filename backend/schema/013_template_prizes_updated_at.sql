-- =====================================================
-- ADD updated_at TO template_prizes
--
-- template_prizes never had an updated_at column, so add_prize_to_template
-- and update_template_prize (backend/app/routes/admin.py) had no way to
-- support optimistic-concurrency checking - unlike every other admin
-- resource (prizes, inventory, special_events, daily_prize_templates,
-- guaranteed_wins), two admins editing the same template-prize row
-- concurrently could silently overwrite each other with no warning.
-- =====================================================

ALTER TABLE template_prizes
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

UPDATE template_prizes SET updated_at = created_at WHERE updated_at IS NULL;

DROP TRIGGER IF EXISTS update_template_prizes_timestamp ON template_prizes;
CREATE TRIGGER update_template_prizes_timestamp
    BEFORE UPDATE ON template_prizes
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();
