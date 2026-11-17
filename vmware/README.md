# VMware Fusion lab

This extends the support exercise to a Linux virtual machine. The Mac acts as
an HTTP client; Ubuntu runs Flask and PostgreSQL.

[Observed validation results](validation.md)

## Design

- VMware Fusion 26H1u1 on an Apple Silicon Mac.
- Ubuntu 24.04 LTS ARM64, 2 virtual CPUs, 4 GiB RAM, 24 GiB thin virtual NVMe disk.
- NAT networking, with no router port forwarding configured by this exercise.
- SSH public-key access to the `lab` account. Its private key stays on the Mac.
- PostgreSQL uses its local Unix socket. Its port is not published to the Mac.
- Flask listens on `0.0.0.0:8000` inside the guest, allowing access through the
  guest's private IP. Loopback in the guest refers to the guest itself.
- A systemd unit runs the lab API as `lab` and records logs in the journal.

The default Ubuntu repository supplies PostgreSQL 16. The original Mac lab uses
17. This VM uses only schema and queries supported by both versions. Check the
validation record for actual test results.

## Reproduce

Create an Ubuntu ARM64 VM in Fusion with the resources above and NAT networking.
Use Ubuntu's official installer, or its official cloud image with NoCloud.
For cloud images, the local workflow converts QCOW2 to VMDK with `qemu-img`,
expands the disk with Fusion's `vmware-vdiskmanager`, and attaches an ISO labelled
`cidata` containing `user-data` and `meta-data`.

`user-data.example` documents the bootstrap commands. Replace the SSH public-key
placeholder before use. Set a unique `instance-id` and `local-hostname` in
`meta-data`. Wait for `cloud-init status --wait` to finish before restarting.
The initial SQL setup requires an empty database. The bootstrap is for a fresh
VM, not a general rerunnable migration script.

After bootstrap, copy `saas-support-api.service` into the VM and run:

```bash
sudo install -m 644 saas-support-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now saas-support-api
systemctl is-active saas-support-api
```

The service assumes the repository is at `/home/lab/saas-support-lab` and a local
PostgreSQL role and database named `lab` and `saas_support_lab` respectively.

Discover the private IP inside Ubuntu:

```bash
ip -brief address
ip route
```

On the Mac, replace `VM_IP` with that address:

```bash
nc -vz VM_IP 8000
curl -i http://VM_IP:8000/studies/LAB-001
curl -i http://VM_IP:8000/studies/LAB-999
python3 vmware/check-api.py http://VM_IP:8000
```

In a freshly prepared VM, `LAB-001` is `received`. The Mac's original resolved
case may be `published`. These are independent databases.

For Postman, import the existing collection and set `base_url` to
`http://VM_IP:8000`. Check both requests and their post-response tests.

## Service incident

Inside the VM:

```bash
sudo systemctl stop saas-support-api
systemctl is-active saas-support-api
```

From the Mac, retry the TCP and HTTP checks. Connection refusal is expected
while the API is stopped. SSH remains available, helping distinguish a stopped
application from a completely unreachable VM.

Recover inside Ubuntu:

```bash
sudo systemctl start saas-support-api
systemctl is-active saas-support-api
journalctl -u saas-support-api --no-pager -n 30
```

Repeat the Mac checks against the same IP and study identifier.

## Snapshot exercise

Shut down Ubuntu cleanly before taking a baseline snapshot. In Fusion's snapshot
manager, create `baseline-api-working`. Start the VM, make a disposable marker
file in the guest, and shut it down cleanly again. Revert only this lab VM to the
baseline snapshot, boot it, verify the marker is absent and repeat the API checks.

Snapshots roll back guest disk state, including database changes after the
snapshot. A snapshot depends on its underlying VM disks and is not an independent
backup. Keep them limited to the learning exercise and monitor disk consumption.

## Scope

This is a local development lab. It uses Flask's development server, a simple
API without authentication and an administrative lab SSH account. NAT allows
outbound access and host-to-guest testing; other guests on that private network
may also have access. Production requires a separate design for authentication,
TLS, filtering, monitoring, backups and application serving.

The repository contains text configuration and evidence. Disk images, snapshots,
private keys, generated seed ISOs and live databases stay outside Git.

## References

- [Ubuntu cloud images](https://cloud-images.ubuntu.com/noble/current/)
- [Cloud-init NoCloud](https://cloudinit.readthedocs.io/en/latest/reference/datasources/nocloud.html)
- [Fusion ARM compatibility](https://knowledge.broadcom.com/external/article/315602/compatibility-considerations-for-arm-gue.html)
