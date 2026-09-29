# Member 2 - Backend Engineering Guide

- **Assigned Git Branch**: `backend/member-2`
- **Target Integration Branch**: `develop`
- **Primary Working Directory**: `backend/`

## Technology Stack

- FastAPI + Uvicorn
- Python 3.11 / 3.12 / 3.13
- SQLAlchemy 2.0 (Async) + Alembic
- PostgreSQL 16
- Redis 7
- Pydantic v2 + pydantic-settings

## Workflow

1. Check out your branch:
   ```bash
   git checkout -b backend/member-2 develop
   ```
2. Run local backend:
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```
3. Implement models in `app/models/`, schemas in `app/schemas/`, and routers in `app/api/v1/`.
4. Follow `/api/v1` conventions documented in `docs/api/API_CONVENTIONS.md`.
5. Ensure `pytest` passes before submitting PR to `develop`.
