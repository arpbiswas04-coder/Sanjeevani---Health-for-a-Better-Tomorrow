# Member 1 - Frontend Engineering Guide

- **Assigned Git Branch**: `frontend/member-1`
- **Target Integration Branch**: `develop`
- **Primary Working Directory**: `frontend/`

## Technology Stack

- React 18 + TypeScript + Vite
- Tailwind CSS
- React Router 6 / 7
- TanStack Query v5
- Zustand (Global UI state)
- React Hook Form + Zod
- i18next (Internationalization)

## Workflow

1. Check out your branch:
   ```bash
   git checkout -b frontend/member-1 develop
   ```
2. Run local frontend dev server:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
3. Implement features inside `frontend/src/modules/<feature>/`.
4. Avoid touching `backend/`, `ai/`, or root infrastructure configs.
5. Ensure `npm run build` succeeds before opening a PR to `develop`.
