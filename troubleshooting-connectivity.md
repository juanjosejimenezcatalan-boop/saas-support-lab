# Diagnose local API connectivity

This exercise uses a Flask API listening on `127.0.0.1:8000`. All checks run on the same Mac as the server.

## Identify the listening process

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
```

With Flask running, this showed a Python process listening on `127.0.0.1:8000`. The PID identifies the process and can change after a restart.

## Check the TCP connection

```bash
nc -vz 127.0.0.1 8000
```

Stopping Flask with Control+C produced `Connection refused`. Restarting Flask restored a successful connection.

In this exercise, stopping the server caused the refusal. In another incident, check the listening process, address and port before drawing a conclusion.

## Inspect the HTTP exchange

```bash
curl -v http://127.0.0.1:8000/studies/LAB-001
```

The output showed a successful TCP connection, the outgoing GET request and an HTTP `200` response containing the stored study status.

An HTTP `404` or `503` is also evidence that an HTTP server responded. Use the response body and application logs to investigate the cause.

## Scope

These checks verify local connectivity through the loopback address. Access from another computer, DNS, firewall rules and virtual machine networking require separate checks.# Diagnose local API connectivity

This exercise uses a Flask API listening on `127.0.0.1:8000`. All checks run on the same Mac as the server.

## Identify the listening process

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
```

With Flask running, this showed a Python process listening on `127.0.0.1:8000`. The PID identifies the process and can change after a restart.

## Check the TCP connection

```bash
nc -vz 127.0.0.1 8000
```

Stopping Flask with Control+C produced `Connection refused`. Restarting Flask restored a successful connection.

In this exercise, stopping the server caused the refusal. In another incident, check the listening process, address and port before drawing a conclusion.

## Inspect the HTTP exchange

```bash
curl -v http://127.0.0.1:8000/studies/LAB-001
```

The output showed a successful TCP connection, the outgoing GET request and an HTTP `200` response containing the stored study status.

An HTTP `404` or `503` is also evidence that an HTTP server responded. Use the response body and application logs to investigate the cause.

## Scope

These checks verify local connectivity through the loopback address. Access from another computer, DNS, firewall rules and virtual machine networking require separate checks.
