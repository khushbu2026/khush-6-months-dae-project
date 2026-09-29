# Evidence Index — Autonomous Cloud SOC
## Khushbu Jalan | DAE Cybersecurity Program | Semester 1

**Repo:** `khushbu2026/khush-6-months-dae-project`  
**Last Updated:** April 2026  
**Status:** Semester 1 — Research, Planning & Simulated Evidence

> All documents in this index are Semester 1 deliverables: structured research plans, methodology documents, and simulated/practice evidence. Live deployment, real honeypot testing, and automated pipeline validation are Semester 2 scope.

---

## RUBRIC 1 — Deliverables

### R1a — Create an Incident Response Plan

| File | Description | Rubric Items Satisfied |
|---|---|---|
| `docs/R1a_IRP.docx` | Full Incident Response Plan covering 4 attack types: RDP Brute-Force, Ransomware, Phishing, DoS/DDoS | Detection method, Containment strategy, Eradication & Recovery steps, Attack type explanation |

**Rubric checklist:**
- [x] At least 1 method for detecting security incidents (Wazuh Event ID 4625 correlation)
- [x] At least 1 containment strategy (n8n automated IP block via firewall rule)
- [x] Eradication and recovery steps (all 4 incident types covered)
- [x] Identifies and explains at least 1 cyber attack type (Brute-Force, Ransomware, Phishing, DoS)

---

### R1b — Develop a Comprehensive Security Policy

| File | Description | Rubric Items Satisfied |
|---|---|---|
| `docs/R1b_Security_Policy.docx` | Security Policy with 5 CIA Triad-mapped rules | 3+ security rules, incident response steps, CIA Triad explanation |

**Rubric checklist:**
- [x] At least 3 key security rules/guidelines (5 rules covering authentication, encryption, access control, logging, patching)
- [x] Incident response plan detailing breach response steps
- [x] CIA Triad section explaining how policies maintain Confidentiality, Integrity, Availability

---

### R1c — Apply Encryption Techniques

| File | Description | Rubric Items Satisfied |
|---|---|---|
| `scripts/encrypt_demo.py` | Python script demonstrating AES-256 encryption/decryption and SHA-256 hashing | AES encryption demo, SHA hashing demo |
| `evidence/R1c_encryption_screenshot.png` | Terminal screenshot showing encrypted ciphertext and decrypted plaintext output | Evidence of functionality |

**Rubric checklist:**
- [x] Encrypted text shown (AES-256 CBC mode ciphertext)
- [x] Corresponding decrypted plaintext shown
- [x] Text hashed with standard hashing function (SHA-256)

---

### R1d — Demonstrate Legal and Ethical Compliance

| File | Description | Rubric Items Satisfied |
|---|---|---|
| `docs/R1a_IRP.docx` — **Section 5** | Legal & Ethical Compliance section embedded in IRP document | CFAA, GDPR Articles 33/34, honeypot ethical justification |

**Rubric checklist:**
- [x] At least 2 relevant laws identified (CFAA 18 U.S.C. § 1030 + GDPR Articles 33/34)
- [x] At least 1 ethical consideration discussed (responsible honeypot use, no counter-attacks, data minimisation)
- [x] Explanation of how the plan upholds legal requirements

---

## RUBRIC 2 — Deliverables

### R2a — Identify and Analyze Cyber Threats

| File | Description | Rubric Items Satisfied |
|---|---|---|
| `docs/R2a_Threat_Analysis.docx` | Full cyber threat analysis document | Malware analysis, phishing template methodology, APT29 MITRE ATT&CK mapping |
| `evidence/R2a_virustotal_eicar.png` | VirusTotal screenshot — EICAR test hash detection results | Malware sample analysis evidence |
| `evidence/R2a_set_phishing_template.png` | SET (Social Engineering Toolkit) credential harvester walkthrough | Phishing template creation evidence |
| `evidence/R2a_apt29_mitre_mapping.png` | APT29 MITRE ATT&CK technique mapping (30+ techniques, G0016) | APT campaign MITRE mapping evidence |

**Rubric checklist:**
- [x] Malware sample analysis using VirusTotal (EICAR hash — MD5: 44d88612fea8a8f36de82e1278abb02f)
- [x] Detection results documented (VirusTotal engine detections)
- [x] Behavioral indicators documented
- [x] Potential impact documented
- [x] 1 phishing template created using SET in Kali Linux
- [x] 1 real APT campaign mapped to MITRE ATT&CK (APT29 / Cozy Bear — G0016)

---

### R2b — Apply Vulnerability Assessment Techniques

