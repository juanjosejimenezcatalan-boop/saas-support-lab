BEGIN;

CREATE TABLE studies (
    study_id TEXT PRIMARY KEY,
    status TEXT NOT NULL
);

CREATE TABLE study_events (
    event_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    study_id TEXT NOT NULL REFERENCES studies (study_id),
    event_type TEXT NOT NULL,
    detail TEXT NOT NULL
);

INSERT INTO studies (study_id, status)
VALUES ('LAB-001', 'received');

INSERT INTO study_events (study_id, event_type, detail)
VALUES
    ('LAB-001', 'received', 'Study upload accepted'),
    ('LAB-001', 'validation_failed', 'Required metadata missing');

COMMIT;
