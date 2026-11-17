-- Supply from_ts and to_ts with psql -v. The interval is [from_ts, to_ts).
-- Count retries separately from affected studies. Include clinics with zero failures.
SELECT c.clinic_id, count(e.event_id) AS failure_events,
       count(DISTINCT e.study_id) AS affected_studies,
       min(e.occurred_at) AS first_failure, max(e.occurred_at) AS last_failure
FROM clinics c
LEFT JOIN studies s ON s.clinic_id = c.clinic_id
LEFT JOIN study_events e ON e.study_id = s.study_id
    AND e.event_type = 'validation_failed'
    AND e.occurred_at >= :'from_ts'::timestamptz
    AND e.occurred_at < :'to_ts'::timestamptz
GROUP BY c.clinic_id
ORDER BY c.clinic_id;

-- Current state can differ from the state at the time of a historical failure.
SELECT s.study_id, s.clinic_id, s.status AS current_status,
       count(*) AS failure_events, min(e.occurred_at) AS first_failure
FROM studies s
JOIN study_events e ON e.study_id = s.study_id
WHERE e.event_type = 'validation_failed'
  AND e.occurred_at >= :'from_ts'::timestamptz
  AND e.occurred_at < :'to_ts'::timestamptz
GROUP BY s.study_id, s.clinic_id, s.status
ORDER BY s.clinic_id, s.study_id;

-- Preserve and report events whose historical timestamps are unknown.
SELECT count(*) AS events_with_unknown_time
FROM study_events WHERE occurred_at IS NULL;
