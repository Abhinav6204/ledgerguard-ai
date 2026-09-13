"""
LedgerGuard AI — Pydantic Schemas & Data Contracts
Strict type safety with bounds enforcement for all API contracts.
"""

from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field

class RiskLevel(str, Enum):
    CLEAN = "CLEAN"
    LOW_RISK = "LOW_RISK"
    SUSPICIOUS = "SUSPICIOUS"
    HIGH_RISK = "HIGH_RISK"
    CRITICAL_FRAUD = "CRITICAL_FRAUD"

class FlagSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

class FlagCategory(str, Enum):
    BANK_MISMATCH = "BANK_MISMATCH"
    MATH_DISCREPANCY = "MATH_DISCREPANCY"
    METADATA_TAMPERING = "METADATA_TAMPERING"
    SUSPICIOUS_ENTITY = "SUSPICIOUS_ENTITY"
    DUPLICATE_INVOICE = "DUPLICATE_INVOICE"
    PRESSURE_TACTIC = "PRESSURE_TACTIC"

class LineItem(BaseModel):
    description: str = Field(..., max_length=256)
    quantity: float = Field(default=1.0, ge=0)
    unit_price: float = Field(default=0.0, ge=0)
    total_amount: float = Field(default=0.0, ge=0)

class BankDetails(BaseModel):
    bank_name: Optional[str] = Field(default=None, max_length=128)
    account_number: Optional[str] = Field(default=None, max_length=64)
    routing_number: Optional[str] = Field(default=None, max_length=32)
    iban: Optional[str] = Field(default=None, max_length=40)
    swift_bic: Optional[str] = Field(default=None, max_length=20)
    wire_instructions: Optional[str] = Field(default=None, max_length=256)

class VendorInfo(BaseModel):
    name: str = Field(default="Unknown Vendor", max_length=128)
    email: Optional[str] = Field(default=None, max_length=128)
    domain: Optional[str] = Field(default=None, max_length=128)
    tax_id: Optional[str] = Field(default=None, max_length=64)
    address: Optional[str] = Field(default=None, max_length=256)
    phone: Optional[str] = Field(default=None, max_length=32)

class ForensicFlag(BaseModel):
    category: FlagCategory
    severity: FlagSeverity
    title: str = Field(..., max_length=128)
    description: str = Field(..., max_length=1024)
    recommendation: str = Field(..., max_length=512)

class InvoiceAuditResponse(BaseModel):
    audit_id: str
    filename: str
    risk_score: int = Field(..., ge=0, le=100)
    risk_level: RiskLevel
    verdict: str
    vendor: VendorInfo
    bank_details: BankDetails
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    subtotal: float = 0.0
    tax_amount: float = 0.0
    total_amount: float = 0.0
    calculated_subtotal: float = 0.0
    math_verified: bool = True
    vendor_known: bool = False
    bank_details_matched: Optional[bool] = None
    forensic_flags: List[ForensicFlag] = []
    ai_forensic_rationale: str
    processing_time_ms: float
    audit_timestamp: str

class VendorVaultCreate(BaseModel):
    vendor_name: str = Field(..., min_length=2, max_length=128)
    official_email: str = Field(..., max_length=128)
    tax_id: Optional[str] = Field(default=None, max_length=64)
    trusted_bank_name: str = Field(..., max_length=128)
    trusted_account: str = Field(..., min_length=4, max_length=64)
    trusted_routing: Optional[str] = Field(default=None, max_length=32)
    trusted_iban: Optional[str] = Field(default=None, max_length=40)
    notes: Optional[str] = Field(default=None, max_length=256)

class QuickScanRequest(BaseModel):
    raw_text: str = Field(..., min_length=10, max_length=100000)
    vendor_name_hint: Optional[str] = Field(default=None, max_length=128)
