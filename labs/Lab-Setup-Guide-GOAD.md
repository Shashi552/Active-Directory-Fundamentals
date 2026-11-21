# Active Directory Homelab Setup Guide: Game of Active Directory (GOAD)

> **Goal**: Deploy an enterprise-grade, multi-domain Active Directory lab environment locally on your computer with automated provisioning.

---

## 🏗️ Recommended Lab Architecture: GOAD (Game of Active Directory)

Created by Orange Cyberdefense / Mayfly, **GOAD** is the gold standard vulnerable Active Directory lab. It contains:
* **2 Domains & 1 Forest** (`sevenkingdoms.local` and `north.sevenkingdoms.local`)
* **5 Virtual Machines**:
  * `DC01` (Windows Server 2019 - Domain Controller)
  * `DC02` (Windows Server 2019 - Child Domain Controller)
  * `SRV01` (Windows Server 2019 - MSSQL Server & IIS)
  * `SRV02` (Windows Server 2019 - AD CS Certificate Authority)
  * `SRV03` (Windows Server 2016 - Legacy Web Application)

---

## 🚀 Step-by-Step Installation on VirtualBox / Proxmox

### Prerequisites
* 16 GB to 32 GB RAM
* 100 GB free disk space
* VirtualBox 7.x or VMware Workstation
* Vagrant & Ansible

```bash
# 1. Clone the official GOAD repository
git clone https://github.com/Orange-Cyberdefense/GOAD.git
cd GOAD

# 2. Check prerequisites with goad.sh
./goad.sh -t check -l GOAD -p virtualbox -m local

# 3. Download Windows Server evaluation ISOs and Vagrant boxes
./goad.sh -t download -l GOAD -p virtualbox -m local

# 4. Provision the entire multi-domain forest automatically
./goad.sh -t install -l GOAD -p virtualbox -m local
```

---

## 🧪 Alternative Lightweight Lab: 2-VM Domain Setup

If your host machine has 16 GB RAM or less, deploy a lightweight 2-VM setup:
1. **VM 1: Windows Server 2022 (Domain Controller)**
   * RAM: 4 GB
   * IP: `192.168.56.10`
   * Role: AD DS, DNS, DHCP
   * Domain: `lab.local`
2. **VM 2: Windows 10/11 Enterprise (Client Workstation)**
   * RAM: 4 GB
   * IP: `192.168.56.20`
   * Joined to: `lab.local`
3. **Attacker: Kali Linux VM**
   * RAM: 4 GB
   * IP: `192.168.56.30`
   * Network: Host-Only Adapter (`vboxnet0`)

---

## 📋 Post-Deployment Health Check
Verify network and Kerberos functionality from your Kali attacker machine:
```bash
# Verify DNS resolution against the DC
nslookup dc01.lab.local 192.168.56.10

# Test Kerberos port 88 reachability
nc -zv 192.168.56.10 88

# Check SMB connectivity and signing status
netexec smb 192.168.56.10
```
