# 09. Assessment methodology, reconnaissance, and enumeration

[All topic roadmaps](README.md) | [Original master roadmap](../../ETHICAL_HACKING_ROADMAP.md#09-assessment-methodology-reconnaissance-and-enumeration)

<!-- TOPIC-TOC:START -->

## Contents

- [Build a repeatable assessment process](#build-a-repeatable-assessment-process)
- [Passive reconnaissance and asset ownership](#passive-reconnaissance-and-asset-ownership)
- [Active discovery and service enumeration](#active-discovery-and-service-enumeration)
- [Lab sequence](#lab-sequence)
- [Detailed learning route and assessment notebook](#detailed-learning-route-and-assessment-notebook)
  - [Module A: turn scope into executable decisions](#module-a-turn-scope-into-executable-decisions)
  - [Module B: establish the expected system](#module-b-establish-the-expected-system)
  - [Module C: collect and reconcile discovery evidence](#module-c-collect-and-reconcile-discovery-evidence)
  - [Module D: enumerate access and configuration](#module-d-enumerate-access-and-configuration)
- [Three scenario labs with controls](#three-scenario-labs-with-controls)
  - [Lab 1: segmentation with an incomplete inventory](#lab-1-segmentation-with-an-incomplete-inventory)
  - [Lab 2: apparent service mismatch](#lab-2-apparent-service-mismatch)
  - [Lab 3: ordinary identity versus administrator](#lab-3-ordinary-identity-versus-administrator)
- [Troubleshooting and common reasoning errors](#troubleshooting-and-common-reasoning-errors)
- [Repeatable mini-engagement and pass rubric](#repeatable-mini-engagement-and-pass-rubric)

<!-- TOPIC-TOC:END -->



**Priority:** Core. **Prerequisites:** 01–08 at a working level.

## Build a repeatable assessment process

- [ ] Translate the business objective into security questions: who should access which records, which systems should communicate, and which operations require additional approval?
- [ ] Distinguish black-box, gray-box, and white-box assessments. Document what access and information you were given, and the resulting limitations.
- [ ] Define the test perspective: unauthenticated Internet user, ordinary application user, internal workstation, administrator, or source-code reviewer.
- [ ] Map assets, identities, data flows, entry points, dependencies, and trust boundaries before choosing tests.
- [ ] Create hypotheses with expected secure behavior, minimal test actions, likely evidence, potential impact, and a stop condition.
- [ ] Prioritize reachable, business-critical boundaries. Keep a backlog for other observations instead of repeatedly trying the same favorite technique.
- [ ] Maintain a timestamped activity log and a coverage matrix. Label results as tested, passed, finding, inconclusive, not applicable, or not tested, with reasons.
- [ ] Use control cases: compare an authorized user to an unauthorized user, a valid input to an invalid one, and the vulnerable state to the fixed state.
- [ ] Separate discovery, safe validation, impact analysis, reporting, remediation, retesting, and cleanup. Record uncertainty rather than converting a suspicion into a confirmed vulnerability.

## Passive reconnaissance and asset ownership

- [ ] Learn public DNS records, certificate transparency, RDAP/registration information, IP allocation and ASNs, published documentation, repositories, and archived pages.
- [ ] Separate externally observed facts from guesses. A certificate name or shared IP is evidence to investigate ownership, not an automatic scope expansion.
- [ ] Track source, timestamp, confidence, ownership, environment, and whether an asset may be stale or shared.
- [ ] Review deliberately public artifacts for configuration exposure and accidental secrets using synthetic examples. If a real secret appears during authorized work, follow the agreed handling process; do not use it merely to see what it accesses.
- [ ] Understand the privacy implications of OSINT. Use organizational information needed for the assessment; avoid collecting personal details unrelated to the objective.
- [ ] Learn how modern applications depend on CDNs, reverse proxies, SaaS, identity providers, DNS providers, and managed storage. Confirm which dependencies you can test.

## Active discovery and service enumeration

- [ ] Learn host discovery limitations: filtered probes, sleeping devices, IPv6, cloud security groups, proxies, and NAT can all change observations.
- [ ] Distinguish TCP connection behavior from UDP ambiguity. An unanswered probe is not proof that a service does not exist.
- [ ] Understand open, closed, filtered, and uncertain port states; service identification is a hypothesis until corroborated.
- [ ] Learn the effects of scan timing, retries, parallelism, packet loss, authentication, and fragile services. Start conservatively and use the agreed rate limits.
- [ ] Read what a scanner script does before enabling it. Labels such as discovery or safe are not a guarantee that the action fits your target or scope.
- [ ] Enumerate the configuration and access model of relevant services: HTTP(S), SSH, SMB, RDP, WinRM, DNS, LDAP, Kerberos, NFS, SNMP, SMTP, databases, message brokers, and administrative interfaces.
- [ ] For every service, ask: why is it reachable; who can authenticate; what can an ordinary identity do; where is encryption enforced; what is logged; who maintains it?
- [ ] Learn segmentation assessment, IPv4/IPv6 parity, management-plane separation, VPN exposure, and remote-access policy review using owned lab networks.
- [ ] Learn the purpose and risks of tunnels, proxies, and pivoting in segmented labs. Document exact permitted routes; broader reachability never enlarges authorization.

Use the [Nmap reference guide](https://nmap.org/book/man.html) to understand options and output, and [Wireshark documentation](https://www.wireshark.org/docs/) to correlate a tool's result with the actual network exchange.

## Lab sequence

1. Inventory a small isolated environment from its design documents.
2. Discover its reachable services from two allowed network positions.
3. Compare discovered services with the inventory and explain every discrepancy.
4. Inspect one service using its native client, a packet capture, and its server logs.
5. Change a firewall rule or authentication setting, repeat the observation, and record the difference.
6. Produce a coverage matrix showing what remains unknown and what access would resolve it.

**Ready to move on:** You can create an accurate asset/service map, justify every test, explain ambiguous results, and avoid mistaking a port number for a confirmed product or weakness.

## Detailed learning route and assessment notebook

Complete the following modules in order. The core outcome is a defensible small assessment with clearly stated coverage. Large Internet inventories, specialized discovery protocols, and complex multi-hop environments belong to later infrastructure work; they are not prerequisites for beginning supervised testing.

### Module A: turn scope into executable decisions

- [ ] Create an asset register with identifier, hostname, address, business owner, technical owner, environment, purpose, sensitivity, allowed perspective, and assessment status. Keep ownership evidence separate from technical observations.
- [ ] Convert a sample engagement brief into allowed and excluded actions. Include authentication testing, third-party integrations, maintenance windows, maximum request rates, credential lockout rules, emergency contacts, and cleanup responsibilities.
- [ ] Define what would make you pause: unexpected real data, service degradation, a shared service, an unfamiliar external endpoint, or an action outside the agreed permissions. Attach each condition to a documented next step.
- [ ] State three questions the assessment must answer. For example: can an ordinary employee reach management services, can a tenant read another tenant's records, and can an untrusted network reach a database?
- [ ] Give every planned check an identifier and link it to one question. A long command history is not evidence of meaningful coverage.

**Deliverable:** a one-page scope interpretation plus an approved-assets table. Explain how a newly discovered hostname would enter the table only after ownership and authorization are confirmed.

### Module B: establish the expected system

- [ ] Read architecture and deployment records before collecting observations. Draw networks, gateways, name resolution, identity providers, externally hosted dependencies, and management paths.
- [ ] Distinguish a logical asset from an address. One address can front many applications, while one application can use many addresses or short-lived instances.
- [ ] Record expected protocols, listeners, certificate names, software owners, authentication methods, and intended client populations. Include IPv6 when the environment uses it.
- [ ] Establish time synchronization and consistent time zones in logs. Assign a unique assessment identifier to synthetic requests where the application supports safe correlation.
- [ ] Choose a known working service as a positive control. Confirm that your test host, route, DNS, proxy, and credentials work before interpreting missing results.

**Deliverable:** an expected-reachability table for two test positions and an inventory of assumptions that still need evidence.

### Module C: collect and reconcile discovery evidence

- [ ] Start with the smallest permitted asset set. Save the exact target list, exclusions, tool settings, source interface, date, and output format before a bounded discovery run.
- [ ] Inspect representative packets to learn connection setup, resets, retransmissions, silent drops, and application negotiation. Separate network reachability from successful authentication.
- [ ] Confirm a service with its native protocol where safe. Compare the returned behavior with the scanner's hypothesis rather than treating a port label as identification.
- [ ] Record DNS aliases and reverse lookups as observations, without assuming either proves ownership. Note resolver differences and address changes during the assessment.
- [ ] Reconcile results against owner-provided inventory. Classify discrepancies as missing inventory, changed service, filtering, unsupported check, unavailable host, or unresolved cause.
- [ ] Preserve raw output and create a normalized service table. Keep tool-generated confidence and your own confidence distinct so uncertainty is not lost during reporting.

**Deliverable:** a map another learner can reproduce, including explanations for at least three intentionally introduced discrepancies.

### Module D: enumerate access and configuration

Work from service families to security questions rather than collecting banners indefinitely.

| Service family | Learn to observe | Question to resolve |
| --- | --- | --- |
| Remote administration | Authentication mechanisms, permitted networks, ordinary-user access, logging | Which identities and network positions can administer the host? |
| Directory and identity | Naming context, ordinary read permissions, encryption, account policy | Which directory information is intentionally exposed to which identities? |
| File sharing | Share configuration, effective permissions, synthetic directory listings | Do share and filesystem policies enforce the intended boundary? |
| Databases and brokers | Listener exposure, authentication, transport protection, test-role grants | Can the workload do only its required operations? |
| Mail and DNS | Supported roles, access policy, forwarding/recursion design, logs | Does configuration match the service's intended public or internal role? |
| HTTP services | Routing, virtual hosts, TLS, authentication entry points, application ownership | Which application and identity boundaries exist behind the listener? |

For each family, learn one native client well enough to distinguish authentication failure, authorization denial, protocol incompatibility, and connectivity failure. Save only synthetic records needed to show the distinction.

## Three scenario labs with controls

### Lab 1: segmentation with an incomplete inventory

**Setup:** an isolated client network, application network, and management network; three owned services; an inventory that deliberately omits one listener. Permit testing from two named machines.

**Action:** predict connectivity first, perform bounded discovery, then inspect host firewall and service logs for disputed results. Change one rule and repeat the same observation.

**Expected result:** intended application traffic succeeds; unnecessary management access is denied. Any deliberately permissive state is described precisely before repair.

**Evidence:** network diagram, target list, timestamps, connection observations, firewall change, and matched host events. **Control:** a permitted application connection remains successful. **Fix:** narrow the rule by intended source, destination, protocol, and port; verify both IP families when configured.

### Lab 2: apparent service mismatch

**Setup:** a reverse proxy serving two local applications and one server with a deliberately misleading training banner.

**Action:** compare routing, certificates, protocol negotiation, owner records, and local package information using the access given to you.

**Expected result:** distinguish the public entry point from the actual backend and reject unsupported product/version claims. **Evidence:** annotated observations and confidence labels. **Control:** inspect a service whose product identity is known. **Fix:** correct the inventory and unnecessary information disclosure if applicable; do not invent a vulnerability merely because a banner is unusual.

### Lab 3: ordinary identity versus administrator

**Setup:** a lab file service with a public synthetic folder, a team folder, and an administrator-only folder.

**Action:** compare anonymous, ordinary, and delegated administrative access with identical harmless reads. Inspect effective permissions and logs.

**Expected result:** only intended folders are accessible. **Evidence:** identity, requested action, decision, effective ACL, and event correlation. **Control:** the ordinary user can still read the team folder after repair. **Fix:** correct the responsible group or ACL and retest inherited permissions.

## Troubleshooting and common reasoning errors

- A timeout is ambiguous: inspect routes, name resolution, firewall state, service health, and retries before calling it a closed port.
- A different answer from two positions may reflect load balancing or split DNS. Compare the resolved address and request destination before asserting segmentation failure.
- Failed credentials can make an authenticated assessment effectively unauthenticated. Check the scanner's authentication-success evidence, not merely its saved username.
- Long inventories can hide duplicate assets. Maintain stable identifiers and preserve aliases instead of treating each name as an independent system.
- A reachable service can be intentional. Relate the exposure to a documented requirement, missing control, or demonstrated boundary failure.
- Avoid repeated probing when the remaining question is ownership or authorization. Resolve it through records and the engagement owner.

## Repeatable mini-engagement and pass rubric

Reset the lab, obtain its scope brief, and conduct a complete assessment without consulting your earlier results. Submit scope, architecture, asset/service map, coverage matrix, activity log, two evidence-backed observations, one confirmed finding, one explicitly inconclusive item, remediation verification, and cleanup confirmation.

Pass when another learner can reproduce the confirmed finding, every discovered asset has a scope decision, every claim has evidence or an uncertainty label, and legitimate connectivity still works after remediation. Repeat the exercise after changing one network rule and one identity permission. Explain the changed result rather than copying the earlier report. Use the Nmap and Wireshark references above to resolve tool behavior; use service-owner documentation to resolve intended behavior.