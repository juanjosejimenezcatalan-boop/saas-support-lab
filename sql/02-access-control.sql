BEGIN;

CREATE TABLE IF NOT EXISTS clinics (
    clinic_id TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
INSERT INTO clinics VALUES ('clinic_a', 'Demo Clinic A'), ('clinic_b', 'Demo Clinic B')
ON CONFLICT (clinic_id) DO NOTHING;

ALTER TABLE studies ADD COLUMN IF NOT EXISTS clinic_id TEXT REFERENCES clinics (clinic_id);
-- Existing lab studies are assigned explicitly during this migration.
UPDATE studies SET clinic_id = 'clinic_a' WHERE clinic_id IS NULL;
ALTER TABLE studies ALTER COLUMN clinic_id SET NOT NULL;

CREATE TABLE IF NOT EXISTS app_users (
    username TEXT PRIMARY KEY,
    clinic_id TEXT NOT NULL REFERENCES clinics (clinic_id),
    role TEXT NOT NULL CHECK (role IN ('reader', 'restricted')),
    password_env TEXT NOT NULL UNIQUE
);
INSERT INTO app_users VALUES
    ('alice', 'clinic_a', 'reader', 'LAB_ALICE_PASSWORD'),
    ('bob', 'clinic_b', 'reader', 'LAB_BOB_PASSWORD'),
    ('carol', 'clinic_a', 'restricted', 'LAB_CAROL_PASSWORD')
ON CONFLICT (username) DO NOTHING;

INSERT INTO studies (study_id, status, clinic_id)
VALUES ('LAB-002', 'received', 'clinic_b')
ON CONFLICT (study_id) DO NOTHING;

COMMIT;
