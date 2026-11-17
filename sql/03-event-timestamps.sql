BEGIN;
ALTER TABLE study_events ADD COLUMN IF NOT EXISTS occurred_at TIMESTAMPTZ;
-- Historical event times are unknown; only new events receive a default time.
ALTER TABLE study_events ALTER COLUMN occurred_at SET DEFAULT CURRENT_TIMESTAMP;
CREATE INDEX IF NOT EXISTS study_events_failure_time
ON study_events (occurred_at, study_id) WHERE event_type = 'validation_failed';
COMMIT;
