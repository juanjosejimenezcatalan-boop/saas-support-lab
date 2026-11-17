BEGIN;
-- Serialize repeated fixture loads to avoid duplicating example events.
SELECT pg_advisory_xact_lock(178321046);
INSERT INTO studies (study_id, status, clinic_id) VALUES
    ('SQL-A001', 'received', 'clinic_a'),
    ('SQL-A002', 'published', 'clinic_a'),
    ('SQL-B001', 'received', 'clinic_b'),
    ('SQL-B002', 'published', 'clinic_b')
ON CONFLICT (study_id) DO NOTHING;

INSERT INTO study_events (study_id, event_type, detail, occurred_at)
SELECT v.study_id, v.event_type, v.detail, v.occurred_at::timestamptz
FROM (VALUES
    ('SQL-A001', 'validation_failed', 'Missing accession_number', '2026-11-17T09:00:00Z'),
    ('SQL-A001', 'validation_failed', 'Retry still missing accession_number', '2026-11-17T09:05:00Z'),
    ('SQL-A002', 'validation_failed', 'Missing modality', '2026-11-17T09:10:00Z'),
    ('SQL-A002', 'published', 'Corrected resubmission', '2026-11-17T09:20:00Z'),
    ('SQL-B001', 'validation_failed', 'Missing modality', '2026-11-17T10:00:00Z'),
    ('SQL-B002', 'published', 'Validation passed', '2026-11-17T10:10:00Z')
) AS v(study_id, event_type, detail, occurred_at)
WHERE NOT EXISTS (
    SELECT 1 FROM study_events e
    WHERE e.study_id = v.study_id AND e.event_type = v.event_type
      AND e.detail = v.detail AND e.occurred_at = v.occurred_at::timestamptz
);
COMMIT;
