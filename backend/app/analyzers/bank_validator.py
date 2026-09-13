"""
LedgerGuard AI — Bank Details & Vendor Vault Cross-Verification Engine
Calculates IBAN and ABA routing checksums, and executes strict anti-wire-fraud verification against the Vendor Vault.
"""

import re
from typing import Dict, Any, List, Tuple, Optional
from app.models.schemas import ForensicFlag, FlagCategory, FlagSeverity, BankDetails, VendorInfo
from app.models.database import find_vendor_by_name

class BankValidator:
    """Verifies banking coordinates and cross-references against trusted vendor records."""

    @staticmethod
    def validate_aba_routing(routing: str) -> bool:
        """Validates US ABA 9-digit routing transit number checksum."""
        if not routing or not routing.isdigit() or len(routing) != 9:
            return False
        digits = [int(d) for d in routing]
        checksum = (
            3 * (digits[0] + digits[3] + digits[6]) +
            7 * (digits[1] + digits[4] + digits[7]) +
            1 * (digits[2] + digits[5] + digits[8])
        )
        return checksum % 10 == 0

    @staticmethod
    def validate_iban(iban: str) -> bool:
        """Validates international bank account number using ISO 7064 mod-97 check."""
        if not iban:
            return False
        clean = re.sub(r'[\s-]', '', iban).upper()
        if len(clean) < 15 or len(clean) > 34 or not clean[:2].isalpha():
            return False
        # Move first 4 chars to end
        rearranged = clean[4:] + clean[:4]
        # Replace letters with digits (A=10, B=11, ..., Z=35)
        numeric_str = "".join(str(ord(ch) - 55) if ch.isalpha() else ch for ch in rearranged)
        try:
            return int(numeric_str) % 97 == 1
        except ValueError:
            return False

    @classmethod
    def audit_banking_and_vendor(
        cls, 
        vendor: VendorInfo, 
        bank: BankDetails
    ) -> Tuple[bool, Optional[bool], List[ForensicFlag]]:
        """
        Cross-checks invoice details with the persistent Vendor Vault.
        Returns: (is_vendor_known, is_bank_matched, forensic_flags)
        """
        flags: List[ForensicFlag] = []
        is_known = False
        is_matched: Optional[bool] = None

        # 1. Routing Number Checksum Validation
        if bank.routing_number:
            if not cls.validate_aba_routing(bank.routing_number):
                flags.append(ForensicFlag(
                    category=FlagCategory.BANK_MISMATCH,
                    severity=FlagSeverity.HIGH,
                    title="Invalid ABA Routing Transit Number",
                    description=(
                        f"The provided routing number '{bank.routing_number}' failed the Federal Reserve checksum algorithm. "
                        "Funds routed here may bounce or be redirected to an illicit transit account."
                    ),
                    recommendation="Confirm banking instructions with the vendor over the phone using verified contact numbers."
                ))

        # 2. IBAN Checksum Validation
        trusted_record = find_vendor_by_name(vendor.name)
        if bank.iban:
            trusted_iban = trusted_record.get("trusted_iban") if trusted_record else None
            if bank.iban != trusted_iban and not cls.validate_iban(bank.iban):
                flags.append(ForensicFlag(
                    category=FlagCategory.BANK_MISMATCH,
                    severity=FlagSeverity.HIGH,
                    title="Invalid IBAN Mod-97 Checksum",
                    description=f"IBAN '{bank.iban}' failed international checksum validation.",
                    recommendation="Request re-issuance of international wire instructions from verified treasury representative."
                ))

        # 3. Cross-Check Against Vendor Vault
        if trusted_record:
            is_known = True
            trusted_acc = trusted_record["trusted_account"]
            trusted_routing = trusted_record["trusted_routing"] or ""
            trusted_iban = trusted_record["trusted_iban"] or ""

            # Check if invoice provided an account number
            inv_acc = bank.account_number or ""
            inv_routing = bank.routing_number or ""
            inv_iban = bank.iban or ""

            # Detect Account Mismatch
            acc_mismatch = bool(inv_acc and trusted_acc and inv_acc != trusted_acc)
            routing_mismatch = bool(inv_routing and trusted_routing and inv_routing != trusted_routing)
            iban_mismatch = bool(inv_iban and trusted_iban and inv_iban != trusted_iban)

            if acc_mismatch or routing_mismatch or iban_mismatch:
                is_matched = False
                flags.append(ForensicFlag(
                    category=FlagCategory.BANK_MISMATCH,
                    severity=FlagSeverity.CRITICAL,
                    title="CRITICAL WIRE FRAUD RED ALERT: Altered Bank Details",
                    description=(
                        f"Vendor '{vendor.name}' is a registered trusted supplier, BUT the banking coordinates on this invoice "
                        f"do NOT match the vault record!\n"
                        f"Invoice Account: {inv_acc or inv_iban or 'N/A'}\n"
                        f"Authorized Vault Account: {trusted_acc or trusted_iban}\n"
                        f"Authorized Bank: {trusted_record['trusted_bank_name']}"
                    ),
                    recommendation="DO NOT WIRE FUNDS. This is the hallmark signature of Business Email Compromise (BEC). Call vendor directly."
                ))
            elif inv_acc == trusted_acc or (inv_iban and inv_iban == trusted_iban):
                is_matched = True
                flags.append(ForensicFlag(
                    category=FlagCategory.BANK_MISMATCH,
                    severity=FlagSeverity.INFO,
                    title="Verified Trusted Vendor Banking Profile",
                    description=f"Banking details reconcile 100% with authorized profile for '{vendor.name}' in Vendor Vault.",
                    recommendation="Standard payment approval protocol applies."
                ))
        else:
            # Unregistered Vendor
            flags.append(ForensicFlag(
                category=FlagCategory.SUSPICIOUS_ENTITY,
                severity=FlagSeverity.MEDIUM,
                title="Unregistered / First-Time Vendor Profile",
                description=(
                    f"Vendor '{vendor.name}' is not currently registered in the company's authorized Vendor Vault. "
                    "First-time vendor invoices carry higher exposure to impersonation fraud."
                ),
                recommendation="Perform standard Accounts Payable KYC vendor setup and confirm bank ownership before releasing wire."
            ))

        return is_known, is_matched, flags