| File | Description | Rubric Items Satisfied |
|---|---|---|
| `docs/R2b_Vulnerability_Assessment.docx` | Full vulnerability assessment report — Nmap methodology, scan results, network map | Vulnerability scan, asset discovery, network mapping, security implications |
| `evidence/R2b_scan1_scanme_output.txt` | Raw Nmap output — vulnerability scan of scanme.nmap.org *(Semester 2 — live capture)* | Scan output evidence |
| `evidence/R2b_scan2a_host_discovery.txt` | Raw Nmap output — UTM network host discovery *(Semester 2 — live capture)* | Asset discovery evidence |
| `evidence/R2b_scan2b_full_ports.txt` | Raw Nmap output — Windows Honeypot full port scan *(Semester 2 — live capture)* | Full port scan evidence |
| `evidence/R2b_nmap_screenshot.png` | Screenshot of Nmap scan running in Kali Linux terminal *(Semester 2 — live capture)* | Tool usage evidence |

**Rubric checklist:**
- [x] 1 vulnerability scan using Nmap (scanme.nmap.org — authorised public test host)
- [x] Scan configuration documented (flags: -sS -sV -sC --script vuln -T4)
- [x] Summary of findings documented (Apache EOL, CVE-2021-41617, EternalBlue SMBv1)
- [x] Vulnerability classification included (CVSS v3.1 + CIA Triad impact)
- [x] 1 asset discovery scan documented (UTM internal network 192.168.64.0/24)
- [x] Discovered systems and services documented (3 hosts, 5 ports on honeypot)
- [x] Critical asset identification included (WIN-HONEYPOT-01 = CRITICAL)
- [x] Basic network mapping included (ASCII topology diagram + port/service table)

---

### R2c — Implement Threat Intelligence Principles

| File | Description | Rubric Items Satisfied |
|---|---|---|
| `docs/R2c_OpenCTI_ThreatIntel.docx` | Written document explaining OpenCTI platform, 2 IoC analyses, connector configuration plan | IoC analysis, OpenCTI platform documentation, connector integration |
| `evidence/R2c_ioc1_analysis.png` | IoC 1 analysis — IP address indicator *(screenshot of analysis)* | IoC detection evidence |
| `evidence/R2c_ioc2_analysis.png` | IoC 2 analysis — File hash indicator *(screenshot of analysis)* | IoC detection evidence |
| `evidence/R2c_opencti_platform.png` | OpenCTI platform setup documentation *(architecture diagram or written plan)* | Platform documentation |
| `evidence/R2c_opencti_connectors.png` | OpenCTI connector configuration (MITRE ATT&CK + AbuseIPDB connectors) *(documentation)* | Connector integration evidence |

> **Note:** OpenCTI live deployment was not completed in Semester 1 due to resource constraints. The written document covers platform architecture, IoC methodology, and connector configuration as a planning deliverable. Live deployment is scheduled for Semester 2.

**Rubric checklist:**
- [x] Analysis of 2 IoCs with detection methods documented
- [x] Explanation of how IoCs indicate threats
- [x] OpenCTI platform documented (setup approach, connector plan)
- [x] At least 2 connectors documented (MITRE ATT&CK connector + AbuseIPDB connector)

---

### R2d — Develop and Apply Risk Management Strategies

| File | Description | Rubric Items Satisfied |
|---|---|---|
| `docs/R2d_Risk_Register.docx` | Risk register with risks identified from vulnerability scan — 2+ critical risks with treatment recommendations | Risk identification, critical risks, treatment recommendations, mitigation steps |
| `docs/R2d_Monitoring_SOP.docx` | Risk monitoring procedure — Standard Operating Procedure for tracking identified risks | Risk monitoring procedure |

> **Note:** R2d documents are in progress — to be completed and uploaded. Risks feed directly from R2b vulnerability scan findings (EternalBlue/SMBv1 and RDP brute-force as the 2 critical risks).

**Rubric checklist:**
- [ ] Identification of risks from vulnerability scan results *(pending upload)*
- [ ] 2 critical risks with explanations *(pending upload)*
- [ ] Treatment recommendations documented *(pending upload)*
- [ ] Basic mitigation steps included *(pending upload)*
- [ ] 1 risk monitoring procedure created *(pending upload)*

---

### R2e — Implement Security Monitoring and Incident Response

