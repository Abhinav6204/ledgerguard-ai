# 🛡️ LedgerGuard AI — Enterprise Invoice Fraud & Wire Defense Platform

[![License: Proprietary](https://img.shields.io/badge/License-Proprietary%20All%20Rights%20Reserved-red.svg)](./LICENSE)
[![Security: OWASP Fortified](https://img.shields.io/badge/Security-OWASP%20Hardened-blue.svg)](#security-audit--fortification-matrix)
[![Tests: 10/10 Passed](https://img.shields.io/badge/Audit%20Tests-10%2F10%20Passed-brightgreen.svg)](#automated-security-test-matrix)
[![FastAPI: 0.115+](https://img.shields.io/badge/Backend-FastAPI%20%7C%20Python%203.13-009688.svg)](https://fastapi.tiangolo.com)
[![Frontend: React 18 + Vite](https://img.shields.io/badge/Frontend-React%2018%20%7C%20Vite-61dafb.svg)](https://reactjs.org)

> **Automated Accounts Payable Defense Platform designed to prevent Business Email Compromise (BEC), forged PDF invoices, altered vendor bank routing numbers, and unauthorized wire disbursements.**

---

## 1. Executive Summary & Market Problem

According to the FBI Internet Crime Report, **Business Email Compromise (BEC) and vendor payment redirect fraud cost organizations over $2.9 Billion annually**.

### The Vulnerability
Attackers compromise or spoof vendor email accounts and send legitimate-looking PDF invoices where **only the bank account number has been altered by a single digit**. Accounts Payable clerks unwittingly release electronic funds transfers (EFT/ACH/Wire) to offshore mule accounts. Once wired, the capital is irretrievable.

### The Solution: LedgerGuard AI
LedgerGuard AI sits between incoming vendor documents and your treasury payment pipeline:
1. **Instant Ingestion**: Parses PDFs, images, and raw text in a bounded memory sandbox.
2. **Vendor Vault Cross-Check**: Automatically verifies bank coordinates (Account, Routing, IBAN, SWIFT) against an encrypted company registry. If an invoice claims to be from a trusted vendor but requests payment to a new bank, a **CRITICAL WIRE FRAUD RED ALERT** is fired.
3. **Mathematical Balance Audit**: Reconciles individual line items, quantities, unit prices, sales tax, and grand totals, flagging hidden surcharges and rounding discrepancies.
4. **Graphic Manipulation & Metadata Forensics**: Detects if a PDF was forged or altered in Adobe Photoshop, Canva, or PDFedit rather than originating from enterprise billing systems (QuickBooks, NetSuite, SAP, Xero).
5. **Dual-Engine AI Reasoning**: Synthesizes high-speed Groq LLaMA-3.3-70B and Google Gemini inference with deterministic fallback to produce an executive forensic verdict in under 200ms.

---

## 2. System Architecture Blueprint

```
                     +--------------------------------------------+
                     |         VENDOR INVOICE INGESTION           |
                     |     (PDF, Image, Scanned Paper, Text)      |
                     +--------------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                           SECURITY-HARDENED GATEWAY                               |
|   • OWASP Security Headers (CSP, HSTS, nosniff, DENY)                             |
|   • Sliding-Window Rate Limiter (Burst & Sustained Flooding Defense)              |
|   • Binary Magic Byte Verification (%PDF, PNG, JPG)                               |
|   • Path Traversal & ReDoS Neutralization                                         |
+-----------------------------------------------------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                        PARSING & METADATA EXTRACTION                              |
|   • Bounded PyPDF Decompression Bomb Protection (Max 20 pages / 200k chars)       |
|   • Financial Entities Extractor (Invoice #, Date, Due Date, Amounts)             |
|   • Banking Coordinate Extraction (ABA Routing, IBAN Mod-97, SWIFT, Account)      |
+-----------------------------------------------------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                     MULTI-VECTOR DETERMINISTIC FORENSICS                          |
|  [Math Auditor]          [Vendor Vault Validator]       [Metadata Forensics]      |
|  • Line items vs Total   • Cross-checks against Vault   • Detects Photoshop/Canva |
|  • Tax calculation check • ABA Routing Checksum (mod10) • Post-export mod trails  |
|  • Negative sum sanity   • IBAN Checksum (ISO 7064)     • Urgency pressure words  |
+-----------------------------------------------------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                     DUAL-ENGINE AI FORENSIC REASONING                             |
|   • Primary: Groq LLaMA-3.3-70B (Sub-second adversarial reasoning)                |
|   • Secondary: Google Gemini 1.5 Flash (Deep semantic fraud synthesis)           |
|   • Fallback: Deterministic Local Forensic Engine (Zero API Dependency)          |
+-----------------------------------------------------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                        STARK-FINTECH COCKPIT & ACTIONS                            |
|   • Dynamic 0-100 Risk Score & Telemetry Meters                                   |
|   • Split-Screen Live PDF Review & Extracted Metadata Cards                       |
|   • 1-Click Forensic Certificate Download (JSON / Audit Trail)                   |
|   • Automated Stripe SaaS Subscription Gateway ($29/mo Pro, $99/mo Enterprise)    |
+-----------------------------------------------------------------------------------+
```

---

## 3. Automated Security Test Matrix (10/10 Verified)

The comprehensive automated test suite at `backend/tests/test_security_and_audit.py` validates all 10 security vectors:

```text
[TEST 01] Security Headers Enforced (nosniff, DENY, XSS, CSP, Cache-Control) .... [PASS]
[TEST 02] Health Diagnostics & Environmental Readiness .......................... [PASS]
[TEST 03] Zero-Byte Upload Defense (HTTP 400 Empty File Rejection) ............... [PASS]
[TEST 04] Malicious Executable Extension Rejection (.sh / .exe -> HTTP 400) ...... [PASS]
[TEST 05] Disguised File Extension Bypass (Non-%PDF binary headers -> HTTP 400) . [PASS]
[TEST 06] Seeded Vendor Vault Retrieval & Initial Integrity ..................... [PASS]
[TEST 07] Line Item & Tax Calculation Discrepancy Flagging (MATH_DISCREPANCY) ... [PASS]
[TEST 08] BEC / Altered Vendor Bank Account Red Alert (CRITICAL_FRAUD 100/100) .. [PASS]
[TEST 09] Commercial Subscription Checkout Creation (Stripe Sandbox) ............ [PASS]
[TEST 10] Financial DoS Burst Request Throttling (HTTP 429 Too Many Requests) .... [PASS]
-----------------------------------------------------------------------------------------
RESULTS: 10 passed in 4.19s (100% SUCCESS)
```

---

## 4. Quickstart Guide (Under 60 Seconds)

### Option A: The One-Command Launcher (Recommended)
Simply execute the master launcher from the project root:
```bash
./run.sh
```
This automatically initializes the Python virtual environment, installs backend and frontend dependencies, runs the security test suite, and launches both services:
* **Frontend Cockpit**: `http://localhost:5173`
* **Backend API Docs**: `http://localhost:8000/docs`

### Option B: Hardened Docker Container
```bash
docker compose up --build
```
Runs as an unprivileged security user (`ledgerguard`) with dropped capabilities and healthcheck probes.

---

## 5. Commercial SaaS Monetization & Acquisition Strategy

LedgerGuard AI is engineered as a high-ticket B2B FinTech software asset:

| Monetization Model | Target Market | Price Point | Expected Cashflow |
| :--- | :--- | :--- | :--- |
| **SaaS Subscription (Self-Serve)** | Accounting Firms, Law Offices, SMBs | **$29 / month** (Pro)<br>**$99 / month** (Team) | $1,500 – $5,000 / month recurring |
| **Turnkey Source Code Sale** | CodeCanyon / Gumroad | **$49 – $99 / copy** | $1,000 – $3,000 passive income |
| **Direct B2B White-Label** | Regional Logistics & FinTech Startups | **$1,500 – $3,500** per custom deployment | Instant lump-sum cash |
| **Micro-SaaS Startup Exit** | **Acquire.com / Flippa** | **$5,000 – $25,000+** | Full-asset acquisition |

---

## 6. Intellectual Property & Commercial License

**Copyright (c) 2026 Abhinav. All Rights Reserved.**

This platform and its associated source code, algorithms, schemas, and user interfaces are proprietary and confidential. This repository is maintained as a commercial-grade asset prepared for B2B licensing, SaaS monetization, and startup acquisition.

Unauthorized reproduction, distribution, public hosting, or commercial use is strictly prohibited. For commercial licensing, acquisition, or buyout inquiries, contact the author. See [`LICENSE`](./LICENSE) for full legal terms.
