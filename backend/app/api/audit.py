"""
LedgerGuard AI — Invoice Audit API Endpoints
Accepts file uploads and text payloads, executes deep multi-layer forensics, and logs audit trails.
"""

import time
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.core.security import InputSanitizer
from app.parsers.invoice_parser import InvoiceParser
from app.analyzers.math_auditor import MathAuditor
from app.analyzers.bank_validator import BankValidator
from app.analyzers.metadata_forensics import MetadataForensics
from app.analyzers.ai_engine import ForensicAIEngine
from app.models.schemas import InvoiceAuditResponse, QuickScanRequest
from app.models.database import record_audit_log, get_recent_audits

router = APIRouter(prefix="/api/audit", tags=["Audit Engine"])

@router.post("/upload", response_model=InvoiceAuditResponse)
async def audit_invoice_file(file: UploadFile = File(...)):
    start_time = time.time()

    # 1. Sanitize filename
    clean_filename = InputSanitizer.sanitize_filename(file.filename)

    # 2. Read bytes and enforce strict security checks
    content = await file.read()
    is_valid, err_msg = InputSanitizer.validate_file_bytes(clean_filename, content)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Security Validation Failed: {err_msg}"
        )

    # 3. Parse Document Content
    try:
        parsed_data = InvoiceParser.parse_pdf(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Document Parsing Error: {str(e)}"
        )

    # 4. Multi-Layer Deterministic Forensics
    math_verified, math_flags = MathAuditor.audit_figures(parsed_data)
    vendor_known, bank_matched, bank_flags = BankValidator.audit_banking_and_vendor(
        parsed_data["vendor"], parsed_data["bank_details"]
    )
    meta_flags = MetadataForensics.audit_metadata_and_text(
        parsed_data.get("metadata", {}), parsed_data.get("raw_text", "")
    )

    all_flags = math_flags + bank_flags + meta_flags

    # 5. Dual-Engine AI Synthesis
    risk_score, risk_level, verdict, ai_rationale = await ForensicAIEngine.analyze_invoice(
        parsed_data, all_flags
    )

    duration_ms = round((time.time() - start_time) * 1000, 2)
    audit_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    response = InvoiceAuditResponse(
        audit_id=audit_id,
        filename=clean_filename,
        risk_score=risk_score,
        risk_level=risk_level,
        verdict=verdict,
        vendor=parsed_data["vendor"],
        bank_details=parsed_data["bank_details"],
        invoice_number=parsed_data.get("invoice_number"),
        invoice_date=parsed_data.get("invoice_date"),
        due_date=parsed_data.get("due_date"),
        subtotal=parsed_data.get("subtotal", 0.0),
        tax_amount=parsed_data.get("tax_amount", 0.0),
        total_amount=parsed_data.get("total_amount", 0.0),
        calculated_subtotal=parsed_data.get("calculated_subtotal", 0.0),
        math_verified=math_verified,
        vendor_known=vendor_known,
        bank_details_matched=bank_matched,
        forensic_flags=all_flags,
        ai_forensic_rationale=ai_rationale,
        processing_time_ms=duration_ms,
        audit_timestamp=now_iso
    )

    # 6. Record in persistent database
    record_audit_log({
        "audit_id": audit_id,
        "filename": clean_filename,
        "vendor_name": parsed_data["vendor"].name,
        "total_amount": parsed_data.get("total_amount", 0.0),
        "risk_score": risk_score,
        "risk_level": risk_level.value,
        "verdict": verdict,
        "forensic_flags": [f.model_dump() for f in all_flags]
    })

    return response

@router.post("/quick-scan", response_model=InvoiceAuditResponse)
async def audit_invoice_text(payload: QuickScanRequest):
    start_time = time.time()

    # Parse raw text entities
    parsed_data = InvoiceParser.extract_entities_from_text(payload.raw_text)
    if payload.vendor_name_hint:
        parsed_data["vendor"].name = payload.vendor_name_hint.strip()

    math_verified, math_flags = MathAuditor.audit_figures(parsed_data)
    vendor_known, bank_matched, bank_flags = BankValidator.audit_banking_and_vendor(
        parsed_data["vendor"], parsed_data["bank_details"]
    )
    meta_flags = MetadataForensics.audit_metadata_and_text({}, payload.raw_text)

    all_flags = math_flags + bank_flags + meta_flags
    risk_score, risk_level, verdict, ai_rationale = await ForensicAIEngine.analyze_invoice(
        parsed_data, all_flags
    )

    duration_ms = round((time.time() - start_time) * 1000, 2)
    audit_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    return InvoiceAuditResponse(
        audit_id=audit_id,
        filename="quick_scan_text.txt",
        risk_score=risk_score,
        risk_level=risk_level,
        verdict=verdict,
        vendor=parsed_data["vendor"],
        bank_details=parsed_data["bank_details"],
        invoice_number=parsed_data.get("invoice_number"),
        invoice_date=parsed_data.get("invoice_date"),
        due_date=parsed_data.get("due_date"),
        subtotal=parsed_data.get("subtotal", 0.0),
        tax_amount=parsed_data.get("tax_amount", 0.0),
        total_amount=parsed_data.get("total_amount", 0.0),
        calculated_subtotal=parsed_data.get("calculated_subtotal", 0.0),
        math_verified=math_verified,
        vendor_known=vendor_known,
        bank_details_matched=bank_matched,
        forensic_flags=all_flags,
        ai_forensic_rationale=ai_rationale,
        processing_time_ms=duration_ms,
        audit_timestamp=now_iso
    )

@router.get("/history")
async def get_audit_history(limit: int = 10):
    return get_recent_audits(limit=limit)
