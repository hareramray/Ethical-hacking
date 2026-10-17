# 15. Active Directory and enterprise identity

[All topic roadmaps](README.md) | [Original master roadmap](../ETHICAL_HACKING_ROADMAP.md#15-active-directory-and-enterprise-identity)

<!-- TOPIC-TOC:START -->

## Contents

- [Learn administration before assessment](#learn-administration-before-assessment)
- [Assess identity attack paths](#assess-identity-attack-paths)
- [Hybrid identity and SaaS](#hybrid-identity-and-saas)
- [Lab and completion check](#lab-and-completion-check)
- [Expanded enterprise identity learning sequence](#expanded-enterprise-identity-learning-sequence)
  - [Stage 1: operate a small domain correctly](#stage-1-operate-a-small-domain-correctly)
  - [Stage 2: trace authentication and authorization](#stage-2-trace-authentication-and-authorization)
  - [Stage 3: map permissions and access paths](#stage-3-map-permissions-and-access-paths)
- [Credential-related research: required understanding and bounded depth](#credential-related-research-required-understanding-and-bounded-depth)
- [Certificates, hybrid identity, and SaaS modules](#certificates-hybrid-identity-and-saas-modules)
  - [Certificate services](#certificate-services)
  - [Hybrid and SaaS identity](#hybrid-and-saas-identity)
- [Scenario labs](#scenario-labs)
  - [Lab A: excessive group-management delegation](#lab-a-excessive-group-management-delegation)
  - [Lab B: Group Policy ownership and maintenance](#lab-b-group-policy-ownership-and-maintenance)
  - [Lab C: deprovisioning across an application](#lab-c-deprovisioning-across-an-application)
- [Troubleshooting and completion rubric](#troubleshooting-and-completion-rubric)

<!-- TOPIC-TOC:END -->



**Priority:** Core awareness; track depth for internal assessments. **Prerequisites:** Windows, DNS, networking, authentication, and host permissions.

## Learn administration before assessment

- [ ] Domains, forests, organizational units, sites, domain controllers, replication, global catalogs, and trust relationships.
- [ ] Users, computers, groups, nested groups, service accounts, managed service accounts, and privileged administrative identities.
- [ ] AD-integrated DNS, time synchronization, directory naming, LDAP queries, Group Policy, and domain join.
- [ ] Kerberos principals, tickets, ticket-granting services, service principal names, lifetimes, and delegation; compare NTLM at an architectural level.
- [ ] Access-control entries, inheritance, object ownership, delegated administration, and effective rights over directory objects.
- [ ] AD CS certificate authorities, templates, enrollment rights, certificate authentication, revocation, and private-key protection.
- [ ] Trust direction versus access direction, transitivity, authentication boundaries, and forest-level considerations.
- [ ] Distinguish on-premises AD DS from Microsoft Entra ID. Learn hybrid synchronization and federation as additional trust relationships, not interchangeable products.

The [Microsoft AD DS overview](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/get-started/virtual-dc/active-directory-domain-services-overview) is an entry point to the official administration documentation.

## Assess identity attack paths

- [ ] Map ordinary-user capabilities before privileged ones. Inventory privilege-bearing groups and indirect paths created by group nesting or delegated rights.
- [ ] Review excessive directory permissions, stale users/computers, unused trusts, service-account privileges, and inconsistent account lifecycle processes.
- [ ] Review Kerberos service-account exposure and password strength. Understand ticket-related attack classes and their prerequisites in a synthetic domain.
- [ ] Recognize Kerberoasting and AS-REP roasting as credential-auditing study topics; compare their prerequisites and account controls. Understand pass-the-hash and pass-the-ticket as distinct forms of credential-material reuse, with prevention and logging considerations.
- [ ] Study NTLM relay and name-resolution spoofing as protocol/control interactions; learn the roles of signing, channel binding, authentication policy, and network placement.
- [ ] Review constrained, unconstrained, and resource-based delegation concepts, and distinguish legitimate service behavior from unsafe trust.
- [ ] Review certificate template and enrollment permissions, issuance requirements, authentication uses, and certificate-based privilege boundaries.
- [ ] Understand credential reuse, privileged sessions on lower-trust machines, and administrative tier separation.
- [ ] Review GPO editing rights, SYSVOL content access, software deployment, backup infrastructure, and management platforms.
- [ ] Model trust edges using manually collected inventory before introducing graph tools. An apparent path requires validation of permissions, current state, and preconditions.
- [ ] Learn the importance of domain-controller backups, recovery plans, restricted administration, and protected management access.
- [ ] Recognize high-impact capabilities such as directory replication abuse or authentication-ticket forgery conceptually; reserve any practical validation for purpose-built domains with explicit scope.
- [ ] Connect common research terminology such as DCSync and forged authentication tickets to the specific permissions, key material, and trust assumptions involved; avoid treating a technique name as proof that its prerequisites exist.

## Hybrid identity and SaaS

- [ ] Tenant roles, application registrations, enterprise applications, consent, service principals, workload identities, and secret/certificate lifetimes.
- [ ] Federation, provisioning, SCIM, synchronization agents, external guests, cross-tenant relationships, and deprovisioning delays.
- [ ] MFA enrollment and recovery, conditional access, session policies, legacy authentication, and emergency access account controls.
- [ ] SaaS sharing settings, OAuth application access, email forwarding policy, audit availability, and retention.
- [ ] Compare an application's local role model with the identity provider's claims; verify that removing a group or permission eventually removes access as intended.

## Lab and completion check

Build a small isolated domain with a controller, member server, workstation, ordinary users, one service identity, and delegated administrators. Document normal authentication. Introduce two excessive-permission relationships, map their impact using test identities, and remediate them. Add a logging view showing the relevant identity events. If hardware is limited, use a dedicated hosted enterprise lab.

**Ready to move on:** You can explain an identity access path from its permissions and prerequisites, fix the underlying delegation issue, and demonstrate that legitimate work still succeeds.

## Expanded enterprise identity learning sequence

Core awareness means explaining domain administration, authentication, delegated rights, and identity lifecycle. Internal-assessment depth adds detailed permission analysis, enterprise protocols, certificates, hybrid identity, and recovery. Work through these stages in an isolated domain or a dedicated training environment; do not connect a deliberately misconfigured domain to an employer or household network.

### Stage 1: operate a small domain correctly

- [ ] Design a naming and addressing plan for a domain controller, member server, workstation, test users, service identities, and administrator accounts. Document DNS and time dependencies before joining machines.
- [ ] Create organizational units for a simple administrative purpose, then distinguish directory organization from a security boundary.
- [ ] Create role-based groups and assign resources through groups. Explain nesting, group scope, direct membership, and effective membership in your chosen design.
- [ ] Apply one benign Group Policy setting and inspect which objects receive it. Study linking, inheritance, filtering, precedence, and troubleshooting through the resulting policy state.
- [ ] Create a service identity with only its needed rights and document how its credential is managed. Learn managed service-account concepts before assessing their deployment.
- [ ] Practice join, ordinary logon, password change, account disablement, group removal, and clean machine/account retirement.
- [ ] Record backup and restore responsibilities. Understand that snapshots alone are not a complete enterprise identity recovery strategy.

**Deliverable:** an administration runbook and diagram that another learner can use to build the same domain without excessive default privileges.

### Stage 2: trace authentication and authorization

- [ ] Diagram normal Kerberos authentication, service access, ticket lifetimes, service principal names, and the identities responsible for each step. Use a benign file-service access as the reference transaction.
- [ ] Distinguish authentication proof from authorization to a directory object or server resource. A valid ticket does not imply access to every service action.
- [ ] Compare Kerberos and NTLM at the architectural level: credential material, challenge/response or ticket concepts, service identity, and control dependencies.
- [ ] Study how DNS, time, service identity registration, trust configuration, and network reachability affect normal authentication. Diagnose failure before interpreting it as a vulnerability.
- [ ] Learn access-control entries, inheritance, object ownership, effective rights, and delegated administration. Identify which property or action a particular permission controls.
- [ ] Inspect user/computer objects, group-management rights, password-reset delegation, GPO administration, and service configuration rights in your lab.
- [ ] Separate current directory state from access tokens or cached authentication already issued. Document when changed membership affects the actual resource decision.

**Deliverable:** a narrated authentication trace plus two examples showing why successful authentication and authorized resource access are different decisions.

### Stage 3: map permissions and access paths

Create a graph only after you can explain its edges manually. Each edge needs a source identity, destination object, permission or trust relationship, evidence, prerequisites, and a timestamp.

- [ ] Map direct and nested membership in privileged groups; record business owner and justification for each administrative role.
- [ ] Review delegated rights on organizational units, groups, user/computer objects, GPOs, service accounts, and certificate-related objects.
- [ ] Identify permissions that let an ordinary administrator of one component influence a more privileged component. Validate the actual object scope and inheritance rather than relying on a technique label.
- [ ] Review administrative sessions on lower-trust machines, management agents, software deployment, backups, and shared local administration as part of the identity system.
- [ ] Study constrained, unconstrained, and resource-based delegation as different trust designs. Explain the intended service-to-service access and the configuration that limits it.
- [ ] Study trust direction, transitivity, authentication restrictions, and administrative boundaries using diagrams before adding another domain or forest.
- [ ] Introduce graph-analysis tools only after the manual baseline. Check stale inventory, unresolved identities, missing permissions, and assumed prerequisites before reporting a path as confirmed.

**Phase gate:** explain an ordinary-user-to-administrative-influence path entirely in terms of verified rights and conditions, then remove one excessive relationship and show the path no longer exists.

## Credential-related research: required understanding and bounded depth

Learn the named attack families already listed in this roadmap as ways to identify failed assumptions and relevant controls, rather than as a checklist of actions to perform on a real domain.

| Research family | Prerequisites to understand | Defensive study and evidence |
| --- | --- | --- |
| Service-ticket password auditing | Service identity configuration and password-derived key exposure | Service-account design, credential strength/lifecycle, managed identities, and relevant authentication telemetry |
| Pre-authentication-related auditing | Account configuration and obtainable authentication material | Review intended account settings and monitor unusual authentication requests |
| Credential-material reuse | Possession and applicability of a credential artifact | Credential isolation, administrative separation, session hygiene, and logon visibility |
| Relay and name-resolution interactions | Network placement, accepted authentication, and missing protocol protections | Signing, channel binding where applicable, authentication policy, and name-resolution design |
| Delegation misuse | Specific delegation rights and service/principal relationships | Narrow delegation, protected administrative identities, and configuration review |
| Replication or ticket-forgery capabilities | Highly sensitive permissions or key material | Restrict control-plane rights, protect key material, and prepare recovery procedures |

Practical reproduction of the more invasive families belongs only in purpose-built synthetic domains with explicit exercise objectives. For the core track, explain prerequisites, affected trust assumptions, preventive settings, expected telemetry, and how to verify a configuration repair without collecting real credential material.

## Certificates, hybrid identity, and SaaS modules

### Certificate services

- [ ] Distinguish a certificate authority, template, enrollment policy, issued certificate, private key, and relying service.
- [ ] Inspect who can enroll, what identity information is accepted, what approval is required, which purposes the certificate supports, and who can modify the template or CA configuration.
- [ ] Trace certificate-based authentication through chain validation, intended use, identity mapping, validity, and revocation handling in the actual environment.
- [ ] Review private-key protection, agent permissions, enrollment endpoints, certificate renewal, and retirement. A securely stored certificate still needs a correct issuance and identity-binding policy.
- [ ] Use a disposable test CA and synthetic subjects to learn intended enrollment before investigating misconfiguration classes.

### Hybrid and SaaS identity

- [ ] Draw AD DS, Entra ID, synchronization/provisioning agents, federation services, application registrations, service principals, and relying applications as distinct components.
- [ ] Identify the source of authority for each attribute, group, credential, and account state. Record which system can overwrite or restore a value.
- [ ] Study tenant roles, consent, application permissions, workload credentials, conditional access, recovery, and emergency administration through the actual deployment's documentation.
- [ ] Trace joiner, mover, and leaver events from the directory to downstream applications. Measure provisioning delays, cached claims, active sessions, and application-owned API keys.
- [ ] Review guest invitations, shared resources, cross-tenant access, and local application roles. Removing a directory group may not remove separately granted application access.

## Scenario labs

### Lab A: excessive group-management delegation

**Setup:** two ordinary fictional users, a delegated helpdesk group, and a harmless test-resource group. Give the helpdesk role an intentionally overbroad management permission. **Action:** inspect the effective right and change membership only in the synthetic test group. **Expected result:** establish the excessive administrative influence precisely. **Evidence:** ACL, identity, membership event, and resource-access result. **Control:** the intended helpdesk task still works. **Fix:** delegate only the required object/action scope and retest using a fresh session.

### Lab B: Group Policy ownership and maintenance

**Setup:** a benign policy that writes a training banner to lab workstations. **Action:** compare who may read, apply, edit, and link the policy; use a harmless banner change to establish unintended edit rights. **Expected result:** distinguish normal policy application from unauthorized administrative influence. **Evidence:** rights, policy version, resulting policy, and change logs. **Control:** authorized administrators can still maintain the setting. **Fix:** narrow editing/linking permissions and verify inheritance and existing groups.

### Lab C: deprovisioning across an application

**Setup:** a local application or permitted test tenant consuming identity groups, with synthetic users and a documented session lifetime. **Action:** remove a role and disable the user, then inspect new logins, existing sessions, background jobs, and application-issued credentials. **Expected result:** access ends within the specified policy. **Evidence:** a timestamped lifecycle trace and decisions at each boundary. **Control:** an active user retains intended access. **Fix:** correct provisioning, local roles, revocation handling, and session policy as needed.

## Troubleshooting and completion rubric

Common false conclusions arise from DNS/time failures, stale group tokens, replication delays, wrong logon context, inherited permissions, absent auditing, and graph data collected before a configuration change. Establish a working authentication control and identify the exact directory or resource server making the decision. Do not interpret every directory read as sensitive exposure or every administrative capability as unintended escalation.

Pass with an administration runbook, authentication diagram, manually verified permission graph, three repaired delegation/lifecycle findings, logging evidence, and a recovery/cleanup plan. Every path must name its prerequisites and distinguish inferred influence from observed capability. Repeat the assessment after changing one group membership and one delegation rule, and explain which access decisions changed. Choose certificates, hybrid identity, or advanced authentication research as the next specialization based on the environments you expect to assess.