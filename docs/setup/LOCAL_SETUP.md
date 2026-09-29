# Local Development Setup Guide

## Prerequisites

- **Git**
- **Node.js** (v20+ recommended) & **npm** (v10+)
- **Python** (v3.11 - v3.13)
- **Docker & Docker Compose** (Docker Desktop on Windows/macOS)

---

## Quickstart with Docker (Recommended)

1. Clone repository:
   ```bash
   git clone <repo-url>
   cd Sanjeevani-Grid
   ```
2. Copy environment template:
   ```bash
   cp .env.example .env
   # On Windows PowerShell:
   Copy-Item .env.example .env
   ```
3. Start all services:
   ```bash
   docker compose up --build
   ```
4. Access endpoints:
   - Frontend SPA: http://localhost:5173
   - Backend API Docs: http://localhost:8000/api/v1/docs
   - Healthcheck: http://localhost:8000/api/v1/health

---

## Standalone Local Setup (Without Docker)

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Backend
```bash
cd backend
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell:
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
