# Contributing to Sanjeevani Grid

Thank you for contributing to Sanjeevani Grid! To ensure smooth collaboration and zero merge friction across our 4-member team, please adhere to these guidelines.

## Branch Strategy

The repository follows a strict git branching model:

```
main (Production releases only)
└── develop (Active team integration)
    ├── frontend/member-1 (Frontend SPA & Modules)
    ├── backend/member-2  (FastAPI, DB & Core APIs)
    ├── ai/member-3       (ML Models & Pipelines)
    └── infra/member-4    (Docker, Federated AI, OR-Tools, CI/CD)
```

### Golden Rules
1. **Never push feature work directly to `main` or `develop`**.
2. Feature/member branches merge exclusively into `develop`.
3. `develop` undergoes integration testing before merging into `main`.
4. All merges into `develop` and `main` must occur via **Pull Requests (PRs)** with at least one team peer review.

---

## Commit Message Convention

Follow standard Conventional Commits:

| Type | Purpose | Example |
| :--- | :--- | :--- |
| `feat:` | A new user-facing or platform feature | `feat: add ICU bed forecasting endpoint` |
| `fix:` | A bug fix | `fix: resolve stale token refresh in client` |
| `docs:` | Documentation changes only | `docs: update API conventions guide` |
| `test:` | Adding or updating tests | `test: add unit test for healthcheck route` |
| `refactor:` | Code change that neither fixes a bug nor adds a feature | `refactor: extract base solver class` |
| `chore:` | Build tasks, configs, dependency updates | `chore: update dependencies in requirements.txt` |

---

## Pull Request Checklist

Before submitting a PR to `develop`:
- [ ] You are merging from your designated branch (`<subsystem>/member-<N>`).
- [ ] No `.env` or sensitive credentials are included in the diff.
- [ ] Frontend builds cleanly (`npm run build`).
- [ ] Unit tests pass (`pytest`).
- [ ] Commit messages follow the convention above.
- [ ] Relevant documentation under `docs/` is updated if API contracts changed.
