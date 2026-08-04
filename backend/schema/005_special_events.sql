-- =====================================================
-- SPECIAL EVENTS TABLE
-- For festival/promotional prize activations
-- =====================================================
CREATE TABLE IF NOT EXISTS special_events (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    event_type VARCHAR(50) DEFAULT 'promotion' CHECK (event_type IN ('promotion', 'festival', 'flash_sale', 'special')),
    start_datetime TIMESTAMP WITH TIME ZONE NOT NULL,
    end_datetime TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    theme_config JSONB DEFAULT '{}',  -- Frontend theme configuration for this event
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- SPECIAL EVENT PRIZES (Many-to-Many)
-- Links special events to specific prizes with boost multipliers
-- =====================================================
CREATE TABLE IF NOT EXISTS special_event_prizes (
    id SERIAL PRIMARY KEY,
    special_event_id INTEGER NOT NULL REFERENCES special_events(id) ON DELETE CASCADE,
    prize_id INTEGER NOT NULL REFERENCES prizes(id) ON DELETE CASCADE,
    boost_enabled BOOLEAN DEFAULT TRUE,
    weight_multiplier DECIMAL(5,2) DEFAULT 1.5,  -- 1.5x = 50% more likely to win
    quantity_override INTEGER,  -- Optional: override the regular quantity for this event
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(special_event_id, prize_id)
);

-- =====================================================
-- INDEXES
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_special_events_dates ON special_events(start_datetime, end_datetime);
CREATE INDEX IF NOT EXISTS idx_special_events_active ON special_events(is_active);
CREATE INDEX IF NOT EXISTS idx_special_event_prizes_event ON special_event_prizes(special_event_id);
CREATE INDEX IF NOT EXISTS idx_special_event_prizes_prize ON special_event_prizes(prize_id);

-- =====================================================
-- COMMENTS
-- =====================================================
COMMENT ON TABLE special_events IS 'Time-bound promotional events like festivals or flash sales';
COMMENT ON COLUMN special_events.event_type IS 'Type of event: promotion, festival, flash_sale, special';
COMMENT ON COLUMN special_events.theme_config IS 'JSON configuration for frontend theming (background, wheel colors, header, etc.)';
COMMENT ON COLUMN special_event_prizes.weight_multiplier IS 'Multiplier for prize selection weight during event';
COMMENT ON COLUMN special_event_prizes.quantity_override IS 'Optional quantity override for this event period';

-- Migration: Add theme_config column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'special_events' AND column_name = 'theme_config'
    ) THEN
        ALTER TABLE special_events ADD COLUMN theme_config JSONB DEFAULT '{}';
    END IF;
END $$;
