# Expired or invalid access token

## Local setup

Apply migrations 01 and 02 and configure the three local passwords from
[the authorization case](case-access-403.md). Install requirements.txt.
Configure a signing secret locally before starting Flask:

```bash
export LAB_TOKEN_SECRET="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
```

Keep this value stable across restarts to preserve tokens until expiry. In the
VM, add it to the protected local EnvironmentFile and restart the API service.
The signing secret, passwords and issued tokens stay outside Git.

## Request and use a token

```bash
curl -i -u alice -X POST http://127.0.0.1:8000/auth/token
```

Enter Alice's configured password. The JSON contains access_token, token_type
Bearer and expires_in 900. The response includes Cache-Control no-store.
In Postman, set local password variables and execute the token request. Its
post-response script stores the successful token in a local collection variable.

Send Authorization: Bearer followed by the token when requesting a study. The
collection includes an allowed own-clinic request, a cross-clinic denial and an
invalid-token request. Existing Basic Auth requests remain supported.

## Diagnosis and recovery

| Situation | Expected behavior |
| --- | --- |
| Valid token, own clinic and reader role | 200 |
| Valid token, another clinic or restricted role | 403 |
| Expired, malformed or incorrectly signed token | 401 |
| Missing or too-short signing secret | 503 for token operations |
| Incorrect Basic credentials at the token endpoint | 401 |

If an integration returns 401, verify that it targets the intended server,
uses the Bearer scheme and has a token issued by that server. Obtain a new token
with valid Basic credentials, then repeat the same study request. Do not paste
tokens into support tickets or Git commits.

## Implementation and scope

This lab uses itsdangerous signed, timestamped tokens with a fixed 15-minute
maximum age. The token contains only the username. It is signed, not encrypted,
and is a lab-specific format rather than JWT or OAuth. Clinic and role are read
from PostgreSQL on every request, so changing a role affects an existing token.
A token authenticates a user; it does not bypass the clinic ownership check.

Changing the signing secret invalidates all previously issued tokens. Password
rotation does not by itself revoke a token before its expiry. Removing the user
or clearing its configured password denies access. There is no refresh endpoint,
per-token revocation list, rate limiting or TLS termination in this lab.

## Verification

The PostgreSQL-backed suite tests expiry by advancing the signing clock in a
controlled test, then verifies successful access with a freshly issued token.
It also covers malformed tokens, unexpected signed payloads, secret rotation,
role changes and the previous Basic Auth regression cases. These checks use the
normal Flask routes and an isolated PostgreSQL schema. The exported Postman
collection has empty password and token values; configure them locally.

[Timestamped signature documentation](https://itsdangerous.palletsprojects.com/en/stable/timed/)
