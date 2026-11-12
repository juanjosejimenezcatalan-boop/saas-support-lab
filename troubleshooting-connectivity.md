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

## Distinguish name resolution from IPv4 and IPv6 connectivity

```bash
curl -v http://localhost:8000/studies/LAB-001
```

On the test Mac, `localhost` resolved to both `::1` and `127.0.0.1`. The IPv6 connection was refused. curl then connected through IPv4 and received HTTP `200`.

The server had been started with `--host 127.0.0.1`, so it was listening on IPv4 loopback.

To test each address family separately:

```bash
curl -4 -i http://localhost:8000/studies/LAB-001
curl -6 -i http://localhost:8000/studies/LAB-001
```

IPv4 returned HTTP `200`. IPv6 produced curl error `(7)` without an HTTP response.

These results distinguish successful local name resolution from connectivity to the resolved addresses. They do not test an external DNS server.

## Check external DNS and HTTPS separately

```bash
nslookup example.com
```

The DNS query returned two IPv4 addresses. The `Server` field identified the DNS resolver used for the query; the addresses below `Name` belonged to the requested domain.

```bash
curl -I --connect-timeout 10 --max-time 20 https://example.com
```

The HTTPS request returned HTTP `200`. This verified that the client could reach the external service, complete the HTTPS connection and receive an HTTP response at the time of testing.

A successful DNS query alone does not establish that an application is reachable. Check the connection and application response separately.
