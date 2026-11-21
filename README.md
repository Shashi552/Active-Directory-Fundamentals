# 🛡️ Active Directory Security & Exploitation: Zero-to-Hero Curriculum

> A comprehensive, structured, module-by-module courseware and reference manual on Active Directory architecture, identity protocols, attack graph mechanics, and enterprise defense tiering.

---

## 📌 Course Philosophy: The "Why Before How" Approach

Active Directory (AD) powers identity and access management for over 90% of Fortune 1000 enterprises. Attempting to learn Active Directory security by memorizing tool commands leads to fragile knowledge. This curriculum is engineered around **first-principles understanding**:

1. **Architecture First**: You cannot break or defend what you do not understand. Learn how Domain Controllers, LDAP, DNS, and Kerberos interact.
2. **Protocol Mechanics**: Understand what happens on the wire during authentication (tickets, PAC, SPNs, session keys).
3. **Graph Theory & Trust Relationships**: Understand that modern AD security is not about vulnerabilities—it is about relationships and unintended permissions (ACLs).
4. **Defense in Parallel**: Every single exposure vector is accompanied by its corresponding detection signature and hardening configuration.

---

## 🗺️ Progressive Learning Roadmap

```mermaid
flowchart TD
    M0["Module 0: Windows Admin & AD Core Concepts<br/>(SAM vs NTDS, SIDs, Local vs Domain Admins)"]
    M1["Module 1: AD Architecture & Foundations<br/>(Forests, Domains, FSMO, GPOs, LDAP)"]
    M2["Module 2: Authentication Protocols<br/>(NTLM, Kerberos 3-Way Handshake, PAC)"]
    M3["Module 3: Enumeration & Attack Graphs<br/>(RPC, LDAP, BloodHound Graph Theory)"]
    M4["Module 4: Credential & Delegation Vectors<br/>(AS-REP Roasting, Kerberoasting, Delegation)"]
    M5["Module 5: PrivEsc & Domain Dominance<br/>(ACL Abuse, DCSync, Golden/Silver Tickets)"]
    M6["Module 6: Enterprise Defense & Hardening<br/>(Tiering Models, Protected Users, Event IDs)"]

    M0 --> M1 --> M2 --> M3 --> M4 --> M5 --> M6
```

---

## 📚 Curriculum Breakdown

| Module | Core Topic | What You Learn | Why You Must Learn It |
| :--- | :--- | :--- | :--- |
| [**Module 0**](docs/Module-00-Windows-Administration-and-AD-Basics.md) | **Windows Admin & AD Basics** | Workgroup vs. Domain, SAM file vs. `ntds.dit`, SIDs, RIDs, and Admin Scopes | Establishes ground-level understanding of Windows identity before attacking it. |
| [**Module 1**](docs/Module-01-Architecture-and-Foundations.md) | **Architecture & Foundations** | Forests, Trees, Domains, FSMO Roles, Global Catalog, LDAP & DNS | Forms the structural skeleton of enterprise Windows networks. |
| [**Module 2**](docs/Module-02-Authentication-and-Kerberos.md) | **Authentication Protocols** | NTLMv2, Kerberos 3-way exchange, TGT, TGS, PAC validation | Essential for understanding how identity is verified and ticket-based attacks operate. |
| [**Module 3**](docs/Module-03-Enumeration-and-Attack-Graphs.md) | **Enumeration & Graph Theory** | Native queries, PowerView, SharpHound, BloodHound path analysis | Modern assessments rely on finding derivative relationships rather than single exploits. |
| [**Module 4**](docs/Module-04-Credential-Attacks-and-Delegation.md) | **Credentials & Delegation** | AS-REP Roasting, Kerberoasting, Unconstrained & Constrained Delegation | Exploits architectural protocol features rather than software bugs. |
| [**Module 5**](docs/Module-05-Privilege-Escalation-and-Domain-Dominance.md) | **PrivEsc & Dominance** | ACL Abuse (GenericAll/WriteDacl), LAPS, DCSync, Ticket Forgery | Teaches how attackers turn a single domain user into a Domain Administrator. |
| [**Module 6**](docs/Module-06-Defensive-Hardening-and-Detection.md) | **Defense & Enterprise Tiering** | Microsoft Enterprise Access Model, Tier 0 Isolation, Windows Event IDs | Prepares you to architect resilient identity environments and audit security posture. |

---

## 🧪 Recommended Practice Labs

Before practicing, set up an isolated homelab or use pre-configured open-source Active Directory environments:
1. **Game of Active Directory (GOAD)**: Multi-domain, multi-forest lab with automated Vagrant/Terraform deployment.
2. **DetectionLab**: Pre-configured with Windows Domain Controller, WEF/WEC, and Splunk for threat hunting.
3. **ADFS / Azure AD Connect Lab**: For hybrid identity exploration.

---

## 📖 PDF Guide Export
The companion publication-ready PDF manual is compiled in this repository:
- 📄 **[Active_Directory_Security_Course.pdf](Active_Directory_Security_Course.pdf)**
