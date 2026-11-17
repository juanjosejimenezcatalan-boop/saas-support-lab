# VMware validation record

Executed on 17 November 2026. This record describes the observed local lab run.

## Environment

| Component | Observed value |
| --- | --- |
| Hypervisor | VMware Fusion 26H1u1, build 25689522 |
| Guest | Ubuntu 24.04.5 LTS, aarch64 |
| Resources | 2 vCPUs, 4096 MiB RAM, 24 GiB sparse virtual NVMe disk |
| Python | 3.12.3 |
| PostgreSQL | 16.15, Ubuntu distribution package |
| VM private address during test | 192.168.12.128/24, enp2s0 |
| Route gateway during test | 192.168.12.2 |
| API | systemd unit saas-support-api, port 8000 |

The IP is an observed DHCP lease and may change. The Mac's original PostgreSQL
17 database is separate and was not modified by this exercise.

The downloaded Canonical ARM64 cloud image matched its published SHA256SUMS:

```text
50e24e1fb79e89116e939d90aa7738f7af48c442fa1bc2510131e0b39c50348e
```

This checks consistency against the vendor's HTTPS checksum file. The checksum
manifest was not separately verified with a GPG signature.

## Host-to-guest API

Executed from the Mac:

```text
PASS LAB-001: HTTP 200 {'status': 'received', 'study_id': 'LAB-001'}
PASS LAB-999: HTTP 404 {'error': 'Study not found', 'study_id': 'LAB-999'}
Connection to 192.168.12.128 port 8000 [tcp/irdmi] succeeded!
```

The HTTP checks used `python3 vmware/check-api.py http://192.168.12.128:8000`.
TCP was checked using `nc -vz -G 3 192.168.12.128 8000`.

## Service outage and recovery

1. Stopped `saas-support-api` with systemctl inside Ubuntu.
2. `systemctl is-active` returned `inactive`.
3. On the Mac, nc reported `Connection refused` and curl exited with code 7.
4. SSH remained usable, confirming the guest was reachable for administration.
5. Started the API with systemctl.
6. Both HTTP checks passed again with 200 and 404 and the expected bodies.

`systemd-analyze verify` reported no errors for the installed service file.

## Snapshot rollback

1. Shut down Ubuntu cleanly using `shutdown -h now`.
2. Created snapshot `baseline-api-working` with Fusion's vmrun tool.
3. Confirmed `listSnapshots` listed exactly that snapshot.
4. Booted the guest, created `/home/lab/after-snapshot-marker` and verified it
   existed (`MARKER_PRESENT`). The API unit was active.
5. Shut down cleanly and reverted this lab VM to the baseline snapshot.
6. Booted again and confirmed the marker was absent (`SNAPSHOT_MARKER_ABSENT`).
7. Both the API and PostgreSQL units were active. SQL showed LAB-001 in received.
8. Repeated both host-to-guest HTTP checks successfully.

## Bootstrap troubleshooting

The initial bootstrap was interrupted by a reboot while application preparation
was incomplete. SSH and PostgreSQL were available, but the repository and schema
were absent. Inspected cloud-init, filesystem and SQL state, then completed the
missing deployment steps. The reproduction guide explicitly requires waiting
for cloud-init completion before rebooting.

An incorrect first IP candidate was the NAT gateway, not the guest. The DHCP
lease associated with the VM's MAC identified the actual guest address. The
reported SSH and HTTP successes use the verified guest address.

Added the guest hostname to /etc/hosts after observing slow privileged operations.
The published cloud-init example includes `manage_etc_hosts: true`.

## Limits

The cloud-init template is supplied as a fresh-VM example; the complete first-boot
path has not been revalidated on a second VM after the hostname improvement.
The deployed application and service, outage recovery and snapshot rollback were
verified on the VM described above. Postman GUI tests were previously performed
against the Mac service; this VM's 200/404 checks were executed with the included
Python checker and curl/nc. ESXi, vCenter, bridged networking, TLS, authentication
and load testing are outside these results.

## Updated application validation · 17 November 2026

Updated the guest to application commit `5542b0f`, installed the pinned
requirements and applied migrations 02 and 03 plus synthetic fixture script 04.
Configured local practice passwords and the signing secret in a root-owned mode
600 EnvironmentFile, then restarted the systemd API service. These values are
not included in this repository.

The Mac's original lab database was migrated too. Its existing LAB-001 remains
published; the independent VM copy remains received. No historical status was
reset by the migrations.

### Live access and tokens

From the Mac, tested both the Mac API and the VM API. Each environment passed
11 live HTTP checks covering Basic Auth, both clinic-isolation directions,
restricted roles, missing studies, anonymous denial, token issuance, authorized
Bearer access, cross-clinic Bearer denial and a tampered token.

The complete exported Postman collection was also executed locally with Newman
against each server. Each run completed 11 requests and 13 assertions with zero
failures. Credentials were injected locally and no issued tokens were exported.
The desktop Postman collection was imported separately without credential values.

### Guest regression and reports

All 21 PostgreSQL-backed unittest cases passed inside Ubuntu with Python 3.12
and PostgreSQL 16. The tests use and remove a separate temporary schema. They
include controlled-clock expiry and secret rotation checks.

Running the report script against the guest lab database returned:

| Clinic | Failure events | Affected studies |
| --- | --- | --- |
| clinic_a | 3 | 2 |
| clinic_b | 1 | 1 |

The detail report showed SQL-A001 received after two failures, SQL-A002 published
after one failure and SQL-B001 received after one failure. Two original events
retained unknown timestamps.

### Updated snapshot

Created an additional snapshot named `access-tokens-ready` after a clean guest
shutdown. The original `baseline-api-working` remains available for the earlier
exercise. Restarted the updated guest and repeated the complete Newman collection
successfully. The new snapshot contains local practice credential configuration;
keep VM disks and snapshots private and outside Git.

The earlier snapshot rollback test remains recorded above. The new snapshot's
creation and subsequent normal boot were verified; a rollback to this additional
snapshot was not separately performed.

### Desktop Postman with Local Vault

Configured three practice passwords in Postman Local Vault and linked the local
collection password variables using vault references. No password values were
shared to the cloud workspace. Restarted Postman after a transient EHOSTUNREACH
error; macOS already showed its Local Network permission enabled.

Executed `SaaS Support Lab - VMware practice` against the guest from the desktop
Collection Runner. The UI reported 13 tests, zero errors and successful completion
of all 11 requests, including token issuance and authorized/denied Bearer access.
The run used local mode with console logging, response persistence and variable
persistence disabled. The repository export retains empty secret values.
