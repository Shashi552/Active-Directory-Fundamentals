# Module 5: Privilege Escalation & Domain Dominance

## 1. What to Learn
* **Active Directory ACL Abuse**:
  * **GenericAll**: Full rights over a target object (can reset passwords, modify group membership, or edit service paths).
  * **GenericWrite / WriteProperty**: Ability to overwrite object attributes (e.g., adding an SPN or altering scriptPath).
  * **WriteDacl**: Ability to modify the Discretionary Access Control List of an object to grant oneself `GenericAll`.
  * **AllExtendedRights / ForceChangePassword**: Ability to reset passwords of users without knowing their current password.
* **LAPS (Local Administrator Password Solution)**:
  * How LAPS randomizes local administrator passwords on each workstation.
  * Exploiting misconfigured read permissions over `ms-Mcs-AdmPwd` or `msLAPS-Password`.
* **DCSync Attack (MS-DRSR Protocol)**:
  * Emulates a Domain Controller using the Directory Replication Service Remote Protocol (MS-DRSR).
  * Requires `DS-Replication-Get-Changes` and `DS-Replication-Get-Changes-All` extended rights.
  * Allows dumping the NTLM hash of **any** account, including `krbtgt` and `Administrator`, without running code on the DC.
* **Ticket Forgery (Golden & Silver Tickets)**:
  * **Golden Ticket**: Forged Ticket Granting Ticket (TGT) using the `krbtgt` NTLM hash or AES key; gives persistent, untraceable Domain Admin access for up to 10 years.
  * **Silver Ticket**: Forged Service Ticket (TGS) using a target machine/service account hash; communicates directly with the target service without touching the DC.

## 2. Why You Must Learn It
Achieving Domain Admin is rarely the end goal; understanding persistent dominance vectors and replication protocols is what separates amateur script users from professional security engineers:
- DCSync is the ultimate privilege escalation check in an AD penetration test or red team engagement.
- Recovering from a compromised domain requires rotating the `krbtgt` password twice (with a waiting interval for active tickets to expire).

## 3. Dominance Flowchart

```mermaid
graph TD
    subgraph Initial Foothold
        U1["Standard User: jsmith"]
    end

    subgraph ACL Exploitation Path
        U1 -->|GenericWrite| G1["Group: Helpdesk Operators"]
        G1 -->|WriteDacl| G2["Group: Tier 1 Admins"]
        G2 -->|MemberOf| S1["Server: HYPERV-01"]
        S1 -.->|LSASS Dump| DA_HASH["DA Hash: Administrator"]
    end

    subgraph Domain Dominance
        DA_HASH -->|Execute DCSync (MS-DRSR)| DC["Domain Controller (ntds.dit)"]
        DC -->|Replicate Secret| KRB["KRBTGT NTLM Hash"]
        KRB -->|Forge Ticket| GT["Golden Ticket (TGT)"]
        GT -->|Full Forest Control| FOREST["Enterprise Persistence"]
    end

    style U1 fill:#f96,stroke:#333,stroke-width:2px
    style DA_HASH fill:#f66,stroke:#333,stroke-width:2px
    style KRB fill:#f00,stroke:#333,stroke-width:3px
    style GT fill:#900,stroke:#333,stroke-width:3px
```

## 4. Key Defensive Mitigations
* **Restrict Replication Rights**: Audit `DS-Replication-Get-Changes` across the domain root; only Domain Controllers and Azure AD Connect service accounts should possess these rights.
* **Monitor Event ID 4662**: Track operation `1131f6aa-9c07-11d1-f79f-00c04fc2dcd2` (Replication Get Changes All) initiated from non-DC IP addresses.
* **KRBTGT Password Rotation Procedure**: Maintain a strict schedule or post-incident response playbook to rotate the `krbtgt` password twice (24 hours apart) using Microsoft's `New-KrbtgtKeys.ps1` script.
