# Member 4 - Infrastructure, Federated AI & Optimization Guide

- **Assigned Git Branch**: `infra/member-4`
- **Target Integration Branch**: `develop`
- **Primary Working Directories**:
  - `infra/`
  - `federated/`
  - `optimization/`
  - `.github/workflows/`
  - Root orchestration files (`docker-compose.yml`, `Makefile`)

## Technology Stack

- Docker & Docker Compose
- NGINX
- Prometheus & Grafana
- Flower / NVIDIA FLARE (Federated Learning)
- Google OR-Tools (Vehicle routing, integer programming)
- GitHub Actions CI/CD

## Workflow

1. Check out your branch:
   ```bash
   git checkout -b infra/member-4 develop
   ```
2. Maintain container configurations and service healthchecks.
3. Wire the Federated aggregation protocols in `federated/`.
4. Implement redistribution and routing solvers in `optimization/`.
5. Ensure `docker compose up --build` works cleanly on clean machines.
