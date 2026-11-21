import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

BASE_DIR = "/Users/saicharan/Downloads/Active-Directory-Fundamentals"
PDF_PATH = os.path.join(BASE_DIR, "Active_Directory_Security_Course.pdf")
DIAGRAMS_DIR = os.path.join(BASE_DIR, "diagrams")

class MasterNumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            return  # Skip cover page
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#0077B6"))
        # Header
        self.drawString(54, 755, "ACTIVE DIRECTORY EXPLOITATION & DEFENSE: DEFINITIVE MASTER MANUAL")
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#6c757d"))
        self.drawRightString(612 - 54, 755, "POCKETSHARK SECURITY ACADEMY")
        self.setStrokeColor(colors.HexColor("#0096C7"))
        self.setLineWidth(0.75)
        self.line(54, 747, 612 - 54, 747)

        # Footer
        self.line(54, 45, 612 - 54, 45)
        self.drawString(54, 32, "Enterprise Identity Security, Red Teaming & Hardening Curriculum")
        self.drawRightString(612 - 54, 32, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()

def build_pdf():
    doc = SimpleDocTemplate(
        PDF_PATH,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Typography Styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=26,
        leading=32,
        textColor=colors.HexColor("#03045E"),
        alignment=1,
        spaceAfter=12
    )
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0077B6"),
        alignment=1,
        spaceAfter=25
    )
    ch_title_style = ParagraphStyle(
        'ChapterTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#03045E"),
        spaceBefore=14,
        spaceAfter=10,
        keepWithNext=True
    )
    sec_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0077B6"),
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13.5,
        textColor=colors.HexColor("#1A1A2E"),
        spaceAfter=6
    )
    bullet_style = ParagraphStyle(
        'BulletDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12.5,
        textColor=colors.HexColor("#2B2D42"),
        leftIndent=14,
        spaceAfter=4
    )
    code_block_style = ParagraphStyle(
        'CodeBlock',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#023E8A"),
        spaceBefore=4,
        spaceAfter=6
    )
    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12.5,
        textColor=colors.HexColor("#03045E")
    )

    story = []

    def make_callout(text, bg_color="#EBF4FF", border_color="#0077B6"):
        p = Paragraph(f"<b>Key Takeaway:</b> {text}", callout_style)
        t = Table([[p]], colWidths=[504])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(bg_color)),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor(border_color)),
            ('PADDING', (0,0), (-1,-1), 7),
        ]))
        return t

    def make_code(text):
        p = Paragraph(text.replace("\n", "<br/>").replace(" ", "&nbsp;"), code_block_style)
        t = Table([[p]], colWidths=[504])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F1F5F9")),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        return t

    # ==================== COVER PAGE ====================
    story.append(Spacer(1, 30))
    story.append(Paragraph("ACTIVE DIRECTORY EXPLOITATION & DEFENSE", title_style))
    story.append(Paragraph("THE DEFINITIVE ZERO-TO-HERO ENTERPRISE MASTER TEXTBOOK", subtitle_style))
    story.append(HRFlowable(width="85%", thickness=2, color=colors.HexColor("#00B4D8"), spaceAfter=20))
    
    img1 = os.path.join(DIAGRAMS_DIR, "ad_diagram_01.png")
    if os.path.exists(img1):
        story.append(Image(img1, width=440, height=190))
        story.append(Spacer(1, 15))

    meta_rows = [
        [Paragraph("<b>Curriculum Standards:</b>", body_style), Paragraph("PNPT, CRTP, CRTE, SpecterOps Attack Graphs, Microsoft EAM", body_style)],
        [Paragraph("<b>Core Focus:</b>", body_style), Paragraph("Architecture, Protocol Dissection, Attack Paths & Enterprise Tiering", body_style)],
        [Paragraph("<b>Primary Author / Team:</b>", body_style), Paragraph("PocketShark Cybersecurity Engineering Group", body_style)],
        [Paragraph("<b>Repository:</b>", body_style), Paragraph("github.com/Shashi552/Active-Directory-Fundamentals", code_block_style)],
        [Paragraph("<b>Edition & Date:</b>", body_style), Paragraph("Volume I — Complete Master Edition | November 2026", body_style)]
    ]
    meta_table = Table(meta_rows, colWidths=[140, 364])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('PADDING', (0,0), (-1,-1), 6),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#0077B6")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
    ]))
    story.append(meta_table)
    story.append(PageBreak())

    # ==================== TABLE OF CONTENTS ====================
    story.append(Paragraph("Master Course Syllabus & Structural Index", ch_title_style))
    story.append(Paragraph("This comprehensive manual is organized into eight exhaustive chapters. It guides you from the fundamental differences between local workgroups and domain controllers, through deep protocol internals (Kerberos, LDAP, RPC, AD CS), up to advanced red-team persistence, DCSync replication, and zero-trust defensive tiering.", body_style))
    story.append(Spacer(1, 8))

    toc_data = [
        ["Chapter", "Discipline & Title", "Detailed Technical Scope"],
        ["Chapter 0", "Windows Systems Administration", "Workgroups, SAM vs NTDS.dit, SIDs/RIDs, Local vs Domain Admin, GPMC"],
        ["Chapter 1", "Active Directory Architecture", "Forests, Domains, Trees, Trusts, FSMO 5 Roles, LDAP, DNS, Kerberos Ports"],
        ["Chapter 2", "Authentication Protocol Internals", "NTLMv2 Challenge/Response, Kerberos 3-Way Exchange, PAC Verification, TGT/TGS"],
        ["Chapter 3", "Enumeration & Attack Graphs", "PowerView, SharpHound Ingestion, BloodHound Graph Theory, Cypher Analytics"],
        ["Chapter 4", "Credential Attacks & Delegation", "AS-REP Roasting, Kerberoasting (RC4/AES), Unconstrained, Constrained, RBCD"],
        ["Chapter 5", "AD Certificate Services (AD CS)", "PKI Templates, ESC1 SAN Misconfiguration, ESC4 ACL Abuse, ESC8 NTLM Relay"],
        ["Chapter 6", "Privilege Escalation & Dominance", "ACL Abuse (GenericAll/WriteDacl), LAPS Secrets, DCSync MS-DRSR, Golden/Silver"],
        ["Chapter 7", "TCM Security Practical Workflow", "Zero-Credential Footholds, LLMNR/NBT-NS (Responder), SMB Relay, mitm6"],
        ["Chapter 8", "Enterprise Defense & Hardening", "Microsoft Enterprise Access Model, Tier 0 Isolation, PAWs, Security Event IDs"]
    ]
    t_toc = Table(toc_data, colWidths=[65, 175, 264])
    t_toc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#03045E")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8.5),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F8FAFC")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_toc)
    story.append(Spacer(1, 10))
    story.append(make_callout("This manual assumes zero prior Active Directory knowledge, but builds directly towards professional certification standards including PNPT, CRTP, and CRTE.", "#E0F2FE", "#0284C7"))
    story.append(PageBreak())

    # ==================== CHAPTER 0 ====================
    story.append(Paragraph("Chapter 0: Windows Systems Administration & Core Concepts", ch_title_style))
    story.append(Paragraph("<b>1. The Workgroup Problem vs Active Directory Solution:</b> Standalone personal computers in an unmanaged network operate in a <i>Workgroup</i>. Each computer stores its accounts locally in the <b>Security Account Manager (SAM)</b> database file located at <code>C:\\Windows\\System32\\config\\SAM</code>. If an enterprise has 1,000 computers, managing local user accounts, passwords, and security patches individually across 1,000 endpoints is impossible.", body_style))
    story.append(Paragraph("<b>Active Directory Domain Services (AD DS)</b> centralizes all authentication, authorizations, and directory objects into a single, replicated database called <b><code>ntds.dit</code></b>. This database resides exclusively on high-security servers termed <b>Domain Controllers (DCs)</b>. When any employee logs into any corporate endpoint, authentication occurs over the network against the DC rather than locally.", body_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>2. Security Identifiers (SIDs) and Relative IDs (RIDs):</b>", sec_title_style))
    story.append(Paragraph("Windows security principals (users, groups, computers) are identified internally not by names, but by unique alphanumeric strings called SIDs:", body_style))
    story.append(make_code("S-1-5-21-3623811015-3361044348-30300820-500\n[S] Revision  [5] Security Authority  [21-...] Domain Identifier  [500] Relative ID (RID)"))
    story.append(Paragraph("• <b>RID 500:</b> Built-in Local or Domain Administrator account.<br/>• <b>RID 502:</b> <code>krbtgt</code> account (the master Key Distribution Center encryption account).<br/>• <b>RID 512:</b> Domain Admins global group.<br/>• <b>RID 513:</b> Domain Users global group.<br/>• <b>RID 519:</b> Enterprise Admins universal group (controls the entire forest).", bullet_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>3. The Administrative Scope Hierarchy:</b>", sec_title_style))
    story.append(Paragraph("• <b>Local Administrator:</b> Has complete control (SYSTEM privileges) over one standalone machine. Can dump local memory, extract local SAM hashes, and install software. However, a Local Administrator on Workstation A has zero authority over Workstation B or the Domain Controller.", bullet_style))
    story.append(Paragraph("• <b>Domain Administrator:</b> Has full control over all domain controllers, servers, and workstations joined to the domain. By default, the 'Domain Admins' group is automatically injected into the local 'Administrators' group of every domain-joined machine.", bullet_style))
    story.append(Paragraph("• <b>Enterprise Administrator:</b> Exists strictly in the root domain of an AD forest and possesses universal administrative authority across every child domain in that forest.", bullet_style))
    story.append(Spacer(1, 10))

    img2 = os.path.join(DIAGRAMS_DIR, "ad_diagram_02.png")
    if os.path.exists(img2):
        story.append(Image(img2, width=440, height=125))
        story.append(Spacer(1, 10))
    story.append(PageBreak())

    # ==================== CHAPTER 1 ====================
    story.append(Paragraph("Chapter 1: Active Directory Architecture & Components", ch_title_style))
    story.append(Paragraph("<b>1. Forests, Trees, and Domains:</b>", sec_title_style))
    story.append(Paragraph("• <b>Domain:</b> The core administrative boundary containing users, computers, and groups sharing a common directory database. (e.g. <code>us.corp.local</code>).<br/>• <b>Tree:</b> A hierarchical grouping of domains that share a contiguous DNS namespace.<br/>• <b>Forest:</b> The ultimate <b>security boundary</b> of an Active Directory deployment. A forest can contain multiple trees. If an attacker gains Enterprise Admin or compromises the forest root domain controller, the entire forest is compromised.", body_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>2. FSMO Roles (Flexible Single Master Operations):</b>", sec_title_style))
    story.append(Paragraph("While Active Directory uses multi-master replication for most updates, five critical tasks require single-master authority:", body_style))
    story.append(Paragraph("1. <b>Schema Master (Forest-wide):</b> Controls changes to the Active Directory schema definition.<br/>2. <b>Domain Naming Master (Forest-wide):</b> Manages additions or removals of domains in the forest.<br/>3. <b>PDC Emulator (Domain-wide):</b> Manages password updates, account lockouts, and domain-wide NTP clock synchronization (critical for Kerberos tolerance).<br/>4. <b>RID Master (Domain-wide):</b> Allocates pools of Relative Identifiers (RIDs) to DCs to ensure unique SIDs.<br/>5. <b>Infrastructure Master (Domain-wide):</b> Handles cross-domain object reference updates.", bullet_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>3. Critical Active Directory Network Ports:</b>", sec_title_style))
    story.append(Paragraph("During security assessments and network defense, the following DC ports must be recognized:", body_style))
    ports_data = [
        ["Port", "Protocol", "Service Function", "Attacker / Defender Relevance"],
        ["53", "DNS (TCP/UDP)", "Domain Name Resolution & SRV Records", "Locating Domain Controllers (_ldap._tcp)"],
        ["88", "Kerberos (TCP/UDP)", "Authentication Service & Ticket Granting", "AS-REP Roasting, Kerberoasting, Golden Tickets"],
        ["135", "MSRPC (TCP)", "Endpoint Mapper / RPC Endpoint Resolution", "WMI Execution, DCOM lateral movement"],
        ["389 / 636", "LDAP / LDAPS (TCP)", "Directory Search & Object Modification", "BloodHound ingestion, user/group enumeration"],
        ["445", "SMB (TCP)", "File Sharing, IPC$, Named Pipes", "Pass-the-Hash, PsExec, SYSVOL policies, SMB Relay"]
    ]
    t_ports = Table(ports_data, colWidths=[55, 95, 160, 194])
    t_ports.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0077B6")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('PADDING', (0,0), (-1,-1), 4.5),
    ]))
    story.append(t_ports)
    story.append(Spacer(1, 10))

    img3 = os.path.join(DIAGRAMS_DIR, "ad_diagram_03.png")
    if os.path.exists(img3):
        story.append(Image(img3, width=440, height=130))
        story.append(Spacer(1, 10))
    story.append(PageBreak())

    # ==================== CHAPTER 2 ====================
    story.append(Paragraph("Chapter 2: Authentication Protocol Internals — Kerberos vs NTLM", ch_title_style))
    story.append(Paragraph("<b>1. The Fragility of NTLMv2 Authentication:</b>", sec_title_style))
    story.append(Paragraph("NTLM uses a challenge-response handshake over SMB or HTTP. Because NTLM lacks mutual authentication and does not cryptographically bind the session to the transport layer, an attacker positioned on the local network can intercept the challenge-response and relay it directly to another host via tools like <code>ntlmrelayx</code> to gain administrative command execution without ever cracking the password.", body_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>2. Kerberos 3-Way Handshake Deep-Dive:</b>", sec_title_style))
    story.append(Paragraph("Modern Windows environments default to Kerberos over Port 88:", body_style))
    story.append(Paragraph("• <b>Phase 1: Authentication Service (AS) Exchange:</b><br/>The client sends an <code>AS-REQ</code> containing a timestamp encrypted with the user's password hash (pre-authentication). The KDC on the DC decrypts the timestamp, verifying the password. The KDC returns an <code>AS-REP</code> containing the <b>Ticket Granting Ticket (TGT)</b> (encrypted exclusively with the secret <code>krbtgt</code> account hash) and an ephemeral logon session key.", bullet_style))
    story.append(Paragraph("• <b>Phase 2: Ticket Granting Service (TGS) Exchange:</b><br/>When the user needs to access a specific network service (e.g. MSSQL or SMB), the client sends a <code>TGS-REQ</code> presenting its TGT and the target <b>Service Principal Name (SPN)</b>. The KDC verifies the TGT, extracts the user's Privilege Attribute Certificate (PAC), and issues a <code>TGS-REP</code> containing a service ticket encrypted with the <b>target service account's password hash</b>.", bullet_style))
    story.append(Paragraph("• <b>Phase 3: Client/Server (AP) Application Exchange:</b><br/>The client delivers an <code>AP-REQ</code> to the destination application server. The server decrypts the ticket using its own password hash, verifies the user identity and group SIDs inside the PAC, and grants access.", bullet_style))
    story.append(Spacer(1, 8))

    story.append(make_callout("Understanding ticket encryption is the foundation of Active Directory red teaming: The TGT is encrypted with the KRBTGT key (forgeable via Golden Ticket); the TGS is encrypted with the Service Account key (crackable via Kerberoasting or forgeable via Silver Ticket).", "#FEF3C7", "#D97706"))
    story.append(Spacer(1, 10))

    img4 = os.path.join(DIAGRAMS_DIR, "ad_diagram_04.png")
    if os.path.exists(img4):
        story.append(Image(img4, width=440, height=130))
        story.append(Spacer(1, 10))
    story.append(PageBreak())

    # ==================== CHAPTER 3 ====================
    story.append(Paragraph("Chapter 3: Enumeration & Attack Graph Theory", ch_title_style))
    story.append(Paragraph("<b>1. Defenders Think in Lists, Attackers Think in Graphs:</b>", sec_title_style))
    story.append(Paragraph("Traditional vulnerability scanners search for unpatched software (missing CVEs). However, modern Active Directory compromise paths almost never rely on software bugs. They exploit <b>misconfigured trust relationships and excessive permissions</b> across the directory graph.", body_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>2. BloodHound & SharpHound Architecture:</b>", sec_title_style))
    story.append(Paragraph("• <b>Nodes:</b> Represent Active Directory security entities: Users, Computers, Security Groups, Organizational Units (OUs), GPOs, and Domains.<br/>• <b>Edges:</b> Represent directional relationships and privileges: <code>MemberOf</code>, <code>AdminTo</code>, <code>HasSession</code>, <code>GenericAll</code>, <code>WriteDacl</code>, <code>AddMember</code>, and <code>CanRDP</code>.", body_style))
    story.append(Paragraph("SharpHound collects this graph via standard LDAP queries, NetSessionEnum RPC calls, and registry queries without requiring administrative privileges:", body_style))
    story.append(make_code("# Ingest complete domain graph using SharpHound\nSharpHound.exe -c All --zipfilename ad_graph.zip\n\n# Linux remote collection via bloodhound-python\nbloodhound-python -d corp.local -u jsmith -p Password123! -gc corp.local -c All -dc dc01.corp.local"))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>3. Critical BloodHound Cypher Queries for Red Teams & Auditors:</b>", sec_title_style))
    story.append(Paragraph("• <b>Find Shortest Paths to Domain Admins:</b><br/><code>MATCH p=shortestPath((u:User)-[r:MemberOf|AdminTo|GenericAll*1..]->(g:Group {name:'DOMAIN ADMINS@CORP.LOCAL'})) RETURN p</code>", bullet_style))
    story.append(Paragraph("• <b>Find Users with DCSync Replication Rights:</b><br/><code>MATCH (n)-[r:GetChanges*1..]->(d:Domain) RETURN n,r,d</code>", bullet_style))
    story.append(Paragraph("• <b>Find Unconstrained Delegation Servers:</b><br/><code>MATCH (c:Computer {unconstraineddelegation:true}) RETURN c</code>", bullet_style))
    story.append(Spacer(1, 10))

    img5 = os.path.join(DIAGRAMS_DIR, "ad_diagram_05.png")
    if os.path.exists(img5):
        story.append(Image(img5, width=440, height=125))
        story.append(Spacer(1, 10))
    story.append(PageBreak())

    # ==================== CHAPTER 4 ====================
    story.append(Paragraph("Chapter 4: Credential Attacks & Kerberos Delegation", ch_title_style))
    story.append(Paragraph("<b>1. AS-REP Roasting:</b>", sec_title_style))
    story.append(Paragraph("• <b>Vulnerability:</b> Accounts configured with the user account control flag <code>DONT_REQ_PREAUTH</code> (Kerberos pre-authentication not required).<br/>• <b>Exploitation:</b> Any unauthenticated or low-privilege attacker can send an <code>AS-REQ</code> requesting a ticket for that user. The DC immediately responds with an <code>AS-REP</code> containing an encrypted timestamp. The attacker extracts the ticket and cracks it offline using Hashcat mode 18200.", body_style))
    story.append(make_code("# Execute AS-REP Roasting via Impacket\nimpacket-GetNPUsers corp.local/ -usersfile users.txt -format hashcat -outputfile asrep.hashes\nhashcat -m 18200 asrep.hashes rockyou.txt"))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>2. Kerberoasting:</b>", sec_title_style))
    story.append(Paragraph("• <b>Vulnerability:</b> Service Principal Names (SPNs) mapped to standard user accounts (rather than computer accounts).<br/>• <b>Exploitation:</b> Any valid domain user can request a TGS ticket for that SPN. Because the ticket is encrypted with the service account's password hash, the ticket is cracked offline without generating failed logon events on the DC.", body_style))
    story.append(make_code("# Execute Kerberoasting and crack offline\nimpacket-GetUserSPNs corp.local/jsmith:Password123! -request -outputfile kerberoast.hashes\nhashcat -m 13100 kerberoast.hashes rockyou.txt"))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>3. Kerberos Delegation Types & Exploitation:</b>", sec_title_style))
    story.append(Paragraph("• <b>Unconstrained Delegation:</b> The target server is permitted to impersonate users to any service. When a user connects to this server, the user's entire TGT is cached in LSASS. If an attacker compromises an unconstrained server and entices a Domain Admin to connect, the attacker extracts the Domain Admin's TGT from memory.", bullet_style))
    story.append(Paragraph("• <b>Constrained Delegation (S4U2Self & S4U2Proxy):</b> The service is restricted to impersonating users to specific target services. An attacker possessing the service key can forge tickets on behalf of arbitrary privileged users to those allowed targets.", bullet_style))
    story.append(Paragraph("• <b>Resource-Based Constrained Delegation (RBCD):</b> Delegation is controlled by the target resource via the <code>msDS-AllowedToActOnBehalfOfOtherIdentity</code> attribute. If an attacker has write permissions over a computer object, they can configure delegation to that machine from an attacker-controlled computer account.", bullet_style))
    story.append(Spacer(1, 10))

    img6 = os.path.join(DIAGRAMS_DIR, "ad_diagram_06.png")
    if os.path.exists(img6):
        story.append(Image(img6, width=440, height=125))
        story.append(Spacer(1, 10))
    story.append(PageBreak())

    # ==================== CHAPTER 5 ====================
    story.append(Paragraph("Chapter 5: Active Directory Certificate Services (AD CS) Exploitation", ch_title_style))
    story.append(Paragraph("<b>1. Public Key Infrastructure (PKI) in Active Directory:</b>", sec_title_style))
    story.append(Paragraph("AD CS provides digital certificates used for user authentication, VPN access, and smart cards. Misconfigurations in Certificate Templates publish exploitable attack paths cataloged by SpecterOps as <b>ESC1 through ESC8</b>.", body_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>2. Primary Escalation Paths:</b>", sec_title_style))
    story.append(Paragraph("• <b>ESC1 (SAN Misconfiguration):</b> Occurs when a certificate template permits: (1) Client Authentication, (2) Enrollment permissions for regular Domain Users, and (3) The <code>CT_FLAG_ENROLLEE_SUPPLIES_SUBJECT</code> flag. An attacker requests a certificate while supplying the User Principal Name (UPN) of a Domain Administrator in the Subject Alternative Name (SAN). The CA signs the certificate, which is then used to request a Kerberos TGT as that Domain Admin.", bullet_style))
    story.append(Paragraph("• <b>ESC4 (Template Access Control Abuse):</b> A regular user has <code>WriteDacl</code> or <code>GenericAll</code> permissions over an otherwise secure certificate template. The attacker modifies the template configuration to enable ESC1, requests the certificate, and reverts the template.", bullet_style))
    story.append(Paragraph("• <b>ESC8 (AD CS Web Enrollment NTLM Relay):</b> The CA exposes an HTTP web enrollment portal (`/certsrv`) that does not enforce Extended Protection for Authentication (EPA) or HTTPS. An attacker coerces authentication from a Domain Controller (via PetitPotam or PrinterBug) and relays the NTLM authentication to the CA Web Enrollment endpoint to obtain a valid machine certificate for the DC.", bullet_style))
    story.append(make_code("# Audit AD CS vulnerabilities via Certipy\ncertipy find -u jsmith@corp.local -p Password123! -dc-ip 192.168.1.10 -stdout\n\n# Exploit ESC1 to request Domain Admin certificate\ncertipy req -u jsmith@corp.local -p Password123! -ca CORP-CA -template ESC1_Vuln -upn Administrator@corp.local"))
    story.append(Spacer(1, 10))

    img7 = os.path.join(DIAGRAMS_DIR, "ad_diagram_07.png")
    if os.path.exists(img7):
        story.append(Image(img7, width=440, height=125))
        story.append(Spacer(1, 10))
    story.append(PageBreak())

    # ==================== CHAPTER 6 ====================
    story.append(Paragraph("Chapter 6: Privilege Escalation & Domain Dominance", ch_title_style))
    story.append(Paragraph("<b>1. Active Directory Access Control List (ACL) Abuse:</b>", sec_title_style))
    story.append(Paragraph("Every object in Active Directory has a Security Descriptor containing Discretionary Access Control Lists (DACLs) with Access Control Entries (ACEs):", body_style))
    story.append(Paragraph("• <b>GenericAll:</b> Full control over target object. Allows resetting user passwords, adding users to groups, and modifying service paths.<br/>• <b>WriteDacl:</b> Allows the attacker to modify the DACL itself, granting themselves <code>GenericAll</code>.<br/>• <b>WriteOwner:</b> Allows taking ownership of the object, subsequently modifying the DACL.<br/>• <b>ForceChangePassword:</b> Allows resetting the target user's password without knowing their current password.", bullet_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>2. DCSync Attack (Directory Replication Service Remote Protocol):</b>", sec_title_style))
    story.append(Paragraph("• <b>Mechanics:</b> Instead of running executable code on a Domain Controller, an attacker with replication privileges simulates the behavior of a replica Domain Controller using the MS-DRSR protocol. The attacker requests directory synchronization.<br/>• <b>Required Privileges:</b> <code>DS-Replication-Get-Changes</code> and <code>DS-Replication-Get-Changes-All</code>.<br/>• <b>Result:</b> Dumps password hashes for <b>any</b> domain account directly over the network, including the master <code>krbtgt</code> hash and built-in <code>Administrator</code>.", body_style))
    story.append(make_code("# Execute DCSync attack via Impacket secretsdump\nimpacket-secretsdump -hashes :<ADMIN_HASH> corp.local/Administrator@192.168.1.10 -outputfile domain_hashes"))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>3. Ticket Forgery for Enterprise Persistence:</b>", sec_title_style))
    story.append(Paragraph("• <b>Golden Ticket:</b> A forged TGT created using the <code>krbtgt</code> NTLM hash or AES key. Because the DC trusts any ticket signed with its KRBTGT key without validating against the database, the attacker can create a ticket for any user with arbitrary group memberships (e.g. Domain Admins, Enterprise Admins) valid for up to 10 years.<br/>• <b>Silver Ticket:</b> A forged TGS service ticket created using a target computer's machine account password hash. It grants complete administrative control over that specific host/service (CIFS, MSSQL, HOST) without ever communicating with a Domain Controller.", body_style))
    story.append(Spacer(1, 10))

    img8 = os.path.join(DIAGRAMS_DIR, "ad_diagram_08.png")
    if os.path.exists(img8):
        story.append(Image(img8, width=440, height=130))
        story.append(Spacer(1, 10))
    story.append(PageBreak())

    # ==================== CHAPTER 7 ====================
    story.append(Paragraph("Chapter 7: Practical Assessment Methodology (TCM Security PNPT Flow)", ch_title_style))
    story.append(Paragraph("<b>1. Zero-Credential Initial Foothold:</b>", sec_title_style))
    story.append(Paragraph("When conducting black-box internal penetration tests starting with zero credentials:", body_style))
    story.append(Paragraph("• <b>Step 1: LLMNR/NBT-NS Poisoning:</b> Listen for broadcast queries with Responder to capture NetNTLMv2 hashes: <code>sudo responder -I eth0 -dwv</code>.<br/>• <b>Step 2: SMB Relaying:</b> Find hosts where SMB Signing is disabled. Relay NetNTLM authentication to dump local SAM databases or spawn SOCKS proxies: <code>impacket-ntlmrelayx -tf targets.txt -smb2support -socks</code>.<br/>• <b>Step 3: IPv6 DHCP Takeover:</b> Run <code>mitm6 -d corp.local</code> to spoof DNS responses and relay credentials to LDAPS on the DC.", bullet_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>2. Post-Foothold Lateral Movement:</b>", sec_title_style))
    story.append(Paragraph("• <b>Pass-the-Hash (PtH):</b> Authenticate across workstations using NTLM hashes over SMB or WMI without cracking plaintext passwords: <code>impacket-wmiexec -hashes :<HASH> Administrator@192.168.1.50</code>.<br/>• <b>WinRM Execution:</b> Interactive PowerShell management over port 5985: <code>evil-winrm -i 192.168.1.50 -u Administrator -H <HASH></code>.<br/>• <b>Network Pivoting:</b> Tunnel traffic into isolated subnets using reverse SOCKS proxies like <b>Chisel</b>.", bullet_style))
    story.append(Spacer(1, 8))

    story.append(make_callout("TCM Security's PNPT framework emphasizes clean methodology: Document every step, minimize network impact, avoid noisy brute-force lockouts, and confirm all privilege escalation findings with clear proofs of concept.", "#DCFCE7", "#16A34A"))
    story.append(Spacer(1, 10))

    # ==================== CHAPTER 8 ====================
    story.append(Paragraph("Chapter 8: Enterprise Defense, Detection Engineering & Tiering", ch_title_style))
    story.append(Paragraph("<b>1. Microsoft Enterprise Access Model (The Tiering Architecture):</b>", sec_title_style))
    story.append(Paragraph("The fundamental architectural defense against lateral movement is strict credential boundary enforcement:", body_style))
    story.append(Paragraph("• <b>Tier 0 (Control Plane):</b> Domain Controllers, PKI, ADFS, Azure AD Connect, Domain Admins. Tier 0 credentials must <b>never</b> be typed or cached on lower-tier machines. Administrators must access Tier 0 exclusively from dedicated physical <b>Privileged Access Workstations (PAWs)</b>.<br/>• <b>Tier 1 (Server Plane):</b> Enterprise servers, databases, and business line applications.<br/>• <b>Tier 2 (Workstation Plane):</b> User endpoints and laptops managed via localized LAPS credentials.", body_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>2. Critical Windows Security Event IDs for Active Directory Auditing:</b>", sec_title_style))
    ev_table_data = [
        ["Event ID", "Category", "Event Meaning", "High-Priority Threat Indicator"],
        ["4624", "Logon", "Successful Account Logon", "Type 3 network logons using NTLM instead of Kerberos"],
        ["4625", "Logon", "Failed Account Logon", "Spike across multiple distinct usernames indicates password spray"],
        ["4662", "Directory", "Directory Service Access", "Access mask 0x100 with replication GUID indicates DCSync"],
        ["4768", "Kerberos", "TGT Request (AS-REQ)", "Pre-authentication failure (Result code 0x18 indicates AS-REP attack)"],
        ["4769", "Kerberos", "Service Ticket (TGS-REQ)", "Encryption downgrade to 0x17 (RC4) indicates Kerberoasting"],
        ["4728", "Group", "Member Added to Global Group", "Unauthorized user added to Domain Admins or Enterprise Admins"],
        ["4738", "User", "User Account Modified", "SPN attribute added or DONT_REQ_PREAUTH flag enabled"]
    ]
    t_ev = Table(ev_table_data, colWidths=[55, 65, 150, 234])
    t_ev.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#03045E")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 7.5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_ev)
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>3. Five Mandatory Hardening Directives:</b>", sec_title_style))
    story.append(Paragraph("1. <b>Deploy Windows LAPS Everywhere:</b> Automatically randomizes local administrator passwords on every computer, eliminating lateral movement via Pass-the-Hash.<br/>2. <b>Protected Users Security Group:</b> Place all Domain Admins and Tier 0 accounts inside `Protected Users` to prevent credential caching in LSASS and block NTLM.<br/>3. <b>Enforce SMB & LDAP Signing:</b> Mandate cryptographic signing across all workstations and servers to defeat SMB Relay and NTLM-to-LDAP coercion.<br/>4. <b>Enforce Kerberos AES:</b> Disable legacy RC4 encryption on all user and service accounts.<br/>5. <b>Rotate KRBTGT Password Twice Post-Incident:</b> Use Microsoft's official `New-KrbtgtKeys.ps1` script with a 24-hour interval between rotations to invalidate forged Golden Tickets.", bullet_style))

    doc.build(story, canvasmaker=MasterNumberedCanvas)
    print(f"🎉 MASTER BOOK COMPILED! Total pages: {doc.page} at {PDF_PATH}")

if __name__ == "__main__":
    build_pdf()
