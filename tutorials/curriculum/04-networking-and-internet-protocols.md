# 04. Networking and Internet protocols

[All topic roadmaps](README.md) | [Original master roadmap](../../ETHICAL_HACKING_ROADMAP.md#04-networking-and-internet-protocols)

<!-- TOPIC-TOC:START -->

## Contents

- [Network models, addressing, and delivery](#network-models-addressing-and-delivery)
- [Transport and infrastructure services](#transport-and-infrastructure-services)
- [Web traffic, encrypted connections, and remote access](#web-traffic-encrypted-connections-and-remote-access)
- [Safe practice and exit criteria](#safe-practice-and-exit-criteria)
- [Detailed learning sequence](#detailed-learning-sequence)
  - [Stage 1 — Trace local and routed delivery](#stage-1--trace-local-and-routed-delivery)
  - [Stage 2 — Give IPv6 equal attention](#stage-2--give-ipv6-equal-attention)
  - [Stage 3 — Understand transports and measurement](#stage-3--understand-transports-and-measurement)
  - [Stage 4 — Resolve names and locate infrastructure](#stage-4--resolve-names-and-locate-infrastructure)
  - [Stage 5 — Follow browser traffic end to end](#stage-5--follow-browser-traffic-end-to-end)
- [Guided labs with evidence](#guided-labs-with-evidence)
  - [Lab A — Addressing and local service delivery](#lab-a--addressing-and-local-service-delivery)
  - [Lab B — Four failures, four explanations](#lab-b--four-failures-four-explanations)
  - [Lab C — Encryption boundary and dual-stack comparison](#lab-c--encryption-boundary-and-dual-stack-comparison)
- [Capstone, rubric, and retention](#capstone-rubric-and-retention)

<!-- TOPIC-TOC:END -->



**Prerequisites:** Section 03 and basic command-line use. **Priority:** Core; deeper routing engineering is a specialization.

## Network models, addressing, and delivery

- [ ] Use OSI and TCP/IP models to explain encapsulation, headers, payloads, and where switches, routers, firewalls, proxies, and applications operate.
- [ ] Understand Ethernet frames, MAC addresses, ARP, broadcast domains, switches, VLANs, trunks, and the distinction between physical and logical topology.
- [ ] Calculate IPv4 network ranges using CIDR and subnet masks. Recognize private, public, loopback, link-local, multicast, and special-purpose addresses.
- [ ] Explain default gateways, routing tables, longest-prefix matching, static routing, NAT/PAT, connection tracking, and why NAT is not a complete security policy.
- [ ] Learn IPv6 notation, prefixes, global and link-local addresses, multicast, Neighbor Discovery, Router Advertisements, SLAAC, DHCPv6, and dual-stack operation.
- [ ] Understand MTU, fragmentation, path-MTU discovery, ICMP/ICMPv6, packet loss, jitter, bandwidth, throughput, and asymmetric routing.
- [ ] Distinguish stateful/stateless firewall behavior, allow/deny rules, inbound/outbound controls, segmentation, and application-layer filtering.
- [ ] **Advanced:** Understand STP, link aggregation, dynamic routing, BGP trust relationships, overlays, SDN, load balancing, and high-availability designs.

For the IPv6 protocol itself, use the [IETF IPv6 specification](https://www.rfc-editor.org/rfc/rfc8200) as a reference after learning the basic vocabulary.

## Transport and infrastructure services

- [ ] Explain TCP handshakes, sequence/acknowledgment numbers, retransmission, flow/congestion control, connection teardown, ports, and sockets.
- [ ] Explain UDP tradeoffs and that UDP applications can implement reliability themselves. Recognize QUIC's relationship to UDP and TLS.
- [ ] Understand DNS resolvers, authoritative servers, recursion, caching, TTLs, delegation, forward/reverse lookups, and A/AAAA/CNAME/MX/TXT/NS/SOA/SRV records.
- [ ] Distinguish DNSSEC validation from encrypted DNS transport; understand split DNS and why resolver choice affects results.
- [ ] Understand DHCP leases/options, time synchronization, and why incorrect clocks break authentication, certificates, and evidence correlation.
- [ ] Recognize the purpose and trust boundaries of SSH, SMB, LDAP, Kerberos, RDP, SNMP, NTP, SMTP, IMAP, and POP. Learn normal traffic before assessing weaknesses.
- [ ] Distinguish a service's conventional port from proof of its actual identity; a service can use a different port.

## Web traffic, encrypted connections, and remote access

- [ ] Trace a URL through DNS, connection establishment, TLS, HTTP request, application processing, response, and browser rendering.
- [ ] Learn HTTP methods, status codes, headers, cookies, sessions, content types, caching, compression, redirects, proxies, and HTTP/1.1, HTTP/2, and HTTP/3 at a conceptual level.
- [ ] Understand TLS certificates, hostname checks, certificate chains, trust stores, negotiation, and why encrypted transport still requires endpoint authentication.
- [ ] Learn VPN tunneling, split/full tunneling, remote-access versus site-to-site designs, reverse proxies, CDNs, and the visibility each intermediary has.
- [ ] Recognize WebSockets, server-sent events, and long-lived API connections; understand that browser traffic is broader than page downloads.

## Safe practice and exit criteria

**Labs:** Draw a two-VM network; calculate its address range; run a local web service; inspect only your lab traffic with a packet analyzer. Identify DNS, TCP, TLS, and HTTP stages. Introduce separate DNS, route, firewall, and application failures and diagnose each. Compare IPv4 and IPv6 connectivity. Capture a local unencrypted demonstration request and explain which fields an observer can read.

**Exit gate:** Annotate one connection's packet sequence, subnet a small lab correctly, distinguish name-resolution failure from service failure, and explain where encryption starts and ends.

**Common gaps:** Ignoring IPv6; assuming ping failure proves a host is down; treating a listening port as a vulnerability; reading packet-analyzer summaries without inspecting fields; overlooking proxy behavior, clock skew, or encrypted DNS.

## Detailed learning sequence

Study ordinary delivery before assessment tools. The **practical track** covers addressing, local routing, DNS, transports, HTTP/TLS, captures, and fault diagnosis on your own virtual network. The **awareness track** covers enterprise switching, dynamic routing, Internet interconnection, and overlays until your specialization needs configuration experience.

### Stage 1 — Trace local and routed delivery

- [ ] Draw three separate views of the same lab: devices and links; IP subnets and gateways; services and trust boundaries. Label interfaces individually because a machine can have several addresses and several routes.
- [ ] Explain the destination address at each layer. For an off-subnet destination, the IP packet targets the remote host while the local Ethernet frame normally targets the next-hop router. MAC addresses do not identify a host across the Internet.
- [ ] Inspect an interface's address, prefix, link state, and route table before sending traffic. Calculate whether a destination is on-link, then identify the selected next hop using longest-prefix matching.
- [ ] Work through `192.168.56.0/27`: 32 total addresses, network `.0`, broadcast `.31`, and ordinary host range `.1` through `.30`. Calculate adjacent `/27` subnets. Learn `/31` point-to-point and `/32` host routes as exceptions to simplistic “always subtract two” rules.
- [ ] Recognize that private ranges can overlap between a VPN, home network, and lab. Diagnose overlapping routes instead of choosing an arbitrary private address and assuming isolation.
- [ ] Observe ARP requests and replies on the lab link, inspect the neighbor cache, and explain how cache entries reduce repeated broadcasts. Distinguish ARP from DNS: they answer different questions at different scopes.
- [ ] At awareness depth, explain access ports, tagged VLAN trunks, loop prevention, and routing between VLANs. A VLAN separates broadcast domains; the routing and firewall configuration determines permitted cross-VLAN communication.
- [ ] Describe NAT/PAT as address/port translation with state. Draw the original and translated flow tuples, return path, and timeout. Keep translation separate from the actual permit/deny policy.

### Stage 2 — Give IPv6 equal attention

- [ ] Expand and compress IPv6 notation correctly, using `::` no more than once in an address. Identify prefix length without assuming that the final four groups always describe a device in every network design.
- [ ] Distinguish `::1`, unspecified `::`, link-local addresses, unique-local addresses, global unicast, and multicast. Learn why a link-local destination often needs an interface/zone identifier on a multihomed host.
- [ ] Explain that Neighbor Discovery uses ICMPv6 for functions including neighbor discovery; IPv6 does not use ARP or broadcast. Map Router Solicitation/Advertisement and Neighbor Solicitation/Advertisement to their purposes.
- [ ] Separate address assignment from default-router discovery. SLAAC and DHCPv6 can contribute configuration, while IPv6 default routers are ordinarily learned from Router Advertisements, not supplied as a DHCPv6 default-gateway option.
- [ ] Inspect duplicate-address detection and address lifetimes conceptually. Learn that temporary and stable addresses can coexist, so an observed address is not necessarily a permanent device identifier.
- [ ] Test IPv4 and IPv6 explicitly and compare routes, name resolution, listener bindings, and firewall rules. A dual-stack application can work over one family while the other fails.
- [ ] Learn IPv6 MTU behavior: routers do not fragment forwarded IPv6 packets; source fragmentation and ICMPv6 Packet Too Big messages have distinct roles. Blocking necessary ICMPv6 can impair normal delivery. Consult the [IETF IPv6 specification](https://datatracker.ietf.org/doc/html/rfc8200) for these protocol rules.

### Stage 3 — Understand transports and measurement

- [ ] Identify a flow by source/destination addresses, source/destination ports, and transport protocol. Distinguish a listening socket from a particular established connection and ephemeral client ports from conventional service ports.
- [ ] Annotate TCP SYN, SYN-ACK, ACK, payload, FIN, and RST in a small capture. Follow sequence and acknowledgment numbers, remembering that acknowledgment concerns receipt of bytes rather than successful business processing.
- [ ] Separate receiver flow control from network congestion control. Explain why retransmissions, changing congestion windows, latency, and application buffering affect throughput differently.
- [ ] Compare UDP datagrams with TCP's byte stream. A UDP receive preserves a datagram boundary; a TCP application must define message framing. Neither choice by itself establishes authentication or confidentiality.
- [ ] At awareness depth, explain how QUIC adds transport behavior over UDP and uses TLS, and why HTTP/3 should not be interpreted as ordinary HTTP/1.1 packets with a different port.
- [ ] Measure latency with repeated small samples; report sample count and variation. Separate bandwidth capacity from achieved throughput, and throughput from useful application goodput. A single ping result is a narrow observation.
- [ ] Study MTU versus TCP MSS, fragmentation versus segmentation, and path-MTU discovery. Learn capture offload artifacts: a host capture can display checksum or segmentation appearances that differ from packets actually transmitted on the wire.

### Stage 4 — Resolve names and locate infrastructure

- [ ] Follow stub resolver, recursive resolver, cache, root/TLD delegation, and authoritative answer at a conceptual level. Explain which participant is authoritative for a name and which is merely returning cached data.
- [ ] Inspect query name, query type, response code, answer section, authority section, and TTL. Distinguish `NXDOMAIN`, a successful response with no record of the requested type, and a timeout.
- [ ] Practice A, AAAA, CNAME, PTR, MX, TXT, NS, SOA, and SRV records using a tiny lab zone or documented examples. A PTR answer is a reverse mapping, not proof that a host is trustworthy.
- [ ] Learn negative caching, alias chains, split DNS, search suffixes, and hosts-file overrides. Record which resolver and source address produced an answer before declaring two different answers inconsistent.
- [ ] Separate DNSSEC's validation of signed DNS data from DNS-over-TLS or DNS-over-HTTPS transport protection. Encrypted transport does not make the resolver's policy or every returned answer trustworthy.
- [ ] Trace a DHCP lease through discovery, offer, request, and acknowledgment at awareness depth, then inspect a real lease's address, gateway, resolver, and expiry. Learn how time synchronization supports TLS and enterprise authentication.
- [ ] Build a protocol-purpose table for SSH, SMB, LDAP, Kerberos, RDP, SNMP, NTP, SMTP, IMAP, and POP. Include identity mechanism, encryption options, normal client/server roles, and data sensitivity; use ports as hints requiring confirmation.

### Stage 5 — Follow browser traffic end to end

- [ ] Parse scheme, host, port, path, query, and fragment. Learn that a URL fragment is normally handled by the client and is not part of the HTTP request target sent to the server.
- [ ] Read a request method, target, headers, and optional body; read a response status, headers, and body. Distinguish transport failure, HTTP error response, and an application error encoded inside a successful HTTP response.
- [ ] Compare cookies, authorization headers, browser storage, and server session state. Trace redirects across origins and record where credentials are intended to be sent.
- [ ] Understand content negotiation, caching validators, cache keys, compression, and proxy handling. Learn HTTP/2 multiplexing conceptually and observe protocol negotiation in developer tools instead of assuming every page uses the same HTTP version.
- [ ] Explain certificate chain validation, hostname validation, validity periods, trust anchors, and the difference between a public certificate and a private key. A connection can encrypt traffic yet fail to authenticate the intended endpoint.
- [ ] Draw TLS termination at a reverse proxy and a separate upstream connection. Mark plaintext access by each endpoint. For a VPN, mark the tunnel endpoints and the traffic outside the tunnel; encryption boundaries depend on configuration.
- [ ] Distinguish WebSocket upgrades, server-sent event streams, and ordinary request/response traffic. Observe timeouts and reconnects using a local demonstration application.

## Guided labs with evidence

### Lab A — Addressing and local service delivery

**Setup:** Create two owned VMs on a host-only or internal virtual switch. Select a private subnet that does not conflict with existing routes. Permit only the lab service port between the VMs. Record any host access and avoid bridging to a shared physical LAN.

**Actions:** Assign addresses, record route and neighbor tables, and start a tiny static web service on a documented lab address. Request one synthetic page from the other VM. Capture only the relevant interface and bounded exchange.

**Expected observation:** Same-subnet traffic uses neighbor resolution and direct local delivery; it does not need an Internet gateway. The client selects an ephemeral port, and the server receives the request on its listener.

**Evidence:** Diagram, address calculations, listener identity, firewall rule, request output, and an annotated frame/packet/segment/application view. Do not include unrelated host traffic in the exported capture.

**Troubleshooting:** Check link, prefix, duplicate addresses, neighbor discovery, listener binding, and firewall separately. A service bound only to loopback cannot be reached through the VM's lab interface.

### Lab B — Four failures, four explanations

**Setup:** Keep the working baseline from Lab A and a local test name mapped through your lab's resolver or a lab hosts entry. Keep console access to both guests.

**Actions:** One at a time, use an incorrect name mapping, remove a required lab route where routing is part of your design, add a narrowly scoped deny rule for the lab port, and stop the service. Restore the baseline after each case. Compare a name lookup, direct-address connection, route inspection, listener inspection, and packet capture.

**Expected observation:** Failures occur at different stages. A name error can coexist with working IP connectivity; a service refusal differs from a silent drop; an application response proves more than a successful TCP connection.

**Evidence:** A fault matrix containing symptom, observation, hypothesis, discriminating test, cause, repair, and retest. Do not claim that every firewall implementation returns the same error.

**Troubleshooting:** If results appear inconsistent, inspect cached DNS, persistent connections, proxies, address-family selection, and rule order. Repeating a browser refresh may reuse an existing connection and bypass the intended setup step.

### Lab C — Encryption boundary and dual-stack comparison

**Setup:** Add local TLS to the synthetic service using a lab CA trusted only by the lab client or a dedicated client trust file. Configure IPv6 on the isolated link if your virtualization platform supports it.

**Actions:** Compare an HTTP request with HTTPS, then explicitly request IPv4 and IPv6. Inspect browser timing, the certificate, DNS answers, connection endpoints, and packet metadata. Test a mismatched hostname without disabling certificate checks.

**Expected observation:** HTTP content is readable in the unencrypted lab exchange; TLS protects application content on the encrypted connection while some metadata remains observable. IPv4 success does not establish IPv6 success. A hostname mismatch should prevent normal authenticated use.

**Evidence:** Two small annotated captures, the exact trust configuration, address-family results, and a diagram of what client, proxy, server, and network observer can see.

**Troubleshooting:** Verify certificate SANs, client clock, CA trust, listener bindings, and family-specific rules. Remove lab trust changes at cleanup. Avoid changing the host clock to simulate certificate failure.

## Capstone, rubric, and retention

Build a reproducible two-subnet lab with a router VM only after the single-link labs work. Run one local service, provide a lab name, document permitted traffic, and diagnose an unknown fault introduced by a peer or selected from your own shuffled fault cards. Capture only a few necessary exchanges.

Pass when you can independently: calculate the subnet; predict the selected route and next hop; explain IPv4 and IPv6 behavior; distinguish DNS/TCP/TLS/HTTP failures; annotate a capture; and restore the intended policy. Mark each **missing**, **guided**, or **independent**. All six should reach independent; unexplained traffic or a failed recovery means repeat that exercise.

The day after each lab, draw the connection from memory. Later, repeat with a different prefix, an IPv6 address, and a different failure. Keep a “prediction versus observation” log. When results surprise you, update the model and evidence rather than memorizing a new command. Continue with [Linux](05-linux-administration.md), [Windows](06-windows-administration.md), and [cryptography](08-security-principles-and-cryptography.md).
