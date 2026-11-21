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

class NumberedCanvas(canvas.Canvas):
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
        self.setFillColor(colors.HexColor("#00B4D8"))
        # Header
        self.drawString(54, 755, "ACTIVE DIRECTORY SECURITY & EXPLOITATION: ZERO-TO-HERO MANUAL")
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#6c757d"))
        self.drawRightString(612 - 54, 755, "CONFIDENTIAL & EDUCATIONAL")
        self.setStrokeColor(colors.HexColor("#0077B6"))
        self.setLineWidth(0.75)
        self.line(54, 747, 612 - 54, 747)

        # Footer
        self.line(54, 45, 612 - 54, 45)
        self.drawString(54, 32, "PocketShark Security Research Academy | Active Directory Fundamentals")
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
    
    # Custom styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=28,
        leading=34,
        textColor=colors.HexColor("#03045E"),
        alignment=1, # Center
        spaceAfter=15
    )
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=13,
        leading=18,
        textColor=colors.HexColor("#0077B6"),
        alignment=1,
        spaceAfter=30
    )
    h1_style = ParagraphStyle(
        'Header1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#03045E"),
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'Header2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#0077B6"),
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#1A1A2E"),
        spaceAfter=6
    )
    bullet_style = ParagraphStyle(
        'BulletDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#2B2D42"),
        leftIndent=15,
        spaceAfter=4
    )
    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#03045E")
    )
    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#0077B6"),
        spaceAfter=4
    )

    story = []

    # ------------------ COVER PAGE ------------------
    story.append(Spacer(1, 40))
    story.append(Paragraph("ACTIVE DIRECTORY SECURITY & EXPLOITATION", title_style))
    story.append(Paragraph("ZERO-TO-HERO COMPREHENSIVE CURRICULUM & ARCHITECTURE MANUAL", subtitle_style))
    story.append(HRFlowable(width="80%", thickness=2, color=colors.HexColor("#00B4D8"), spaceAfter=25))
    
    # Cover diagram if available
    diagram1_path = os.path.join(DIAGRAMS_DIR, "ad_diagram_01.png")
    if os.path.exists(diagram1_path):
        story.append(Image(diagram1_path, width=420, height=190))
        story.append(Spacer(1, 20))

    meta_data = [
        [Paragraph("<b>Target Audience:</b>", body_style), Paragraph("Penetration Testers, Red Teamers & Enterprise Defenders", body_style)],
        [Paragraph("<b>Prerequisites:</b>", body_style), Paragraph("Basic Networking, TCP/IP, and Windows Concepts", body_style)],
        [Paragraph("<b>Core Focus:</b>", body_style), Paragraph("Protocol Mechanics (Kerberos/NTLM), Attack Graphs & Defense Tiering", body_style)],
        [Paragraph("<b>Repository:</b>", body_style), Paragraph("github.com/Shashi552/Active-Directory-Fundamentals", code_style)],
        [Paragraph("<b>Publication Date:</b>", body_style), Paragraph("November 2026 | Edition 1.0", body_style)]
    ]
    t = Table(meta_data, colWidths=[130, 320])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F0F8FF")),
        ('PADDING', (0,0), (-1,-1), 6),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#0077B6")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CAE9FF")),
    ]))
    story.append(t)
    story.append(PageBreak())

    # ------------------ TABLE OF CONTENTS ------------------
    story.append(Paragraph("Course Syllabus & Module Breakdown", h1_style))
    story.append(Paragraph("This manual is divided into six progressive modules designed around the 'Why Before How' principle. Master the underlying protocols, graph relationships, and defenses.", body_style))
    story.append(Spacer(1, 10))

    toc_data = [
        ["Module", "Core Subject", "Key Concepts"],
        ["Module 1", "Architecture & Foundations", "Forests, Domains, FSMO Roles, Global Catalog, LDAP & DNS"],
        ["Module 2", "Authentication Protocols", "NTLMv2, Kerberos 3-Way Handshake, TGT, TGS, and PAC Validation"],
        ["Module 3", "Enumeration & Attack Graphs", "Directory Search, PowerView, SharpHound, BloodHound Shortest Paths"],
        ["Module 4", "Credential & Delegation Vectors", "AS-REP Roasting, Kerberoasting, Unconstrained & RBCD Delegation"],
        ["Module 5", "PrivEsc & Domain Dominance", "ACL Abuse (GenericAll/WriteDacl), LAPS, DCSync Replication, Golden Tickets"],
        ["Module 6", "Enterprise Defense & Hardening", "Microsoft Enterprise Access Model, Tier 0 Isolation, Windows Event IDs"]
    ]
    toc_table = Table(toc_data, colWidths=[65, 175, 260])
    toc_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#03045E")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F8F9FA")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CED4DA")),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(toc_table)
    story.append(Spacer(1, 15))


    # ------------------ MODULE 0 ------------------
    story.append(Paragraph("Module 0: Windows Systems Administration & Core Concepts", h1_style))
    story.append(Paragraph("<b>1. What is Active Directory?</b> In a standalone <i>Workgroup</i>, every computer maintains its own isolated <code>SAM</code> (Security Account Manager) user database. Active Directory Domain Services (AD DS) eliminates this fragmentation by centralizing all identities, computers, and access control lists into a single master database named <code>ntds.dit</code> hosted on Domain Controllers (DCs).", body_style))
    story.append(Paragraph("• <b>Local Accounts vs Domain Accounts:</b> Local accounts (e.g. <code>PC-01\Alice</code>) live in the local SAM and cannot access network resources. Domain accounts (e.g. <code>CORP\Alice</code>) live in <code>ntds.dit</code> and authenticate centrally via Kerberos across the entire forest.", bullet_style))
    story.append(Paragraph("• <b>Security Identifiers (SIDs):</b> Windows tracks identity via binary SIDs. High-value built-in RIDs include <b>500</b> (Administrator), <b>502</b> (KRBTGT master KDC account), and <b>512</b> (Domain Admins group).", bullet_style))
    story.append(Paragraph("• <b>Administrative Scopes:</b> A <i>Local Administrator</i> controls one machine. A <i>Domain Administrator</i> controls the domain and is automatically in the local Administrators group of all joined machines. An <i>Enterprise Administrator</i> controls the entire forest root.", bullet_style))
    story.append(Spacer(1, 10))
    # ------------------ MODULE 1 ------------------
    story.append(Paragraph("Module 1: Active Directory Architecture & Foundations", h1_style))
    story.append(Paragraph("<b>1. What to Learn:</b> Active Directory Domain Services (AD DS) organizes identity across logical and physical boundaries. The <b>Forest</b> represents the ultimate security boundary, while <b>Domains</b> represent administrative boundaries. Key structural components include:", body_style))
    story.append(Paragraph("• <b>Domain Controllers (DCs):</b> The hosts holding the <code>ntds.dit</code> database and running Kerberos Key Distribution Center (KDC).", bullet_style))
    story.append(Paragraph("• <b>FSMO Roles:</b> Schema Master, Domain Naming Master, PDC Emulator, RID Master, and Infrastructure Master.", bullet_style))
    story.append(Paragraph("• <b>LDAP & DNS:</b> Port 389/636 for object querying and SRV records for DC locator services.", bullet_style))
    story.append(Spacer(1, 5))

    diagram2_path = os.path.join(DIAGRAMS_DIR, "ad_diagram_02.png")
    if os.path.exists(diagram2_path):
        story.append(Image(diagram2_path, width=440, height=130))
        story.append(Spacer(1, 10))

    story.append(Paragraph("<b>2. Why You Must Learn It:</b> You cannot compromise or defend an environment without understanding where the actual security perimeter lies. Standard users can query virtually the entire directory by default via LDAP. Understanding the hierarchy reveals how GPOs propagate configurations and where trust relationships terminate.", body_style))
    story.append(Spacer(1, 15))

    # ------------------ MODULE 2 ------------------
    story.append(Paragraph("Module 2: Authentication Protocols — Kerberos vs NTLM", h1_style))
    story.append(Paragraph("<b>1. Kerberos 3-Way Exchange:</b> Modern Active Directory relies primarily on Kerberos (Port 88) rather than NTLM:", body_style))
    story.append(Paragraph("• <b>AS Exchange:</b> Client sends <code>AS-REQ</code> with an encrypted timestamp. The KDC validates and returns an <code>AS-REP</code> containing the Ticket Granting Ticket (TGT) encrypted with the KRBTGT key.", bullet_style))
    story.append(Paragraph("• <b>TGS Exchange:</b> Client presents TGT and requests access to an SPN. KDC returns a <code>TGS-REP</code> encrypted with the target service account's secret key.", bullet_style))
    story.append(Paragraph("• <b>AP Exchange:</b> Client presents the service ticket to the application server for access verification.", bullet_style))
    story.append(Paragraph("• <b>PAC (Privilege Attribute Certificate):</b> Cryptographically signed structure inside tickets detailing group SIDs and user rights.", bullet_style))
    story.append(Spacer(1, 5))

    diagram3_path = os.path.join(DIAGRAMS_DIR, "ad_diagram_03.png")
    if os.path.exists(diagram3_path):
        story.append(Image(diagram3_path, width=440, height=140))
        story.append(Spacer(1, 10))

    story.append(Paragraph("<b>2. Why You Must Learn It:</b> Kerberos protocol structures form the attack surface for AS-REP Roasting, Kerberoasting, and Ticket Forgery. Understanding ticket encryption keys enables you to understand exactly why offline password cracking succeeds.", body_style))
    story.append(PageBreak())

    # ------------------ MODULE 3 ------------------
    story.append(Paragraph("Module 3: Enumeration & Attack Graph Theory", h1_style))
    story.append(Paragraph("<b>1. The Power of Graphs:</b> Attackers do not think in lists of users; they think in directional graphs. BloodHound maps Active Directory as a mathematical graph of nodes (Users, Computers, Groups) connected by directional edges (AdminTo, MemberOf, GenericAll, WriteDacl, HasSession).", body_style))
    story.append(Paragraph("• <b>SharpHound Ingestion:</b> Collects session data, ACLs, and group memberships via LDAP, NetSessionEnum, and Registry APIs.", bullet_style))
    story.append(Paragraph("• <b>Shortest Path to Domain Admin:</b> Highlights transitive trust paths that bypass traditional firewall boundaries.", bullet_style))
    story.append(Spacer(1, 5))

    diagram4_path = os.path.join(DIAGRAMS_DIR, "ad_diagram_04.png")
    if os.path.exists(diagram4_path):
        story.append(Image(diagram4_path, width=440, height=130))
        story.append(Spacer(1, 10))

    story.append(Paragraph("<b>2. Defensive Countermeasure:</b> Monitor for rapid spikes in LDAP queries from non-admin workstations (Event ID 4662) and block remote MSRPC/SAMR queries from regular endpoints.", body_style))
    story.append(Spacer(1, 15))

    # ------------------ MODULE 4 ------------------
    story.append(Paragraph("Module 4: Credential Attacks & Kerberos Delegation", h1_style))
    story.append(Paragraph("<b>1. Protocol Abuse Vectors:</b>", body_style))
    story.append(Paragraph("• <b>AS-REP Roasting:</b> Targets user accounts with pre-authentication disabled (<code>DONT_REQ_PREAUTH</code>). Attackers request an AS-REP ticket without knowing the password and crack the timestamp offline.", bullet_style))
    story.append(Paragraph("• <b>Kerberoasting:</b> Any domain user requests a TGS ticket for accounts with Service Principal Names (SPNs). The ticket is encrypted with the service account password hash, crackable offline with Hashcat.", bullet_style))
    story.append(Paragraph("• <b>Unconstrained & Constrained Delegation:</b> Allows web servers to impersonate users to back-end databases. If compromised, unconstrained servers capture and cache complete user TGTs.", bullet_style))
    story.append(Spacer(1, 5))

    callout_data = [[Paragraph("<b>Key Mitigation:</b> Migrate all service accounts to Group Managed Service Accounts (gMSA) with 120-character random passwords, enforce Kerberos AES-128/256, and add high-privilege users to the Protected Users security group.", callout_style)]]
    callout_table = Table(callout_data, colWidths=[500])
    callout_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EBF4FF")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#0077B6")),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(callout_table)
    story.append(Spacer(1, 15))

    # ------------------ MODULE 5 ------------------
    story.append(Paragraph("Module 5: Privilege Escalation & Domain Dominance", h1_style))
    story.append(Paragraph("<b>1. Advanced Escalation Mechanisms:</b>", body_style))
    story.append(Paragraph("• <b>ACL Exploitation:</b> Abuse of <code>GenericAll</code>, <code>WriteDacl</code>, or <code>ForceChangePassword</code> rights over groups or users.", bullet_style))
    story.append(Paragraph("• <b>DCSync (MS-DRSR Replication):</b> Emulates a DC using Directory Replication Service Remote Protocol to request password hashes for any account (including <code>krbtgt</code>) without running code on the DC.", bullet_style))
    story.append(Paragraph("• <b>Golden & Silver Tickets:</b> Forging Kerberos TGTs using the master <code>krbtgt</code> key, granting unrestricted domain access with arbitrary group memberships.", bullet_style))
    story.append(Spacer(1, 15))

    # ------------------ MODULE 6 ------------------
    story.append(Paragraph("Module 6: Enterprise Defense, Detection Engineering & Tiering", h1_style))
    story.append(Paragraph("<b>1. The Enterprise Access Model:</b> Microsoft's three-tier model prevents credential crossover:", body_style))
    story.append(Paragraph("• <b>Tier 0 (Control Plane):</b> Domain Controllers, PKI, ADFS, Domain Admins. Managed strictly via dedicated Privileged Access Workstations (PAWs).", bullet_style))
    story.append(Paragraph("• <b>Tier 1 (Server Plane):</b> Application servers, database servers, hypervisors.", bullet_style))
    story.append(Paragraph("• <b>Tier 2 (Workstation Plane):</b> Standard endpoints and daily user accounts.", bullet_style))
    story.append(Spacer(1, 8))

    ev_data = [
        ["Event ID", "Meaning", "Security Relevance"],
        ["4624", "Successful Logon", "Track Logon Type 3 (Network) and 10 (Remote Desktop)"],
        ["4625", "Failed Logon", "Critical for detecting password spraying and brute force"],
        ["4768", "TGT Request", "Monitor AS-REQ exchanges for anomalous user activity"],
        ["4769", "Service Ticket Request", "Detect Kerberoasting via RC4 encryption downgrade (0x17)"],
        ["4662", "Directory Access", "Detect DCSync replication from non-DC IP addresses"]
    ]
    ev_table = Table(ev_data, colWidths=[65, 145, 290])
    ev_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#03045E")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8.5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CED4DA")),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(ev_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"🎉 PDF successfully compiled at: {PDF_PATH}")

if __name__ == "__main__":
    build_pdf()
