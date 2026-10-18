# 17. Wireless and network appliance security

[All topic roadmaps](README.md) | [Original master roadmap](../../ETHICAL_HACKING_ROADMAP.md#17-wireless-and-network-appliance-security)

<!-- TOPIC-TOC:START -->

## Contents

- [Knowledge and skill checklist](#knowledge-and-skill-checklist)
- [Safe projects and evidence](#safe-projects-and-evidence)
- [Detailed learning sequence](#detailed-learning-sequence)
  - [Stage 1: Follow one connection through every layer](#stage-1-follow-one-connection-through-every-layer)
  - [Stage 2: Build an authentication decision tree](#stage-2-build-an-authentication-decision-tree)
  - [Stage 3: Separate users, devices, and administrators](#stage-3-separate-users-devices-and-administrators)
  - [Stage 4: Review appliance lifecycle and recovery](#stage-4-review-appliance-lifecycle-and-recovery)
  - [Stage 5: Add short-range systems deliberately](#stage-5-add-short-range-systems-deliberately)
- [Worked lab: trusted, guest, and management zones](#worked-lab-trusted-guest-and-management-zones)
- [Debugging blind spots and pass criteria](#debugging-blind-spots-and-pass-criteria)
- [Practical prerequisite: wireless capture capabilities](#practical-prerequisite-wireless-capture-capabilities)

<!-- TOPIC-TOC:END -->



**Prerequisites:** TCP/IP, Ethernet, subnetting, routing, packet analysis, authentication, certificates, and network segmentation. Start with equipment you own and an isolated network. Radio signals can extend beyond a room; owning an access point does not authorize interacting with nearby clients.

## Knowledge and skill checklist

- [ ] Explain radio frequencies, channels, interference, signal strength, antenna behavior, and the difference between visibility and permission to test.
- [ ] Read 802.11 management, control, and data frames; understand discovery, association, authentication, roaming, and the relationship between a wireless client and the wired network.
- [ ] Compare open networks, obsolete WEP/TKIP, WPA2, WPA3, Personal versus Enterprise deployments, SAE, protected management frames, and transition-mode tradeoffs. Learn mechanisms and configuration implications rather than treating every protocol version as equivalent.
- [ ] Understand 802.1X, EAP methods, RADIUS, certificate chains, server identity validation, client certificates, enrollment, revocation, and failure behavior.
- [ ] Assess guest isolation, client isolation, management VLANs, access-point administration, onboarding, WPS exposure, captive portals, device inventory, and trusted certificate deployment.
- [ ] Identify rogue access-point and lookalike-network risks conceptually; understand how inventory, certificate validation, monitoring, and user education reduce them.
- [ ] Inspect wireless configuration exports, update policies, controller access, administrator roles, logging, and recovery procedures. Treat configuration backups as sensitive because they may contain secrets.
- [ ] Study Bluetooth Classic and BLE architecture, pairing versus bonding, GATT services, discoverability, authentication, encryption, and privacy. Use your own development peripherals for practical work.
- [ ] Understand NFC/RFID identification versus authentication and where cloning resistance, reader trust, and backend authorization differ. Keep experiments to training tags and readers.
- [ ] Review routers, switches, firewalls, VPN gateways, proxies, load balancers, DNS appliances, and storage appliances as management-plane and data-plane systems.
- [ ] Assess administrative exposure, AAA, SNMP versions, SSH/TLS configuration, unused services, firmware support, configuration drift, backup integrity, centralized logs, and time synchronization.
- [ ] Validate firewall and segmentation policy using a permitted source/destination/service matrix, including IPv6, rather than assuming an IPv4 rule protects every path.
- [ ] Understand routing-protocol authentication, DHCP protections, ARP-related controls, switch port configuration, high availability, and the operational consequences of configuration changes.

## Safe projects and evidence

1. Build a guest and trusted network on a spare router. Document intended flows, test only your clients, and show that guest access cannot reach the administration interface.
2. Compare two wireless security configurations using settings, client behavior, and your own traffic captures. Record compatibility limitations without performing disruptive radio tests.
3. Review a sample appliance configuration and produce a prioritized hardening plan with backup and rollback steps.

**Exit criteria:** Explain an enterprise wireless authentication flow, interpret your own connection capture, demonstrate segmentation with positive and negative tests, and produce reproducible configuration findings. Use [NIST WLAN guidance](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=910174) for lifecycle and monitoring foundations; it is older guidance, so supplement it with the current documentation for the exact device and wireless features you study.

## Detailed learning sequence

### Stage 1: Follow one connection through every layer

Draw the path from a station through an access point, switch, gateway, DNS resolver, and application. Label the SSID, BSSID, VLAN, subnet, default gateway, DHCP server, and administrative interface separately. Learn why an SSID is a service name rather than a trustworthy identity and why being associated does not imply Internet access. Practice converting signal measurements into a diagnosis: interference, low signal, authentication failure, address allocation failure, and DNS failure are different problems.

- [ ] Identify channel width, overlapping channels, signal-to-noise ratio, retransmissions, airtime contention, and rate adaptation in your own connection observations.
- [ ] Explain the roles of beacons, probe traffic, association, authentication, and key establishment without collecting unrelated users' traffic.
- [ ] Correlate an access-point event, a client event, and a DHCP event using timestamps and your device identifiers.
- [ ] Describe what encryption protects on the wireless hop and where traffic becomes visible after the access point.

### Stage 2: Build an authentication decision tree

Compare shared credentials with individual enterprise identities. Trace supplicant, authenticator, and authentication server roles. For a certificate-based training configuration, document the certificate issuer, expected server name, validity period, trust anchor, client identity, and renewal owner. Work through revoked credentials, expired certificates, a wrong server name, an unavailable authentication server, and a client clock error. Learn which decision occurs on the client and which occurs on the network.

- [ ] Explain why accepting any certificate destroys an intended server-authentication boundary.
- [ ] Document enrollment and offboarding: issuing credentials, distributing trust, revoking access, and confirming old devices fail to connect.
- [ ] Compare password sharing, device-specific credentials, and certificate enrollment by operational burden and revocation precision.
- [ ] Record the configured protected-management-frame behavior and client compatibility; do not infer support from an access point's marketing label.
- [ ] Treat captive-portal login, wireless encryption, and application authentication as three independent mechanisms.

### Stage 3: Separate users, devices, and administrators

Build a flow table before changing a firewall. Include trusted clients, guest clients, management hosts, infrastructure services, and the Internet as rows and columns. Define both allowed flows and forbidden flows. Record IPv4 and IPv6 independently, including local discovery and required support services. A successful ping proves a limited reachability fact; a failed ping alone does not prove isolation.

Understand stateful return traffic, rule ordering, implicit defaults, VLAN trunks, native VLAN assumptions, management access lists, and controller-originated traffic. Study how client isolation differs from routing policy. Trace a guest-to-guest flow, guest-to-admin flow, and guest-to-Internet flow. Include wired clients because an access-point configuration cannot prove the whole network is segmented.

### Stage 4: Review appliance lifecycle and recovery

Create an inventory with device role, management address, hardware model, installed firmware, support source, configuration owner, backup location, and maintenance window. Review local versus centralized administrator accounts, unique credentials, role separation, session expiration, audit logs, and emergency access. Identify services bound to all interfaces, remote administration defaults, exposed discovery services, and configuration exports containing authentication material.

Study upgrade verification, signed firmware where supported, release-note interpretation, compatibility dependencies, and recovery mechanisms. Treat high availability as a separate test plan: state synchronization, failover behavior, management reachability, and configuration consistency can each fail. A backup is useful only when the correct device state can be restored and access recovered.

### Stage 5: Add short-range systems deliberately

For BLE, map device discovery, connection, pairing, bonding, service discovery, characteristic permissions, and application authorization. A characteristic that requires an encrypted link may still lack authorization for a particular account. For training NFC tags, distinguish a readable identifier from a cryptographic identity proof. Document the reader, middleware, and backend decision rather than assuming the tag determines access.

## Worked lab: trusted, guest, and management zones

**Setup:** Use a spare router or supported local network simulator, two owned clients, and a third logical management zone when supported. Save the initial configuration and identify the recovery interface. Choose a short test window and record exact addresses.

**Actions:** Connect each client, verify address assignment, and test the approved flow table using ordinary application connections. Confirm that an authorized management client can administer the appliance while a guest cannot. Repeat with IPv6 if enabled. Reconnect after credential rotation and compare logs. Export a sanitized configuration and annotate the relevant rules.

**Expected behavior:** Each client receives the intended network settings; guest access reaches permitted services; administrative access is restricted; denied connections have explainable outcomes; old credentials cease working after the documented transition.

**Evidence:** Retain the topology, sanitized configuration diff, test matrix, timestamps, client state, and selected logs. Record whether denial came from routing, firewall policy, authentication, or a stopped service.

**Correction:** If a forbidden flow succeeds, locate its actual path before editing rules. If an allowed flow fails, inspect DHCP, routing, DNS, firewall state, and service listening state in that order. Restore the saved configuration if management access is lost.

## Debugging blind spots and pass criteria

Avoid treating weak reception as an authentication defect, a hidden SSID as access control, MAC filtering as strong identity, or a portal as link encryption. Check whether hardware offload, controller tunneling, bridge interfaces, or stale client sessions explain unexpected packet visibility. Remember that a configuration screenshot can show intended policy while runtime behavior differs.

- [ ] Reconstruct one connection failure from three independent evidence sources.
- [ ] Complete every row of a documented positive and negative segmentation matrix.
- [ ] Explain one authentication failure caused by certificate validation and one caused by network reachability.
- [ ] Restore your appliance configuration and confirm management access without relying on undocumented default settings.
- [ ] Deliver prioritized fixes with affected devices, compatibility tradeoffs, rollback steps, and a repeatable retest.

**Further reading:** Use the NIST WLAN publication above for assessment structure, then the exact device manufacturer's administrator and recovery manuals. For protocol analysis, study the [Wireshark User's Guide](https://www.wireshark.org/docs/wsug_html_chunked/) alongside captures of your own training traffic. Keep captures and configuration exports out of a public portfolio unless thoroughly sanitized.

## Practical prerequisite: wireless capture capabilities

Raw 802.11 management/control-frame analysis requires compatible adapter, driver, operating-system, and capture support. Monitor mode and the correct channel may be necessary; an ordinary managed-interface capture can expose translated Ethernet data instead of the radio frames you intend to study. Verify capabilities before buying equipment or interpreting absent frames as absent traffic. Use supplied training captures when your hardware cannot collect the required frame types. A generic network simulator can teach network logic but does not establish actual radio-layer behavior. Consult [Wireshark's WLAN capture guide](https://wiki.wireshark.org/CaptureSetup/WLAN) for the capture method relevant to your environment.

