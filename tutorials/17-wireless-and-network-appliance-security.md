# 17. Tutorial: wireless and network appliance security

[Index](README.md) | [Complete source curriculum](curriculum/17-wireless-and-network-appliance-security.md) | [Original roadmap](../roadmaps/17-wireless-and-network-appliance-security.md)

Prerequisites: chapter 04 networking, chapter 08 identity and certificates, and a recoverable lab. Use a spare router and your own clients, or complete the policy simulation first. Radio visibility does not identify an authorized test target. The practical work here observes normal connections and configuration; it needs no disruption or traffic from neighboring devices.

## Lesson 1: follow a connection instead of guessing

Draw `client → access point → switch/VLAN → gateway → DNS/application`. Label the SSID (network name), BSSID (radio interface identifier), client address, subnet, gateway, and management address separately. The SSID is a name others can reuse. Association with an access point does not prove successful enterprise authentication, address assignment, routing, or application access.

Management frames coordinate discovery and association; control frames help coordinate radio access; data frames carry higher-layer traffic. After joining, your client may obtain network configuration, resolve a name, and establish TCP/TLS. Roaming introduces another access-point association while the application expects continuity. Capture one owned client's normal reconnect and align client, AP, and DHCP timestamps. A DHCP failure after successful association is a different diagnosis from a certificate rejection before network admission.

Wireless link encryption protects the radio hop and terminates at the access point or the relevant controller/tunnel termination in that design. It does not automatically protect the complete subsequent network path. Application TLS supplies a separate protection between its own endpoints; draw both termination points when deciding where plaintext may be observed.

| Observation | Mechanism and discriminating check |
| --- | --- |
| Low signal strength | Received power alone says little about noise; compare signal-to-noise ratio and location. |
| Good signal, poor throughput | Interference, overlapping channel use, airtime contention, retransmissions, or a slow uplink may dominate. Compare radio retries with wired throughput. |
| Wider channel, worse performance | More spectrum can increase interference exposure; throughput is not determined by channel width alone. |
| Variable link rate | Rate adaptation responds to observed conditions; advertised maximum is not a promised application rate. |
| Different antenna orientation changes results | Antenna pattern and obstructions alter propagation; record placement to reproduce measurements. |

