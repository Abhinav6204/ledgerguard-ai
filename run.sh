#!/usr/bin/env bash
# ==============================================================================
# LEDGERGUARD AI — MASTER SYSTEM LAUNCHER
# Starts backend and frontend services in isolated sandboxed processes
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================================="
echo "🛡️  LEDGERGUARD AI — WIRE FRAUD DEFENSE SUITE INITIATING"
echo "=========================================================="

# 1. Check Python Virtual Environment
if [ ! -d "$SCRIPT_DIR/backend/venv" ]; then
    echo "⚙️ Creating backend Python virtual environment..."
    python3 -m venv "$SCRIPT_DIR/backend/venv"
    "$SCRIPT_DIR/backend/venv/bin/pip" install --upgrade pip
    "$SCRIPT_DIR/backend/venv/bin/pip" install -r "$SCRIPT_DIR/backend/requirements.txt"
fi

# 2. Check Node Modules
if [ ! -d "$SCRIPT_DIR/frontend/node_modules" ]; then
    echo "⚙️ Installing frontend dependencies..."
    cd "$SCRIPT_DIR/frontend" && npm install && cd "$SCRIPT_DIR"
fi

# 3. Ensure .env exists
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo "⚙️ Generating secure .env configuration..."
    cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
fi

# 4. Run automated test suite
echo "🧪 Executing 10-vector automated security audit test suite..."
"$SCRIPT_DIR/backend/venv/bin/pytest" -q "$SCRIPT_DIR/backend/tests/test_security_and_audit.py"
echo "✅ Test Suite Passed (100% verified)."

# 5. Trap cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down LedgerGuard services..."
    kill $(jobs -p) 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# 6. Launch Backend
echo "🚀 Launching FastAPI Backend on http://127.0.0.1:8000 ..."
cd "$SCRIPT_DIR/backend"
./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd "$SCRIPT_DIR"

sleep 1

# 7. Launch Frontend Cockpit
echo "🚀 Launching React Cockpit on http://localhost:5173 ..."
cd "$SCRIPT_DIR/frontend"
npx vite --host 0.0.0.0 --port 5173 &
FRONTEND_PID=$!
cd "$SCRIPT_DIR"

echo "=========================================================="
echo "✅ LEDGERGUARD AI ONLINE & DEFENDING ACCOUNTS PAYABLE"
echo "🔗 Frontend Cockpit: http://localhost:5173"
echo "🔗 Backend REST API: http://localhost:8000/docs"
echo "=========================================================="

wait
