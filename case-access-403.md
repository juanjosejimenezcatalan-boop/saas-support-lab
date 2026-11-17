# Study access restricted by clinic and role

This simulated case uses HTTP Basic authentication with locally configured
passwords. It introduces authorization before a separate token exercise.

## Setup

On an existing lab database, apply the migration once (it also supports reruns):

```bash
psql -d saas_support_lab -v ON_ERROR_STOP=1 -f sql/02-access-control.sql
```

For a fresh database, run `01-setup.sql` first, then `02-access-control.sql`.
Existing studies, including a previously published LAB-001, keep their status
and history and are assigned to clinic_a. New studies must specify clinic_id.

Set three distinct local passwords before starting Flask:

```bash
export LAB_ALICE_PASSWORD='replace-with-a-local-password'
export LAB_BOB_PASSWORD='replace-with-another-local-password'
export LAB_CAROL_PASSWORD='replace-with-a-third-local-password'
```

The placeholder strings illustrate configuration. Choose local values and keep
them outside Git. For the VM service, use a local EnvironmentFile and restart
the service after changing it. Basic authentication here is for a local lab;
its credentials need TLS when crossing an untrusted network.

## Expected results

| User | Clinic | Role | Study | HTTP |
| --- | --- | --- | --- | --- |
| alice | clinic_a | reader | LAB-001 | 200 |
| alice | clinic_a | reader | LAB-002 | 403 |
| bob | clinic_b | reader | LAB-002 | 200 |
| bob | clinic_b | reader | LAB-001 | 403 |
| carol | clinic_a | restricted | LAB-001 | 403 |
| alice | clinic_a | reader | LAB-999 | 404 |
| absent or invalid credentials | — | — | LAB-001 | 401 |

Try `curl -i -u alice http://127.0.0.1:8000/studies/LAB-001` and enter the local
password at the prompt. Changing the identifier to LAB-002 must produce 403.
The server derives clinic and role from app_users, never from client headers or
URL parameters. It checks these on every request. The cross-clinic denial body
contains no study status or owner. This lab intentionally uses 403 for an existing
study owned by another clinic; the difference from 404 reveals that it exists.

## Support reasoning

Compare the authenticated user, role, assigned clinic and study owner. A valid
password does not confer a reader role or ownership of every study. Correct only
a verified erroneous assignment; do not widen access simply to remove an error.

## Operational change

The formerly anonymous studies endpoint now requires authentication. Existing
curl commands need `-u`, and Postman requests need Basic Auth. Authentication is
checked before study lookup. Missing password configuration fails closed with
401. Database/schema errors with credentials present retain the generic 503.

This is simulated access control, without password management, rate limiting,
tokens or a login endpoint.

## Validation

On 17 November 2026, ten PostgreSQL-backed unittest cases passed on the Mac.
The migration was applied twice in an isolated schema after setting LAB-001 to
published; its status and original two history rows were preserved. Both clinic
directions were denied with no study details. Restricted roles and missing or
invalid credentials were checked, alongside 404 and database-error behavior.
The existing VM snapshot remains a record of the previous anonymous API.
