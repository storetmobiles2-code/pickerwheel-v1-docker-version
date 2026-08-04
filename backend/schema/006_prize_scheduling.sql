-- =====================================================
-- PRIZE SCHEDULING SYSTEM
-- Templates, date assignments, and guaranteed wins
-- =====================================================

-- =====================================================
-- DAILY PRIZE TEMPLATES
-- Define reusable prize configurations
-- =====================================================
CREATE TABLE IF NOT EXISTS daily_prize_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Ensure only one default template
CREATE UNIQUE INDEX IF NOT EXISTS idx_single_default_template 
ON daily_prize_templates (is_default) WHERE is_default = TRUE;

-- =====================================================
-- TEMPLATE PRIZES
-- Prizes and quantities for each template
-- =====================================================
CREATE TABLE IF NOT EXISTS template_prizes (
    id SERIAL PRIMARY KEY,
    template_id INTEGER NOT NULL REFERENCES daily_prize_templates(id) ON DELETE CASCADE,
    prize_id INTEGER NOT NULL REFERENCES prizes(id) ON DELETE CASCADE,
    quantity INTEGER DEFAULT 1 CHECK (quantity >= 0),
    daily_limit INTEGER DEFAULT NULL,  -- Max wins per day, NULL = unlimited
    is_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(template_id, prize_id)
);

CREATE INDEX IF NOT EXISTS idx_template_prizes_template ON template_prizes(template_id);
CREATE INDEX IF NOT EXISTS idx_template_prizes_prize ON template_prizes(prize_id);

-- =====================================================
-- DATE TEMPLATE ASSIGNMENTS
-- Assign templates to specific dates
-- =====================================================
CREATE TABLE IF NOT EXISTS date_template_assignments (
    id SERIAL PRIMARY KEY,
    target_date DATE NOT NULL,
    template_id INTEGER NOT NULL REFERENCES daily_prize_templates(id) ON DELETE CASCADE,
    notes TEXT,  -- Optional notes for this date
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(target_date)
);

CREATE INDEX IF NOT EXISTS idx_date_assignments_date ON date_template_assignments(target_date);
CREATE INDEX IF NOT EXISTS idx_date_assignments_template ON date_template_assignments(template_id);

-- =====================================================
-- GUARANTEED WINS QUEUE
-- Schedule specific prize wins
-- =====================================================
CREATE TABLE IF NOT EXISTS guaranteed_wins (
    id SERIAL PRIMARY KEY,
    prize_id INTEGER NOT NULL REFERENCES prizes(id) ON DELETE CASCADE,
    scheduled_at TIMESTAMP WITH TIME ZONE,  -- NULL = next spin (immediate)
    target_identifier VARCHAR(255),          -- Optional: specific user/phone/IP
    reason VARCHAR(255),                     -- Admin note: "VIP reward", "Demo", etc.
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'triggered', 'expired', 'cancelled')),
    priority INTEGER DEFAULT 0,              -- Higher priority = processed first
    triggered_at TIMESTAMP WITH TIME ZONE,
    triggered_by_user VARCHAR(255),          -- Who actually won it
    created_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_guaranteed_wins_status ON guaranteed_wins(status);
CREATE INDEX IF NOT EXISTS idx_guaranteed_wins_scheduled ON guaranteed_wins(scheduled_at) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_guaranteed_wins_target ON guaranteed_wins(target_identifier) WHERE target_identifier IS NOT NULL;

-- =====================================================
-- ENHANCE GUARANTEED_WINS TABLE
-- Add quantity limits and expiry
-- =====================================================
DO $$
BEGIN
    -- max_triggers: How many times this win can be triggered (NULL = 1 for backwards compatibility)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'guaranteed_wins' AND column_name = 'max_triggers') THEN
        ALTER TABLE guaranteed_wins ADD COLUMN max_triggers INTEGER DEFAULT 1;
    END IF;
    
    -- triggered_count: How many times this win has been triggered so far
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'guaranteed_wins' AND column_name = 'triggered_count') THEN
        ALTER TABLE guaranteed_wins ADD COLUMN triggered_count INTEGER DEFAULT 0;
    END IF;
    
    -- expires_at: Stop triggering after this date even if max_triggers not reached
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'guaranteed_wins' AND column_name = 'expires_at') THEN
        ALTER TABLE guaranteed_wins ADD COLUMN expires_at TIMESTAMP WITH TIME ZONE;
    END IF;
END $$;

COMMENT ON COLUMN guaranteed_wins.max_triggers IS 'Max times this can be triggered (1 = single win, NULL = unlimited)';
COMMENT ON COLUMN guaranteed_wins.triggered_count IS 'How many times triggered so far';
COMMENT ON COLUMN guaranteed_wins.expires_at IS 'Stop after this date even if max_triggers not reached';

-- =====================================================
-- ENHANCE SPECIAL EVENTS TABLE
-- Add banner text and featured flag
-- =====================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'special_events' AND column_name = 'banner_text') THEN
        ALTER TABLE special_events ADD COLUMN banner_text VARCHAR(255);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'special_events' AND column_name = 'is_featured') THEN
        ALTER TABLE special_events ADD COLUMN is_featured BOOLEAN DEFAULT FALSE;
    END IF;
END $$;

-- =====================================================
-- HELPER FUNCTIONS
-- =====================================================

-- Get template for a specific date (or default)
CREATE OR REPLACE FUNCTION get_template_for_date(p_date DATE)
RETURNS INTEGER AS $$
DECLARE
    v_template_id INTEGER;
BEGIN
    -- First check for date-specific assignment
    SELECT template_id INTO v_template_id
    FROM date_template_assignments
    WHERE target_date = p_date;
    
    -- If no specific assignment, get default template
    IF v_template_id IS NULL THEN
        SELECT id INTO v_template_id
        FROM daily_prize_templates
        WHERE is_default = TRUE AND is_active = TRUE
        LIMIT 1;
    END IF;
    
    RETURN v_template_id;
END;
$$ LANGUAGE plpgsql;

-- Get pending guaranteed win for a user
CREATE OR REPLACE FUNCTION get_pending_guaranteed_win(
    p_user_identifier VARCHAR DEFAULT NULL
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
    ORDER BY 
        gw.priority DESC,
        CASE WHEN gw.scheduled_at IS NULL THEN 0 ELSE 1 END,  -- Next spin first
        gw.created_at ASC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- SEED DEFAULT TEMPLATE
-- =====================================================
INSERT INTO daily_prize_templates (name, description, is_default, is_active)
VALUES ('Default Template', 'Standard daily prize configuration', TRUE, TRUE)
ON CONFLICT DO NOTHING;

-- =====================================================
-- COMMENTS
-- =====================================================
COMMENT ON TABLE daily_prize_templates IS 'Reusable prize configuration templates';
COMMENT ON TABLE template_prizes IS 'Prizes and quantities for each template';
COMMENT ON TABLE date_template_assignments IS 'Assign templates to specific dates';
COMMENT ON TABLE guaranteed_wins IS 'Queue of scheduled/guaranteed prize wins';
COMMENT ON COLUMN guaranteed_wins.scheduled_at IS 'NULL means next spin (immediate)';
COMMENT ON COLUMN guaranteed_wins.target_identifier IS 'Optional user phone/IP to target';
