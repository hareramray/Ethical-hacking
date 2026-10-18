# 09. Tutorial: assessment methodology, reconnaissance, and enumeration

[Index](README.md) · [Complete source curriculum](curriculum/09-assessment-methodology-reconnaissance-and-enumeration.md) · [Original roadmap](../roadmaps/09-assessment-methodology-reconnaissance-and-enumeration.md)

## Start with the question, not the scanner

An assessment converts uncertainty into evidence about a particular security boundary. For example, “Can an ordinary employee administer the reporting server?” contains a subject, an action, a resource, and an expected decision. “Find open ports” is only a collection activity supporting that question. Work through tutorials 01–08 first; you should understand routing, accounts, permissions, HTTP, and a command shell. Use two disposable VMs for network exercises, or the loopback exercise below when only one computer is available.

Black-box work supplies little internal information; gray-box work supplies selected accounts or diagrams; white-box work supplies implementation and configuration access. These describe available information, not permission to perform every possible test. Also record your perspective: Internet client, internal workstation, ordinary user, administrator, or code reviewer. An administrative configuration read and an ordinary-user access attempt answer different questions.

Write a hypothesis before each check: “From client A, ordinary user Lina should read team reports but should not modify service configuration.” Add the smallest action, a positive control, expected evidence, likely impact, and a stop condition. Unexpected real data, an unfamiliar external dependency, instability, or a shared system should trigger the agreed escalation process. Keep discovery, validation, impact analysis, reporting, repair, retest, and cleanup as distinct stages.

## Lesson 1: turn scope into an executable notebook

Create four small tables. The asset register contains stable asset ID, names and addresses, business/technical owner, environment, purpose, sensitivity, ownership evidence, allowed perspective, and status. The test register links each check ID to a business question. The activity log records time, source host/interface, target, identity, action, request identifier, output location, and changes. The coverage matrix records the conclusion and remaining uncertainty.

| Coverage label | Meaning | Example |
| --- | --- | --- |
| Tested/passed | The stated expected behavior was observed | Team member reads a synthetic team document |
| Finding | Evidence establishes an unintended boundary failure | Ordinary user changes a privileged service's harmless label |
| Inconclusive | Necessary evidence is missing or contradictory | Timeout without target logs or a working route control |
| Not tested | The check has not been performed | IPv6 excluded because the fixture has no configured IPv6 service |
| Not applicable | The control does not apply, with reason | No file-upload feature exists in the reviewed application |

Do not turn “not tested” into a pass. Prioritize reachable boundaries affecting critical data and administration. Put lower-priority observations in a backlog instead of repeatedly trying a familiar tool. Define rate limits, windows, lockout behavior, permitted authentication tests, emergency contact, third-party exclusions, and cleanup ownership in the scope interpretation. Newly discovered names enter an investigation queue until ownership and authorization are established.

## Lesson 2: establish the expected system

Draw client → resolver → gateway/proxy → application → database and separately draw management paths and the identity provider. Record expected listener, certificate name, authentication method, intended client population, maintainer, and logs. A logical application may span several transient addresses; one proxy address may serve several applications. Preserve aliases under a stable asset ID instead of counting them as unrelated machines.

Make an expected-reachability table before observing traffic:

| Source | Destination | Intended result | Why |
| --- | --- | --- | --- |
| Ordinary workstation | HTTPS application | Allow | Normal employee work |
| Ordinary workstation | Management interface | Deny | Administration uses a dedicated path |
| Management workstation | Management interface | Allow with authorized identity | Maintenance |
| Application | Database | Allow only required protocol/identity | Runtime operation |

Record DNS answers, NAT, VPN routes, cloud security groups, proxies, IPv4/IPv6, and split DNS. These can explain different observations without a security defect. Synchronize VM clocks and record time zones. A unique benign request marker such as `assessment-09-001` helps correlate client, proxy, and server events without collecting confidential content.

## Lesson 3: passive reconnaissance and ownership

Passive sources describe what others publish. DNS supplies names and routing hints; certificate-transparency records reveal certificate names and issuance history; RDAP/registration and ASN allocation records help identify registrants and network operators. Published documentation, repositories, and archived pages may reveal architecture or obsolete configuration. None automatically proves ownership of the underlying service or authorizes active requests.

For each observation, preserve source, retrieval time, confidence, proposed owner, environment, and stale/shared status. A hostname on a certificate can belong to a historical deployment. A CDN address can serve many unrelated customers. A SaaS login page may be a dependency whose underlying platform is excluded. Resolve these ambiguities with inventory and the assessment owner.

Practice with a fictional public configuration file containing `TRAINING_ONLY_NOT_A_SECRET`. Record that the artifact exposes a credential-shaped value, who could retrieve it, and the handling process. Do not try real discovered credentials. Restrict OSINT to organizational information needed for the question; unrelated personal details increase privacy risk without improving the assessment.

## Lesson 4: understand active observations

