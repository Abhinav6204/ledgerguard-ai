"""
LedgerGuard AI — Vendor Vault Management API
Manages verified trusted vendor banking records against which incoming invoices are reconciled.
"""

from fastapi import APIRouter, HTTPException, status
from app.models.schemas import VendorVaultCreate
from app.models.database import list_all_vendors, insert_vendor

router = APIRouter(prefix="/api/vendors", tags=["Vendor Vault"])

@router.get("/")
async def get_all_vendors():
    """Retrieves all authorized trusted vendor profiles."""
    return list_all_vendors()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_vendor(vendor: VendorVaultCreate):
    """Enrolls a new trusted vendor banking profile into the vault."""
    try:
        created = insert_vendor(vendor.model_dump())
        return {
            "status": "success",
            "message": f"Vendor '{vendor.vendor_name}' enrolled in trusted vault.",
            "vendor": created
        }
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Vendor '{vendor.vendor_name}' is already enrolled in the vault."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register vendor: {str(e)}"
        )
