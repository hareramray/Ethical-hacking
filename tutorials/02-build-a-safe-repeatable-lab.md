# 02. Build a lab you can explain and restore

[Index](README.md) | [Complete source curriculum](curriculum/02-build-a-safe-repeatable-lab.md) | [Original roadmap](../roadmaps/02-build-a-safe-repeatable-lab.md)

## Prerequisites and outcome

Complete tutorial 01 and use only equipment you own or are authorized to configure. Start with one ordinary Linux VM or an existing local development environment. You need a text editor, Python 3 for the tiny service below, and console access. Hypervisor installation is platform-specific: check the publisher's current requirements and your license before selecting one. This lesson focuses on design, verification, and recovery rather than a fragile click-by-click installer walkthrough.

The finished lab has an inventory, diagram, flow policy, synthetic service, observable logs, reset instructions, and demonstrated restoration. A complicated lab without these properties teaches troubleshooting by accident rather than security deliberately.

## 1. Size the lab around an exercise

Survey host OS/edition, CPU architecture, virtualization support, RAM, free disk, existing hypervisors, backup location, and organizational restrictions. Leave memory and storage for the host, snapshots, updates, and logs. Resource allocation is not a competition: an unresponsive host makes observations unreliable.

About 8 GB of RAM suggests one small VM or browser training environment; about 16 GB often permits a workstation plus one or two modest targets; about 32 GB can support a small domain lab depending on allocations. These are planning estimates, not minimum requirements. Hosted training may be the practical choice when local resources are unavailable.

| Mechanism | What it provides | Boundary to inspect |
| --- | --- | --- |
| VM | Guest OS/kernel with virtual CPU, memory, disks, and adapters | Hypervisor, device passthrough, shared folders, clipboard |
| Container | Application environment with kernel-level isolation features | Shared kernel, mounted paths, published ports, privileges |
| WSL/compatibility environment | Convenient development and integration with the host | Windows paths, network access, host execution, credentials |
| Snapshot/checkpoint | A point to revert selected VM state | External volumes, other services, notes, and backup independence |
| Clone | Another instance derived from an image | Copied identities, addresses, secrets, and resource consumption |

CPU virtualization makes guest execution efficient, but does not make every integration safe. A virtual disk is a file or storage object backing a guest's disk; deleting a guest does not necessarily delete every associated disk or snapshot. Learn your hypervisor's inventory and storage layout before multiplying machines.

Start with a general-purpose Linux distribution for administration. A security distribution can become a later tools workstation. Use publisher-provided or otherwise documented trusted images, record release and architecture, verify supplied signatures/checksums through a trusted channel, and record license/evaluation terms for Windows images. A hash downloaded from the same compromised place as an image does not independently establish publisher trust.

## 2. Establish a clean baseline

Create a normal account, apply appropriate updates, verify clock/time zone, document adapters, and confirm console recovery. Record package/image versions and image source. Save a baseline after the system works and before deliberate configuration weaknesses. A powered-off baseline simplifies consistency; application-aware checkpoints have their own platform requirements.

Keep the clean image separate from changing experiments. A snapshot chain still depends on its storage; it is not an independent backup. Back up notes and important configuration separately, and rehearse rebuilding from those files. Record which artifacts live on the host and which belong to the guest snapshot.

Use an inventory like this:

| Field | Example |
| --- | --- |
| Hostname / owner | target01 / learner |
| Purpose | Synthetic static web content |
| Image and version | Exact installed distribution/release |
| Network / address | Internal lab / recorded private address |
| Credentials | Password-manager reference, never password text |
| Baseline | clean-2026-10; capture actual date |
| Data reset | Copy synthetic fixture from documented source |
| Recovery | Restore baseline and verify content plus permissions |

## 3. Draw connectivity before enabling it

```text
Personal host
  └─ Hypervisor
       └─ internal/private virtual switch
            ├─ tester
            ├─ target
            └─ optional logger
Temporary update adapter: enabled only for deliberate maintenance
```

Bridged networking places a guest on a physical network. NAT usually translates guest traffic through an upstream system and may include configurable forwarding. Host-only includes the host, so the host is part of that trust boundary. Internal/private networking normally confines communication to connected guests, but exact terminology differs by hypervisor. Inspect actual adapter and forwarding configuration.

Choose a private range that does not overlap your home network, VPN, or other virtual networks. Record each interface, subnet, gateway, DNS server, and route. A vulnerable target normally needs no Internet default route for these lessons. If a tester has two adapters, confirm it is not forwarding between them. Check IPv4 and IPv6; an IPv4 restriction does not establish IPv6 isolation.

| Flow | Intended result | Evidence |
| --- | --- | --- |
| Tester → target service | Allowed on the single lesson port | Successful request and target log |
| Target → logger | Allowed only if configured | Benign event appears with correct identity/time |
| Target → personal network | No route or explicit deny | Route/forwarding inspection and permitted owned-endpoint check |
| Internet → vulnerable target | No ingress or published forwarding | Hypervisor, router, host, and container configuration |
| Update guest → update sources | Controlled maintenance access | Temporary route and connection record; removed afterward |

