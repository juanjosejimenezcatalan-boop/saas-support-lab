# SaaS Support Lab

A technical support exercise based on a fictional medical imaging portal. A clinic reports that study `LAB-001` is missing from the portal after upload.

## Reproduce the incident

You need PostgreSQL 17 running locally and access to `createdb` and `psql`. Run the commands from the repository folder. Use a fresh database for the setup script.

```bash
createdb saas_support_repro
psql -d saas_support_repro -v ON_ERROR_STOP=1 -f sql/01-setup.sql
```

If you installed PostgreSQL 17 with Homebrew and your shell cannot find the commands, run `export PATH="$(brew --prefix postgresql@17)/bin:$PATH"` in the current terminal before running the setup.

## Investigate

Connect with `psql -d saas_support_repro` and run:

```sql
SELECT s.study_id, s.status, e.event_type, e.detail
FROM studies AS s
JOIN study_events AS e ON e.study_id = s.study_id
WHERE s.study_id = 'LAB-001'
ORDER BY e.event_id;
```

The query returns the study's stored status and two events. The upload was accepted, then validation failed. To identify the missing field, return to your terminal with `\q` and search the simulated validation log:

```bash
grep -F 'study_id=LAB-001 ' logs/validation.log
```

## Case report

See [the support ticket](case-lab-001.md) for the diagnosis, the customer response and the verification after the simulated resubmission. All study data and log entries are fictional.
