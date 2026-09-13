# ==============================================================================
# LEDGERGUARD AI — PRODUCTION HARDENED DOCKERFILE
# Multi-stage container: Node 20 builder + Python 3.13 minimal secure runtime
# ==============================================================================

# Stage 1: Build React Frontend Cockpit
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci --silent

COPY frontend/ ./
RUN npm run build

# Stage 2: Hardened Python Application Server
FROM python:3.13-slim AS runtime

# Security: Prevent root execution
RUN groupadd -r ledgerguard && useradd -r -g ledgerguard -d /app -s /sbin/nologin ledgerguard

# Security: Install minimal OS security packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend application
COPY backend/app /app/app
COPY backend/pytest.ini /app/pytest.ini

# Copy compiled frontend assets from Stage 1
COPY --from=frontend-builder /app/frontend/dist /app/static

# Create data directory with strict non-root ownership
RUN mkdir -p /app/data && chown -R ledgerguard:ledgerguard /app

# Switch to unprivileged security user
USER ledgerguard

# Expose service port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Launch production server with 4 workers
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
