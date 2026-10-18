# 15. Tutorial: Active Directory and enterprise identity

[Index](README.md) · [Complete source curriculum](curriculum/15-active-directory-and-enterprise-identity.md) · [Original roadmap](../roadmaps/15-active-directory-and-enterprise-identity.md)

## Learn normal administration before assessing access paths

Enterprise identity is a network of authority: accounts join groups, groups receive rights over objects, services trust authentication, and applications maintain their own sessions. A graph can summarize those relationships, but it cannot establish that every inferred path is currently usable. Prerequisites are Windows administration, DNS, networking, authentication, host permissions, and tutorials 12 and 14.

Use an isolated Windows domain or a dedicated enterprise training environment, never a deliberately weakened domain connected to household or employer networks. Plan a controller, member server, workstation, ordinary fictional users, one service identity, and delegated administrators. If resources are limited, perform the synthetic policy exercise first and mark domain-dependent evidence as not yet collected.

## Lesson 1: understand the directory's structure

| Component | What it means | Assessment implication |
| --- | --- | --- |
| Domain and forest | A domain organizes directory identity/policy; a forest groups domains under shared directory architecture and trust assumptions | Do not treat every organizational unit as an independent security boundary |
| Organizational unit | Administrative grouping used for delegation and policy application | Review its object scope, inherited permissions, and linked policies |
| Domain controller and replication | Controllers maintain directory data and propagate changes | Identify which controller supplied evidence and allow for replication state |
| Sites and global catalog | Sites model topology; global catalogs support forest-wide directory lookup functions | Authentication and lookup paths may depend on topology and availability |
| Trust relationship | One authority accepts authentication from another under configured rules | Authentication acceptance and actual resource authorization remain separate |
| Users, computers, groups | Directory identities and membership relationships | Resolve nested membership and effective rights, not only direct membership |
| Service/managed service accounts | Workload identities with credential-management requirements | Restrict rights and review how credentials and service bindings are maintained |

The directory stores objects and information used for authentication and access management. Start from the [Microsoft AD DS overview](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/get-started/virtual-dc/active-directory-domain-services-overview) and follow the administration documentation for the chosen server environment. On-premises AD DS and Microsoft Entra ID are distinct systems; hybrid synchronization or federation creates additional relationships between them.

Create a naming/addressing plan and document DNS and time sources before domain join. AD-integrated DNS supports finding domain services; time affects authentication validity. Separate everyday accounts from privileged administration. Create role-oriented groups and grant resource access through groups, documenting group scope and nesting. Use managed service-account capabilities where appropriate to the actual workload, without assuming every application supports them.

Apply one benign Group Policy setting, such as a training banner. Record the link location, inheritance, filtering, precedence, and resulting applied policy. Practice join, ordinary logon, password change, disablement, membership removal, and clean machine/account retirement. Document backup and recovery responsibilities; a VM snapshot by itself is not a complete domain recovery strategy.

## Lesson 2: trace authentication and authorization

Use a harmless file-share read as the reference transaction. The client establishes domain identity, requests service access through Kerberos, presents a ticket to the intended service, and the service evaluates access to the requested resource. Identify principal, key distribution service, ticket-granting ticket/service, service principal name, service ticket, lifetime, and target service identity. Tickets are authentication artifacts; resource ACLs still govern the action.

NTLM uses a challenge/response architecture rather than Kerberos service-ticket behavior. Protocol choice, service identity, network placement, signing, channel binding where applicable, and authentication policy affect security. Diagnose DNS, time, SPN registration, trust, and reachability failures before interpreting failed authentication as a vulnerability.

Read-only commands on a joined Windows lab machine:

```powershell
whoami /user
whoami /groups
klist
gpresult /r
```

These show current identity/membership, available ticket information, and applied policy context. They do not prove every possible effective right. Run a permitted synthetic share read before and after a membership change. Record whether the old session continues to work, whether a new session sees the new group state, and which server made the resource decision. Do not copy ticket material or real account information into a public portfolio.

Directory objects have access-control entries, inheritance, ownership, and delegated rights. Distinguish reading an attribute, changing one property, managing group membership, resetting a password, editing a GPO, and changing ownership. A general label such as “has access” hides the action that matters. Ordinary directory reads may be intentional; establish policy and sensitivity before reporting exposure.

