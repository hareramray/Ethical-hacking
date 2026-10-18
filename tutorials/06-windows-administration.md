# 06. Explain Windows identity, access, and service behavior

[Index](README.md) | [Complete source curriculum](curriculum/06-windows-administration.md) | [Original roadmap](../roadmaps/06-windows-administration.md)

## Prerequisites and lab boundary

Use a disposable Windows VM with a baseline checkpoint, console access, synthetic accounts, and an isolated virtual network. Complete computing and networking foundations first. Read-only inspection can run in a normal PowerShell session. Account, share, firewall, and task changes belong only in the guest and may require elevation. Feature/module availability varies by edition, build, and PowerShell version; inspect local help before applying examples.

## 1. Identify the execution environment

```powershell
$PSVersionTable
Get-ComputerInfo | Select-Object WindowsProductName,WindowsVersion,OsBuildNumber,OsArchitecture
whoami
whoami /user
whoami /groups
whoami /priv
Get-Command Get-LocalUser,Get-NetIPConfiguration -ErrorAction SilentlyContinue
```

Record edition/build, update state, architecture, guest name, local computer name, signed-in authority, and PowerShell edition. Windows PowerShell and newer PowerShell can have different modules and native-command behavior. A missing cmdlet may reflect the shell/module/platform rather than a broken OS.

Firmware starts the boot chain; the kernel manages protected execution, memory, devices, and scheduling. User-mode processes request operations through OS interfaces. Threads execute within processes, handles refer to resources, DLLs supply reusable code, services run background workloads, and drivers operate at the device/OS boundary. An installed executable is not proof a process is running.

NTFS stores objects and metadata on volumes; drive letters provide one naming view. `C:\Windows`, Program Files, ProgramData, user profiles, AppData, and temporary directories have different system/per-user roles. Use environment variables intentionally rather than copying another person's profile path. Junctions, symbolic links, and other reparse points can redirect paths; verify resolved targets before recursive operations.

Registry hives divide configuration by scope, including machine and user settings. Values have types; 32-bit and 64-bit application views can differ. Presence of a startup entry proves configuration, not successful execution. Export only the synthetic key being changed in an exercise; an arbitrary registry export is not a full backup.

## 2. Separate account, token, and permissions

A SID identifies a security principal. `MACHINE\alex` and `DOMAIN\alex` can display the same short name but represent different principals. An access token contains the process's identity, groups, privileges, and other security information. UAC can produce different effective tokens for the same administrator account. Compare ordinary and elevated terminals using the read-only identity commands above; do not infer elevation from group membership alone.

