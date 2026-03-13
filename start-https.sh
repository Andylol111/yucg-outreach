#!/bin/bash
# Start YUCG Outreach with HTTPS (self-signed certs for local dev)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || { echo "Could not change to script directory"; exit 1; }

CERT_DIR="./backend/certs"
mkdir -p "$CERT_DIR"

if [ ! -f "$CERT_DIR/key.pem" ]; then
  echo "Generating self-signed certificates..."
  openssl req -x509 -newkey rsa:2048 -keyout "$CERT_DIR/key.pem" -out "$CERT_DIR/cert.pem" \
    -days 365 -nodes -subj "/CN=localhost"
fi

echo "Starting backend with HTTPS on https://localhost:8000"
cd backend
source venv/bin/activate
python -m uvicorn main:app --reload --port 8000 --ssl-keyfile=certs/key.pem --ssl-certfile=certs/cert.pem &
cd ..

echo "Starting frontend with HTTPS on https://localhost:5173"
cd frontend
VITE_HTTPS=true npm run dev &
cd ..

echo ""
echo "=== HTTPS servers ==="
echo "  Frontend: https://localhost:5173 (accept self-signed cert in browser)"
echo "  Backend:  https://localhost:8000"
echo ""
echo "For Google OAuth: add https://localhost:8000/api/auth/google/callback to authorized redirect URIs"
wait