## Lesson 3: map rights manually before graph tools

Each edge needs source identity, destination object, exact permission/trust, scope/inheritance, evidence, prerequisite, and timestamp. Example: `helpdesk-training → can modify member attribute → report-readers`. Another edge says `report-readers → read → fictional report`. Together they demonstrate influence over this report's access, not domain-wide administration.

Review privileged groups and nesting, stale users/computers, unused trusts, service-account privileges, OU/group/user/computer delegations, GPO administration, certificate objects, and object owners. Include management agents, software deployment, backup infrastructure, shared local administration, and privileged sessions on lower-trust machines. These components may influence identity even when they are not directory objects.

Trust direction describes who accepts whose authentication. If resource domain A trusts identity domain B, identities from B may be authenticated for resources in A, but only actual grants permit specific actions. Transitivity and authentication restrictions change the model; draw the exact relationship before adding a second domain/forest.

Delegation lets a service act in a user's context under a configured trust design. Unconstrained, constrained, and resource-based constrained delegation place control and restrictions in different locations. Identify intended service-to-service access, service principals, configuration owner, and limits. Do not treat a technique name as proof that relevant rights and conditions exist.

Graph tools help inventory larger environments after this manual baseline. Validate stale collection, unresolved identities, inferred edges, missing permissions, and prerequisite assumptions. Keep “possible influence,” “verified effective permission,” and “observed harmless action” as different confidence levels.

## Lesson 4: a portable delegation exercise

Save this as `delegation_lab.py`; run with Python 3 on Windows or Linux. It models a small explicit policy and is **not an AD effective-access engine**. Its purpose is to teach source/object/action evidence without touching directory accounts.

```python
groups = {"report-readers": {"alice"}, "training-auditors": set()}
delegated = {("helpdesk", "report-readers", "change-members"),
             ("helpdesk", "training-auditors", "change-members")}

def add_member(actor, group, member):
    if (actor, group, "change-members") not in delegated:
        return "DENIED"
    groups[group].add(member)
    return "CHANGED"

assert add_member("helpdesk", "training-auditors", "bob") == "CHANGED"
groups["training-auditors"].remove("bob")  # Restore synthetic state.
delegated.remove(("helpdesk", "training-auditors", "change-members"))
assert add_member("helpdesk", "training-auditors", "bob") == "DENIED"
assert add_member("helpdesk", "report-readers", "bob") == "CHANGED"
print("unintended scope denied; intended helpdesk work preserved")
```

The fix removes only the unintended relationship and retains intended helpdesk work. In an actual isolated domain, use two ordinary fictional users, a delegated helpdesk group, and a harmless resource group. Inspect the actual effective directory right, change membership only in that synthetic group, correlate the event, restore membership, narrow delegation at its source, and repeat with a fresh session. Record inherited rights as well as local ACL entries; removing one explicit grant may leave another path.

## Lesson 5: understand credential-related research families

The purpose of this module is to identify assumptions, prerequisites, controls, and telemetry. It does not require extracting hashes, tickets, or secrets or exercising replication abuse. Those high-impact research tasks belong to separately scoped purpose-built domains.

| Family and terminology | Prerequisite/failed assumption | Prevention and observable evidence |
| --- | --- | --- |
| Kerberoasting / service-ticket password auditing | Relevant service-account configuration and obtainable ticket material can permit password-strength analysis | Strong managed credentials where supported, minimal service rights, credential lifecycle, authentication telemetry |
| AS-REP roasting / pre-authentication-related auditing | Particular account settings expose material without the expected pre-authentication requirement | Review intended account settings, remove unnecessary exceptions, inspect authentication requests |
| Pass-the-hash | Possession of applicable credential material may permit authentication without knowing the original password | Credential isolation, protected administration, reduced reuse, logon visibility |
| Pass-the-ticket | Possession and usability of an authentication ticket can convey its existing authority | Session hygiene, restricted privileged sessions, ticket lifetime and authentication monitoring |
| NTLM relay and name-resolution spoofing | Accepted authentication, network positioning, and missing protocol bindings/protections interact | Signing/channel binding where supported and applicable, authentication policy, controlled name resolution/network placement |
| Delegation misuse | Specific service/principal relationships allow unintended impersonation | Narrow delegation, protect sensitive identities, review who controls the relationship |
| DCSync / replication abuse | Highly sensitive directory replication rights are available to an unintended identity | Restrict control-plane permissions, monitor sensitive changes and replication-related activity, recovery planning |
| Forged authentication tickets | Sensitive signing/key material and trust assumptions are compromised | Protect key material, isolate administration, investigate and recover through documented procedures |