A security descriptor includes ownership, a DACL governing discretionary access, and a SACL associated with auditing. ACEs describe entries; inheritance copies relevant rules from parent containers. Access decisions consider the requested rights and actual token. “Deny always wins” is too simple because ordering and explicit/inherited entries matter. [Microsoft access-control components](https://learn.microsoft.com/en-us/windows/win32/secauthz/access-control-components)

Read permits selected viewing operations; write changes selected content; modify also permits operations such as deletion; full control adds broad management rights. Ownership and permission-changing rights are more powerful than content editing. Privileges/user rights, such as allowed logon types or backup privileges, differ from object permissions. Integrity levels and UAC are additional parts of execution context.

For an SMB file request, both share permissions and NTFS access constrain the operation. A successful local-path read does not exercise the share permission check. Existing tokens and SMB sessions may retain earlier identity state; a new group membership does not rewrite every running process instantly.

## 3. Build an access matrix in a synthetic directory

In an elevated guest session, create two ordinary users with unique lab-only passwords entered interactively. Check names are unused first:

```powershell
Get-LocalUser -Name LabReader,LabEditor -ErrorAction SilentlyContinue
New-LocalUser -Name LabReader -Password (Read-Host 'LabReader password' -AsSecureString)
New-LocalUser -Name LabEditor -Password (Read-Host 'LabEditor password' -AsSecureString)
New-LocalGroup -Name LabReaders
New-LocalGroup -Name LabEditors
Add-LocalGroupMember -Group LabReaders -Member LabReader
Add-LocalGroupMember -Group LabEditors -Member LabEditor
$labFolder = 'C:\LabAccessTutorial'
New-Item -ItemType Directory -Path $labFolder -ErrorAction Stop
Set-Content -LiteralPath "$labFolder\invoice.txt" -Value 'Synthetic invoice' -Encoding UTF8
Get-Acl -LiteralPath $labFolder | Format-List
```

Use File Explorer's advanced security dialog on this new folder to save the baseline permissions, inspect inherited entries, and configure the intended group grants. Keep necessary administrator/SYSTEM management access, grant LabReaders read/execute, and LabEditors modify. If inheritance supplies broader access, explicitly resolve that on this synthetic folder rather than assuming your added entries restrict it. Record the resulting ACL with `Get-Acl` and `icacls`. Do not modify unrelated profile or system directories.

Predict and test from fresh actual user sign-ins:

| Actor | Read invoice | Create/edit/delete content | Change permissions |
| --- | --- | --- | --- |
| LabReader | Allowed | Denied | Denied |
| LabEditor | Allowed | Allowed in assigned folder | Denied unless separately granted |
| Unrelated normal user | According to deliberately configured baseline; normally denied | Denied | Denied |

If results differ, inspect active SID/groups, every relevant ACL, inheritance, ownership, and the operation requested. A write success does not establish delete or permission-change access. Save exact paths and errors.

For the optional two-VM SMB extension, create only this named share in the isolated guest, if the SMB module is available:

```powershell
New-SmbShare -Name LabInvoices -Path $labFolder -ReadAccess "$env:COMPUTERNAME\LabReaders" -ChangeAccess "$env:COMPUTERNAME\LabEditors"
Get-SmbShareAccess -Name LabInvoices
```

Scope SMB reachability to the internal lab through the guest firewall. From the owned client, use `\\guest-name\LabInvoices` with the intended synthetic identity. Compare local and network outcomes, then temporarily restrict the editor's share access to read and repeat. Local NTFS modify can still work while SMB modification is denied. Restore the original share policy and retest. Remove the named share with `Remove-SmbShare` at cleanup; preserve evidence and files until review is finished.

## 4. Use PowerShell objects as evidence

PowerShell pipelines carry objects rather than only text. Discover commands with `Get-Command`, read `Get-Help`, and examine types/properties with `Get-Member`. Filter and select before formatting:

```powershell
Get-Service | Get-Member
Get-Service | Where-Object Status -eq Running |
    Select-Object Name,DisplayName,Status |
    Export-Csv -LiteralPath "$labFolder\running-services.csv" -NoTypeInformation -Encoding UTF8
Get-Process | Sort-Object WorkingSet64 -Descending |
    Select-Object -First 5 Id,ProcessName,WorkingSet64
```

`Format-Table` is for display; inserting it before an export loses the original useful objects. CSV handles flat rows; JSON can preserve nested structure when sufficient depth is specified. Choose fields explicitly and sanitize personal or sensitive paths before sharing.

Functions, arrays, hashtables, script blocks, modules, parameter binding, and providers support administration. Cmdlets and native programs differ: inspect `$LASTEXITCODE` for a native executable where appropriate. Some PowerShell errors are nonterminating; use `-ErrorAction Stop` on an operation that must enter `catch` rather than globally suppressing errors.

```powershell
try {
    Get-Content -LiteralPath "$labFolder\missing.txt" -ErrorAction Stop
} catch {
    [pscustomobject]@{ Operation='Read synthetic file'; Error=$_.Exception.Message }
}
```

The expected result describes the missing file; it should not claim a successful inventory. Keep errors separate from a pipeline intended to contain only inventory records.

## 5. Correlate service configuration with runtime

Inspect ordinary services without changing them:

```powershell
Get-CimInstance Win32_Service |
    Select-Object -First 10 Name,State,StartMode,StartName,ProcessId,PathName
Get-NetTCPConnection -State Listen | Select-Object LocalAddress,LocalPort,OwningProcess
```

A service's account, executable path, start mode, dependencies, recovery actions, and process ID explain its context. Interactive-user access does not equal service access to files or remote shares. Task Manager shows processes, Resource Monitor connects resource use, Services shows configuration/state, Task Scheduler shows schedules, and Event Viewer shows recorded events. Correlate IDs, timestamps, identities, and paths rather than display names alone.

For a harmless task experiment, save a script in the new synthetic tree that writes a timestamp to a fixed output file. Run it manually as the chosen ordinary account, then create a scheduled task through Task Scheduler for that same account with an explicit script path and working directory. Record the task definition and trigger one run. Observe both execution result and file output. Change only the output path to a nonexistent subfolder, run again, capture the failure, restore the original path, and rerun. This avoids changing an operating-system service to manufacture a fault.

Query a bounded event interval:

```powershell
$eventStart = (Get-Date).AddMinutes(-15)
Get-WinEvent -FilterHashtable @{LogName='System'; StartTime=$eventStart} -MaxEvents 30 |
    Select-Object TimeCreated,ProviderName,Id,LevelDisplayName,Message
```

Use the appropriate Task Scheduler, application, Security, or PowerShell channel/provider for the actual experiment. Some channels/audit settings must be enabled before events exist. Preserve timestamps and relevant XML/EVTX when necessary. An absent event may reflect the wrong channel, time filter, collection gap, or disabled policy. Local security policy, audit policy, PowerShell logging, and centralized collection serve related but different purposes.

## 6. Maintain network and recovery boundaries

Inspect `Get-NetIPConfiguration`, `Get-NetRoute`, `Get-DnsClientServerAddress`, `Get-NetConnectionProfile`, and relevant firewall rules. Network profiles influence rule applicability; a change from Private to Public can explain why a previously working connection fails. Create narrow lab rules for one program/service, protocol/port, source subnet, and intended profile. Preserve console access. Verify a permitted service and an unrelated denied port, in both IP families when enabled.

RDP and other remote administration need restricted reachability and intended account/logon permissions. SMB administrative shares deserve awareness but are not the test folder. Remoting adds authentication and authorization boundaries; start locally and use approved lab endpoints only.

Patch management maintains supported builds and dependencies. Defender provides protective functions; application allowlisting controls permitted execution; endpoint telemetry records behavior; privilege management limits authority. These are distinct controls. Inspect health and relevant evidence if a lab application is blocked, then correct the application or exact policy issue rather than disabling protections broadly.

Secure Boot concerns trusted startup, BitLocker volume encryption concerns protected storage, and recovery environments support repair. Recovery keys must remain separately accessible before altering boot/encryption settings. Credential Manager and certificate stores protect/manage credentials and trust according to their scopes; do not export unrelated secrets for this lesson. Protected OS components are not practice folders.

Restore points, VM checkpoints, file backups, and system images cover different state. Restore the synthetic application into a fresh folder or guest, recreate its groups/task/share, and test allowed and denied users. New local accounts have new SIDs even when names match, so repair stale ACL mappings explicitly. Verify bytes, identities, permissions, network profile, dependencies, and application output. WSL/containers require an inventory of host mounts, network exposure, environment, and accessible credentials; a separate shell is not complete isolation.

## 7. Prepare for enterprise identity

| Concept | Working explanation |
| --- | --- |
| Workgroup | Local account administration without an AD DS domain relationship |
| AD DS domain / domain controller | Directory and authentication domain / server providing domain services |
| Forest / trust | Directory security/administrative structure / defined inter-domain authentication relationship |
| OU / computer object | Administrative grouping/delegation scope / directory representation of a device |
| Cloud identity / registration / join | Distinct account/device relationships; not synonyms for AD domain join |
| DNS and time | Domain-controller discovery and authentication dependencies |
| Kerberos / NTLM | Authentication mechanisms with different models and policy implications |
| LDAP / SMB | Directory access / file and policy-related transport |
| Certificate services | Issuance and trust infrastructure whose templates and access need governance |
| Group Policy | Scoped policy processing with inheritance/filtering and an effective result to inspect |

An OU is not a network segment. A linked policy is not proof every device applied it; inspect resulting policy. Delegated administration, group-managed service accounts, privileged-access design, local administrator password management, and enrollment/deprovisioning solve separate identity-lifecycle problems. Use current Microsoft implementation documentation for your exact platform when configuring them.

Only after local foundations work, create a separate owned domain lab with a server, client, synthetic users, test OU, and harmless policy. Configure domain DNS first, verify ordinary join/sign-in and policy processing, then trace identity to directory, ticket, service, and logs. Keep workplace credentials and DNS outside this lab.

## Completion and repair guidance

Deliver environment inventory, SID/token explanation, local-versus-share matrix, task timeline, event queries, scoped network policy, and successful restore. If local succeeds but SMB fails, inspect both permission layers and active network identity. If a task starts but produces no file, check working directory, account rights, and errors. If a policy appears configured but behavior differs, inspect its effective result. Repeat these with a changed user/path after several days; independent diagnosis and recovery are the exit criteria.
