# 04. Trace a connection from address to application

[Index](README.md) | [Complete source curriculum](curriculum/04-networking-and-internet-protocols.md) | [Original roadmap](../roadmaps/04-networking-and-internet-protocols.md)

## Prerequisites and lab

Complete computing foundations and the isolated lab. Use Python 3, a local HTTP client, and optionally a packet analyzer on your own loopback/internal interface. Begin with loopback; extend to two owned VMs only after recording addresses, routes, and permitted ports. The goal is to predict where delivery occurs, observe the relevant layer, diagnose one failure at a time, and restore normal behavior.

## 1. Learn layers through one message

The OSI model separates physical, data-link, network, transport, session, presentation, and application concerns. TCP/IP groups these more coarsely into link, Internet, transport, and application layers. Use them to organize questions, not to force every modern protocol into one box.

A browser request becomes application bytes inside transport data, inside an IP packet, inside a link frame. Each header describes delivery or processing at its layer. A switch forwards frames using link information; a router forwards IP packets between networks; a firewall applies traffic policy; a proxy receives a connection and creates another; the application interprets business meaning.

For a remote subnet, the IP destination remains the remote host while the Ethernet destination is normally the local next-hop router. MAC addresses operate on a link; they are not Internet-wide host identities. ARP finds an IPv4 neighbor's link address. DNS finds information associated with names. They answer different questions.

Switches learn MAC locations. A broadcast domain is the area reached by link broadcasts. VLANs separate such domains logically; access ports normally carry one assigned VLAN and trunks carry tagged VLAN traffic. Routing and firewall policy decide whether VLANs communicate. Physical cables alone do not describe logical topology.

## 2. Calculate IPv4 and route selection

An IPv4 address has 32 bits. `/27` means 27 network bits and five remaining bits: 32 addresses per block. For `192.168.56.0/27`, the network is `.0`, broadcast `.31`, and ordinary host range `.1`–`.30`. The next block is `.32/27`, ending at `.63`. `/31` point-to-point links and `/32` host routes are exceptions to blindly subtracting two addresses.

Verify with Python:

```python
import ipaddress
net = ipaddress.ip_network("192.168.56.0/27")
print(net.netmask, net.num_addresses, net.broadcast_address)
print(ipaddress.ip_address("192.168.56.20") in net)
print(ipaddress.ip_address("192.168.56.40") in net)
```

Expect `255.255.255.224 32 192.168.56.31`, then `True`, then `False`. On-link destinations can be delivered directly after neighbor resolution; others need a route. The most specific matching prefix wins. A `/32` route can override a `/24`, which overrides a default `/0`; route metrics resolve choices among applicable routes according to the platform.

Private IPv4 ranges include `10.0.0.0/8`, `172.16.0.0/12`, and `192.168.0.0/16`. Loopback uses `127.0.0.0/8`, link-local uses `169.254.0.0/16`, and multicast uses `224.0.0.0/4`. Public and special-purpose classifications need context: not every address outside private ranges is a suitable ordinary public target. Overlapping VPN/home/lab prefixes cause ambiguous routing; private addressing alone does not provide isolation.

NAT rewrites addresses; PAT also maps ports. Draw `guest:ephemeral → server:port` and the translated source tuple, plus the state needed for returning traffic. Translation is not an application authorization decision. Connection tracking also supports stateful firewall decisions; stateless rules evaluate packets without that flow history. Inbound/outbound rules, segmentation, and application filtering must match the intended traffic policy.

Read-only Linux inspection:

```bash
ip -br address
ip route
ip route get 127.0.0.1
ip neigh
```

On Windows, inspect `Get-NetIPConfiguration`, `Get-NetRoute`, and `Get-NetNeighbor`. A route tells you intended forwarding, not that an application will answer.

## 3. Give IPv6 its own model

IPv6 has 128-bit addresses written as hexadecimal groups. Leading zeroes within a group may be omitted; one run of zero groups can be compressed with `::`. Thus `2001:db8::1` is a documentation address example, not a live target. `::1` is loopback, `::` is unspecified, `fe80::/10` is link-local, `fc00::/7` is unique-local, and `ff00::/8` is multicast. Link-local addresses often need a zone/interface identifier because the same address scope can exist on several links.