A failed connection might mean a broken service rather than isolation. Always pair a positive permitted check with configuration inspection and an appropriate negative check. Do not probe unrelated systems to “prove” the boundary.

## 4. Run a tiny synthetic service

In a Linux guest with Python 3, create a new dedicated directory:

```bash
mkdir -p "$HOME/lab-web/content" "$HOME/lab-web/evidence"
printf '%s\n' 'Synthetic lab page' > "$HOME/lab-web/content/index.html"
python3 -m http.server 8000 --bind 127.0.0.1 --directory "$HOME/lab-web/content"
```

This is an educational static server, not a production application. The explicit loopback binding confines this first exercise to that guest. Python documents both the command-line binding option and the server's limited security scope. [Python HTTP server reference](https://docs.python.org/3/library/http.server.html)

In another terminal:

```bash
curl --max-time 3 -i http://127.0.0.1:8000/
curl --max-time 3 -i http://127.0.0.1:8000/missing.txt
ss -ltnp
```

The first response should contain the synthetic page with a successful HTTP status. The second should be an HTTP not-found response. `ss` should show a listener on `127.0.0.1:8000`; process detail depends on privileges. The server terminal records requests. These establish normal behavior and a harmless error, not authentication: a static server has no two-user authorization model.

Stop with Ctrl+C. For a two-VM lesson, bind to the target's documented internal lab address instead of loopback and permit that port only from the tester. Recheck the listener, routes, and firewall before requesting it from the second guest. Avoid a wildcard bind merely to eliminate a connection problem.

For later application labs, add synthetic customer A and B, owner-tagged records, an expected authorized action, a denied cross-owner action, and a harmless malformed input. Record server and client evidence and a deterministic reset procedure. Container users must inspect host port publishing as well as the process's bind address.

## 5. Make observation and recovery part of setup

For each event, capture time with offset, actor, operation, object, result, and correlation identifier when available. First generate one known benign event and find it in the intended log. An empty log is not evidence of safe behavior if collection was never enabled. Compare guest and host clocks and preserve original timestamp formats; collection delay and clock skew are different explanations.

Test a snapshot concretely. Create `recovery-demo.txt` containing `baseline`, record its hash, and snapshot. Change it to `changed`, alter one harmless application setting, then restore. Check both the file and setting, then make a successful request. Store notes outside the snapshot so reverting does not erase the evidence. Document which external state was unaffected.

Test a separate backup by copying synthetic configuration/data to another lab location and restoring into a fresh directory or clean guest. Verify bytes, owner, permissions, service identity, dependencies, and behavior. A correct file digest with incorrect permissions may leave the application unusable.

Write setup instructions before automating: image identifiers, accounts by purpose, dependencies, adapter mapping, file paths, service command, verification, reset, known limitations, and teardown. Automation should implement understood steps rather than hide unknown changes.

## 6. Control integrations and extend gradually

Disable unnecessary shared folders, clipboard sharing, USB passthrough, host mounts, and personal account synchronization. Use unique lab passwords. For interception, use a dedicated browser profile, route only lab traffic, and track any trusted CA certificate. Remove the proxy/trust changes during cleanup. A proxy project may contain credentials even when records are synthetic.

Extend in stages: application plus database/proxy; Linux and Windows services/file shares; isolated AD domain; local container/cluster; then track-specific mobile emulator, hardware, or reverse-engineering VM. For AD, establish DNS and ordinary sign-in before unsafe permissions. For mobile work, distinguish emulator-supported behavior from physical-device-only features. Kernel or malware analysis requires a reconsidered isolation design and suitable supervision, rather than reusing a daily VM automatically.

Cloud planning belongs in the inventory even though this exercise does not deploy anything. A future lab requires a separate project/account, MFA, quotas/resource limits, billing alerts, current provider conditions, and explicit teardown. An alert may notify without stopping cost. Stopped VMs can leave storage, addresses, logs, databases, or other billable resources. Verify provider inventory after teardown, including credentials and retained backups.

## Troubleshooting and repair

| Symptom | Distinguishing check | Targeted fix and retest |
| --- | --- | --- |
| VM will not start | Exact error, architecture, virtualization support, free RAM | Correct platform/allocation; boot and inspect guest |
| No guest address | Adapter network, link, DHCP or static config | Correct one attachment/address setting |
| Address works, name fails | Resolver, suffix, local record | Repair name configuration and compare both requests |
| Local page works, remote fails | Listener binding, route, guest firewall | Change only intended lab exposure and retest allowed/denied flows |
| TLS proxy fails | Trust profile, hostname, route, pinning | Correct lab client trust/routing; preserve normal verification |
| Logs disagree | Clock offset versus display zone versus delay | Correct time source; generate a new event |
| Restore incomplete | External volumes/services and snapshot exclusions | Add missing backup/reset steps and restore again |

Your acceptance drill is a clean rebuild, one allowed connection, one intended denial, one traceable event, one data reset, and one configuration restore. Explain every route and host integration. If any result depends on memory or undocumented state, update the runbook and repeat that part.
