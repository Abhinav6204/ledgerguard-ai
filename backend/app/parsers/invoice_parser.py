"""
LedgerGuard AI — Secure Invoice & Document Extraction Pipeline
Extracts structured financial metadata, line items, and binary forensic signatures from PDF documents.
"""

import re
import io
from typing import Dict, Any, List, Tuple
from pypdf import PdfReader
from app.config import settings
from app.models.schemas import LineItem, BankDetails, VendorInfo

class InvoiceParser:
    """Bounded, memory-safe PDF and text invoice parser."""

    @classmethod
    def parse_pdf(cls, content: bytes) -> Dict[str, Any]:
        """
        Parses PDF content with strict boundaries against decompression bombs
        and unbounded loops.
        """
        pdf_file = io.BytesIO(content)
        reader = PdfReader(pdf_file)

        num_pages = len(reader.pages)
        if num_pages > settings.MAX_PDF_PAGES:
            raise ValueError(f"PDF contains {num_pages} pages, exceeding safety ceiling of {settings.MAX_PDF_PAGES}.")

        # Extract text safely
        extracted_text_chunks = []
        total_chars = 0
        fonts_detected = set()

        for idx, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            extracted_text_chunks.append(page_text)
            total_chars += len(page_text)

            # Inspect font structures if available
            if "/Resources" in page and "/Font" in page["/Resources"]:
                try:
                    font_dict = page["/Resources"]["/Font"]
                    for font_key in font_dict:
                        fonts_detected.add(str(font_key))
                except Exception:
                    pass

            if total_chars > settings.MAX_TEXT_CHARACTERS:
                break

        full_text = "\n".join(extracted_text_chunks)[:settings.MAX_TEXT_CHARACTERS]

        # Extract document metadata
        raw_metadata = reader.metadata or {}
        metadata = {
            "creator": str(raw_metadata.get("/Creator", "")),
            "producer": str(raw_metadata.get("/Producer", "")),
            "creation_date": str(raw_metadata.get("/CreationDate", "")),
            "mod_date": str(raw_metadata.get("/ModDate", "")),
            "page_count": num_pages,
            "fonts_count": len(fonts_detected)
        }

        # Parse entities from text
        parsed_data = cls.extract_entities_from_text(full_text)
        parsed_data["metadata"] = metadata
        parsed_data["raw_text"] = full_text
        return parsed_data

    @classmethod
    def extract_entities_from_text(cls, text: str) -> Dict[str, Any]:
        """Extracts vendor, financial figures, and banking coordinates using precision regex."""

        # 1. Financial Amounts
        # Look for Total / Amount Due / Balance Due
        total_amount = 0.0
        subtotal = 0.0
        tax_amount = 0.0

        total_match = re.search(r'(?i)(?:total\s+amount\s+due|amount\s+due|balance\s+due|grand\s+total|total)[:\s]*[\$€£]?\s*([0-9,]+\.[0-9]{2})', text)
        if total_match:
            try:
                total_amount = float(total_match.group(1).replace(',', ''))
            except ValueError:
                pass

        subtotal_match = re.search(r'(?i)(?:subtotal|sub-total|net\s+amount)[:\s]*[\$€£]?\s*([0-9,]+\.[0-9]{2})', text)
        if subtotal_match:
            try:
                subtotal = float(subtotal_match.group(1).replace(',', ''))
            except ValueError:
                pass

        tax_match = re.search(r'(?i)(?:tax|vat|gst|sales\s+tax)[:\s]*[\$€£]?\s*([0-9,]+\.[0-9]{2})', text)
        if tax_match:
            try:
                tax_amount = float(tax_match.group(1).replace(',', ''))
            except ValueError:
                pass

        # 2. Invoice Identifiers
        inv_num_match = re.search(r'(?i)(?:invoice\s*#?|inv\s*#?|bill\s*#?)[:\s]*([A-Z0-9\-_]{3,24})', text)
        invoice_number = inv_num_match.group(1).strip() if inv_num_match else None

        date_match = re.search(r'(?i)(?:date|invoice\s*date)[:\s]*([0-9]{1,4}[-/.][0-9]{1,2}[-/.][0-9]{1,4}|[A-Za-z]{3,9}\s+[0-9]{1,2},?\s+[0-9]{4})', text)
        invoice_date = date_match.group(1).strip() if date_match else None

        due_match = re.search(r'(?i)(?:due\s*date|payment\s*due)[:\s]*([0-9]{1,4}[-/.][0-9]{1,2}[-/.][0-9]{1,4}|[A-Za-z]{3,9}\s+[0-9]{1,2},?\s+[0-9]{4})', text)
        due_date = due_match.group(1).strip() if due_match else None

        # 3. Vendor Coordinates
        email_match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)
        vendor_email = email_match.group(0).strip() if email_match else None

        tax_id_match = re.search(r'(?i)(?:tax\s*id|vat\s*id|ein|gstin)[:\s]*([A-Z0-9\-_]{6,20})', text)
        tax_id = tax_id_match.group(1).strip() if tax_id_match else None

        # Heuristic for vendor name: top line or preceding header
        vendor_name = "Unknown Vendor"
        lines = [line.strip() for line in text.splitlines() if len(line.strip()) > 3]
        if lines:
            # First line often contains vendor name
            candidate = lines[0]
            if not re.search(r'(?i)invoice|statement|bill\s+to|page', candidate):
                vendor_name = candidate[:64]
            elif len(lines) > 1 and not re.search(r'(?i)invoice|statement|bill\s+to|page', lines[1]):
                vendor_name = lines[1][:64]

        # 4. Bank Coordinates
        iban_match = re.search(r'\b([A-Z]{2}[0-9]{2}[A-Z0-9]{11,30})\b', text)
        iban = iban_match.group(1).strip() if iban_match else None

        account_match = re.search(r'(?i)(?:account\s*#?|acc\s*#?|account\s*number)[:\s]*([0-9]{6,18})', text)
        account_number = account_match.group(1).strip() if account_match else None

        routing_match = re.search(r'(?i)(?:routing\s*#?|aba|sort\s*code|routing\s*number)[:\s]*([0-9]{9}|[0-9]{2}-[0-9]{2}-[0-9]{2})', text)
        routing_number = routing_match.group(1).strip() if routing_match else None

        swift_match = re.search(r'(?i)(?:swift|bic)[:\s]*([A-Z]{6}[A-Z0-9]{2}(?:[A-Z0-9]{3})?)', text)
        swift_bic = swift_match.group(1).strip() if swift_match else None

        bank_name_match = re.search(r'(?i)(?:bank\s*name|bank)[:\s]*([A-Za-z\s&,.-]{4,40})', text)
        bank_name = bank_name_match.group(1).strip() if bank_name_match else None

        # Extract line items
        line_items = cls.extract_line_items(text)
        calc_subtotal = sum(item.total_amount for item in line_items)

        return {
            "vendor": VendorInfo(
                name=vendor_name,
                email=vendor_email,
                tax_id=tax_id
            ),
            "bank_details": BankDetails(
                bank_name=bank_name,
                account_number=account_number,
                routing_number=routing_number,
                iban=iban,
                swift_bic=swift_bic
            ),
            "invoice_number": invoice_number,
            "invoice_date": invoice_date,
            "due_date": due_date,
            "subtotal": subtotal,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
            "line_items": line_items,
            "calculated_subtotal": calc_subtotal
        }

    @classmethod
    def extract_line_items(cls, text: str) -> List[LineItem]:
        """Extracts tabular line items with quantities and totals."""
        items = []
        # Pattern matching: Description ... Qty ... Price ... Total
        pattern = re.compile(r'([A-Za-z0-9\s/_-]{4,40})\s+([0-9]{1,4})\s+[\$€£]?\s*([0-9,]+\.[0-9]{2})\s+[\$€£]?\s*([0-9,]+\.[0-9]{2})')
        for match in pattern.finditer(text):
            desc, qty_str, price_str, total_str = match.groups()
            try:
                qty = float(qty_str)
                price = float(price_str.replace(',', ''))
                total = float(total_str.replace(',', ''))
                items.append(LineItem(description=desc.strip(), quantity=qty, unit_price=price, total_amount=total))
            except ValueError:
                continue
        return items