| File | Description | Rubric Items Satisfied |
|---|---|---|
| `docs/R2e_Security_Monitoring.docx` | Full security monitoring and incident response document — Wazuh use case + IRS-01 scenario | Detection rules, alert prioritisation, response procedures, incident classification, lessons learned |
| `evidence/R2e_wazuh_running.png` | Docker Desktop screenshot — Wazuh containers running *(Semester 1 local setup)* | Evidence of monitoring setup |
| `evidence/R2e_wazuh_rule_100100.xml` | Custom Wazuh detection rule — brute-force correlation (Rule 100100) | Detection rule evidence |
| `evidence/R2e_n8n_workflow.json` | Exported n8n SOAR workflow JSON | Response automation evidence |
| `evidence/R2e_grafana_dashboard.png` | Grafana dashboard screenshot with alert panels | Dashboard evidence |
| `evidence/R2e_brute_force_alert.png` | Live Wazuh alert — Rule 100100 fired *(Semester 2 — live capture)* | Live detection evidence |
| `evidence/R2e_ip_block_log.txt` | n8n execution log — IP block action triggered *(Semester 2 — live capture)* | Automated response evidence |

**Rubric checklist:**
- [x] Setup of basic security monitoring documented (Wazuh + n8n + Grafana)
- [x] 1 use case with detection rules (UC-01 — RDP brute-force, Rule 100100)
- [x] Alert prioritisation process documented (Levels 1–15 response tiers)
- [x] Response procedures documented (7-step n8n SOAR workflow)
- [x] Evidence of functionality included
- [x] 1 incident response scenario documented (IRS-01-2026 — RDP brute-force)
- [x] Incident classification included (HIGH, T1110, T1021.001)
- [x] Response steps taken documented (all 6 PICERL phases)
- [x] Lessons learned documented (5 lessons with improvement actions)

---

## Full File Inventory

```
khush-6-months-dae-project/
├── docs/
│   ├── R1a_IRP.docx                          → R1a + R1d
│   ├── R1b_Security_Policy.docx              → R1b
│   ├── R2a_Threat_Analysis.docx              → R2a
│   ├── R2b_Vulnerability_Assessment.docx     → R2b
│   ├── R2c_OpenCTI_ThreatIntel.docx          → R2c
│   ├── R2d_Risk_Register.docx                → R2d
│   ├── R2d_Monitoring_SOP.docx               → R2d
│   └── R2e_Security_Monitoring.docx          → R2e
├── scripts/
│   └── encrypt_demo.py                       → R1c
└── evidence/
    ├── R1c_encryption_screenshot.png         → R1c
    ├── R2a_virustotal_eicar.png              → R2a
    ├── R2a_set_phishing_template.png         → R2a
    ├── R2a_apt29_mitre_mapping.png           → R2a
    ├── R2b_scan1_scanme_output.txt           → R2b  [Semester 2]
    ├── R2b_scan2a_host_discovery.txt         → R2b  [Semester 2]
    ├── R2b_scan2b_full_ports.txt             → R2b  [Semester 2]
    ├── R2b_nmap_screenshot.png               → R2b  [Semester 2]
    ├── R2c_ioc1_analysis.png                 → R2c
    ├── R2c_ioc2_analysis.png                 → R2c
    ├── R2c_opencti_platform.png              → R2c
    ├── R2c_opencti_connectors.png            → R2c
    ├── R2e_wazuh_running.png                 → R2e
    ├── R2e_wazuh_rule_100100.xml             → R2e
    ├── R2e_n8n_workflow.json                 → R2e
    ├── R2e_grafana_dashboard.png             → R2e
    ├── R2e_brute_force_alert.png             → R2e  [Semester 2]
    ├── R2e_ip_block_log.txt                  → R2e  [Semester 2]
    └── Evidence_Index.md                     → All rubrics
```

---

## Rubric Completion Status

| Rubric | Title | Status |
|---|---|---|
| R1a | Create an Incident Response Plan | ✅ Complete |
| R1b | Develop a Comprehensive Security Policy | ✅ Complete |
| R1c | Apply Encryption Techniques | ✅ Complete |
| R1d | Demonstrate Legal and Ethical Compliance | ✅ Complete (embedded in R1a Section 5) |
| R2a | Identify and Analyze Cyber Threats | ✅ Complete |
| R2b | Apply Vulnerability Assessment Techniques | ✅ Complete |
| R2c | Implement Threat Intelligence Principles | ✅ Complete (written plan — live deployment Semester 2) |
| R2d | Develop and Apply Risk Management Strategies | 🔄 In Progress |
| R2e | Implement Security Monitoring and Incident Response | ✅ Complete |

---

*Generated: April 2026 | docs/evidence/Evidence_Index.md*
