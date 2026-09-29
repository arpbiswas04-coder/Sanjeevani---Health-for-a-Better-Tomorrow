# Team Integration & Branching Guide

This project follows an isolated workstream branching model designed to minimize merge conflicts across all 4 team members.

## Branch Hierarchy

```
main (Production Releases)
└── develop (Integration & Continuous Delivery)
    ├── frontend/member-1 (SPA, UI components, client state)
    ├── backend/member-2 (FastAPI, SQLAlchemy, PostgreSQL, Redis)
    ├── ai/member-3 (ML pipelines, demand forecasting, scoring)
    └── infra/member-4 (Docker, Federated Learning, OR-Tools, CI/CD)
```

## Integration Rules

1. **Never commit directly to `main` or `develop`**.
2. Work only on your allocated member branch.
3. Keep branches synchronized with `develop`:
   ```bash
   git fetch origin
   git merge origin/develop
   ```
4. Merge into `develop` only via Pull Requests (PRs).
5. All CI workflows must pass before PR approval.
6. Root files (`docker-compose.yml`, `.env.example`, `Makefile`) should only be modified collaboratively or by Member 4.
