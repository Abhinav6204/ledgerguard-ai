"""
LedgerGuard AI — Vendor Vault & Audit Storage Database
SQLite-backed persistent repository for authorized vendor banking profiles and forensic audit trails.
"""

import sqlite3
import os
import json
import uuid
from typing import List, Optional, Dict, Any
from app.config import settings

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "ledgerguard.db")

def get_db_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema and seeds initial trusted vendors."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Vendor Bank Vault Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vendor_vault (
        id TEXT PRIMARY KEY,
        vendor_name TEXT UNIQUE NOT NULL,
        official_email TEXT NOT NULL,
        tax_id TEXT,
        trusted_bank_name TEXT NOT NULL,
        trusted_account TEXT NOT NULL,
        trusted_routing TEXT,
        trusted_iban TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Audit Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        audit_id TEXT PRIMARY KEY,
        filename TEXT NOT NULL,
        vendor_name TEXT,
        total_amount REAL,
        risk_score INTEGER NOT NULL,
        risk_level TEXT NOT NULL,
        verdict TEXT NOT NULL,
        forensic_flags_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Seed Default Trusted Vendors if empty
    cursor.execute("SELECT COUNT(*) FROM vendor_vault")
    if cursor.fetchone()[0] == 0:
        default_vendors = [
            (
                str(uuid.uuid4()),
                "CloudScale Networks Inc.",
                "billing@cloudscalenetworks.com",
                "US-849302194",
                "JPMorgan Chase Bank, N.A.",
                "9842109482",
                "021000021",
                "US64CHAS0210000219842109482",
                "Primary Cloud Infrastructure Vendor"
            ),
            (
                str(uuid.uuid4()),
                "Apex Cyber Logistics LLC",
                "ap@apexlogistics.io",
                "US-993821045",
                "Bank of America",
                "4439021984",
                "026009593",
                "US92BOFA0260095934439021984",
                "Global Server & Hardware Fulfillment"
            ),
            (
                str(uuid.uuid4()),
                "Stark Legal & Compliance Partners",
                "finance@starklegal.com",
                "US-102938475",
                "Wells Fargo Bank",
                "7738201934",
                "121000248",
                "US11WFBI1210002487738201934",
                "Corporate Retainer Counsel"
            )
        ]
        cursor.executemany("""
        INSERT INTO vendor_vault (id, vendor_name, official_email, tax_id, trusted_bank_name, trusted_account, trusted_routing, trusted_iban, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, default_vendors)

    conn.commit()
    conn.close()

def find_vendor_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Fuzzy / substring search for trusted vendor profile."""
    if not name or len(name.strip()) < 3:
        return None

    conn = get_db_connection()
    cursor = conn.cursor()
    clean = name.strip()

    # Exact match first
    cursor.execute("SELECT * FROM vendor_vault WHERE LOWER(vendor_name) = LOWER(?)", (clean,))
    row = cursor.fetchone()
    if not row:
        # Substring search
        cursor.execute("SELECT * FROM vendor_vault WHERE LOWER(vendor_name) LIKE ? OR LOWER(?) LIKE LOWER(vendor_name)", 
                       (f"%{clean.lower()}%", clean))
        row = cursor.fetchone()

    conn.close()
    return dict(row) if row else None

def list_all_vendors() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vendor_vault ORDER BY vendor_name ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def insert_vendor(vendor_data: Dict[str, Any]) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    v_id = str(uuid.uuid4())
    cursor.execute("""
    INSERT INTO vendor_vault (id, vendor_name, official_email, tax_id, trusted_bank_name, trusted_account, trusted_routing, trusted_iban, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        v_id,
        vendor_data["vendor_name"],
        vendor_data["official_email"],
        vendor_data.get("tax_id"),
        vendor_data["trusted_bank_name"],
        vendor_data["trusted_account"],
        vendor_data.get("trusted_routing"),
        vendor_data.get("trusted_iban"),
        vendor_data.get("notes")
    ))
    conn.commit()
    cursor.execute("SELECT * FROM vendor_vault WHERE id = ?", (v_id,))
    created = dict(cursor.fetchone())
    conn.close()
    return created

def record_audit_log(log_data: Dict[str, Any]):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO audit_logs (audit_id, filename, vendor_name, total_amount, risk_score, risk_level, verdict, forensic_flags_json)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        log_data["audit_id"],
        log_data["filename"],
        log_data.get("vendor_name"),
        log_data.get("total_amount", 0.0),
        log_data["risk_score"],
        log_data["risk_level"],
        log_data["verdict"],
        json.dumps(log_data.get("forensic_flags", []))
    ))
    conn.commit()
    conn.close()

def get_recent_audits(limit: int = 10) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        if d.get("forensic_flags_json"):
            try:
                d["forensic_flags"] = json.loads(d["forensic_flags_json"])
            except Exception:
                d["forensic_flags"] = []
        result.append(d)
    return result