A completed TCP connection shows a listener accepted that connection from that position. A reset often indicates a reachable closed port; silence can reflect filtering, loss, unavailable routing, or an unresponsive service. UDP often provides less decisive evidence because a healthy service need not answer an arbitrary datagram. Port states are observations from a particular test, not permanent properties of a host. [Nmap port-state reference](https://nmap.org/book/man-port-scanning-basics.html).

Retries and parallelism affect results and load. Begin with a few approved endpoints and low concurrency; record timeouts and rate limits. Read each optional scanner script's behavior, privileges, requests, and side effects before enabling it. A “safe” category is not a target-specific safety guarantee. Corroborate a scanner's service label with native protocol behavior, server configuration, package records, and logs.

The following lab uses Python 3 on Windows or Linux and binds only to loopback. Create an empty working directory and place a single file named `marker.txt` containing `assessment-09-001`. In that directory run:

```text
python -m http.server 8765 --bind 127.0.0.1
```

In another terminal run this Python program:

```python
import socket
from urllib.request import urlopen

for port in (8765, 8766):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=2):
            print(port, "TCP connection accepted")
    except OSError as exc:
        print(port, type(exc).__name__)

with urlopen("http://127.0.0.1:8765/marker.txt", timeout=2) as response:
    print(response.status, response.read(100).decode().strip())
```

Expect port 8765 to accept, port 8766 usually to refuse if nothing else uses it, and the HTTP read to return `200 assessment-09-001`. If another program occupies 8766, select another unused port and document the change. Stop the server with Ctrl+C and repeat: the previously working control should now fail. This proves the probe detects the fixture's state change; it does not prove anything about a remote firewall.

Optionally inspect loopback traffic in Wireshark using a display filter `tcp.port == 8765`. Identify connection establishment, the request, response, and termination; compare the server's access log. Packet capture availability depends on the installed capture interface and permissions. Preserve only the synthetic exchange. Use the [Wireshark documentation](https://www.wireshark.org/docs/) for your capture platform.

## Lesson 5: enumerate access models by service family

After identifying a service, ask why it is reachable, who authenticates, what ordinary identities can do, where encryption applies, what is logged, and who maintains it. Learn one native client per relevant family rather than collecting banners indefinitely.

| Family and topics | Interpretation to practice | Minimal harmless evidence |
| --- | --- | --- |
| HTTP(S), reverse proxies, administrative interfaces | Routing/virtual hosts can select different applications behind one listener; TLS identity and application authorization are separate | Known marker response, certificate/configuration, route owner |
| SSH, RDP, WinRM, VPN | Connectivity, authenticated logon, and administrative authority are separate decisions | Approved login with a dedicated account, permitted groups and source networks |
| SMB and NFS | Share/export and filesystem policy jointly determine intended access | Read a synthetic public/team/private marker as each test identity |
| LDAP and Kerberos | Directory reads may be intentional; authentication does not grant every directory operation | Ordinary read of a fictional account and documented effective rights |
| Databases and message brokers | Runtime identities need narrow operations, not general administration | Read one training row or consume one permitted test message |
| DNS and SMTP | Public authoritative/mail-receiving roles differ from internal recursion, relay, or administration | Owner-supplied configuration, bounded native-client observation, matching logs |
| SNMP and management services | Exposed management data and write capability require distinct review | Read-only synthetic inventory with the intended test credential |

Classify failures as connectivity, protocol negotiation, authentication, or authorization. “Login failed” is not evidence of a firewall block. “Directory listing succeeded” does not imply write permission. Treat tunnels, proxies, and pivot routes as explicitly named paths in a segmented lab: additional reachability never changes authorized assets.

## Lesson 6: three controlled scenarios

**Segmentation and missing inventory.** In isolated VM networks, place an application service, a management service, and a third listener deliberately omitted from the inventory. Use two named client positions. Predict each connection, perform only the bounded checks, then reconcile differences with routes, firewall logs, and listener configuration. Narrow the unintended rule by source, destination, protocol, and port. Recheck configured IPv4 and IPv6 paths and verify normal application traffic still works. A loopback-only exercise cannot substitute for this segmentation evidence.

**Misleading service identity.** Give a local training application a fictional outdated response header and place two applications behind an owned reverse proxy. Compare hostname routing, certificates, native behavior, installed build, and owner records. The correct result may be an inventory correction and an unsupported version suspicion, rather than a vulnerability. A known application is the positive identification control.

**Ordinary versus administrative identity.** Create synthetic public, team, and administrative folders. Record anonymous, ordinary, and delegated administrator read decisions using the same marker request. Repair the excessive group or ACL, refresh sessions where necessary, and recheck inheritance. Keep team collaboration working. Record identity, object, action, policy, outcome, and correlated event; do not infer ordinary-user influence from an administrator's successful operation.

## Reconciliation, troubleshooting, and assessment

Normalize raw results into one service table while retaining original output and tool confidence. Classify discrepancies as missing inventory, changed service, filtering, unsupported check, unavailable host, duplicate/alias, or unresolved cause. Save target lists, exclusions, tool settings, source position, dates, and output formats so another learner can reproduce the observation.

A timeout requires a working control and route/DNS/service evidence. Different answers from two sources require comparing actual destinations before declaring a segmentation issue. An authenticated scan needs authentication-success evidence, not merely a stored username. A reachable service needs an unintended boundary or missing requirement before becoming a finding.

For the final mini-engagement, reset the fixture, change one network rule and one identity permission, and assess it without copying earlier results. Submit scope interpretation, architecture, inventory, coverage matrix, activity log, two supported observations, one confirmed finding, one inconclusive item, retest, and cleanup. Your explanation should predict why the changes alter outcomes.

**Answer-guided checks:** Why is a certificate name not permission to test? It supplies discovery evidence but may be stale or third-party owned. Why is a port number insufficient identification? Applications can use nonstandard ports and proxies hide backends. Why retain a positive control after repair? A broken route or unavailable service can otherwise imitate successful restriction. What resolves an unknown ownership question? Owner/authorization evidence, rather than more probing.