IPv6 uses Neighbor Discovery through ICMPv6 rather than ARP or broadcast. Neighbor Solicitation/Advertisement discovers neighbors; Router Solicitation/Advertisement discovers router information. SLAAC can derive addresses from advertised prefixes; DHCPv6 supplies configuration in relevant deployments. Default routers are ordinarily learned through Router Advertisements, not a DHCPv6 default-gateway option. Duplicate-address detection, preferred/valid lifetimes, and temporary addresses affect what you observe.

IPv6 routers do not fragment forwarded packets. Sources can fragment, and ICMPv6 Packet Too Big messages support path-MTU discovery. Blocking all ICMPv6 can therefore break normal delivery. [IETF IPv6 specification](https://www.rfc-editor.org/rfc/rfc8200)

Test families separately: a hostname can have A and AAAA answers, but one listener, route, or firewall family may fail. Do not disable IPv6 to make the symptom disappear before you understand it. On Linux, `ip -6 address` and `ip -6 route` show separate state.

## 4. Understand transport and measurement

A flow is identified by source/destination addresses, ports, and transport protocol. A listening socket is waiting for clients; an established connection belongs to one conversation. Client ports are often temporary, while conventional service ports are only hints to identity.

TCP begins with SYN, SYN-ACK, ACK, then exchanges a byte stream using sequence numbers and acknowledgments. Retransmission handles missing data. FIN closes a direction orderly; RST aborts a connection. A TCP acknowledgment means bytes reached the peer transport, not that an invoice was processed successfully. Applications must frame messages within the byte stream.

Flow control protects the receiver's capacity; congestion control responds to network conditions. UDP preserves datagram boundaries but does not itself supply TCP-style reliable delivery. An application can build reliability over UDP. QUIC does that and more, integrating TLS for secure transport; HTTP/3 is carried over QUIC, not ordinary HTTP/1.1 with a changed port.

MTU limits packet size on a link; TCP MSS concerns transport payload. Segmentation, IP fragmentation, and application message boundaries differ. Path-MTU discovery avoids oversized paths. Asymmetric routes can make forward and return behavior differ. Host capture offload can display apparent checksum/segmentation artifacts that differ from on-wire packets.

Bandwidth is capacity; throughput is achieved transfer rate; goodput excludes overhead and repeated work. Latency is delay, jitter is delay variation, and loss affects delivery. Record sample count and spread rather than reporting one ping as a complete measurement. A blocked echo request does not prove a host is down.

## 5. Resolve names and infrastructure services

A stub resolver asks a recursive resolver. That resolver may answer from cache or follow delegation through root/TLD information to an authoritative server. TTL limits cache lifetime; negative answers can also be cached. Split DNS, search suffixes, hosts-file overrides, and resolver policy can produce different legitimate answers. Record resolver and source context.

| Record | Meaning | Interpretation caution |
| --- | --- | --- |
| A / AAAA | IPv4 / IPv6 address | Address does not establish service health |
| CNAME | Alias to another name | Follow the chain and its ownership boundary |
| PTR | Reverse mapping | Not proof of identity or trust |
| MX | Mail exchanger | Priority and hostname, not inbox content |
| TXT | Text data used by various protocols | Interpret according to the protocol |
| NS / SOA | Delegation and zone authority metadata | Distinguish authoritative data from a cache |
| SRV | Service location with priority, weight, port | Common in service discovery |

`NXDOMAIN` means the name does not exist in that response context. A successful response with no record of the requested type differs from a timeout. DNSSEC authenticates signed DNS data under its validation chain; encrypted DNS transports protect a connection to a resolver. They solve different problems.

DHCP's discover/offer/request/acknowledgment sequence assigns leased configuration such as address, gateway, resolver, and expiry. Inspect the actual lease rather than assuming defaults. NTP/time synchronization supports authentication, certificate validity, and log correlation; display time zones differ from actual clock error.

| Protocol | Normal purpose and boundary |
| --- | --- |
| SSH | Authenticated remote terminal/file operations; verify host identity and user access |
| SMB | File/service access; share and filesystem authorization matter |
| LDAP | Directory queries; bind identity, transport, and directory permissions matter |
| Kerberos | Ticket-based authentication dependent on trusted services and time |
| RDP | Remote interactive desktop; account/logon policy and restricted reachability matter |
| SNMP | Device monitoring/management; versions and credentials determine protection |
| NTP | Clock synchronization; source trust affects time-dependent systems |
| SMTP | Message transfer/submission; relay policy and transport differ from content trust |
| IMAP / POP | Mailbox access; authentication and protected transport matter |

## 6. Follow the browser end to end

For `http://127.0.0.1:8000/item?q=demo#section`, the scheme selects a protocol, host/port select a destination, path/query identify the request, and the fragment normally stays in the client. A name-based URL may require DNS before connecting. HTTPS adds authenticated TLS before application data.

Requests contain method, target, headers, and optional body. Responses contain status, headers, and body. GET retrieves; POST commonly submits; PUT/PATCH update according to application semantics; DELETE requests removal. A 404 is an application-layer response, not a failed TCP connection. A 200 can still contain an application-level error object.

Headers describe content type, negotiation, caching, authorization, and other context. Cookies may carry session identifiers; server state determines their authority. Browser storage, cookies, and authorization headers have different access/transmission rules. Follow redirects across origins and verify where credentials go. Compression changes representation, cache validators support reuse, and cache keys decide which requests share content. HTTP/2 multiplexes streams; developer tools show actual negotiated protocol.

TLS checks a certificate chain to a trusted anchor, intended hostname, usage, and validity. A certificate contains public information; the associated private key must remain private. Encryption without correct endpoint authentication can protect traffic to the wrong party. Reverse proxies/CDNs may terminate TLS and create a new upstream connection, so mark where plaintext exists. VPNs protect traffic between tunnel endpoints; split tunnels protect selected routes, while full tunnels route more traffic through the tunnel. Remote-access and site-to-site designs have different endpoints.

WebSockets provide a long-lived bidirectional channel, server-sent events stream server updates, and ordinary requests can also be long-lived. Timeouts/reconnects matter beyond page downloads.

## 7. Worked connection and fault lab

Run the loopback service from tutorial 02, then request its page with `curl --max-time 3 -v http://127.0.0.1:8000/`. Observe connect, request, response, and server log. Capture only this loopback exchange if your analyzer supports it; loopback captures may not include Ethernet/ARP because no physical link is used. In a two-VM internal lab, observe ARP and Ethernet separately. Annotate SYN/SYN-ACK/ACK, request bytes, response, and teardown; do not export unrelated traffic.

Build four fault cards: wrong lab name, wrong route in an explicitly routed two-subnet lab, a narrow deny for the lab port, and stopped service. Restore between cards. Predict the first failing stage, then compare resolver result, direct-address request, selected route, listener, logs, and bounded capture. A refusal and silent timeout suggest different observations but are not universal firewall fingerprints.

For TLS, use tutorial 08's lab certificate checks and a dedicated client trust file. Compare HTTP readable content with TLS-protected application records, while noting visible connection metadata. Test correct trust/name, untrusted issuer, mismatched hostname, and out-of-validity time without disabling verification. Repeat IPv4 and IPv6 where configured.

## Advanced map and completion

STP prevents switching loops; link aggregation combines links under a coordination model; dynamic routing distributes reachability; BGP relies on interdomain policy and trust. Overlays carry virtual networks over an underlay; SDN separates or centralizes control decisions; load balancing distributes work; high-availability design handles component failure. Each adds state and failure modes. Study configuration deeply when your track needs it, after you can explain a single link.

Deliver address calculations, interface/route diagrams, protocol annotations, four repaired faults, and an encryption-boundary diagram. If a name fails but IP works, investigate resolution. If local works but remote fails, inspect binding/routing/policy. If TCP succeeds but the page is wrong, investigate HTTP/application state. If only IPv6 fails, compare family-specific settings. Pass when you can explain and independently repair the exact observed layer, then repeat later with a different prefix and fault.
