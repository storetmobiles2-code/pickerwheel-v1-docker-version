-- PickerWheel PostgreSQL Schema
-- 001_create_tables.sql - Core tables with proper constraints
-- Created: January 2026

-- Enable UUID extension for unique identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- EVENTS TABLE
-- Stores contest/event configuration
-- =====================================================
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'paused', 'ended')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- PRIZE CATEGORIES TABLE
-- Defines prize tiers: ultra_rare, rare, common
-- =====================================================
CREATE TABLE IF NOT EXISTS prize_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    weight INTEGER DEFAULT 10 CHECK (weight >= 0 AND weight <= 100),
    color VARCHAR(20) DEFAULT '#4ECDC4',
    text_color VARCHAR(20) DEFAULT '#FFFFFF',
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- PRIZES TABLE
-- Core prize definitions with enable/disable support
-- =====================================================
CREATE TABLE IF NOT EXISTS prizes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category_id INTEGER NOT NULL REFERENCES prize_categories(id) ON DELETE RESTRICT,
    type VARCHAR(20) DEFAULT 'single' CHECK (type IN ('single', 'combo')),
    emoji VARCHAR(10) DEFAULT '🎁',
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_enabled BOOLEAN DEFAULT TRUE,  -- Controls if prize can be won (shown but excluded from spin)
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- PRIZE INVENTORY TABLE
-- Tracks quantities per date with daily limits
-- =====================================================
CREATE TABLE IF NOT EXISTS prize_inventory (
    id SERIAL PRIMARY KEY,
    prize_id INTEGER NOT NULL REFERENCES prizes(id) ON DELETE CASCADE,
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    available_date DATE NOT NULL,
    initial_quantity INTEGER NOT NULL DEFAULT 0 CHECK (initial_quantity >= 0),
    remaining_quantity INTEGER NOT NULL DEFAULT 0 CHECK (remaining_quantity >= 0),
    daily_limit INTEGER DEFAULT 1 CHECK (daily_limit >= 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(prize_id, event_id, available_date)
);

-- =====================================================
-- TRANSACTIONS TABLE
-- Records all prize wins and adjustments with full audit
-- =====================================================
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    prize_id INTEGER NOT NULL REFERENCES prizes(id) ON DELETE RESTRICT,
    user_identifier VARCHAR(255),
    transaction_type VARCHAR(50) DEFAULT 'win' CHECK (transaction_type IN ('win', 'adjustment', 'refund', 'admin_add', 'admin_remove')),
    quantity INTEGER DEFAULT 1,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- USER SESSIONS TABLE
-- Tracks user activity for analytics
-- =====================================================
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    session_id UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    first_visit TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    total_spins INTEGER DEFAULT 0,
    total_wins INTEGER DEFAULT 0
);

-- =====================================================
-- AUDIT LOG TABLE
-- Complete audit trail for all changes
-- =====================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER,
    old_value JSONB,
    new_value JSONB,
    performed_by VARCHAR(255) DEFAULT 'system',
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- DAILY STATS TABLE
-- Aggregated daily statistics
-- =====================================================
CREATE TABLE IF NOT EXISTS daily_stats (
    id SERIAL PRIMARY KEY,
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    stat_date DATE NOT NULL,
    total_spins INTEGER DEFAULT 0,
    total_wins INTEGER DEFAULT 0,
    unique_users INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(event_id, stat_date)
);

-- =====================================================
-- COMMENTS
-- =====================================================
COMMENT ON TABLE prizes IS 'Prize definitions with is_enabled for excluding from wins while keeping on wheel';
COMMENT ON COLUMN prizes.is_enabled IS 'When FALSE, prize shows on wheel but cannot be won';
COMMENT ON COLUMN prizes.is_active IS 'When FALSE, prize is completely hidden from wheel';
COMMENT ON COLUMN prizes.display_order IS 'Order of prize on the wheel (lower = first)';
