# 16. Cloud, containers, and Kubernetes

[All topic roadmaps](README.md) | [Original master roadmap](../ETHICAL_HACKING_ROADMAP.md#16-cloud-containers-and-kubernetes)

<!-- TOPIC-TOC:START -->

## Contents

- [Cloud concepts that transfer between providers](#cloud-concepts-that-transfer-between-providers)
- [Choose one provider, then translate](#choose-one-provider-then-translate)
- [Cloud assessment skills](#cloud-assessment-skills)
- [Containers](#containers)
- [Kubernetes](#kubernetes)
- [Lab and completion check](#lab-and-completion-check)
- [Detailed cloud learning path and specialization choices](#detailed-cloud-learning-path-and-specialization-choices)
  - [Foundation module: design a disposable assessment environment](#foundation-module-design-a-disposable-assessment-environment)
- [AWS study sequence](#aws-study-sequence)
  - [AWS 1: hierarchy and effective permissions](#aws-1-hierarchy-and-effective-permissions)
  - [AWS 2: network, workloads, and data](#aws-2-network-workloads-and-data)
  - [AWS 3: visibility and capstone](#aws-3-visibility-and-capstone)
- [Azure study sequence](#azure-study-sequence)
  - [Azure 1: distinguish tenant identity and resource authorization](#azure-1-distinguish-tenant-identity-and-resource-authorization)
  - [Azure 2: workloads, storage, and private access](#azure-2-workloads-storage-and-private-access)
  - [Azure 3: visibility and capstone](#azure-3-visibility-and-capstone)
- [Google Cloud study sequence](#google-cloud-study-sequence)
  - [Google Cloud 1: hierarchy and IAM](#google-cloud-1-hierarchy-and-iam)
  - [Google Cloud 2: network, data, and execution](#google-cloud-2-network-data-and-execution)
  - [Google Cloud 3: visibility and capstone](#google-cloud-3-visibility-and-capstone)
- [Container curriculum: image, runtime, host, and registry](#container-curriculum-image-runtime-host-and-registry)
- [Kubernetes curriculum: policy must match effective behavior](#kubernetes-curriculum-policy-must-match-effective-behavior)
- [Troubleshooting and final readiness rubric](#troubleshooting-and-final-readiness-rubric)
  - [Cross-provider scenario: inherited access survives a narrow local fix](#cross-provider-scenario-inherited-access-survives-a-narrow-local-fix)

<!-- TOPIC-TOC:END -->



**Priority:** Core concepts; track depth in one provider first. **Prerequisites:** networking, IAM, APIs, Linux, and basic application deployment.

## Cloud concepts that transfer between providers

- [ ] Shared responsibility for IaaS, PaaS, SaaS, and serverless; control plane versus workload/data plane.
- [ ] Organizations, accounts/subscriptions/projects, regions, resource hierarchies, management groups, and separation of development from production.
- [ ] Human and workload identities, role assumption, federated login, temporary credentials, trust policies, resource policies, and inherited permissions.
- [ ] Explicit deny, policy conditions, role scope, privilege boundaries, organization controls, and the interaction of identity and resource policies.
- [ ] Virtual networks, subnets, routes, security groups/firewalls, private endpoints, public exposure, egress, DNS, load balancers, and administrative access.
- [ ] Object storage, managed databases, message queues, compute instances, serverless functions, secrets services, and key management.
- [ ] Instance/workload metadata concepts, service-account credentials, default permissions, and the relationship between application flaws and cloud identity.
- [ ] Audit logging, data-access logging, retention, centralized collection, alerting, and who can disable or delete evidence.
- [ ] Encryption keys, backup ownership, snapshots, image sharing, replication, and data lifecycle.
- [ ] Infrastructure as code, configuration drift, deployment identities, state-file sensitivity, and destructive-change review.

## Choose one provider, then translate

| Area | AWS vocabulary to learn | Azure vocabulary to learn | Google Cloud vocabulary to learn |
| --- | --- | --- | --- |
| Organization | Organizations, accounts, SCPs | Tenants, management groups, subscriptions | Organizations, folders, projects, organization policy |
| Identity | IAM roles/policies, STS | Entra identities, Azure RBAC, managed identities | IAM roles/policies, service accounts, workload identity |
| Networking | VPC, security groups, endpoints | VNet, NSG, Private Link | VPC, firewall policies, private access |
| Compute | EC2, Lambda, ECS/EKS | VMs, Functions, App Service, AKS | Compute Engine, Cloud Run, GKE |
| Storage and secrets | S3, KMS, Secrets Manager | Storage accounts, Key Vault | Cloud Storage, Cloud KMS, Secret Manager |
| Visibility | CloudTrail and relevant service logs | Activity, sign-in, and resource logs | Cloud Audit Logs and service logs |

The names organize your study; they do not imply identical behavior. Read the documentation for the service and policy type actually in use. Provider introductions: [AWS documentation](https://docs.aws.amazon.com/), [Azure documentation](https://learn.microsoft.com/en-us/azure/), and [Google Cloud security](https://cloud.google.com/security).

## Cloud assessment skills

- [ ] Inventory resources and effective permissions using a dedicated read-only review identity wherever possible.
- [ ] Identify excessive roles, unsafe trust relationships, long-lived keys, unowned service identities, public data, and unmanaged exposure.
- [ ] Review CI/CD-to-cloud federation, claim restrictions, workload identity scope, and the difference between deployment and runtime permissions.
- [ ] Test cross-account/tenant boundaries using two accounts you own or are explicitly permitted to use, with synthetic objects.
- [ ] Review serverless triggers, event-source permissions, environment configuration, dependencies, and function identity.
- [ ] Assess managed database access, backup sharing, secret retrieval permissions, signed URLs, and object lifecycle.
- [ ] Correlate a permitted test action with provider audit logs. Record which actions need additional data-plane logging.
- [ ] Review provider testing policies, cost constraints, and teardown before launching vulnerable cloud training environments.

## Containers

- [ ] Images versus containers, layers, registries, tags versus digests, build contexts, runtime configuration, and image provenance.
- [ ] Linux namespaces and cgroups, root inside a container versus host authority, user namespaces, rootless operation, and capabilities.
- [ ] Privileged mode, host networking/PID sharing, writable host mounts, runtime sockets, device access, and security profiles.
- [ ] Non-root workloads, read-only filesystems where practical, minimal images, dependency patching, secret injection, and resource limits.
- [ ] Image scanning versus runtime configuration review: a clean package scan does not prove safe privileges or trustworthy code.
- [ ] Registry access, signing/verification, build secrets, sensitive layers, and reproducible deployment.

## Kubernetes

- [ ] Control-plane components, API server, etcd, kubelets, namespaces, pods, deployments, services, ingress, and network plugins.
- [ ] Authentication, RBAC roles/bindings, service accounts, workload identity, token handling, and effective permissions.
- [ ] Pod Security admission, security contexts, capabilities, host access, admission controls, and trusted image policy.
- [ ] NetworkPolicy enforcement depends on the installed network plugin; namespaces alone do not create full tenant isolation.
- [ ] Secrets storage and encryption, configuration exposure, audit policy, control-plane access, backups, and node lifecycle.
- [ ] Helm charts, operators, custom resources, controllers, and the permissions granted to installed extensions.
- [ ] Multi-tenancy assumptions, cluster-admin access paths, managed-service boundaries, and container/host isolation limitations.

Use the [Kubernetes security checklist](https://kubernetes.io/docs/concepts/security/security-checklist/) to select applicable checks and then verify their behavior in your actual cluster.

## Lab and completion check

Deploy a small application with synthetic records in a disposable cloud project or account. Draw its network and identity paths. Correct one excessive workload permission and one unintended exposure. Produce before/after evidence and audit logs. Separately, deploy a local containerized application, document its privileges, and reduce them while preserving function. Add a local Kubernetes cluster only after you understand containers.

**Ready to move on:** You can distinguish application, identity, network, and platform responsibility; explain effective access; demonstrate a cloud or container fix; and remove all billable lab resources using a checked teardown inventory.

## Detailed cloud learning path and specialization choices

Begin with the shared concepts, complete one provider track, then add containers. Learn Kubernetes after you can explain a single container's identity, filesystem, network, and privileges. The other provider tracks are translation exercises or later specializations; a beginner does not need production-level expertise across all three clouds before moving forward.

### Foundation module: design a disposable assessment environment

- [ ] Draw the resource hierarchy, billing ownership, identity sources, public/private network paths, data stores, workload credentials, and logging destinations before deployment.
- [ ] Use dedicated lab identities and synthetic data. Separate the human administrator, read-only reviewer, deployment identity, and runtime identity so their permissions can be compared.
- [ ] Define region, service, resource-count, and spending constraints. Learn what budget notifications and service quotas do, how they are enforced, and what must still be checked manually.
- [ ] Read the provider's current testing policy for the selected services. Identify any additional restrictions associated with managed infrastructure and shared services.
- [ ] Create a teardown inventory that includes compute, disks, addresses, load balancers, gateways, snapshots, logs, registries, and retained backups. Some resources outlive the application that created them.
- [ ] Version the infrastructure and capture the intended configuration. Treat state files, deployment credentials, and exported configuration according to their sensitivity.
- [ ] Establish a known permitted request and a known denied request before investigating findings. Record the identity, action, resource, context, policy, and observed decision.

**Foundation deliverable:** an architecture diagram, identity matrix, resource ledger, data classification, and teardown procedure. Do not assume that public reachability and public authorization are the same condition.

## AWS study sequence

### AWS 1: hierarchy and effective permissions

- [ ] Learn Organizations and account boundaries, IAM principals, roles, role sessions, temporary credentials, policies, and resource identifiers.
- [ ] Distinguish permission to assume a role from permissions exercised after assumption. Review the trust relationship and the resulting session separately.
- [ ] Study identity policies, resource policies, permissions boundaries, session policies, and organization controls through the specific request being assessed. Read the nuanced evaluation rules rather than reducing every case to one simplified formula.
- [ ] Review policy actions, resources, conditions, wildcard scope, cross-account relationships, and service-specific policy behavior. Explain why a boundary or organization restriction does not by itself grant an action.

Use the official [AWS policy evaluation logic](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html) to justify effective-permission conclusions, including explicit denies and interactions among policy types.

### AWS 2: network, workloads, and data

- [ ] Trace VPC subnets, routes, gateways, security groups, network ACLs, endpoints, DNS, load balancers, and administrative access for one small application.
- [ ] Compare EC2 instance roles, Lambda execution roles, and container task/workload roles. Identify who can assign a powerful identity to a workload and who can change that workload's code.
- [ ] Review S3 object access, bucket policies, public-access controls, signed access, encryption, versioning, and lifecycle using synthetic objects.
- [ ] Inspect KMS and Secrets Manager access together with workload permissions. Key-use and secret-read permissions need their own review.
- [ ] Study event triggers, queues, functions, backups, snapshots, and image sharing. Include resource policies and the identities producing/consuming events.

### AWS 3: visibility and capstone

Learn CloudTrail management versus data-event coverage and the additional service logs required for your selected operations. Prove visibility with a known synthetic action; do not infer that a management-event record proves object-read logging. Consult [CloudTrail management-event documentation](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/logging-management-events-with-cloudtrail.html) and the linked service-specific guidance.

**Capstone:** deploy a private synthetic object store and a workload that needs one narrow operation. Compare an intended role with an overbroad lab role, remove the unnecessary permission, and verify application success plus denial of the extra action. Retain policy evidence, exact resource identifiers, request outcomes, and audit records. Tear down from the resource ledger.

## Azure study sequence

### Azure 1: distinguish tenant identity and resource authorization

- [ ] Learn the relationship among Entra tenants, management groups, subscriptions, resource groups, and resources. Record which identities and administrators govern each layer.
- [ ] Separate Entra directory roles from Azure resource roles. Review principal, role definition, assignment scope, inheritance, conditions where used, and data-plane permissions for the selected service.
- [ ] Compare users, groups, service principals, managed identities, and federated workload access. Determine who can modify an identity's credential or attach it to a workload.
- [ ] Review role-assignment and policy-management authority separately from ordinary resource-operation permissions.

Use the [Azure RBAC overview](https://learn.microsoft.com/en-us/azure/role-based-access-control/overview) to study assignment scope and effective resource access; verify the service's data-plane model independently.

### Azure 2: workloads, storage, and private access

- [ ] Trace VNets, subnets, routes, NSGs, DNS, public endpoints, Private Link, gateways, and application ingress. Verify both routing and name resolution for private access.
- [ ] Compare VM, App Service, Functions, and AKS identity attachment and configuration. Separate deployment privileges from runtime data access.
- [ ] Review Storage account access, container sharing, delegated access mechanisms, key handling, and resource/data permissions using synthetic objects.
- [ ] Review Key Vault permissions, network restrictions, secret/certificate lifecycle, recovery settings, and the workload's actual retrieval path.
- [ ] Study Azure Policy as governance alongside RBAC authorization. Check what a policy evaluates, what it enforces, and what remediation requires.

### Azure 3: visibility and capstone

Trace administrative changes through the Activity Log, authentication through appropriate Entra logs, and workload/data actions through relevant resource logs. Learn configuration, retention, access controls, and export for each required evidence source. The [Azure Activity Log documentation](https://learn.microsoft.com/en-us/azure/azure-monitor/fundamentals/activity-log) explains its control-plane role; it should not be treated as complete application telemetry.

**Capstone:** grant a managed identity only the synthetic storage or secret access its application requires. Demonstrate an unnecessary inherited grant, narrow it at the correct scope, and verify valid application behavior. Record role assignments, network/DNS behavior, data-access outcome, and the relevant logs before checking teardown.

## Google Cloud study sequence

### Google Cloud 1: hierarchy and IAM

- [ ] Learn organizations, folders, projects, resources, principals, service accounts, and the difference among basic, predefined, and custom roles.
- [ ] Trace inherited allow policies and applicable conditions, deny policies, and other access boundaries used in your environment. Identify the exact permission required for a chosen API action.
- [ ] Distinguish using a service account as a workload identity from authority to impersonate or administer that service account. Review who can change its credentials, policies, or attached workload.
- [ ] Study workload federation and short-lived access before relying on long-lived service-account keys. Record issuer, subject, audience, and attribute restrictions for the actual integration.

Use the [Google Cloud IAM overview](https://docs.cloud.google.com/iam/docs/overview) to map principals, roles, resources, inheritance, and access controls. Account for policy propagation when timing a retest instead of assuming every change is instantaneous.

### Google Cloud 2: network, data, and execution

- [ ] Trace VPCs, subnets, firewall policies, routes, DNS, private access, load balancing, and administrative connectivity.
- [ ] Compare Compute Engine, Cloud Run, and GKE workload identities and deployment authority. Determine who can change code or configuration running under a privileged service account.
- [ ] Review Cloud Storage access, signed access, object lifecycle, encryption, and project-level inherited grants with synthetic data.
- [ ] Review Secret Manager and Cloud KMS permissions separately from the permission to deploy the application consuming them.
- [ ] Study Pub/Sub producer/consumer access, serverless event routing, managed database connectivity, backup ownership, and resource sharing relevant to your application.

### Google Cloud 3: visibility and capstone

Study Admin Activity, Data Access, System Event, and Policy Denied logs, then check which categories and services are relevant to your test. Confirm configuration and record a known action before concluding that missing evidence means no access occurred. Use the [Cloud Audit Logs overview](https://docs.cloud.google.com/logging/docs/audit) for service-specific coverage and configuration details.

**Capstone:** deploy a synthetic application under a dedicated service account, remove a broad inherited or project-level grant, and preserve the precise data operation the application needs. Capture hierarchy, policy, identity, request result, and audit evidence. Verify that unused keys, deployment artifacts, and retained billable resources are removed or explicitly accounted for.

## Container curriculum: image, runtime, host, and registry

1. **Build and provenance:** inspect the build context, base image, dependency lockfiles, build stages, image layers, artifact digest, package inventory, and registry permissions. Learn why deleting a secret in a later layer may not remove earlier stored content.
2. **Runtime identity:** inspect user/group IDs, capabilities, namespace configuration, user mappings, security profiles, resource limits, and writable paths. Distinguish application needs from convenience privileges.
3. **Host boundaries:** review bind mounts, devices, host namespace sharing, privileged configuration, and runtime socket access. State what host authority each configuration exposes without attempting a container escape.
4. **Network and secrets:** identify published ports, internal networks, outbound destinations, injected credentials, and log handling. Verify secrets are available only to intended workloads and absent from images and unnecessary logs.
5. **Operations:** test readiness, graceful shutdown, bounded resource use, patch/rebuild workflow, image promotion, and rollback. A clean image scan does not establish a safe runtime configuration.

The [Docker Engine security documentation](https://docs.docker.com/engine/security/) is a starting point for namespaces, resource controls, daemon access, capabilities, and host security mechanisms. Review your actual runtime configuration rather than assuming its defaults are sufficient.

**Lab:** run a benign report service with an unnecessarily writable synthetic directory and excessive capabilities. Record its effective identity, mounts, and permissions. Reduce privileges and writable paths, then verify legitimate report creation and denial of access to an unrelated sentinel file. Evidence includes image digest, runtime configuration, positive/negative results, and logs. Restore the lab after each experiment.

## Kubernetes curriculum: policy must match effective behavior

- [ ] Map API server, datastore, scheduler, controllers, kubelets, nodes, namespaces, workloads, services, ingress, and the installed network implementation. Identify managed-provider responsibilities separately.
- [ ] Review authentication identities, kubeconfig protection, RBAC roles/bindings, service accounts, token use, and workload federation. Check effective verbs/resources and namespace or cluster scope.
- [ ] Study permissions to create workloads, change controllers, bind roles, read secrets, and access interactive workload operations. Explain their indirect impact in the actual cluster without assuming all permissions are equivalent.
- [ ] Inspect security contexts, allowed capabilities, host access, volume types, security profiles, and Pod Security admission. Test whether the selected policy admits or rejects representative benign manifests.
- [ ] Apply network policy only after confirming plugin enforcement. Test intended ingress, egress, DNS, and necessary platform traffic from two synthetic workloads.
- [ ] Review secret storage, API access, encryption configuration, audit policy, backup protection, node patching, image trust, registry credentials, and admission extensions.
- [ ] Inspect Helm charts, operators, controllers, webhooks, and custom resources as software with privileges. Their installation can introduce broad authority even when the application workload is restricted.
- [ ] Learn reconciliation and drift: a manual fix to a running pod may be overwritten by its controller or next deployment. Repair the versioned configuration that defines the desired state.

**Lab:** create two namespaces and separate service accounts in a local cluster. Deploy synthetic workloads, verify intended API access, and test network reachability using harmless requests. Repair one overbroad binding and one missing isolation rule. Evidence must show both denied cross-boundary access and permitted application/DNS traffic. Use the Kubernetes checklist linked above to compare configuration with observed enforcement.

## Troubleshooting and final readiness rubric

An access denial can come from identity policy, resource policy, hierarchy controls, encryption-key access, network restrictions, DNS, or an expired credential. Identify the decision point before adding permissions. A missing log can mean the category was not enabled, collection was delayed, or you queried the wrong account/project/region. A private endpoint can coexist with other public access paths. A Kubernetes namespace alone is not a complete isolation policy.

Pass the core cloud track by completing one provider capstone and the container lab, with architecture, identity matrix, before/after policy evidence, legitimate controls, logs, and verified teardown. Pass the Kubernetes extension only when API permissions, workload restrictions, and network policy are tested independently. For a second provider, write a translation table that names semantic differences rather than substituting service names. Advanced multi-cloud, cluster multi-tenancy, and platform research remain explicit specialist goals.

### Cross-provider scenario: inherited access survives a narrow local fix

**Setup:** in your chosen provider's disposable lab, create two synthetic data resources, an intended reader identity, and an inherited permission that also grants access to the second resource. Record the complete hierarchy and effective-policy evidence before changing anything.

**Action:** remove only the local grant, repeat a harmless read using a fresh credential where appropriate, and inspect why access remains. Then remove or narrow the responsible inherited grant at its actual source.

**Expected result:** the second synthetic resource becomes inaccessible while the intended first resource remains readable. Account for documented policy propagation and avoid interpreting an immediate stale result as final.

**Evidence:** identity/session, resource identifiers, hierarchy, policy versions, timestamps, request decisions, and available data-access logs. **Control:** the application continues its intended read with the same runtime identity. **Fix:** apply least privilege at the correct hierarchy level, verify no alternate grant still supplies the permission, update the versioned configuration, and record teardown of both synthetic resources.
