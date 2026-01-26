-- PickerWheel PostgreSQL Schema
-- 002_create_indexes.sql - Performance indexes
-- Created: January 2026

-- =====================================================
-- PRIZES INDEXES
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_prizes_category ON prizes(category_id);
CREATE INDEX IF NOT EXISTS idx_prizes_active ON prizes(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_prizes_enabled ON prizes(is_enabled) WHERE is_enabled = TRUE;
CREATE INDEX IF NOT EXISTS idx_prizes_display_order ON prizes(display_order);
CREATE INDEX IF NOT EXISTS idx_prizes_active_enabled ON prizes(is_active, is_enabled);

-- =====================================================
-- PRIZE INVENTORY INDEXES
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_inventory_date ON prize_inventory(available_date);
CREATE INDEX IF NOT EXISTS idx_inventory_prize ON prize_inventory(prize_id);
CREATE INDEX IF NOT EXISTS idx_inventory_event ON prize_inventory(event_id);
CREATE INDEX IF NOT EXISTS idx_inventory_remaining ON prize_inventory(remaining_quantity) WHERE remaining_quantity > 0;
CREATE INDEX IF NOT EXISTS idx_inventory_date_prize ON prize_inventory(available_date, prize_id);

-- =====================================================
-- TRANSACTIONS INDEXES
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_transactions_prize ON transactions(prize_id);
CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_identifier);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_transactions_created ON transactions(created_at);
-- Note: For date-based queries on transactions, use created_at with range conditions
-- The idx_transactions_created index above handles timestamp-based lookups

-- =====================================================
-- USER SESSIONS INDEXES
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_sessions_ip ON user_sessions(ip_address);
CREATE INDEX IF NOT EXISTS idx_sessions_last_activity ON user_sessions(last_activity);

-- =====================================================
-- AUDIT LOG INDEXES
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_log(created_at);

-- =====================================================
-- DAILY STATS INDEXES
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_stats(stat_date);
CREATE INDEX IF NOT EXISTS idx_daily_stats_event ON daily_stats(event_id);

-- =====================================================
-- EVENTS INDEXES
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_events_status ON events(status);
CREATE INDEX IF NOT EXISTS idx_events_dates ON events(start_date, end_date);
