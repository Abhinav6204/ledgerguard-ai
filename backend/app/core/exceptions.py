"""
LedgerGuard AI — Sanitized Exception Handler
Guarantees zero internal file path or stack trace leakage to clients.
"""

import logging
import traceback
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("ledgerguard.security")

async def global_exception_handler(request: Request, exc: Exception):
    """Intercepts uncaught server exceptions, logs trace internally, returns sanitized message."""
    logger.error(f"Internal Exception on {request.method} {request.url.path}: {str(exc)}")
    logger.error(traceback.format_exc())

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "error_code": "INTERNAL_SECURITY_HALT",
            "message": "An internal processing error occurred. The forensic audit engine halted to protect system integrity."
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Sanitizes Pydantic input validation failures."""
    errors = []
    for err in exc.errors():
        field = " -> ".join(str(loc) for loc in err.get("loc", []))
        errors.append(f"{field}: {err.get('msg')}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "error_code": "INPUT_VALIDATION_FAILED",
            "message": "Supplied input failed strict security schema validation.",
            "details": errors
        }
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handles standard HTTPExceptions cleanly."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error_code": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "detail": exc.detail
        }
    )
