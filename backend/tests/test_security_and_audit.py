"""
LedgerGuard AI — Automated Security & Forensic Audit Test Suite
10-vector verification matrix ensuring bank-grade defense and high-precision fraud detection.
"""

import pytest
import io
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)

def test_01_security_headers_enforced():
    """Vector 1: OWASP Defense Headers Presence."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert "default-src 'self'" in response.headers.get("Content-Security-Policy", "")

def test_02_health_diagnostics():
    """Vector 2: System Health and Environmental Readiness."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["system"] == "LedgerGuard AI"

def test_03_empty_file_rejected():
    """Vector 3: Zero-Byte Upload Defense (HTTP 400)."""
    files = {"file": ("empty.pdf", b"", "application/pdf")}
    response = client.post("/api/audit/upload", files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()

def test_04_disallowed_extension_rejected():
    """Vector 4: Malicious Executable Extension Rejection (.sh / .exe)."""
    files = {"file": ("malicious_script.sh", b"echo 'hack'", "text/x-sh")}
    response = client.post("/api/audit/upload", files=files)
    assert response.status_code == 400
    assert "unsupported file extension" in response.json()["detail"].lower()

def test_05_fake_pdf_magic_byte_rejected():
    """Vector 5: Disguised File Extension Bypass (Non-%PDF binary headers)."""
    fake_pdf_content = b"This is plain text pretending to be a PDF."
    files = {"file": ("fake_invoice.pdf", fake_pdf_content, "application/pdf")}
    response = client.post("/api/audit/upload", files=files)
    assert response.status_code == 400
    assert "signature mismatch" in response.json()["detail"].lower()

def test_06_vendor_vault_initialization():
    """Vector 6: Seeded Vendor Vault Retrieval."""
    response = client.get("/api/vendors/")
    assert response.status_code == 200
    vendors = response.json()
    assert len(vendors) >= 3
    vendor_names = [v["vendor_name"] for v in vendors]
    assert "CloudScale Networks Inc." in vendor_names

def test_07_math_mismatch_detection():
    """Vector 7: Line Item & Tax Calculation Discrepancy Flagging."""
    inconsistent_invoice = """
    Invoice #INV-9021
    Date: 2026-09-01
    Vendor: General Supply Co.
    Subtotal: $1,000.00
    Tax: $100.00
    Total: $1,450.00
    Account: 883920194
    """
    response = client.post("/api/audit/quick-scan", json={"raw_text": inconsistent_invoice})
    assert response.status_code == 200
    data = response.json()
    assert data["math_verified"] is False
    flag_categories = [f["category"] for f in data["forensic_flags"]]
    assert "MATH_DISCREPANCY" in flag_categories

def test_08_critical_wire_fraud_bank_mismatch():
    """Vector 8: BEC / Altered Vendor Bank Account Red Alert."""
    # CloudScale Networks Inc. has authorized account '9842109482'.
    # Here, invoice specifies rogue account '1112223334'.
    spoofed_invoice = """
    CloudScale Networks Inc.
    Invoice #CS-4402
    Date: 2026-09-10
    Total: $12,500.00
    Subtotal: $12,500.00
    Tax: $0.00
    Bank Name: Fraudulent Off-Shore Bank
    Account Number: 1112223334
    Routing: 021000021
    """
    response = client.post("/api/audit/quick-scan", json={"raw_text": spoofed_invoice, "vendor_name_hint": "CloudScale Networks Inc."})
    assert response.status_code == 200
    data = response.json()
    assert data["vendor_known"] is True
    assert data["bank_details_matched"] is False
    assert data["risk_level"] == "CRITICAL_FRAUD"
    assert data["risk_score"] >= 80

def test_09_billing_sandbox_checkout():
    """Vector 9: Commercial Subscription Checkout Creation."""
    payload = {
        "tier": "pro",
        "success_url": "http://localhost:5173/success",
        "cancel_url": "http://localhost:5173/cancel"
    }
    response = client.post("/api/billing/create-checkout-session", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "checkout_url" in data
    assert data["tier"] == "pro"

def test_10_sliding_rate_limiter_burst():
    """Vector 10: Financial DoS Burst Request Throttling (HTTP 429)."""
    hit_429 = False
    for _ in range(25):
        resp = client.post("/api/audit/quick-scan", json={"raw_text": "Sample valid invoice text 1234567890"})
        if resp.status_code == 429:
            hit_429 = True
            break
    assert hit_429 is True