Ordinary captures may show translated Ethernet traffic, with no raw management frames. Adapter, driver, OS, channel selection, and monitor-mode support determine what can be observed. Use supplied captures when necessary; a simulator cannot establish actual radio behavior. See the [Wireshark WLAN capture guide](https://wiki.wireshark.org/CaptureSetup/WLAN).

## Lesson 2: distinguish the authentication mechanisms

An open network has no ordinary Wi-Fi link encryption. WEP and TKIP are legacy mechanisms; recognize them in inventories and plan replacement. WPA2 and WPA3 describe families of negotiated security behavior, so record the actual mode and client compatibility. Personal deployments commonly share a network credential; WPA3-Personal uses SAE for password-authenticated key establishment. Transition modes retain compatibility paths whose security properties must be assessed separately. Protected management frames protect selected management traffic, not every radio frame or every availability problem.

Enterprise access commonly separates three roles: the client supplicant, the access-point authenticator, and an authentication server reached through RADIUS. EAP is a framework containing methods with different credentials and trust requirements. For certificate-based authentication, draw which side validates which certificate. Check issuer/trust anchor, expected server identity, validity time, client identity where applicable, enrollment, renewal, and revocation behavior. An “accept any certificate” setting removes meaningful server identity validation.

Create five fictional failure cards: wrong server name, expired certificate, client clock error, revoked credential, unavailable authentication server. For each, predict whether failure occurs at client trust evaluation, server identity/account evaluation, or network reachability. Do not label all five “bad Wi-Fi password.” Individual credentials allow targeted offboarding; a shared password often needs broader rotation and client migration.

A captive portal controls a later application/network access step. It does not independently supply radio encryption or prove that a named wireless network is trustworthy. Hidden SSIDs and MAC allowlists likewise do not replace cryptographic identity. WPS/onboarding should have an owner and explicit policy. Inventory unexpected/lookalike access points through approved monitoring and validated identity, without connecting to unrelated devices.

## Lesson 3: turn segmentation into testable requirements

Before changing equipment, write this matrix and replace labels with exact owned addresses:

| Source | Destination/service | Expected | Positive control |
| --- | --- | --- | --- |
| Guest | Management HTTPS | Denied | Management client can open the same interface. |
| Guest | Approved DNS | Allowed | Resolver answers the intended lab name. |
| Guest | Trusted client's training service | Denied | Trusted client can reach that running service. |
| Guest | Another guest | According to isolation policy | Confirm the peer service is actually listening. |
| Management | Appliance administration | Allowed | Login with a dedicated authorized account. |

Test IPv4 and IPv6 separately. Client isolation operates at an AP/bridge boundary; inter-VLAN firewall policy operates on routed paths. One cannot establish the other's behavior. Review VLAN membership and trunks, native VLAN assumptions, stateful return traffic, rule ordering, default policy, controller tunnels, and wired clients. Failed ping is inconclusive when ICMP is disabled; compare an actual allowed application connection and its server-side logs.

**Offline exercise:** mark each proposed flow allowed/denied on paper. Then add a management interface reachable on a second VLAN and repeat. Expected discovery: a restriction on one address does not cover another path. This validates your reasoning, not a physical device's enforcement.

## Lesson 4: perform the owned-router lab

1. Save the starting configuration securely and identify the documented recovery path. Record firmware/model, ownership, time, and intended routes.
2. Create or identify trusted, guest, and management zones supported by the device. Keep administration reachable from your management client before applying restrictions.
3. Join your two clients, record addresses and gateways, and perform every matrix row using ordinary connections. Record source, destination, protocol, time, and result.
4. Correlate failed connections with routing, service state, and firewall logs. A stopped service is not evidence of successful isolation.
5. Correct only the rule or interface assignment causing the unexpected flow. Repeat both allowed and forbidden cases.
6. Rotate a disposable credential, reconnect the owned clients, and confirm the intended old-credential behavior. Save a sanitized diff and restore the initial lab configuration when finished.

Expected evidence is a topology, complete matrix, configuration excerpt, and correlated logs. If you lose management access, use the planned recovery route; improvising changes without knowing the active path compounds the problem.

## Lesson 5: apply the same reasoning to appliances and short-range devices

| Area | What to examine and why |
| --- | --- |
| Routers, switches, firewalls, VPNs | Separate management authority from forwarded data; check AAA, scoped administration, route authentication, port configuration, DHCP/ARP protections, and remote access. |
| Proxies, load balancers, DNS/storage appliances | Administrative access can alter traffic, name answers, or data; inspect both management and workload interfaces. |
| SNMP, SSH, TLS, discovery | Determine authentication/encryption settings and interface bindings; unused listeners enlarge exposure. |
| Firmware and drift | Compare approved and running configuration, support status, update provenance, release dependencies, signed-update support, and backup restoration. |
| High availability | Verify configuration consistency, state synchronization, failover management, and recovery in a separate maintenance exercise. |
| Central logging | Record time synchronization, administrative changes, failed logins, collection loss, and protected configuration backups. |
| Bluetooth Classic/BLE | Pairing establishes keys; bonding retains them. BLE GATT services expose characteristics whose read/write permissions and application authorization must both be checked. Encryption alone does not authorize every operation. |
| NFC/RFID | A readable identifier is not necessarily cryptographic proof. Model tag, reader, middleware, and backend authorization separately using training tags. |

For BLE, inventory a development peripheral's services, identify one read-only characteristic, and compare unauthenticated versus documented paired access without changing critical state. For NFC, use a diagram to explain why copying an identifier and defeating a challenge-response credential are different claims.

SNMP v1/v2c community-based access differs from SNMPv3's configurable authentication/privacy security levels; a version label alone does not establish that authentication and encryption are enabled. Check administrator session expiry, role separation, and protected emergency access as part of appliance recovery. For BLE, distinguish temporary discoverability from retained bonding keys, remove obsolete bonds during offboarding, and examine address/identifier privacy across reconnects. Deleting a mobile companion app does not necessarily delete the peripheral's retained bond.

**Check your understanding:** If a guest cannot ping administration but can load its login page, isolation failed for HTTPS. If a strong signal accompanies failed server-certificate validation, changing the channel will not repair identity trust. If a backup restores settings but not management access, recovery is incomplete. Pass this chapter when you can explain those distinctions, reproduce each flow result, and restore the owned configuration. For device-specific settings, use the manufacturer's exact model/firmware manual; the complete curriculum preserves the lifecycle references and every source checklist.
