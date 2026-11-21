# Module 11: Enterprise Zero-Trust Defense, Hardening & Detection Engineering

> **Navigation**: [⬅️ Module 10: Operator Playbook & Troubleshooting](Module-10-Field-Operator-Playbook-and-Troubleshooting.md) | [🏠 Master Index](../README.md) | [Module 12: Real-World Case Studies ➡️](Module-12-Real-World-Case-Studies-and-War-Stories.md)

---


## 1. Microsoft Enterprise Access Model (EAM) & Tiering Architecture

The traditional Active Directory Administrative Tier Model (Tier 0, Tier 1, Tier 2) has evolved into Microsoft’s modern **Enterprise Access Model (EAM)**. The model is built on one foundational axiom: **The Clean Source Principle**.

```
+-----------------------------------------------------------------------------------------+
| MICROSOFT ENTERPRISE ACCESS MODEL (EAM) ARCHITECTURE                                    |
|                                                                                         |
|  PRIVILEGED ACCESS WORKSTATIONS (PAWs)                                                  |
|  * Dedicated hardware, zero internet browsing, zero email access                        |
|  * Hardware-bound FIDO2 MFA tokens                                                      |
|                                                                                         |
|  ===================================[ CONTROL PLANE ]=================================  |
|  * Domain Controllers & Active Directory Domain Services (AD DS)                        |
|  * Active Directory Certificate Services (AD CS Root & Sub CAs)                         |
|  * Azure AD Connect / Entra ID Connect Sync Servers                                     |
|  * Identity & Access Management Systems (Okta, Ping, ADFS)                              |
|  * Tier 0 Administrators (Domain Admins, Enterprise Admins)                             |
|                                                                                         |
|  ==================================[ MANAGEMENT PLANE ]================================  |
|  * Enterprise Member Servers (File Servers, MSSQL Databases, Web Applications)          |
|  * Hypervisors (VMware ESXi, Hyper-V, Nutanix)                                          |
|  * Backup Infrastructure (Veeam, Commvault - Air-Gapped)                                |
|  * Tier 1 Server Administrators                                                         |
|                                                                                         |
|  ====================================[ USER PLANE ]===================================  |
|  * End-user Laptops, Desktops, Virtual Desktops                                         |
|  * Standard Domain Users, Contractors, Mobile Devices                                   |
|  * Tier 2 Workstation Support Staff                                                     |
+-----------------------------------------------------------------------------------------+
```

### The Clean Source Principle
> *"A security control cannot be maintained if the system used to administer it is less secure than the system being administered."*

If a Domain Administrator logs into a Tier 2 workstation (standard laptop) to troubleshoot a printer issue:
1. The Domain Admin's credentials (NTLM hash, Kerberos TGT, plaintext in LSASS) are cached in the workstation's memory.
2. Any local administrator or compromised user process on that workstation can dump LSASS and elevate directly to **Domain Admin**!
* **Golden Rule**: Credentials must **NEVER** flow down tiers. Tier 0 administrators may only log into Tier 0 assets from dedicated Privileged Access Workstations (PAWs).

---

## 2. The "Protected Users" Security Group

Introduced in Windows Server 2012 R2, the **Protected Users** security group (`CN=Protected Users,CN=Users,DC=corp,DC=local`) provides automatic, non-configurable architectural protections for high-value administrative accounts:

