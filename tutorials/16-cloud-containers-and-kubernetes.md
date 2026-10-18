# 16. Tutorial: cloud, containers, and Kubernetes

[Index](README.md) · [Complete source curriculum](curriculum/16-cloud-containers-and-kubernetes.md) · [Original roadmap](../roadmaps/16-cloud-containers-and-kubernetes.md)

## Learn shared boundaries, then one provider deeply

Cloud assessment asks which identity can operate on which resource, from which path, under which effective policy. A private address does not prove correct authorization, and a public endpoint does not automatically mean public data. Prerequisites are networking, Linux, APIs, IAM, and basic deployment. Complete the common lessons, one provider capstone, and the container lab before adding Kubernetes. All three provider tracks are included for translation and later depth.

Use a dedicated disposable account/subscription/project with synthetic data and separate human administrator, read-only reviewer, deployment identity, and runtime identity. Define service/region/resource-count/spending constraints and read the chosen provider's current testing policy before deploying a lab. Budget notifications, quotas, and hard spending enforcement are different mechanisms; verify what your selected controls actually enforce. No paid deployment is required for the local exercises in this chapter.

## Lesson 1: map responsibility and resources

In IaaS, you normally manage more guest operating-system and workload configuration; PaaS and serverless shift more platform operation to the provider; SaaS adds application administration and sharing policy. Exact responsibility depends on the service. Separate control plane (create/configure resources) from data/workload plane (use the resource's service). Managing a database resource and reading its records can require different authority.

Draw organization/hierarchy, billing owner, environment separation, regions, networks, DNS, identities, workload credential delivery, storage, keys, secrets, backups, and logging destinations. Include metadata services conceptually: a workload can obtain credentials through platform mechanisms, so an application flaw can expose the permissions of its attached identity. Do not query real metadata credentials for a lab proof; review identity attachment and use a harmless local mock where needed.

Create an identity/action/resource/context/decision table with a permitted and denied control. Inventory resources using a read-only reviewer where possible. Review long-lived keys, unowned identities, excessive roles, unsafe trust, public data, cross-account/tenant relationships, and who can change code executing under a powerful identity.

Version infrastructure and preserve intended configuration. State files, plan outputs, exported configuration, and deployment credentials can be sensitive. Compare desired and applied state for drift. Plan teardown before deployment: compute, disks, addresses, load balancers, gateways, snapshots, logs, registries, functions, queues, secrets, and retained backups can outlive an application. Maintain an explicit ledger with identifiers, owner, region, dependency, retention, and verified disposition.

## Lesson 2: translate concepts without assuming identical semantics

| Area | AWS | Azure | Google Cloud |
| --- | --- | --- | --- |
| Hierarchy | Organizations, accounts, organization controls | Entra tenant, management groups, subscriptions, resource groups | Organization, folders, projects, organization policy |
| Identity | IAM principals/roles, sessions, STS | Users/groups, service principals, managed identities, Azure RBAC | Principals, service accounts, roles/policies, workload federation |
| Network | VPC, subnets, routes, security groups, ACLs, endpoints | VNet, subnets, routes, NSGs, Private Link | VPC, subnets, firewall policies, routes, private access |
| Execution | EC2, Lambda, ECS/EKS | VMs, App Service, Functions, AKS | Compute Engine, Cloud Run, GKE |
| Data and secrets | S3, managed databases, KMS, Secrets Manager | Storage, managed databases, Key Vault | Cloud Storage, managed databases, Cloud KMS, Secret Manager |
| Events/visibility | Queues/triggers, CloudTrail and service logs | Event sources, Activity/Entra/resource logs | Pub/Sub/events, Cloud Audit Logs and service logs |

Identity trust permits an identity transition; the resulting role's permissions govern later actions. Resource policies, hierarchy controls, explicit denies, conditions, session restrictions, and key permissions can change the decision. Use the provider's exact policy evaluation, not a universal “allow minus deny” formula. Review CI/CD federation issuer, subject, audience, and claim restrictions independently from the runtime identity.

## Lesson 3: AWS study sequence

**Hierarchy and effective access.** Map organization/account boundaries, principals, role trust, role sessions, temporary credentials, and resource identifiers. Evaluate the request using identity policies, resource policies, boundaries, session policies, and organization controls. A boundary or organization restriction limits authority; it does not itself grant an operation. Explicit deny and principal/session distinctions require the documented rules. [AWS policy evaluation](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html).

**Network, execution, and data.** Trace subnets, route tables, gateways, security groups, network ACLs, endpoints, DNS, load balancers, and administrative access. Compare EC2 instance, Lambda execution, and container task/workload roles. Identify who may attach a role or change the code using it. Review S3 policies/public-access controls, object rights, signed access, encryption, versioning, lifecycle, snapshots/backups/images, and sharing. Check KMS key use and Secrets Manager retrieval separately. Inspect queues/triggers and producer/consumer resource policies.

**Visibility.** CloudTrail management evidence concerns resource administration; data operations require the relevant event configuration/service coverage. A management event does not establish that object reads are recorded. Prove the selected logging path with a known synthetic request and preserve account, region, identity/session, resource, operation, and time. [CloudTrail management events](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/logging-management-events-with-cloudtrail.html).

**Capstone.** In the disposable account, create two private synthetic objects and a workload requiring one narrow read. Establish intended read success and unrelated read denial. Introduce an overbroad **lab-only** role relationship, inspect its effective policy, then remove it at the source. Verify the application still reads the intended object and cannot read the other; retain relevant data-access evidence. Review key and network decisions if the expected read fails. Restore versioned configuration and complete the ledger-based teardown.

## Lesson 4: Azure study sequence

**Identity and hierarchy.** Separate Entra directory roles from Azure resource roles. A role assignment combines principal, role definition, and scope; inherited assignments and service data-plane permissions matter. Review users, groups, service principals, managed identities, federated workloads, credential modification, identity attachment, and authority to assign roles. Azure Policy governance is a separate control from RBAC authorization. [Azure RBAC overview](https://learn.microsoft.com/en-us/azure/role-based-access-control/overview).

**Workloads and data.** Map VNet routes, NSGs, DNS, gateways, ingress, public endpoints, and Private Link. Private endpoint deployment needs correct routing and name resolution, and may coexist with other access paths. Compare VM, App Service, Functions, and AKS deployment/runtime identities. Inspect Storage account/container sharing, delegated access, keys, data permissions, and lifecycle. For Key Vault, inspect retrieval permission, network restrictions, secret/certificate lifecycle, recovery settings, and the application's actual access path. Check what each Azure Policy definition audits/enforces and what remediation needs.

**Visibility.** Use Activity Log for control-plane evidence, appropriate Entra logs for authentication, and service/resource logs for workload/data actions. Configure needed categories, retention, export, and evidence-reader permissions; prove collection with a synthetic action. [Azure Activity Log](https://learn.microsoft.com/en-us/azure/azure-monitor/fundamentals/activity-log).

**Capstone.** Give a managed identity only the synthetic storage/secret operation its application needs. Record an unnecessary inherited grant, remove the local grant first to observe why inherited authority remains, then narrow the responsible assignment at its actual scope. Repeat both intended and unrelated reads, accounting for documented propagation and session behavior. Capture assignment, identity, network/DNS, data result, and logs, then check teardown including retained recovery/backup resources.

## Lesson 5: Google Cloud study sequence

**Hierarchy and IAM.** Map organizations, folders, projects, and resources. Compare basic, predefined, and custom roles by their actual permissions. Review inherited allow policies, conditions, applicable deny policies and access boundaries. Workload use of a service account differs from impersonating, administering, or changing its attached workload. Prefer supported short-lived/federated access designs over unnecessary long-lived keys, with explicit issuer/subject/audience/attribute restrictions. [Google Cloud IAM overview](https://docs.cloud.google.com/iam/docs/overview).

**Network, data, and execution.** Trace VPC, subnets, firewall policies, routes, DNS, private access, load balancing, and administration. Compare Compute Engine, Cloud Run, and GKE identity attachment and deployment authority. Review Cloud Storage sharing/signed access/lifecycle/encryption and inherited project grants. Check Secret Manager and Cloud KMS permissions independently of deployment rights. Include Pub/Sub producer/consumer permission, event routing, managed database connectivity, backup ownership, and sharing.

**Visibility.** Study Admin Activity, Data Access, System Event, and Policy Denied categories, then verify service-specific coverage and configuration. A missing event can reflect disabled collection, delay, wrong project/region, or an incorrect query. [Cloud Audit Logs overview](https://docs.cloud.google.com/logging/docs/audit).

**Capstone.** Run a synthetic application under a dedicated service account. Remove a broad inherited/project grant while preserving one required data operation. Record the hierarchy, policy versions, exact permissions, session identity, request outcomes, and audit evidence. Account for documented propagation during retest. Retire unused keys, artifacts, and retained billable resources through the ledger.

## Lesson 6: inherited-access reasoning without a cloud account

Run this Python 3 model locally. It illustrates only additive inherited grants; it is not an AWS/Azure/Google policy simulator and deliberately omits their deny/condition semantics.

```python
local_grants = {"object-a"}
inherited_grants = {"object-a", "object-b"}
def can_read(resource):
    return resource in local_grants | inherited_grants

assert can_read("object-b")
local_grants.discard("object-b")
assert can_read("object-b")  # The effective source was not changed.
inherited_grants.remove("object-b")
assert not can_read("object-b")
assert can_read("object-a")
print("unrelated read denied; intended read preserved")
```

Translate the model into your chosen provider by identifying the actual grant source and evaluator. Record policy version, change time, request identity, resource identifiers, and session/propagation considerations. Cross-account/tenant tests require two owned or explicitly permitted environments and synthetic objects. A failed read can also result from network policy, DNS, key-use permission, or an expired credential; identify the enforcing layer before adding rights.

## Lesson 7: container image and runtime boundaries

An image is packaged filesystem/configuration; a container is a runtime instance. Layers preserve build history, tags can change, and digests identify content. Inspect base images, context, build stages, lockfiles, package inventory, lifecycle scripts, registries, signing/verification, provenance, and promotion. Deleting a secret in a later layer may leave it in earlier content; use supported build-secret mechanisms and inspect artifacts rather than copying credentials into the build context.

Namespaces separate views of resources; cgroups control resources; capabilities divide some Linux privileges. Root inside a container is not automatically identical to unrestricted host root, but privileged mode, host networking/PID namespaces, host mounts, devices, runtime sockets, or weak isolation can expose host authority. User namespaces/rootless operation and security profiles change the model. Review effective configuration and avoid testing escapes. [Docker Engine security](https://docs.docker.com/engine/security/).

Use non-root workload identities, minimal runtime images, only necessary writable paths/capabilities, secret injection, read-only filesystems where practical, and resource limits. Image scanning and runtime review answer different questions: a clean package scan says nothing about an exposed runtime socket. Also review published ports, internal networks, egress, registry credentials, logs, readiness, graceful shutdown, patch/rebuild, promotion, and rollback.

## Lesson 8: a local container write-boundary lab

Prerequisite: Docker running Linux containers on a disposable Linux host or Docker Desktop VM, with an approved local Python image. On Windows PowerShell, replace the example image reference with the approved image you actually have; record its digest and provenance before use. The `python:3-slim` tag below is a selectable training input, not a claim of a fixed/reproducible release. Pulling it requires network access; the running fixture does not.

```powershell
docker pull python:3-slim
$TrainingImage = docker image inspect python:3-slim --format '{{index .RepoDigests 0}}'
if (-not $TrainingImage) { throw 'No image digest recorded' }
$TrainingCode = @'
from pathlib import Path
Path('/reports/report.txt').write_text('TRAINING_REPORT')
print(Path('/reports/report.txt').read_text())
try:
    Path('/tmp/unrelated.txt').write_text('TRAINING_MARKER')
except OSError:
    print('unrelated write denied')
else:
    raise AssertionError('unexpected writable path')
'@
docker run --rm --network none --read-only --user 10001:10001 --cap-drop ALL --security-opt no-new-privileges --memory 128m --cpus 0.5 --pids-limit 64 --tmpfs /reports:rw,noexec,nosuid,size=1m,uid=10001,gid=10001 $TrainingImage python -c $TrainingCode
```

Expect `TRAINING_REPORT` followed by `unrelated write denied`. The permitted tmpfs is writable by the runtime user while the rest of the root filesystem is read-only. There are no host bind mounts, published ports, or runtime socket. The report disappears when the container exits. If the tmpfs options are unsupported by your runtime configuration, document the limitation and consult its documentation instead of granting broad host access.

For comparison, remove only `--read-only` in a separate disposable run and predict `/tmp` behavior; adjust the assertion to report the result rather than treating the deliberately writable state as the fixed state. Reapply restriction and verify the positive report control. Record digest, user, capabilities, mounts, limits, output, and cleanup. This demonstrates a filesystem boundary, not complete container security.

## Lesson 9: Kubernetes architecture and independent controls

Map API server, etcd/datastore, scheduler, controllers, kubelets, nodes, namespaces, pods, deployments, services, ingress, and the installed network plugin. Managed providers own selected layers; document actual responsibility. Controllers reconcile desired state, so manual pod edits may disappear. Repair versioned deployment/Helm/operator configuration rather than only a running object.

| Control family | What to assess | Required independent evidence |
| --- | --- | --- |
| Authentication and RBAC | Kubeconfig, users, service accounts, tokens, federation, roles/bindings, namespace/cluster scope | Effective verb/resource decision with intended and denied identities |
| Indirect privilege | Creating workloads, changing controllers, binding roles, reading secrets, interactive operations | Explain actual downstream authority and prerequisites, without assuming equal impact |
| Workload admission | Pod Security admission, security context, capabilities, host access, volumes, profiles, image trust | Benign compliant manifest accepted and prohibited configuration rejected |
| Network policy | Plugin enforcement, ingress/egress, selectors, DNS and required platform traffic | Actual harmless connections between synthetic workloads, not just accepted YAML |
| Secrets and control plane | Storage/encryption, API access, audit policy, backup protection, control-plane exposure | Configuration plus authorized action and relevant logs |
| Operations/extensions | Node lifecycle, patching, registries, Helm charts, operators, CRDs, controllers, webhooks | Extension permissions, source trust, reconciliation/drift behavior |

Namespaces organize resources but do not create complete tenant isolation. NetworkPolicy requires a supporting network implementation; policy objects alone do not prove filtering. [Kubernetes NetworkPolicy documentation](https://kubernetes.io/docs/concepts/services-networking/network-policies/). Cluster-admin paths and container/host isolation limits remain important even when namespaced RBAC looks narrow. Use the [Kubernetes security checklist](https://kubernetes.io/docs/concepts/security/security-checklist/) to map applicable controls, then test actual enforcement.

## Lesson 10: local-cluster lab and final evidence

In a disposable local cluster with a known enforcing network plugin, create namespaces `training-a` and `training-b`, separate service accounts, and two benign HTTP workloads serving distinct markers. Confirm your current kubeconfig context before any mutation. Keep all manifests in the lab repository and inventory objects for teardown.

First give each workload only its required API permissions and check an intended read versus a prohibited resource/namespace action using the actual test identities. Record roles, bindings, effective decisions, and tokens' intended scope without logging credentials. Repair one excessive binding at the true source, accounting for any cluster-level grants.

Next test baseline cross-namespace reachability with harmless requests, then apply the intended ingress/egress policy through versioned manifests. Verify denied cross-boundary traffic, permitted application traffic, and DNS separately. A policy that breaks all traffic is not a successful application repair. Independently submit a benign compliant security-context manifest and one intentionally disallowed host-access configuration to observe admission decisions; no container escape attempt is needed.

If network behavior does not change, verify plugin support, selectors, direction, addresses, and existing policy interactions. If RBAC denial seems inconsistent, confirm identity, verb, subresource, binding scope, and inherited cluster grants. If a manual fix disappears, inspect the owning controller. If an image scan passes, continue runtime/admission review.

Complete one provider capstone plus the container lab with architecture, identity matrix, before/after policy evidence, legitimate controls, logs, and verified teardown. Complete Kubernetes separately when API authorization, workload admission, and network isolation are each demonstrated. For a second provider, write a translation table explaining semantic differences rather than merely swapping product names. Preserve all untested modules as explicit remaining practice, alongside their explanations here.

**Answer-guided checks:** Why can access survive deleting a local grant? Another inherited/resource/session relationship may still allow it. Why is a private endpoint insufficient evidence? Other public paths or permissive identities may remain. Why is an SBOM/scan insufficient for runtime security? It does not describe effective mounts, namespaces, capabilities, or identity. Why test DNS after isolation? Necessary platform traffic can be accidentally blocked. Why check the resource ledger after application removal? Retained disks, snapshots, logs, addresses, and backups may remain active or billable.
