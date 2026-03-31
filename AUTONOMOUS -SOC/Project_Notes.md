# Project Notes — Autonomous Cloud SOC & Threat Intelligence System
**Khushbu Jalan | DAE Cybersecurity Program | Semester 1 — Month 1**
**Date:** 31 March 2026 | **Repo:** `autonomous-cloud-soc`

---

## Table of Contents
1. [What This Project Actually Is — My Understanding](#1-what-this-project-actually-is)
2. [The Full SOC Pipeline — Explained in Plain English](#2-the-full-soc-pipeline)
3. [Tech Stack Breakdown](#3-tech-stack-breakdown)
4. [Architecture — How the Pieces Connect](#4-architecture-how-the-pieces-connect)
5. [Rubric 1 — Complete Analysis (R1a to R1d)](#5-rubric-1-complete-analysis)
6. [Rubric 2 — Complete Analysis (R2a to R2e)](#6-rubric-2-complete-analysis)
7. [Semester 1 vs Semester 2 — What Gets Done When](#7-semester-1-vs-semester-2)
8. [Key Risks & How to Avoid Breaking Things](#8-key-risks)
9. [Evidence File Master List](#9-evidence-file-master-list)

---

## 1. What This Project Actually Is

In my own words: I am building a **completely free, fully automated security guard** for a computer hosted in Oracle Cloud. The "guard" watches for people trying to hack in by guessing passwords, figures out whether the attacker is a known bad actor using a public database, and then automatically tells the cloud firewall to block that attacker — all without me needing to do anything manually. Every attack attempt gets logged and displayed on a live dashboard.

The project serves two purposes at once:

- **For the DAE rubric:** It gives me a real, working system to demonstrate every concept the rubric asks about — encryption, incident response, vulnerability scanning, threat intelligence, risk management, and security monitoring.
- **For a portfolio:** It shows any future employer that I built a functional enterprise-grade SOC from scratch at zero cost, which is genuinely impressive in the industry.

**The key constraint for Semester 1:** The courses I am taking right now (Network Security 1, Cybersecurity Basics 1, Cyber Threats and Vulnerabilities 1) are foundational. The program expects me to learn concepts and document plans this semester, not to have a fully live attack-testing pipeline. That means:

- Written reports, scripts, and documented plans = **Semester 1 deliverables**
- Live Wazuh deployment with real agent data, live honeypot attack testing, full n8n automation = **Semester 2**

This distinction is critical. If I try to do live Wazuh agent testing in Week 2, I am getting ahead of myself and I will run out of time for the actual rubric documents.

---

## 2. The Full SOC Pipeline

### The Story of One Attack — From First Packet to Blocked IP

Here is exactly what happens when someone tries to break into the Windows Honeypot, explained as a story:

---

### Stage 1 — The Honeypot: Setting the Trap

A **Windows Server VM** is deployed on Oracle Cloud (or a local VirtualBox VM for Semester 1 testing). The critical configuration is that **RDP port 3389 is deliberately left open to the public internet**. This sounds dangerous, and it is — that is the point. Hackers worldwide run automated scanners that look for open port 3389, and when they find it, they immediately start trying to log in by guessing common username/password combinations. This is called a **brute-force attack** or **credential stuffing**.

Every failed login attempt on Windows gets written to the Windows Security Event Log as **Event ID 4625**. Think of this like a paper notebook that automatically writes down "Someone tried to unlock the door and failed" every time it happens. The Windows machine becomes the "bait" — the honeypot.

---

### Stage 2 — Wazuh SIEM: The Security Guard Reading the Log Book

**Wazuh** is a Security Information and Event Management (SIEM) platform. It runs on the main Oracle Cloud Linux VM (the "SOC brain"). A small Wazuh **agent** is installed on the Windows Honeypot — this agent reads the Windows Event Log continuously and ships every Event ID 4625 entry to the Wazuh **Manager** over an encrypted connection.

The Wazuh Manager applies **detection rules**. The custom rule I define says: *"If I see 5 or more Event ID 4625 entries from the same source IP address within 60 seconds, create a HIGH severity alert at Level 10."* This threshold means normal mistyped passwords don't trigger anything, but an automated bot hammering the machine at high speed immediately trips the alarm.

When the threshold is hit, Wazuh generates a structured alert JSON object containing: the attacker's IP address, the timestamp, the number of failures, the alert level, and the affected username. This alert is stored in the **Wazuh Indexer** (which is an OpenSearch database) and displayed on the **Wazuh Dashboard**.

Wazuh also does **File Integrity Monitoring (FIM)** — it watches `C:\Windows\System32` and alerts if any system files are modified, which would indicate the attacker got in and is trying to install malware.

---

### Stage 3 — The Integration Script: Passing the Baton

When Wazuh generates a Level 10 alert, it runs a custom **Python integration script** I write. This script extracts the attacker's IP address from the alert JSON and sends it as an HTTP POST request (a "webhook") to n8n's webhook URL. Think of this as Wazuh calling n8n on a phone and saying "Hey, I've got a suspicious IP for you to investigate."

The Python script lives at `scripts/wazuh_to_n8n.py` in my GitHub repo. It is called by Wazuh via the `ossec.conf` integration configuration.

---

### Stage 4 — AbuseIPDB: The Background Check

Before taking any action, my system does a **background check on the attacker's IP address** using the AbuseIPDB API. AbuseIPDB is a free public database where security researchers from around the world report malicious IP addresses. Every reported IP gets an **Abuse Confidence Score from 0 to 100%**.

- 0% = clean, never seen doing anything malicious
- 50%+ = suspicious, some reports of abuse
- 75%+ = high confidence this IP is actively malicious (usually automated botnets)

My n8n workflow sends an HTTP GET request to `https://api.abuseipdb.com/api/v2/check?ipAddress=[IP]` and reads back the score. This step serves two purposes: (1) it prevents false positives from blocking legitimate users who mistyped their password a few times, and (2) it adds a layer of **threat intelligence** that shows I am enriching alerts with external data, not just reacting to raw numbers.

---

### Stage 5 — n8n SOAR: The Decision-Maker and Automator

**n8n** is a Security Orchestration, Automation and Response (SOAR) platform. It runs on the same OCI Linux VM as a Docker container. The workflow I build in n8n has exactly 5 nodes:

**Node 1 — Webhook:** Receives the IP address from the Wazuh Python script. This is the entry point.

**Node 2 — Whitelist Check:** Before anything else, checks whether the incoming IP matches my own home/office IP address. This is the most critical safety step in the entire project. If I accidentally blocked my own IP, I would lock myself out of my cloud server permanently. This node hard-codes my public IP and immediately stops processing if there is a match.

**Node 3 — AbuseIPDB HTTP Request:** Calls the AbuseIPDB API and retrieves the confidence score for the attacker's IP.

**Node 4 — IF Logic Gate:** Evaluates the score. If `abuseConfidenceScore > 50`, proceed to block. If ≤50, log it but take no automatic action (this protects against false positives).

**Node 5 — OCI API Update NSG:** Calls the Oracle Cloud API to add a new **DENY rule** to the Network Security Group (NSG) attached to the Windows Honeypot VM. Once this rule is in place, OCI's firewall drops all packets from that IP before they even reach the VM. The attacker is now completely blocked at the cloud infrastructure level.

The entire pipeline from Wazuh alert to OCI block should complete in under 30 seconds. This is one of the measurable KPIs for the project.

---

### Stage 6 — Grafana Dashboard: Making It Visual

**Grafana** is a data visualisation platform. It connects to the Wazuh Indexer (OpenSearch database) as a data source and queries the stored alert data to produce live visualisations. My planned dashboard has 4 panels:

- **World Attack Map (Geomap panel):** Plots each attacker's IP as a dot on a world map, coloured by threat severity. This is the "wow factor" visual that immediately shows where attacks are coming from geographically.
- **Total Alerts Today (Stat panel):** A single large number showing how many HIGH alerts have been triggered in the last 24 hours.
- **Top 10 Attacking IPs (Table panel):** A ranked table of the IP addresses that have generated the most alerts, with their country of origin and AbuseIPDB score.
- **Alerts by Severity (Bar chart):** A breakdown of alerts by Wazuh severity level over time, showing attack patterns.

---

### The Complete Data Flow — One Line Summary

```
Windows Honeypot (Event ID 4625 × 5)
  → Wazuh Agent (ships log)
  → Wazuh Manager (evaluates rule → Level 10 alert)
  → Python Integration Script (extracts IP → HTTP POST)
  → n8n Webhook (receives IP)
  → n8n Whitelist Check (is this my own IP?)
  → n8n AbuseIPDB Request (GET confidence score)
  → n8n IF Node (score > 50%?)
  → n8n OCI API Call (add DENY rule to NSG)
  → OCI Firewall (drops all packets from attacker IP)
  → Grafana Dashboard (visualises everything in real time)
```

**Target latency:** Event ID 4625 on Windows → Wazuh alert: **< 10 seconds**
**Target remediation:** Wazuh alert → IP blocked in OCI: **< 30 seconds**
**Target cost:** Monthly OCI billing: **$0.00**

---

## 3. Tech Stack Breakdown

### Oracle Cloud Infrastructure (OCI) — The Hosting Platform

Oracle's "Always Free" tier is genuinely free forever, not just a free trial. The key resource is the **A1 Ampere instance** — an ARM-based virtual machine with:
- 4 OCPUs (ARM cores, very efficient)
- 24 GB RAM (critical — Wazuh's indexer needs significant memory)
- 200 GB block storage
- A public IP address

Everything runs on this one VM via Docker containers. This is how I keep the cost at $0.

**Key OCI components used:**
- **VCN (Virtual Cloud Network):** The private network inside OCI. Like a virtual router.
- **Subnet:** A segment of the VCN where the VM lives.
- **Internet Gateway (IGW):** Allows traffic to flow in and out of the VCN.
- **Security List / Network Security Group (NSG):** The cloud firewall. I control which ports are open and which IPs can connect. The n8n automation writes DENY rules here.
- **API Key:** Used by n8n to authenticate against the OCI API when calling the NSG update endpoint.

**Memory management:** Wazuh's Indexer (OpenSearch) is memory-hungry. Even on 24 GB RAM, I configure a 4 GB swap file to handle spikes without crashing.

### Wazuh — The SIEM

Wazuh is an open-source SIEM platform. The full stack runs as three Docker containers managed by Docker Compose:
- `wazuh-manager`: The brain. Receives logs from agents, evaluates rules, generates alerts.
- `wazuh-indexer`: An OpenSearch database that stores all the alert data.
- `wazuh-dashboard`: A web UI (on port 443) for viewing alerts, FIM results, and agent status.

**Key concepts to understand:**
- `ossec.conf`: The main Wazuh configuration file. Controls which logs are collected, what integrations run, and retention settings.
- **Alert levels 1–15:** 1 = informational noise, 10 = high severity (my brute-force threshold), 15 = critical.
- **Custom rules XML:** The format for writing detection logic. My brute-force rule lives here.
- **14-day log retention:** Configured in the indexer to prevent the 200 GB disk from filling up.

### n8n — The SOAR

n8n is a no-code/low-code workflow automation tool. The Community Edition has no usage limits, making it perfect for this project. It runs as a Docker container on the OCI VM and is accessible on port 5678 (restricted to my IP only).

### OpenCTI — The Threat Intelligence Platform

OpenCTI is an open-source threat intelligence platform. I deploy it via Docker Compose on the OCI VM (port 8080). It stores and manages **Indicators of Compromise (IoCs)** — things like malicious IP addresses, file hashes, and domain names that indicate an attack has happened or is happening.

Two connectors I configure:
- **MITRE ATT&CK connector:** Automatically imports the entire ATT&CK knowledge base into OpenCTI, so I can link IoCs to known attack techniques.
- **AbuseIPDB connector:** Enriches IP address observables with reputation data from AbuseIPDB.

### Grafana — Visualisation

Grafana is an open-source analytics and monitoring platform. It connects to Wazuh's OpenSearch database as a data source and renders the attack dashboard. Runs as a Docker container on port 3000.

### Kali Linux — Red Team Tools

Kali Linux is a security-focused Linux distribution that comes pre-installed with hundreds of security testing tools. I run it in VirtualBox on my local machine. For this project I use:
- **SET (Social Engineering Toolkit):** For the R2a phishing template demonstration.
- **Nmap:** For the R2b vulnerability assessment scan.

---

## 4. Architecture — How the Pieces Connect

```
┌─────────────────────────────────────────────────────────────┐
│                  ORACLE CLOUD (Always Free)                  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  A1 Ampere VM (Ubuntu 22.04) — 4 OCPUs / 24 GB RAM  │  │
│  │                                                       │  │
│  │  ┌─────────────┐  ┌──────────┐  ┌───────────────┐   │  │
│  │  │   Wazuh     │  │   n8n    │  │   OpenCTI     │   │  │
│  │  │  Manager    │  │  :5678   │  │    :8080      │   │  │
│  │  │  Indexer    │  │  SOAR    │  │  Threat Intel │   │  │
│  │  │  Dashboard  │  │ Workflow │  │  Platform     │   │  │
│  │  │   :443      │  └──────────┘  └───────────────┘   │  │
│  │  └──────┬──────┘       │                             │  │
│  │         │    Alert     │  OCI API call               │  │
│  │         ▼    webhook   ▼  (add DENY rule)            │  │
│  │  ┌─────────────┐  ┌────────────────────────────────┐ │  │
│  │  │  Grafana    │  │  OCI Network Security Group    │ │  │
│  │  │  :3000      │  │  (Cloud Firewall Rules)        │ │  │
│  │  │  Dashboard  │  └────────────────────────────────┘ │  │
│  │  └─────────────┘                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────┐                              │
│  │  Windows Server VM       │  ← Port 3389 open to         │
│  │  (Honeypot)              │    public internet            │
│  │  Wazuh Agent installed   │                              │
│  │  Event ID 4625 logged    │                              │
│  └──────────────────────────┘                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          ▲
                Attackers from the internet
                (automated bots trying RDP)
```

**Port map (what I must allow in OCI Security List — from MY IP only):**

| Port | Protocol | Service |
|------|----------|---------|
| 22 | TCP | SSH — admin access to Linux VM |
| 443 | TCP | Wazuh Dashboard HTTPS |
| 5678 | TCP | n8n workflow UI |
| 3000 | TCP | Grafana Dashboard |
| 8080 | TCP | OpenCTI |
| 3389 | TCP | Windows Honeypot RDP — open to ALL (intentional) |
| 1514 | UDP/TCP | Wazuh agent communication (internal Docker network only) |

---

## 5. Rubric 1 — Complete Analysis

---

### R1a — Create an Incident Response Plan

**What the rubric asks for:**
> An incident response plan with: at least 1 method for detecting security incidents, 1 containment strategy, steps for eradication and recovery, and identification + explanation of at least 1 cyber attack type (Malware, Phishing, Ransomware, or Denial of Service).

**What I need to submit:**
A Word document (`docs/R1a_IRP.docx`) structured as a formal Incident Response Plan. It must have clearly labelled sections for Detection, Containment, Eradication, and Recovery. I must explain one specific attack type in enough detail to show I understand it.

**What "Complete" looks like:**

- **Attack type identified:** Brute-Force Credential Stuffing. Explanation covers: what it is (automated guessing of username/password pairs using leaked credential databases), why it is dangerous (compromises valid user accounts without any malware), and how it relates to my project (this is exactly what the honeypot is designed to attract).
- **Phase 1 — DETECT:** The Wazuh SIEM monitors Windows Event ID 4625 (failed login). When ≥5 failures from one IP occur within 60 seconds, Wazuh generates a Level 10 HIGH alert. Target detection time: < 10 seconds from first failed login to alert.
- **Phase 2 — CONTAIN:** n8n receives the webhook from Wazuh, queries AbuseIPDB to validate the threat, and (if score > 50%) calls the OCI API to add a DENY rule in the Network Security Group. The attacker's IP is now blocked at the cloud firewall level. Target containment time: < 30 seconds from alert to block.
- **Phase 3 — ERADICATE:** After blocking, review the Wazuh dashboard for evidence of lateral movement (did the attacker get in before being blocked?). Check FIM alerts for any file system changes. If a breach occurred, restore the Windows VM from a clean boot volume snapshot.
- **Phase 4 — RECOVER:** Review the NSG DENY rule after 24 hours. If confirmed as a false positive, remove the block. Update custom Wazuh detection rules based on lessons learned. Log the incident in the incident register.

**Important note for my document:** This is a PLANNED incident response procedure for a system I am building. It is not yet live. I should note in the document that Phases 2 and 3 will be tested live in Semester 2 when Wazuh agents are deployed on the Windows Honeypot.

**Can this be done in Semester 1?** **YES.** This is a written planning document. I am describing what the system *will* do, not running it live. The rubric says "outlines" and "detailing steps" — it wants a plan, not a live demonstration.

---

### R1b — Develop a Comprehensive Security Policy

**What the rubric asks for:**
> A security policy document with: at least 3 key security rules/guidelines, an incident response plan section, and an explanation of how policies maintain the CIA Triad.

**What I need to submit:**
A Word document (`docs/R1b_Security_Policy.docx`) structured as a formal Security Policy. It needs exactly 3 numbered security rules, a reference to or summary of the IRP, and a dedicated section explaining how the policies enforce Confidentiality, Integrity, and Availability.

**What "Complete" looks like:**

**Rule 1 — Access Control Policy:**
All management ports (SSH 22, Wazuh 443, n8n 5678, Grafana 3000, OpenCTI 8080) are restricted to my authorised IP address via OCI Security Lists. No management interface is ever exposed to the public internet. Access requires SSH key authentication — password authentication is disabled on the Linux VM.

**Rule 2 — Log Retention Policy:**
All security events ingested by Wazuh are retained for a minimum of 14 days in the Wazuh Indexer. After 14 days, logs are automatically pruned to prevent the 200 GB storage from filling up. This 14-day window is sufficient to investigate any incident that may not be immediately noticed.

**Rule 3 — Encryption Policy:**
All data in transit between Wazuh agents and the manager uses TLS encryption. The Wazuh Dashboard is served over HTTPS (port 443) with a valid SSL certificate. Sensitive credentials (API keys for OCI and AbuseIPDB) are stored as environment variables in Docker Compose `.env` files, never hardcoded in scripts or committed to GitHub. Passwords are stored as SHA-256 hashes.

**CIA Triad section:**
- **Confidentiality:** The OCI Network Security Group and Security Lists enforce strict access control. Only my authorised IP address can reach management interfaces. All in-transit data is encrypted via TLS. AbuseIPDB and OCI API keys are stored as environment variables, never in source code.
- **Integrity:** Wazuh File Integrity Monitoring (FIM) continuously monitors the Windows Honeypot's `C:\Windows\System32` directory. Any unauthorised file creation, modification, or deletion triggers an immediate alert. This ensures that if an attacker bypasses the brute-force detection and gets into the system, any malicious file changes are detected.
- **Availability:** The autonomous nature of the SOC ensures that threat detection and response continue 24/7 without requiring manual intervention. The automated n8n blocking workflow means attackers are contained even while I am not monitoring the dashboard. The OCI A1 instance with 4 GB swap file is sized to handle Wazuh's memory requirements without crashing.

**Can this be done in Semester 1?** **YES.** This is a purely written policy document. Nothing about it requires a live system.

---

### R1c — Apply Encryption Techniques

**What the rubric asks for:**
> Show an encrypted text and its corresponding decrypted plaintext using AES. Show text hashed with SHA (MD5 or SHA).

**What I need to submit:**
A Python script (`scripts/encrypt_demo.py`) that runs and produces visible output, plus a screenshot of that output (`evidence/R1c_encryption_screenshot.png`).

**What "Complete" looks like:**

The script must demonstrate all four steps in sequence:
1. A plaintext string (e.g., `"My secret SOC password: Hunter2"`)
2. The AES-256-CBC encrypted ciphertext (shown as a hex string — it should look like random characters)
3. The decrypted text — must exactly match the original plaintext, proving the encryption was reversible
4. The SHA-256 hash of the original plaintext (64-character hex string)

The screenshot must show the terminal with all four lines of output clearly visible. The script uses the `pycryptodome` Python library (`pip install pycryptodome`).

**Key concepts the rubric is testing:**
- AES-256 = Advanced Encryption Standard with a 256-bit key. This is the same encryption standard used by governments and banks for top-secret data. The "-CBC" means Cipher Block Chaining — each block of data is XOR'd with the previous block before encryption, making the output more secure.
- SHA-256 = Secure Hash Algorithm producing a 256-bit (64 hex character) output. It is a **one-way function** — you can hash a password and store the hash, but you cannot reverse the hash to get the password back. This is why websites store password hashes, not passwords.

**Can this be done in Semester 1?** **YES.** This is a standalone Python script with no dependency on any cloud infrastructure. It runs entirely on my local machine.

---

### R1d — Demonstrate Legal and Ethical Compliance

**What the rubric asks for:**
> A section in the IRP explaining: at least 2 relevant laws or regulations, at least 1 ethical consideration, and how the plan upholds these legal requirements and ethical principles.

**What I need to submit:**
This is an additional **Section 5** added to my existing `docs/R1a_IRP.docx`. It does not need to be a separate document.

**What "Complete" looks like:**

**Law 1 — Computer Fraud and Abuse Act (CFAA), 18 U.S.C. § 1030:**
The CFAA is the primary U.S. federal law governing computer crime. It makes it a federal offence to access a computer "without authorisation" or to "exceed authorised access." My incident response plan upholds the CFAA because: (1) every system I monitor — the OCI Linux VM and the Windows Honeypot — is infrastructure I personally own and control on my own Oracle Cloud account. I have full legal authorisation to monitor, scan, and test it. (2) My Nmap vulnerability scans are run against `scanme.nmap.org` (Nmap's explicitly authorised practice target) or against my own OCI VM. I will never run scans against external systems I do not own. (3) The n8n automation blocks attackers on infrastructure I control — it does not attempt any counter-attack or access the attacker's systems.

**Law 2 — General Data Protection Regulation (GDPR), Article 33:**
GDPR Article 33 requires that organisations notify the relevant supervisory authority of a personal data breach within 72 hours of becoming aware of it. While my honeypot project does not store personal user data, the principle applies to any real-world deployment scenario. My IRP upholds this requirement because: the detection pipeline (Wazuh → n8n) is designed to generate alerts within seconds of a breach event, far within the 72-hour notification window. In a real deployment, this would give the organisation ample time to assess the breach, prepare a notification, and contact the relevant authority well before the legal deadline.

**Ethical Consideration:**
The honeypot I am deploying on my own OCI infrastructure is a deliberate trap designed to attract attackers. This raises an important ethical question: is it acceptable to lure attackers into a system specifically to observe their behaviour? My conclusion is that this is ethical because: (1) the honeypot is hosted entirely within my own cloud account — I am not putting anyone else's systems at risk. (2) I am not "entrapment" in any legal sense — the honeypot does not induce anyone to commit a crime. Attackers choose to probe port 3389 of their own initiative. (3) The automatic blocking response does not involve any counter-attack against the attacker's machine — it simply stops them from accessing my system. (4) Any genuine attacker data (IP addresses, attack patterns) collected should be treated responsibly — it could be contributed to threat intelligence feeds like AbuseIPDB to help the broader security community, but should never be used to identify or harm individuals.

**Can this be done in Semester 1?** **YES.** This is a written legal/ethical analysis section. No live system required.

---

## 6. Rubric 2 — Complete Analysis

---

### R2a — Identify and Analyze Cyber Threats

**What the rubric asks for:**
> Analysis of a malware sample using VirusTotal or Any.Run. Creation of 1 phishing template using SET (Social Engineering Toolkit) in Kali Linux. Mapping of 1 real APT campaign to MITRE ATT&CK.

**What I need to submit:**
Three separate evidence files plus one consolidated report document.

**What "Complete" looks like:**

**Part A — Malware Analysis with VirusTotal:**
- Go to `virustotal.com`
- Search for this hash: `44d88612fea8a8f36de82e1278abb02f`
- This is the **EICAR test file** — an industry-standard harmless test file that every antivirus engine detects as a "virus" for testing purposes. It is completely safe but will show a high detection ratio.
- Take a screenshot of the results page showing: detection ratio (e.g., 58/72 engines detect it), the threat label names, and the file type.
- In the report, write: what the file is, what "detection ratio" means, what "behavioral indicators" it would show in a sandbox, and what the potential impact would be if this were a real malware sample.
- Save screenshot as `evidence/R2a_VirusTotal_screenshot.png`

**Part B — Phishing Template with SET:**
- Open the Kali VM
- Run: `sudo setoolkit`
- Navigate: 1 (Social-Engineering Attacks) → 2 (Website Attack Vectors) → 3 (Credential Harvester Attack Method) → 2 (Site Cloner)
- Enter a target URL to clone — use `http://testphp.vulnweb.com` (an intentionally vulnerable demo site)
- SET will create a fake copy of that login page running locally on the Kali VM
- Take a screenshot showing the cloned login page and the SET terminal output
- In the report, explain: what a credential harvester does, how a real attacker would use this (e.g., sending a phishing email with a link to this fake page), and how to defend against it (user awareness training, multi-factor authentication, email filtering).
- Save screenshot as `evidence/R2a_SET_screenshot.png`
- **IMPORTANT:** Run this entirely within the VirtualBox VM. Never use SET against real websites.

**Part C — APT Campaign Mapping to MITRE ATT&CK:**
- Go to `attack.mitre.org` → Groups → APT29 (also known as Cozy Bear, the Russian state-sponsored group that conducted the SolarWinds attack)
- Open the ATT&CK Navigator: `mitre-attack.github.io/attack-navigator`
- Create a new layer, search for APT29, and highlight these three techniques:
  - **T1078** — Valid Accounts (using stolen credentials)
  - **T1021.001** — Remote Desktop Protocol (RDP brute force — directly relevant to my project)
  - **T1110** — Brute Force (the core attack my SOC is designed to detect)
- Export the layer as JSON → save as `evidence/R2a_MITRE_APT29.json`
- In the report, explain what APT29 is, what these three techniques mean in practice, and why they are relevant to my SOC project.

**Final deliverable:** `docs/R2a_Threat_Analysis.docx` with three sections (Malware Analysis, Phishing Template, APT29 ATT&CK Mapping), each with the corresponding evidence screenshot embedded or referenced.

**Can this be done in Semester 1?** **YES** — VirusTotal works in a browser, SET runs in Kali VM on my local laptop, ATT&CK Navigator runs in a browser. No OCI infrastructure required.

---

### R2b — Apply Vulnerability Assessment Techniques

**What the rubric asks for:**
> 1 vulnerability scan with Nmap or OpenVAS (config, findings, classification). 1 asset discovery scan documenting discovered systems, services, critical assets, and basic network map. All with methodology and security implications.

**What I need to submit:**
A real Nmap scan output file plus a comprehensive planning document.

**What "Complete" looks like:**

**The practice scan (what I actually run in Semester 1):**
```bash
nmap -sV -O scanme.nmap.org -oN evidence/R2b_practice_scan.txt
```
- `-sV` = probe open ports to determine service/version
- `-O` = attempt to identify the operating system
- `scanme.nmap.org` = Nmap's own server, explicitly authorised for scanning practice
- `-oN` = save output in human-readable text format

This produces real Nmap output that I paste into the planning document and analyse.

**`docs/R2b_Vulnerability_Assessment_Plan.docx` must contain:**

*Section 1 — What is a Vulnerability Scan?*
Definition, purpose, difference between a port scan and a vulnerability scan, why organisations run regular scans.

*Section 2 — Nmap Command Reference for Honeypot Assessment*
Every command I plan to run on the Windows Honeypot in Semester 2, with a full explanation of each flag and what information it provides.

*Section 3 — Port Risk Classification*
Port 3389 (RDP) = CRITICAL — deliberately open, primary attack vector for the project
Port 22 (SSH) = HIGH — restricted to my IP only via Security List, but must monitor
Port 445 (SMB) = CRITICAL if open — often exploited for lateral movement
Port 3389 being open and internet-facing is the intentional design of the honeypot, but in any real environment this would be flagged as a critical finding requiring immediate remediation.

*Section 4 — Asset Discovery Template*
A documented template for recording: discovered IP addresses, open ports per IP, identified services and version numbers, operating system guesses, and risk classification of each open port.

*Section 5 — Analysis of Practice Scan Results*
Paste the actual output from `nmap -sV -O scanme.nmap.org` and write a full analysis: which ports were found open, what services are running, what the OS detection shows, what a real attacker could learn from this information, and what the security implications are.

**Can this be done in Semester 1?** **YES** — Nmap runs in Kali VM, the practice scan targets an authorised server. The vulnerability assessment of the actual Windows Honeypot is deferred to Semester 2 when the honeypot is live, but the planning document and practice scan are fully achievable now.

---

### R2c — Implement Threat Intelligence Principles

**What the rubric asks for:**
> Analysis of 2 IoCs with detection methods and how they indicate threats. Deployment of OpenCTI using Docker or system install. Configuration of at least 2 connectors. Documentation of platform setup and connector integration. Basic usage demonstration.

**What I need to submit:**
A running OpenCTI instance (deployed on OCI VM), 4 screenshots proving it works, and brief documentation.

**What "Complete" looks like:**

**The OpenCTI deployment:**
SSH into the OCI VM → create `~/opencti/` directory → download docker-compose.yml from OpenCTI docs → create `.env` file with admin credentials and a generated UUID token → `docker-compose up -d` → wait 15 minutes for all services to start → open port 8080 in OCI Security List → navigate to `http://[OCI_IP]:8080` in browser → login with admin credentials.

**2 Connectors to configure:**

*Connector 1 — MITRE ATT&CK:*
Settings → Connectors → search for MITRE ATT&CK → Enable it. This connector automatically imports the entire MITRE ATT&CK knowledge base (all tactics, techniques, groups, and software) into OpenCTI. Once running, it shows a status of "Active" or "Running."
Screenshot: Settings page showing MITRE ATT&CK connector with Active/Running status.

*Connector 2 — AbuseIPDB:*
Settings → Connectors → search for AbuseIPDB → Configure → enter my AbuseIPDB API key → Enable. This connector allows OpenCTI to enrich IP address observables with AbuseIPDB reputation data.
Screenshot: Settings page showing AbuseIPDB connector with Active/Running status.

**2 IoCs to create:**

*IoC 1 — Malicious IP Address:*
Analysis → Observables → + Create → Observable Type: IPv4 Address → enter a known bad IP from AbuseIPDB's "Most Reported" list (e.g., a known Mirai botnet node) → add Labels: "Brute-Force" and "Malicious" → Save.
In the documentation, explain: an IP address IoC tells security teams to watch for any connection attempts from this address. It indicates this host has been reported performing malicious activity. Detection method: compare all inbound connection logs against a blocklist of known malicious IPs — this is exactly what my n8n AbuseIPDB check does in real time.

*IoC 2 — Malicious File Hash:*
Analysis → Observables → + Create → Observable Type: File SHA256 → enter `44d88612fea8a8f36de82e1278abb02f` (the EICAR test hash from R2a) → Labels: "Malware" and "EICAR-Test" → Save.
In the documentation, explain: a file hash IoC tells security teams that if this exact file is ever found on a system, it is malicious. Detection method: Wazuh's File Integrity Monitoring compares SHA256 hashes of all monitored files against known malicious hashes — any match triggers an immediate alert.

**Screenshots needed (4 total):**
1. `evidence/R2c_mitre_connector.png` — MITRE ATT&CK connector showing Active/Running
2. `evidence/R2c_abuseipdb_connector.png` — AbuseIPDB connector showing Active/Running
3. `evidence/R2c_ioc1_ip.png` — IPv4 IoC visible in OpenCTI Observables
4. `evidence/R2c_ioc2_hash.png` — SHA256 hash IoC visible in OpenCTI Observables

**Can this be done in Semester 1?** **YES** — but it requires the OCI VM to be provisioned first (Week 2 task). OpenCTI deployment is scheduled for Week 3. The OCI VM setup is feasible in Semester 1 since it is just VM provisioning, not live security testing.

---

### R2d — Develop and Apply Risk Management Strategies

**What the rubric asks for:**
> Identification of 2 critical risks from vulnerability scan results, with explanations, treatment recommendations, and mitigation steps. 1 risk monitoring procedure showing how to track identified risks.

**What I need to submit:**
Two Word documents: a Risk Register and a Monitoring SOP.

**What "Complete" looks like:**

**`docs/R2d_Risk_Register.docx` — must contain a formal risk register table with these fields for each risk:**
- Risk ID, Risk Name, Description, Related MITRE ATT&CK Technique
- Likelihood (Low / Medium / High), Impact (Low / Medium / High / Critical)
- Inherent Risk Level (= Likelihood × Impact), Treatment Recommendation
- Mitigation Steps (specific and technical), Residual Risk Level (after mitigation)

**Critical Risk 1 — Open RDP Port 3389 Exposed to Internet**

This risk is directly visible from a Nmap scan: `3389/tcp open ms-wbt-server Microsoft Terminal Services`. Port 3389 being open and accessible from the internet is the single highest risk finding from a vulnerability assessment perspective.

- **MITRE ATT&CK Technique:** T1021.001 — Remote Desktop Protocol
- **Likelihood:** HIGH — automated bots continuously scan the internet for open port 3389. Within hours of being live, the honeypot receives real attack attempts.
- **Impact:** CRITICAL — successful RDP login gives an attacker full interactive control of the Windows VM, equivalent to sitting at the keyboard.
- **Inherent Risk Level:** CRITICAL
- **Treatment Recommendation:** Mitigate (we cannot simply close port 3389 as it is the honeypot's purpose — instead we layer detection and automated response around it)
- **Mitigation Steps:** (1) Deploy Wazuh agent to collect Event ID 4625 in real time. (2) Configure brute-force detection rule: 5 failures/60s = Level 10 alert. (3) n8n automation blocks attacking IP via OCI NSG within 30 seconds. (4) Restrict RDP access to specific IPs for legitimate admin access using the Whitelist node in n8n.
- **Residual Risk Level:** LOW (automated detection and blocking significantly reduces the window of exposure)

**Critical Risk 2 — Weak or Absent Multi-Factor Authentication on RDP**

Even when a brute-force threshold is set, a highly targeted attacker using a known valid username with a very slow, low-volume attack (e.g., 1 attempt per hour) would not trigger the 5-in-60-seconds rule.

- **MITRE ATT&CK Technique:** T1110 — Brute Force
- **Likelihood:** HIGH — brute-force is the dominant attack method against internet-exposed RDP endpoints
- **Impact:** HIGH — successful authentication grants full system access
- **Inherent Risk Level:** HIGH
- **Treatment Recommendation:** Mitigate
- **Mitigation Steps:** (1) In a production environment, enforce MFA on all RDP connections. (2) Implement account lockout policy: lock account after 10 failed attempts. (3) Use Wazuh to also alert on abnormally long patterns of low-frequency failures (e.g., more than 20 failures from same IP over 24 hours). (4) Use strong, randomly generated passwords for all accounts on the honeypot.
- **Residual Risk Level:** LOW

**`docs/R2d_Monitoring_SOP.docx` — the risk monitoring procedure:**

*Daily:* Login to Wazuh Dashboard → check "Security Alerts" view for any Level 10+ alerts generated since last check → verify n8n is running and webhook is active → confirm no new IPs have been added to OCI NSG Deny List unexpectedly.

*Weekly:* Review OCI NSG Deny List — how many IPs have been blocked this week? → Check Wazuh disk usage: confirm `wazuh-indexer` volume is below 80% of 200 GB → Review n8n workflow error logs for any failed webhook calls or API errors → Review Grafana dashboard for trend changes in attack volume.

*Monthly:* Re-run Nmap scan against the Windows Honeypot to confirm only expected ports are open and no new unexpected services have started → Update the Risk Register: review whether risk levels have changed based on observed attack patterns → Review the 14-day log retention setting against current storage usage → Check for Wazuh and n8n Docker image updates and schedule patching.

**Can this be done in Semester 1?** **YES** — both documents are pure research and planning deliverables. The risks are based on the documented architecture of my project, not on live scan results. I reference Nmap findings from the practice scan on `scanme.nmap.org` and the known design of the honeypot to justify the risk assessments.

---

### R2e — Implement Security Monitoring and Incident Response

**What the rubric asks for:**
> Basic security monitoring setup with 1 use case (detection rules, alert prioritization, response procedures). 1 incident response scenario (incident classification, response steps, lessons learned). Evidence of functionality and clear documentation.

**What I need to submit:**
Two Word documents: a Security Monitoring Use Case and a simulated IR Scenario.

**What "Complete" looks like:**

**`docs/R2e_Use_Case.docx` — Security Monitoring Use Case:**

*Use Case Name:* Brute-Force Attack Detection and Automated Containment

*Detection Rule Design:*
Rule trigger: ≥5 occurrences of Windows Event ID 4625 from the same source IP within a 60-second sliding window.
Rule logic: Wazuh Manager evaluates this using its frequency-based rules (`<frequency>5</frequency><timeframe>60</timeframe>` in the custom rules XML). When the condition is met, a Level 10 HIGH alert is generated containing: source IP, timestamp, number of attempts, target username, and affected system.

*Alert Prioritisation Process:*

| Alert Level | Severity | Response Time | Action |
|-------------|----------|--------------|--------|
| Level 10–15 | HIGH / CRITICAL | Immediate — automated | n8n auto-block via OCI NSG |
| Level 7–9 | Medium-High | Review within 1 hour | Manual investigation of Wazuh dashboard |
| Level 4–6 | Medium | Review within 24 hours | Log analysis during next daily check |
| Level 1–3 | Low | Weekly review | Include in weekly trend report |

*Step-by-Step Response Procedure:*
1. Wazuh Manager detects ≥5 Event ID 4625 from source IP `185.x.x.x` in 60 seconds
2. Wazuh generates Level 10 alert → stored in Wazuh Indexer → visible on Wazuh Dashboard
3. Wazuh executes integration script: `scripts/wazuh_to_n8n.py` → sends IP to n8n webhook via HTTP POST
4. n8n Whitelist Check: is `185.x.x.x` my authorised IP? No → continue
5. n8n AbuseIPDB Check: GET `api.abuseipdb.com/api/v2/check?ipAddress=185.x.x.x` → returns `abuseConfidenceScore: 94`
6. n8n IF node: `94 > 50` = TRUE → proceed to block
7. n8n OCI API Call: PUT request to OCI NSG API → adds DENY rule for `185.x.x.x`
8. OCI firewall confirms rule applied → all future packets from `185.x.x.x` are dropped
9. Grafana dashboard auto-updates: blocked IP appears on attack map, total blocked count increments

**`docs/R2e_IR_Scenario.docx` — Simulated Incident Response Scenario:**

*Incident Classification:* Brute-Force / Credential Stuffing Attack — Severity: HIGH

*Simulated Timeline (all times and IPs are fictional for this document):*

```
T + 0s    Attacker IP 185.220.101.47 begins RDP brute force against Honeypot VM
           Windows Security Log records first Event ID 4625

T + 8s    5th failed login recorded. Wazuh rule threshold met.
           Wazuh Manager generates Level 10 HIGH alert.
           Alert stored in Wazuh Indexer (OpenSearch).

T + 9s    Wazuh executes wazuh_to_n8n.py integration script.
           HTTP POST sent to n8n webhook: {"ip": "185.220.101.47", "count": 5}

T + 11s   n8n Webhook node receives POST.
           Whitelist check: 185.220.101.47 ≠ my authorised IP. Continue.

T + 13s   n8n HTTP Request node: GET https://api.abuseipdb.com/api/v2/check?ipAddress=185.220.101.47
           Response: {"abuseConfidenceScore": 94, "countryCode": "DE", "totalReports": 847}

T + 15s   n8n IF node evaluates: 94 > 50 = TRUE. Proceed to block.

T + 17s   n8n OCI API node: PUT request to OCI NSG endpoint.
           Adds Ingress rule: DENY TCP 3389 from 185.220.101.47/32

T + 19s   OCI confirms rule applied. Attacker's packets now dropped at cloud firewall.
           All subsequent connection attempts from 185.220.101.47 fail silently.

T + 22s   Grafana dashboard auto-refreshes. World map dot appears over Germany.
           "Total Blocked Today" stat increments to 1.

T + 60s   Security analyst (me) logs into Wazuh Dashboard during next check.
           Reviews alert. Confirms legitimate block — AbuseIPDB shows 847 prior reports.
           No evidence of successful login (no Event ID 4624 in logs).
           No FIM alerts — no file system changes detected.

T + 24h   Daily review: NSG rule still in place. No further attempts from this IP.
           Rule retained. Incident closed.
```

*Lessons Learned:*
1. The automated detection-to-block pipeline performed within the 30-second target (actual: 19 seconds)
2. AbuseIPDB enrichment correctly identified a known malicious IP with 847 prior reports — the IF node threshold of 50% is appropriately calibrated
3. No false positive risk in this case (high confidence score + no successful login events)
4. Future improvement: add a Slack/email notification node in n8n to alert me when a block is triggered, even when I am not actively monitoring the dashboard

**Can this be done in Semester 1?** **YES** — the Use Case document is a design specification. The IR Scenario is explicitly SIMULATED with a fictional timeline and fictional IP addresses. This is research-based documentation, not a live test. The rubric says "document 1 incident response scenario" — it does not require the scenario to have actually happened.

---

## 7. Semester 1 vs Semester 2 — What Gets Done When

### Semester 1 (Now — Months 1–4): Research, Documents, Tool Setup

Everything achievable without a live agent-monitored Windows Honeypot generating real attack data:

| Rubric Item | Deliverable Type | S1 Achievable? |
|-------------|-----------------|----------------|
| R1c — Encryption | Python script + screenshot | ✅ YES — runs on local machine |
| R2a — Threat Analysis | VirusTotal + SET demo + ATT&CK | ✅ YES — browser + Kali VM |
| R1a — IRP | Written plan document | ✅ YES — research/plan |
| R1b — Security Policy | Written policy document | ✅ YES — research/plan |
| R1d — Legal & Ethical | Written compliance section | ✅ YES — research/plan |
| R2b — Vulnerability Assessment | Nmap plan + practice scan | ✅ YES — scan authorised target |
| R2c — Threat Intel / OpenCTI | Deploy OpenCTI on OCI VM + connectors | ✅ YES — needs OCI VM |
| R2d — Risk Management | Risk Register + SOP | ✅ YES — research/plan |
| R2e — Security Monitoring | Use Case doc + simulated IR | ✅ YES — simulation acceptable |

### Semester 2 (Months 5–8): Live Deployment, Real Testing, Full Automation

The "live" elements that require real agents, real attacks, and real pipeline testing:

- Deploy Wazuh agents on Windows Honeypot → collect real Event ID 4625 data
- Deploy Windows Honeypot with RDP open → attract real internet scanners
- Test the full Wazuh → n8n → OCI block pipeline with a real simulated attack
- Measure actual detection latency (target: < 10 seconds)
- Measure actual remediation time (target: < 30 seconds)
- Build Grafana world attack map with live data
- Test the n8n whitelist safety net (verify I cannot block my own IP)
- Deploy File Integrity Monitoring rules and test FIM alerts
- Configure log retention and monitor disk usage over time

---

## 8. Key Risks

### Self-Lockout (CRITICAL — Read This Carefully)

If the n8n automation blocks my own IP address, I will be permanently locked out of my OCI VM. There is no "back door" — the firewall rule would prevent my SSH connection, my Wazuh Dashboard, my n8n interface, and everything else. **The fix:** Node 2 of the n8n workflow must always check the incoming IP against my home/office public IP before proceeding. To find my public IP: go to `whatismyip.com` and note the IPv4 address. Hard-code this into the n8n whitelist node as an exact match condition. Test this by running the workflow with my own IP first — it must stop at the whitelist check with zero OCI API calls.

### OCI "Out of Capacity" Errors

The Always Free ARM (A1 Ampere) instances are extremely popular and heavily oversubscribed in certain regions (particularly US East and US West). When provisioning the A1 VM, I may encounter an error: `Out of capacity for shape VM.Standard.A1.Flex`. **The fix:** Try at different times of day (early morning tends to have more capacity available), try a different OCI region (UK South or Australia East are less congested), or retry the same region multiple times over several days. This is a known issue in the Oracle Cloud community and patience is the primary mitigation.

### Wazuh Memory Spikes

Wazuh's Indexer (OpenSearch) can consume more memory than available RAM during indexing spikes, causing the container to crash. On a 24 GB RAM instance this should be manageable, but the 4 GB swap file is essential insurance. **Configure the swap file before deploying Wazuh** — it is much harder to add later.

### Oracle "Idle Instance" Deletion

Oracle Cloud has a policy where VMs in Always Free accounts that show zero CPU activity for an extended period may be flagged for deletion. **The fix:** Keep the Windows Honeypot active (having port 3389 open to the internet means it will receive constant connection attempts, which registers as CPU activity). Export n8n workflow JSONs to GitHub weekly so that if the VM is ever reclaimed, the automation logic is not lost.

### Storage Bloat

With port 3389 open to the internet, the Windows Honeypot will receive thousands of failed login attempts per day. Each Event ID 4625 entry gets shipped to Wazuh and stored in the Indexer. Without a retention policy, the 200 GB disk can fill up within weeks. **The fix:** Configure the Wazuh Indexer's Index Lifecycle Management (ILM) to automatically delete indices older than 14 days. Set up a disk usage alert in Grafana to notify when usage exceeds 80%.

---

## 9. Evidence File Master List

This table lists every file that needs to exist in the GitHub repository by the end of Month 1 (Week 4 validation).

| File Path | Rubric | Week | What It Proves |
|-----------|--------|------|----------------|
| `scripts/encrypt_demo.py` | R1c | Wk 1 | AES-256 + SHA-256 working Python script |
| `evidence/R1c_encryption_screenshot.png` | R1c | Wk 1 | Terminal showing all 4 output lines |
| `evidence/R2a_VirusTotal_screenshot.png` | R2a | Wk 1 | EICAR hash detection results on VirusTotal |
| `evidence/R2a_SET_screenshot.png` | R2a | Wk 1 | SET phishing page running in Kali VM |
| `evidence/R2a_MITRE_APT29.json` | R2a | Wk 1 | ATT&CK Navigator layer export |
| `docs/R2a_Threat_Analysis.docx` | R2a | Wk 1 | 3-section threat analysis report |
| `docs/R1a_IRP.docx` | R1a + R1d | Wk 2 | Incident Response Plan with Legal section |
| `docs/R1b_Security_Policy.docx` | R1b | Wk 2 | Security Policy with 3 rules + CIA Triad |
| `evidence/R2b_practice_scan.txt` | R2b | Wk 2 | Real Nmap output from scanme.nmap.org |
| `docs/R2b_Vulnerability_Assessment_Plan.docx` | R2b | Wk 2 | Full plan + practice scan analysis |
| `evidence/R2c_mitre_connector.png` | R2c | Wk 3 | MITRE ATT&CK connector Active in OpenCTI |
| `evidence/R2c_abuseipdb_connector.png` | R2c | Wk 3 | AbuseIPDB connector Active in OpenCTI |
| `evidence/R2c_ioc1_ip.png` | R2c | Wk 3 | IPv4 IoC in OpenCTI Observables |
| `evidence/R2c_ioc2_hash.png` | R2c | Wk 3 | SHA256 IoC in OpenCTI Observables |
| `docs/R2d_Risk_Register.docx` | R2d | Wk 3 | Risk register with 2 critical risks |
| `docs/R2d_Monitoring_SOP.docx` | R2d | Wk 3 | Daily/weekly/monthly monitoring SOP |
| `docs/R2e_Use_Case.docx` | R2e | Wk 4 | Security monitoring use case |
| `docs/R2e_IR_Scenario.docx` | R2e | Wk 4 | Simulated IR scenario with timeline |
| `evidence/Evidence_Index.md` | All | Wk 4 | Master index mapping files to rubrics |
| `evidence/KPI_zero_cost.png` | KPI | Wk 4 | OCI billing showing $0.00 |
| `research/Project_Notes.md` | Reference | Wk 1 | This document |
| `research/Tool_Overview.md` | Reference | Wk 1 | Wazuh / n8n / Grafana overview |
| `research/Threat_Research_Notes.md` | Reference | Wk 1 | Brute-force, malware, phishing concepts |
| `research/Wazuh_Deep_Dive.md` | Reference | Wk 2 | Full Wazuh data path + custom rule XML |
| `research/Wazuh_Docker_Plan.md` | Reference | Wk 3 | Full planned docker-compose.yml |
| `research/n8n_Workflow_Plan.md` | Reference | Wk 4 | 5-node workflow plan + JSON structure |
| `research/Grafana_Dashboard_Plan.md` | Reference | Wk 4 | 4-panel dashboard plan with queries |
| `configs/oci_setup_notes.md` | Reference | Wk 2 | Tenancy OCID, region, fingerprint (NO .pem) |
| `DAE_SOC_Semester1_Evidence.zip` | Delivery | Wk 4 | ZIP of all docs + evidence + scripts |

**GitHub Tags to create:**
- `week2` — after Week 2 commit (66% rubric complete)
- `week3` — after Week 3 commit (77% rubric complete)
- `v1.0` — after Week 4 final commit (100% complete, Month 1 done)

---

*Document created: 31 March 2026*
*Repository: `autonomous-cloud-soc`*
*Branch: `main`*
*Next commit message: `Initial project notes and architecture documentation`*