```
+---------------------------------------------------------------------------------------+
| PROTECTIONS ENFORCED ON MEMBERS OF THE "PROTECTED USERS" GROUP                        |
+-----------------------------------+---------------------------------------------------+
| Security Domain                   | Technical Protection Enforced                     |
+-----------------------------------+---------------------------------------------------+
| **NTLM Authentication**           | **COMPLETELY DISABLED**. Members cannot           |
|                                   | authenticate via NTLM. Prevents NTLM relay attacks|
|                                   | and NetNTLM hash capture.                         |
+-----------------------------------+---------------------------------------------------+
| **Kerberos Encryption**           | **DES and RC4 DISABLED**. Authentication fails    |
|                                   | unless AES-128 or AES-256 is used. Defeats RC4    |
|                                   | Kerberoasting downgrade attacks.                  |
+-----------------------------------+---------------------------------------------------+
| **LSASS Memory Caching**          | **CREDENTIAL CACHING DISABLED**. Plaintext        |
|                                   | passwords and NTLM hashes are NOT cached in LSASS |
|                                   | on member computers after logon. Defeats Mimikatz.|
+-----------------------------------+---------------------------------------------------+
| **Kerberos Delegation**           | **DELEGATION BLOCKED**. Accounts cannot be        |
|                                   | delegated via Unconstrained, Constrained, or RBCD.|
+-----------------------------------+---------------------------------------------------+
| **Ticket Lifetime**               | **REDUCED TGT LIFETIME**. Maximum TGT lifetime    |
|                                   | is reduced from 10 hours to 4 hours.              |
+-----------------------------------+---------------------------------------------------+
```

```powershell
# Add all Domain Admins and Enterprise Admins to Protected Users:
Add-ADGroupMember -Identity "Protected Users" -Members "Administrator", "admin_sec"
```

---

## 3. Defensive Group Policy Objects (GPO) Hardening Baseline

Enterprise defenders must enforce the following hardened GPO settings to eliminate baseline attack vectors:

### 1. Disable LLMNR and NetBIOS:
* `Computer Configuration -> Administrative Templates -> Network -> DNS Client`:
  - **Turn off multicast name resolution** = `Enabled`
* Configure DHCP Scope Option `043` with sub-option `001 = 2` (Disable NetBIOS over TCP/IP).

### 2. Enforce SMB Signing & Encryption:
* `Computer Configuration -> Windows Settings -> Security Settings -> Local Policies -> Security Options`:
  - **Microsoft network client: Digitally sign communications (always)** = `Enabled`
  - **Microsoft network server: Digitally sign communications (always)** = `Enabled`

### 3. Enforce LDAP Signing & Channel Binding:
* Configure registry on all Domain Controllers:
  ```powershell
  # Enforce LDAP Server Integrity (Signing)
  Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\NTDS\Parameters" -Name "LDAPServerIntegrity" -Value 2 -Type DWord
  
  # Enforce LDAP Channel Binding Tokens (CBT)
  Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\NTDS\Parameters" -Name "LdapEnforceChannelBinding" -Value 2 -Type DWord
  ```

### 4. Enable LSA Protection (RunAsPPL) & Credential Guard:
* Protect `lsass.exe` from memory dumping:
  ```powershell
  Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" -Name "RunAsPPL" -Value 1 -Type DWord
  ```
* Enable Virtualization-Based Security (VBS) via GPO:
  `Computer Configuration -> Administrative Templates -> System -> Device Guard -> Turn On Virtualization Based Security` = `Enabled`.

### 5. Enable Restricted Admin Mode for RDP:
Prevents credentials from leaking to the remote server's LSASS memory during RDP administration:
```powershell
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" -Name "DisableRestrictedAdmin" -Value 0 -Type DWord
```
* Administrators connect via: `mstsc.exe /restrictedadmin`.

---

## 4. Master SOC & SIEM Detection Engineering Matrix

This matrix maps every major Active Directory attack vector directly to Windows Security Event IDs, Sysmon Events, and operational detection queries:

