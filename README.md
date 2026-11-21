# 🛡️ Active Directory Security & Exploitation: Zero-to-Hero Master Curriculum

> An exhaustive, university-grade courseware, practical operator playbook, and reference textbook covering Windows operating system internals, Kerberos protocol mechanics, BloodHound graph theory, AD CS exploitation, DCSync replication, and zero-trust defensive tiering.

---

## 🗺️ The Step-by-Step Practical Learning Pathway

Follow this sequential 8-phase pathway to progress from zero Windows knowledge to enterprise-grade penetration testing and defensive engineering proficiency.

```mermaid
flowchart TD
    P1["🟢 Phase 1: OS & Identity Foundations<br/>(Windows Internals, SAM vs NTDS, SIDs, FSMO)"]
    P2["🟡 Phase 2: Unauthenticated Footholds<br/>(LLMNR/NBT-NS Poisoning, SMB Relay, mitm6)"]
    P3["🟠 Phase 3: Protocol Internals & Graphs<br/>(Kerberos 3-Way Exchange, BloodHound Cypher)"]
    P4["🔴 Phase 4: Credential & Delegation Attacks<br/>(AS-REP Roasting, Kerberoasting, RBCD)"]
    P5["🟣 Phase 5: AD CS PKI Exploitation<br/>(Certificate Templates, ESC1 - ESC8)"]
    P6["🟤 Phase 6: Domain Dominance & Persistence<br/>(ACL Abuse, DCSync, Golden/Silver Tickets)"]
    P7["🔵 Phase 7: Real-World Tradecraft & Playbook<br/>(War Stories, Operator Flag Dissection)"]
    P8["🛡️ Phase 8: Enterprise Defense & Tiering<br/>(Enterprise Access Model, Tier 0, Event IDs)"]

    P1 --> P2 --> P3 --> P4 --> P5 --> P6 --> P7 --> P8
```

---

## 🚦 Phase-by-Phase Course Roadmap

| Phase Indicator | Stage Name | Included Modules & Labs | Difficulty | Focus & Core Milestone |
| :---: | :--- | :--- | :---: | :--- |
| **🟢 PHASE 1** | **OS & Identity Foundations** | [**Module 0**](docs/Module-00-Windows-Administration-and-AD-Basics.md)<br/>[**Module 1**](docs/Module-01-Architecture-and-Foundations.md)<br/>[**Module 9**](docs/Module-09-Windows-Internals-File-and-Memory-Architecture.md) | **Beginner** | Understand the Workgroup vs Domain model, the SAM database vs `ntds.dit`, SIDs, RIDs, User vs Kernel Mode (Ring 3 vs Ring 0), and LSASS memory architecture. |
| **🟡 PHASE 2** | **Initial Footholds & Poisoning** | [**Module 7**](docs/Module-07-TCM-Security-Practical-Methodology.md)<br/>[**Lab 1**](labs/Lab-01-LLMNR-Poisoning-and-Hash-Cracking.md) | **Beginner-Int** | Obtain an initial foothold from zero credentials. Master LLMNR/NBT-NS poisoning with Responder, SMB relaying with `ntlmrelayx`, and Hashcat mode 5600. |
| **🟠 PHASE 3** | **Kerberos Internals & Attack Graphs** | [**Module 2**](docs/Module-02-Authentication-and-Kerberos.md)<br/>[**Module 3**](docs/Module-03-Enumeration-and-Attack-Graphs.md) | **Intermediate** | Dissect the Kerberos 3-way handshake (AS, TGS, AP exchanges), PAC structure, and map shortest paths to Domain Admin using BloodHound & SharpHound. |
| **🔴 PHASE 4** | **Credential & Delegation Attacks** | [**Module 4**](docs/Module-04-Credential-Attacks-and-Delegation.md)<br/>[**Lab 2**](labs/Lab-02-Kerberoasting-and-TGS-Extraction.md) | **Intermediate** | Request and crack service tickets (Kerberoasting), exploit pre-authentication (AS-REP Roasting), and abuse Unconstrained, Constrained, and RBCD delegation. |
| **🟣 PHASE 5** | **AD Certificate Services (AD CS)** | [**Module 5**](docs/Module-05-Privilege-Escalation-and-Domain-Dominance.md)<br/>[**Attack Matrix**](docs/Active-Directory-Attack-Matrix-and-References.md) | **Advanced** | Audit Active Directory PKI using Certipy. Weaponize misconfigured certificate templates (ESC1 SAN abuse, ESC4 ACL abuse, ESC8 Web Enrollment NTLM relay). |
| **🟤 PHASE 6** | **PrivEsc, DCSync & Forest Dominance** | [**Module 5**](docs/Module-05-Privilege-Escalation-and-Domain-Dominance.md)<br/>[**Lab 3**](labs/Lab-03-DCSync-and-Domain-Dominance.md) | **Advanced** | Exploit directory ACLs (`GenericAll`, `WriteDacl`), simulate DC replication via DCSync (`secretsdump.py`), and forge Golden Tickets using the `krbtgt` key. |
| **🔵 PHASE 7** | **Operator Tradecraft & War Stories** | [**Module 8**](docs/Module-08-Real-World-Case-Studies-and-War-Stories.md)<br/>[**Operator Playbook**](docs/Active-Directory-Field-Operator-Playbook.md) | **Expert** | Study real-world enterprise breaches (zero-click SCF share traps, hospital ransomware simulations). Master exact tool flags for Impacket, Rubeus, and Mimikatz. |
| **🛡️ PHASE 8** | **Enterprise Defense & Zero Trust** | [**Module 6**](docs/Module-06-Defensive-Hardening-and-Detection.md)<br/>[**Attack Matrix**](docs/Active-Directory-Attack-Matrix-and-References.md) | **Architect** | Implement Microsoft's Enterprise Access Model, Tier 0 isolation, Privileged Access Workstations (PAWs), Protected Users, and SIEM Event ID detection. |

