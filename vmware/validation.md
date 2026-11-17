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
