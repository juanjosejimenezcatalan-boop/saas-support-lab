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

## Run the local API

After creating the database with `sql/01-setup.sql`, run these commands from the repository folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
DATABASE_URL="dbname=saas_support_repro connect_timeout=5" python -m flask --app app run --host 127.0.0.1 --port 8000
```

Keep the server running and open another terminal to send requests:

```bash
curl -i http://127.0.0.1:8000/studies/LAB-001
curl -i http://127.0.0.1:8000/studies/LAB-999
```

The first request returns HTTP `200` with the stored study status. A fresh setup contains `LAB-001` in `received`. The second request returns HTTP `404` because `LAB-999` does not exist.

The API defaults to `saas_support_lab` when `DATABASE_URL` is omitted. The command above explicitly selects the reproduction database created earlier in this README.

See [the database configuration incident](case-api-503.md) for a simulated HTTP `503` failure and recovery. PostgreSQL errors are recorded in the server terminal.

This API uses Flask's development server and listens locally on port `8000`.

## Test the API with Postman

Import `postman/saas-support-lab.postman_collection.json` into Postman. The collection includes a `base_url` variable set to `http://127.0.0.1:8000`.

Start the Flask API before sending requests. The collection contains two requests with four automated checks:

- **Get existing study** checks HTTP `200`, the requested study identifier and a non-empty status.
- **Get missing study** checks HTTP `404`, the error message and the missing study identifier.

Both requests were verified after importing the exported JSON.

If Postman reports `ECONNREFUSED`, check that Flask is running at the address and port configured in `base_url`.

## Diagnose connectivity

See [the local connectivity guide](troubleshooting-connectivity.md) for a practical sequence using `lsof`, `nc` and `curl -v`. The exercise covers a stopped Flask server, connection refusal and recovery after restart.