For each family, write a non-operational scenario naming the required permission/configuration/material, the trust boundary, the relevant control, and a configuration retest. Credential reuse and privileged sessions on low-trust machines can connect otherwise separate systems. Administrative tier separation reduces these relationships. A tool naming a family is not proof of the prerequisites or of actual compromise.

## Lesson 6: certificates and AD CS

Distinguish certificate authority, certificate template, enrollment policy, issued certificate, private key, and relying service. The CA issues credentials under policy; a template describes requested properties and intended use; the relying service decides whether a certificate authenticates the expected identity.

For a disposable test CA and synthetic subject, inspect who can enroll, who can change the template/CA, accepted identity information, required approval, allowed purposes, and enrollment endpoints/agents. Trace chain validation, intended use, identity mapping, validity, and revocation handling in the actual application. A protected private key cannot compensate for a policy that issues a certificate for an unintended identity.

Practice legitimate enrollment, renewal, and retirement before investigating misconfiguration. Record private-key access, agent authority, certificate rollover, and relying-service behavior after revocation. Avoid assuming every certificate use has identical revocation timing or identity mapping; verify the specific deployment's documentation and behavior.

## Lesson 7: hybrid identity and SaaS lifecycle

Draw AD DS, Entra tenant, synchronization/provisioning agents, federation services, application registrations, enterprise applications/service principals, and relying SaaS applications as separate components. For every attribute, credential, group, and account-state flag, identify the authoritative system and what can overwrite or restore it.

Tenant roles, app consent, application permissions, workload identities, secret/certificate lifetimes, and emergency accounts define cloud authority. Conditional access, MFA enrollment/recovery, session policy, and legacy authentication need their own evaluation. A local application role can remain privileged after an identity-provider group has changed.

Trace joiner, mover, and leaver events through SCIM, synchronization, federation, local roles, cached claims, active sessions, application API keys, external guests, invitations, and cross-tenant sharing. Review SaaS sharing settings, OAuth application access, email-forwarding policy, audit availability, and retention. Record the intended deprovisioning deadline before measuring it.

Use a fictional employee: remove one role, then disable the account. At each timestamp test new login, existing session, queued job, and application-issued credential against synthetic data. Keep another active employee as the control. If access persists, identify whether the cause is provisioning delay, independent local grant, cached claim, or session/token lifetime. Repair the actual responsible component and retest.

## Scenario labs, recovery, and completion

**Delegated group management:** apply the portable model in the isolated domain, verify the exact synthetic object scope, remove excessive rights, refresh session, and preserve intended helpdesk work. **GPO ownership and maintenance:** use a training-banner policy; distinguish read, apply, edit, and link permissions, change only the harmless text, inspect resulting policy/version/logs, and narrow unintended editing/linking rights. **Application deprovisioning:** perform the timed lifecycle exercise and fix local/provisioned/session authority consistently.

Common false conclusions arise from wrong logon context, stale tokens, replication delays, DNS/time failures, inherited ACLs, missing auditing, and outdated graph data. Establish a working authentication control and identify the exact controller/resource server. A successful logon is not a successful authorization check, and a normal directory read is not automatically a finding.

Protect controller administration, management paths, backups, recovery credentials, and restore procedures. Keep a cleanup ledger for memberships, delegations, test users/computers, GPO changes, certificates, application grants, and retained evidence. Verify the lab's normal operations after restoration.

Complete an administration runbook, narrated authentication diagram, manually verified permission graph, three repaired delegation/lifecycle findings, logging evidence, and recovery plan. Repeat after changing one membership and one delegation rule and explain the changed resource decisions. Select certificate, hybrid, or advanced authentication research depth based on the environments you intend to assess.

**Answer-guided checks:** Why is an OU not an independent security boundary? It organizes administration within broader directory authority. Why can role removal leave access? Existing tokens/sessions or independent grants may remain. Why does a graph path need verification? It may encode stale facts or unproven conditions. Why review certificate issuance as well as key storage? Incorrect identity binding can create an unintended valid credential even when its key is protected.
