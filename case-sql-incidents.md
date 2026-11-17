# Investigate validation failures by clinic and time

## Scenario

Support receives reports of failed studies from several clinics. Determine the
number of affected studies, the number of failure events, the interval of failures
and whether affected studies have since been published.

## Prepare a local lab database

After migrations 01 and 02, apply the timestamp migration and optional synthetic
fixtures. Replace the database name if using a separate reproduction database.

```bash
psql -d saas_support_lab -v ON_ERROR_STOP=1 -f sql/03-event-timestamps.sql
psql -d saas_support_lab -v ON_ERROR_STOP=1 -f sql/04-incident-fixtures.sql
psql -d saas_support_lab -v ON_ERROR_STOP=1 \
  -v from_ts='2026-11-17T00:00:00Z' -v to_ts='2026-11-18T00:00:00Z' \
  -f sql/05-incident-investigation.sql
```

Fixture IDs begin with SQL-. They add six synthetic events across four studies.
Repeated fixture loads do not duplicate matching events. Concurrent executions
of this fixture script are serialized with a transaction advisory lock.

## Expected interpretation

| Clinic | Failure events | Distinct affected studies |
| --- | --- | --- |
| clinic_a | 3 | 2 |
| clinic_b | 1 | 1 |

SQL-A001 failed twice. SQL-A002 failed once and its current state is published.
SQL-B001 failed once. SQL-B002 published without a recorded failure.

The first query uses LEFT JOIN to retain clinics with no failures. Its event
filters are in the join condition so the zero-failure rows survive. COUNT of
event_id ignores null rows and COUNT DISTINCT study_id avoids counting retries
as separate affected studies.

The interval includes from_ts and excludes to_ts. With 09:00Z to 10:00Z on the
fixture date, clinic_b has zero failures because its failure is exactly at 10:00Z.
TIMESTAMPTZ and explicit UTC offsets make the interval unambiguous. Session output
may display timestamps in the local timezone.

The second query reports current study status alongside historical failures.
A published study can still have failed earlier. The third query counts historical
events with unknown time. Migration 03 leaves their timestamps NULL rather than
inventing dates, and only future events get the current-time default.

## Verification and scope

The isolated PostgreSQL suite applies the migrations and fixtures twice, verifies
six fixture events, checks the daily aggregates and boundary behavior, and runs
all three report queries. It preserves the original LAB-001 history and state.
These reports run through psql with a trusted local database account; they are
administrative cross-clinic reports, not a new tenant-facing API endpoint.
They count validation failures, not every possible kind of operational incident.