---

## 🔬 Hands-On Practice Labs & Field Artifacts

| Lab Guide | Target Technology | Real-World Console Artifacts Included |
| :--- | :--- | :--- |
| [**Lab 1: LLMNR Poisoning & Cracking**](labs/Lab-01-LLMNR-Poisoning-and-Hash-Cracking.md) | Network Broadcast Abuse | Responder console session, NetNTLMv2 capture, Hashcat benchmark |
| [**Lab 2: Kerberoasting & Service Tickets**](labs/Lab-02-Kerberoasting-and-TGS-Extraction.md) | Kerberos TGS Exploitation | Impacket GetUserSPNs output, ticket structure analysis, Hashcat mode 13100 |
| [**Lab 3: DCSync & Domain Dominance**](labs/Lab-03-DCSync-and-Domain-Dominance.md) | MS-DRSR Replication Protocol | Secretsdump NTDS.dit extraction, Golden Ticket forgery with ticketer |
| [**Homelab Setup: Game of Active Directory**](labs/Lab-Setup-Guide-GOAD.md) | Multi-Domain Forest Lab | Step-by-step Vagrant & VirtualBox deployment of the 5-VM GOAD environment |

---

## 📖 Full 17-Page Master Textbook (Direct Browser View)

> **No Download Required**: View the entire publication-grade 17-page master volume directly in GitHub.

* 📚 [**Open the Complete 17-Page Master Visual Reader (MASTER_TEXTBOOK.md)**](MASTER_TEXTBOOK.md)
* 📥 [**Download the Raw Master PDF (Active_Directory_Master_Textbook.pdf)**](Active_Directory_Master_Textbook.pdf)

### 📑 Individual Page Quick Links
| Page | Chapter / Topic | Direct Image Link |
| :---: | :--- | :---: |
| **01** | Cover Page & Architecture Overview | [View Page 1](assets/textbook_pages/page_01.png) |
| **02** | Preface & Course Philosophy | [View Page 2](assets/textbook_pages/page_02.png) |
| **03** | Part I Divider: Foundations & Identity | [View Page 3](assets/textbook_pages/page_03.png) |
| **04** | Chapter 1: Ground-Level Windows Systems Administration | [View Page 4](assets/textbook_pages/page_04.png) |
| **05** | Chapter 2: Forest, Domain & Trust Architecture | [View Page 5](assets/textbook_pages/page_05.png) |
| **06** | Part II Divider: Authentication Internals | [View Page 6](assets/textbook_pages/page_06.png) |
| **07** | Chapter 3: NTLM Authentication & Relaying | [View Page 7](assets/textbook_pages/page_07.png) |
| **08** | Chapter 4: Kerberos Protocol & PAC Verification | [View Page 8](assets/textbook_pages/page_08.png) |
| **09** | Part III Divider: Attack Graphs & Enumeration | [View Page 9](assets/textbook_pages/page_09.png) |
| **10** | Chapter 5: Active Directory Enumeration & BloodHound | [View Page 10](assets/textbook_pages/page_10.png) |
| **11** | Part IV Divider: Credential Attacks & Delegation | [View Page 11](assets/textbook_pages/page_11.png) |
| **12** | Chapter 6: AS-REP Roasting & Kerberoasting | [View Page 12](assets/textbook_pages/page_12.png) |
| **13** | Chapter 7: Active Directory Certificate Services (AD CS) | [View Page 13](assets/textbook_pages/page_13.png) |
| **14** | Part V Divider: PrivEsc & Dominance | [View Page 14](assets/textbook_pages/page_14.png) |
| **15** | Chapter 8: Privilege Escalation, DCSync & Golden Tickets | [View Page 15](assets/textbook_pages/page_15.png) |
| **16** | Chapters 9 & 10: TCM Security PNPT Flow & Defense | [View Page 16](assets/textbook_pages/page_16.png) |
| **17** | Chapter 11: Real-World Penetration Testing War Stories | [View Page 17](assets/textbook_pages/page_17.png) |

---

## 📖 Complete Master Textbooks (Direct Browser View & Download)

> **Zero Download Required**: Anyone can read the entire 17-page publication manual directly in their web browser with full zoom and page thumbnails.

* 🌐 [**👉 Read Full 17-Page Master Textbook Online in Browser (Instant Web Viewer - No Download)**](https://docs.google.com/viewer?url=https://raw.githubusercontent.com/Shashi552/Active-Directory-Fundamentals/main/Active_Directory_Master_Textbook.pdf)
* 📄 [**View Raw PDF File in Repository (Active_Directory_Master_Textbook.pdf)**](Active_Directory_Master_Textbook.pdf)
* 📘 [**Companion Study Manual (Active_Directory_Security_Course.pdf)**](Active_Directory_Security_Course.pdf)
