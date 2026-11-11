# API returns 503 after a database configuration change

**Scenario.** A simulated configuration change caused `GET /studies/LAB-001` to return HTTP `503` with the JSON error `Database unavailable`.

**Reproduction.** I started the Flask application with `DATABASE_URL` set to `dbname=saas_support_missing connect_timeout=5`, then requested a study known to exist.

**Evidence.** The application logged `Database query failed`. The PostgreSQL error identified the cause:

```text
FATAL: database "saas_support_missing" does not exist
```

**Diagnosis.** PostgreSQL was reachable, but the application was configured to connect to a database that did not exist.

**Resolution.** I stopped Flask and restarted it using the default connection configuration for `saas_support_lab`.

**Verification.** I repeated `GET /studies/LAB-001`. The API returned HTTP `200` with `{"status":"published","study_id":"LAB-001"}`.

**Scope.** This exercise verifies recovery from an incorrect database name. The application currently returns the same generic `503` response for PostgreSQL errors, so the server log is needed to distinguish their causes.