```
+-----------------------------------------------------------------------------------------------------------------------+
| ACTIVE DIRECTORY ATTACK DETECTION MATRIX                                                                              |
+----------------------+--------------------+--------------------+------------------------------------------------------+
| Attack Vector        | Windows Event ID   | Sysmon Event ID    | Detection Logic & Splunk / Elastic Query             |
+----------------------+--------------------+--------------------+------------------------------------------------------+
| **LLMNR / NBT-NS     | Event ID 4624      | Sysmon Event 3     | index=windows EventCode=4624 Logon_Type=3            |
| Poisoning**          | (Logon Type 3)     | (Network Connect)  | Authentication_Package="NTLM" Workstation_Name!=...   |
+----------------------+--------------------+--------------------+------------------------------------------------------+
| **AS-REP Roasting**  | Event ID 4768      | None (Network / DC)| index=windows EventCode=4768 Pre_Auth_Type=0         |
|                      | (TGT Request)      |                    | Ticket_Options="0x40800010" Result_Code="0x0"        |
+----------------------+--------------------+--------------------+------------------------------------------------------+
| **Kerberoasting**    | Event ID 4769      | None (Network / DC)| index=windows EventCode=4769 Service_Name!="*$"      |
|                      | (TGS Request)      |                    | Ticket_Encryption_Type="0x17" Ticket_Options="0x4081*"|
+----------------------+--------------------+--------------------+------------------------------------------------------+
| **DCSync**           | Event ID 4662      | None (RPC Network) | index=windows EventCode=4662                         |
|                      | (Object Operation) |                    | AccessMask="0x100" AND (Properties="*1131f6aa*" OR   |
|                      |                    |                    | Properties="*1131f6ad*") SubjectUserName!="*$"       |
+----------------------+--------------------+--------------------+------------------------------------------------------+
| **Golden Ticket**    | Event ID 4624 /    | None               | index=windows EventCode=4672                         |
|                      | Event ID 4672      |                    | Logon_Type=3 SID="S-1-5-21-*-500"                    |
|                      | (Special Privs)    |                    | NOT [search EventCode=4768] (No prior TGT request!)  |
+----------------------+--------------------+--------------------+------------------------------------------------------+
| **LSASS Memory Dump**| Event ID 4656 /    | Sysmon Event 10    | index=sysmon EventCode=10 TargetImage="*lsass.exe"   |
|                      | Event ID 4663      | (Process Access)   | GrantedAccess IN ("0x1FFFFF", "0x1410", "0x1010")    |
+----------------------+--------------------+--------------------+------------------------------------------------------+
| **AD CS ESC1 / ESC8**| Event ID 4886 /    | Sysmon Event 3     | index=windows EventCode=4887                         |
|                      | Event ID 4887      | (HTTP Connection)  | Attributes="*SAN*administrator*" OR                  |
|                      | (Cert Issued)      |                    | Requester="*$" (Machine account requesting user cert)|
+----------------------+--------------------+--------------------+------------------------------------------------------+
| **AdminSDHolder      | Event ID 5136      | None (LDAP)        | index=windows EventCode=5136                         |
| Backdooring**        | (Directory Mod)    |                    | ObjectDN="*CN=AdminSDHolder*"                        |
+----------------------+--------------------+--------------------+------------------------------------------------------+
```

### Critical DCSync Detection Query (Event ID 4662):
```sql
index=windows EventCode=4662
Properties IN ("*{1131f6aa-9c07-11d1-f79f-00c04fc2dcd2}*", "*{1131f6ad-9c07-11d1-f79f-00c04fc2dcd2}*")
| eval is_machine_account=if(match(SubjectUserName, "\$$"), "YES", "NO")
| where is_machine_account="NO"
| table _time, SubjectUserName, Computer, ObjectName, Properties
```
* **Why it works**: Legitimate Domain Controllers have machine accounts ending in `$`. Any human user account (`SubjectUserName!="*$"`) requesting replication GUIDs `1131f6aa` or `1131f6ad` is **100% indicative of an ongoing DCSync attack**!


---

> **Navigation**: [⬅️ Module 10: Operator Playbook & Troubleshooting](Module-10-Field-Operator-Playbook-and-Troubleshooting.md) | [🏠 Master Index](../README.md) | [Module 12: Real-World Case Studies ➡️](Module-12-Real-World-Case-Studies-and-War-Stories.md)
