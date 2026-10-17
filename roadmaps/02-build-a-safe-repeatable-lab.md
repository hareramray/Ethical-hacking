# 02. Build a safe, repeatable lab

[All topic roadmaps](README.md) | [Original master roadmap](../ETHICAL_HACKING_ROADMAP.md#02-build-a-safe-repeatable-lab)

<!-- TOPIC-TOC:START -->

## Contents

- [Hardware and platform planning](#hardware-and-platform-planning)
- [Network isolation and recovery](#network-isolation-and-recovery)
- [Build in stages](#build-in-stages)
- [Expanded build plan: from one machine to a useful security lab](#expanded-build-plan-from-one-machine-to-a-useful-security-lab)
  - [Stage 1: Survey the host before choosing software](#stage-1-survey-the-host-before-choosing-software)
  - [Stage 2: Establish clean base images](#stage-2-establish-clean-base-images)
  - [Stage 3: Design connectivity explicitly](#stage-3-design-connectivity-explicitly)
  - [Stage 4: Deploy an application with synthetic state](#stage-4-deploy-an-application-with-synthetic-state)
  - [Stage 5: Add observability and repeatability](#stage-5-add-observability-and-repeatability)
  - [Stage 6: Extend for enterprise and specialist work](#stage-6-extend-for-enterprise-and-specialist-work)
- [Troubleshooting the environment](#troubleshooting-the-environment)
- [Lab acceptance and recovery drill](#lab-acceptance-and-recovery-drill)

<!-- TOPIC-TOC:END -->



**Priority:** Core. Start small; add components only when a phase needs them.

## Hardware and platform planning

These are planning estimates, not software minimum requirements:

| Available resources | Practical starting approach |
| --- | --- |
| Limited machine or about 8 GB RAM | Browser-hosted training labs; one lightweight Linux VM at a time; small local development exercises. |
| About 16 GB RAM and SSD storage | A Linux workstation and one or two small targets, adjusting allocations to leave room for the host. |
| About 32 GB RAM or more | A small Windows domain, Linux target, and log collector running together, depending on VM sizing. |
| No suitable local hardware | Provider-hosted training environments; postpone multi-VM enterprise labs. |

- [ ] Learn CPU virtualization, host/guest terminology, resource allocation, virtual disks, snapshots, cloning, and checkpoints.
- [ ] Select a supported hypervisor for your host: Hyper-V, VirtualBox, VMware, or KVM are examples. Read its current requirements and networking documentation before installing.
- [ ] Use an ordinary Linux distribution for administration practice. A security distribution such as Kali can be a later tool workstation; its tool collection does not replace the foundations.
- [ ] Use appropriately licensed Windows and Windows Server images. Check evaluation terms rather than assuming an image remains valid indefinitely.
- [ ] Understand that WSL, containers, and virtual machines provide different isolation properties. WSL is useful for development but is not a substitute for every networking, Windows-domain, kernel, or malware-analysis lab.

## Network isolation and recovery

```text
Personal host
  └── Hypervisor
        ├── Isolated virtual network
        │     ├── Tester workstation
        │     ├── Deliberately vulnerable target
        │     └── Optional log collector / test domain
        └── Controlled update access when required

No unsolicited inbound route from the Internet to vulnerable targets.
```

- [ ] Learn bridged, NAT, host-only, and internal virtual networking. Host-only networks still include the host; NAT does not make an intentionally vulnerable workload harmless.
- [ ] Prefer an internal isolated network for vulnerable targets. Disable forwarding into personal, office, or public networks; verify the actual routes and firewall rules.
- [ ] Keep any Internet-facing update path temporary and controlled. Do not expose a vulnerable training application on a cloud public IP just to make access convenient.
- [ ] Verify the application's listening address and any container port publishing. A container's default exposure may differ from what you intended.
- [ ] Use dedicated browser profiles and lab accounts. Install interception certificates only in the lab browser or device, then remove them when finished.
- [ ] Disable unnecessary shared folders, clipboard integration, USB passthrough, and host mounts. Never reuse real passwords or synchronize lab secrets to personal accounts.
- [ ] Take a known-good snapshot before each exercise. Keep separate backups of important notes: snapshots are not independent backups.
- [ ] Test restoration, verify time synchronization for log correlation, and record software versions.
- [ ] For cloud labs, create a separate project/account, use MFA, set billing alerts and resource limits, and document teardown. A budget alert may notify you without stopping expenditure.

## Build in stages

1. **Starter lab:** Linux workstation, a browser, editor, Git, Python, packet analyzer, and local test web service.
2. **Application lab:** Deliberately vulnerable training app, proxy, database with synthetic records, and application logs.
3. **Infrastructure lab:** Linux target, Windows target, service accounts, file shares, and host logs.
4. **Enterprise lab:** Domain controller, member workstation, member server, dedicated synthetic identities, and centralized logs.
5. **Cloud/container lab:** Disposable tenant/project and a local container/cluster setup when you reach that phase.
6. **Specialist lab:** Mobile emulator, small hardware board, or isolated reverse-engineering VM according to your track.

Keep an inventory containing hostname, purpose, OS/image version, IP address, network, credentials location, snapshot, and owner. Learn to rebuild targets from a short setup document or automation script.

**First deliverable:** A network diagram, inventory, isolation check, and demonstrated snapshot restoration. Confirm that the training app is reachable only by intended lab systems before testing it.

## Expanded build plan: from one machine to a useful security lab

### Stage 1: Survey the host before choosing software

Record the host OS/edition, CPU, RAM, free disk space, virtualization support, existing hypervisors, backup location, and whether the machine is personally owned or managed by an organization. Check the current hypervisor requirements rather than assuming every OS edition supports the same features. Keep enough resources available for the host to remain responsive and for snapshots or logs to grow.

Define the first exercise before purchasing hardware. A browser training lab can teach an HTTP authorization boundary without a large local domain. A local domain requires more memory, licensed images, and time to troubleshoot DNS and identity. Learn what each component contributes so you can omit it until needed.

Official starting references: [Hyper-V overview](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/overview?pivots=windows) and [WSL overview](https://learn.microsoft.com/en-us/windows/wsl/about). Consult the chosen platform's networking documentation for actual switch and adapter behavior; similar names across products can represent different connectivity.

### Stage 2: Establish clean base images

Obtain images from the publisher or a documented trusted distribution source. Record download source, release identifier, signature/checksum information when provided, licensing terms, and installation date. An image hash supports identification; publisher trust depends on how the hash or signature key was obtained.

Install a minimal general-purpose Linux guest. Create a normal account, patch it, verify time, configure console access, and document its network adapters. Create a baseline snapshot only after you know which external connectivity is enabled. Clone the base for experiments rather than turning the only clean copy into a permanently changing target.

**Lab:** Create a file with a known content hash, take a snapshot, change the file and a harmless service setting, then restore. Check both the content and service state. Explain which data was reverted and which external artifacts, such as notes saved on the host, were unaffected.

### Stage 3: Design connectivity explicitly

Choose a private lab address range that does not overlap your host's existing routes, work VPN, or home network. Draw every interface and gateway. Use names that communicate purpose, such as tester, target, and logger, without assuming those names enforce a boundary.

Start with an internal/private virtual network and no default route on the deliberately vulnerable target when practical. If the tester also has update access, ensure it is not unintentionally forwarding traffic between networks. Check IPv4 and IPv6, host-side virtual adapters, published container ports, host firewall rules, and application listening addresses.

Use this permitted-flow matrix before adding tools:

| Source | Destination | Intended connectivity | How to confirm |
| --- | --- | --- | --- |
| Tester | Training app | Only the service ports needed by the lesson. | Open a known page and inspect the target log. |
| Target | Logger | Only the chosen log transport if configured. | Generate a benign event and confirm receipt. |
| Target | Personal LAN | No route or explicitly denied. | Inspect routes and controls; test only a specifically owned benign endpoint if needed. |
| Internet | Vulnerable target | No published ingress. | Inspect hypervisor, router, cloud, and host forwarding configuration. |
| Update-enabled guest | Approved update sources | Controlled when updates are needed. | Check route, DNS, connection records, and remove access afterward if the lab requires isolation. |

A single failed connection does not establish complete isolation. Combine configuration inspection with positive and negative checks. Make the intended permitted connection succeed so a broken application cannot masquerade as an effective network control.

### Stage 4: Deploy an application with synthetic state

Choose one training application or a small application you wrote. Read its startup and networking behavior before running it. Place it in the intended guest or isolated environment; confirm its bind address and port mappings. Create fictional users, records, credentials, and uploaded files.

Add three baseline tests: an expected authorized action, an expected denied action, and a harmless error. Capture server and client observations. Save a reset method that recreates the same accounts and data, so a later experiment does not depend on forgotten state.

For interception practice, use a dedicated browser profile and scoped proxy configuration. Confirm that only lab traffic is routed through it. Track any installed trust certificate and restore the browser/device configuration after the exercise. A proxy capture may contain authentication material even when the target data is synthetic.

### Stage 5: Add observability and repeatability

Collect application logs and relevant host events before adding a complex central platform. Learn the fields you need: time, identity, operation, object, outcome, and correlation identifier. Store original time-zone information and check clock differences. Produce one event you expect to see, then verify it arrives with the required fields.

Write setup instructions that a future version of you can follow without memory. Include package/image identifiers, accounts by purpose, configuration files, network mapping, reset steps, dependencies, and known limitations. Add infrastructure automation only after you can describe the manual process and review what the automation changes.

### Stage 6: Extend for enterprise and specialist work

For an AD lab, add the domain controller and DNS first, then verify ordinary domain joins and sign-ins before introducing deliberately unsafe permissions. Keep real accounts, corporate DNS, and organizational credentials outside this environment. For mobile work, start with an emulator and an owned application; document which features need a physical device.

For cloud exercises, use a separate learning account/project and a resource inventory. Record which services continue billing after a VM stops, such as storage, addresses, databases, or logs where applicable. Billing alerts and quotas serve different purposes. Use an explicit teardown checklist and verify its result in the provider inventory.

Malware analysis and kernel experiments need stronger isolation planning and suitable supervision than an ordinary web lab. Do not reuse your general-purpose daily VM without reconsidering host integration, network access, and recovery boundaries.

## Troubleshooting the environment

| Symptom | First distinctions to check | Useful evidence |
| --- | --- | --- |
| VM does not start | Hardware virtualization, hypervisor compatibility, memory allocation, image architecture. | Exact error and platform configuration. |
| Guest has no address | Adapter attachment, DHCP availability, static addressing, interface state. | Interface and lease configuration. |
| IP works but hostname fails | Resolver configuration, local DNS records, suffix/search behavior. | Resolver query and authoritative answer. |
| Service works locally but not from tester | Bind address, guest firewall, virtual network, wrong target address. | Listening socket, route, target log. |
| TLS interception fails | Proxy route, trust store, hostname, application pinning, wrong profile. | Certificate chain and client error. |
| Logs disagree about time | Time zone display, clock synchronization, collection delay. | Original timestamps and measured offset. |
| Restore is incomplete | Data stored outside snapshot, external service state, credentials changed elsewhere. | Artifact inventory and recovery test. |

## Lab acceptance and recovery drill

Hand your setup document to another learner or follow it yourself from a clean state. Rebuild the basic lab, demonstrate one intended connection and one intended denial, generate and find a benign event, reset synthetic data, and restore a changed configuration. Preserve evidence outside the snapshot being restored.

**Pass:** You can explain every network route and host integration, reproduce the training state, recover from a mistake, and account for all cloud resources and credentials. Recheck these properties whenever the topology, image, tool, or hosting arrangement changes.
