# YUCG Outreach - How to Start

## "Address already in use" error?

Run this first to free ports 8000 and 5173:
```bash
./kill-ports.sh
```

---

## Quick start (from scratch)

### Option 1: One command (starts both backend + frontend)
```bash
./start-all.sh
```

### Option 2: Manual (two terminals)

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python -m uvicorn main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Option 3: Backend only (using start script)
```bash
cd backend
./start.sh
```

---

## First-time setup (if venv or node_modules missing)

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

---

## URLs
- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **Health check:** http://localhost:8000/api/health

---

## HTTPS (optional)

For HTTPS with self-signed certs, run from the project root:
```bash
cd "/Users/andreh./Documents/GitHub/client affairs tools"
./start-https.sh
```
Or use the full path:
```bash
"/Users/andreh./Documents/GitHub/client affairs tools/start-https.sh"
```
- Frontend: https://localhost:5173
- Backend: https://localhost:8000
- Add `https://localhost:8000/api/auth/google/callback` to Google OAuth redirect URIs
