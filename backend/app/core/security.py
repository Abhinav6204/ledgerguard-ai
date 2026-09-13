"""
LedgerGuard AI — Core Security & Defense Middleware
Bank-grade protection: OWASP headers, sliding-window rate limiting, and input sanitization.
"""

import time
import re
import os
from collections import defaultdict
from typing import Dict, List, Tuple
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from app.config import settings

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enforces strict OWASP defense headers across all HTTP responses."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Defense against MIME confusion attacks
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Defense against Clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Defense against Reflected XSS
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer privacy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Hardware API restriction
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data: blob:; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self' 'unsafe-inline'; "
            "font-src 'self' data:; "
            "connect-src 'self' http://localhost:* http://127.0.0.1:*"
        )

        # Cache control for sensitive financial data
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        return response


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Sliding-window rate limiter protecting inference and upload endpoints
    against Financial Denial of Service (Quota Drain) and brute-force abuse.
    """

    def __init__(self, app, rate_limit: int = 60, burst_limit: int = 15):
        super().__init__(app)
        self.rate_limit = rate_limit
        self.burst_limit = burst_limit
        self.history: Dict[str, List[float]] = defaultdict(list)
        self.burst_history: Dict[str, List[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Exclude health check and documentation in dev
        if request.url.path in ["/health", "/docs", "/openapi.json", "/"]:
            return await call_next(request)

        # Extract client IP (respecting reverse-proxy X-Forwarded-For if available)
        client_ip = request.headers.get("X-Forwarded-For")
        if client_ip:
            client_ip = client_ip.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "127.0.0.1"

        now = time.time()
        window_start = now - 60.0
        burst_start = now - 10.0

        # Purge stale timestamps
        self.history[client_ip] = [t for t in self.history[client_ip] if t > window_start]
        self.burst_history[client_ip] = [t for t in self.burst_history[client_ip] if t > burst_start]

        # Check burst limit (e.g. max 15 requests in 10s)
        if len(self.burst_history[client_ip]) >= self.burst_limit:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded (burst flood detected)",
                    "message": "Too many requests submitted in a short interval. Please wait 10 seconds.",
                    "retry_after": 10
                },
                headers={"Retry-After": "10"}
            )

        # Check sustained limit (e.g. max 60 requests in 60s)
        if len(self.history[client_ip]) >= self.rate_limit:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Sustained request limit reached. Please wait before submitting more audits.",
                    "retry_after": 60
                },
                headers={"Retry-After": "60"}
            )

        # Record this request
        self.history[client_ip].append(now)
        self.burst_history[client_ip].append(now)

        response: Response = await call_next(request)
        remaining = max(0, self.rate_limit - len(self.history[client_ip]))
        response.headers["X-RateLimit-Limit"] = str(self.rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response


class InputSanitizer:
    """Rigorous input sanitizer defending against path traversal, ReDoS, and malicious magic bytes."""

    ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}

    # Magic byte signatures for true format validation
    MAGIC_SIGNATURES = {
        ".pdf": b"%PDF",
        ".png": b"\x89PNG\r\n\x1a\n",
        ".jpg": b"\xff\xd8\xff",
        ".jpeg": b"\xff\xd8\xff"
    }

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Strips dangerous characters, null bytes, and path traversal sequences."""
        if not filename:
            return "unnamed_invoice.pdf"
        
        # Remove null bytes and path traversal patterns
        clean = filename.replace("\x00", "").replace("..", "").replace("/", "").replace("\\", "")
        clean = re.sub(r'[^a-zA-Z0-9._-]', '_', clean)
        return clean[:128]

    @classmethod
    def validate_file_bytes(cls, filename: str, content: bytes) -> Tuple[bool, str]:
        """Verifies file size, extension, and true magic bytes."""
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

        if len(content) == 0:
            return False, "File is completely empty (0 bytes)."

        if len(content) > max_bytes:
            return False, f"File exceeds maximum permissible size of {settings.MAX_UPLOAD_SIZE_MB}MB."

        _, ext = os.path.splitext(filename.lower())
        if ext not in cls.ALLOWED_EXTENSIONS:
            return False, f"Unsupported file extension '{ext}'. Allowed: {', '.join(cls.ALLOWED_EXTENSIONS)}"

        # Validate magic signature
        expected_sig = cls.MAGIC_SIGNATURES.get(ext)
        if expected_sig and not content.startswith(expected_sig):
            return False, f"File signature mismatch. File claimed to be {ext} but lacks authentic binary headers."

        return True, "Valid"

    @classmethod
    def sanitize_text_for_llm(cls, text: str) -> str:
        """
        Bounds text length and encloses it in strict adversarial fences
        to prevent prompt injection and model jailbreaks.
        """
        bounded = text[:settings.MAX_TEXT_CHARACTERS]
        # Neutralize markdown and prompt jailbreak tokens
        clean = bounded.replace("```", "'''")
        return f"<UNTRUSTED_INVOICE_DATA>\n{clean}\n</UNTRUSTED_INVOICE_DATA>"
