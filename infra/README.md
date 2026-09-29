# Sanjeevani Grid - Infrastructure & DevOps Subsystem

This subsystem is maintained by **Member 4** (`infra/member-4`).

## Responsibilities

- Containerization (Docker, Docker Compose, Multi-stage builds)
- Reverse proxy and SSL/TLS termination (NGINX)
- Metrics collection and observability (Prometheus & Grafana)
- Production orchestrations and cloud deployment templates
- CI/CD pipelines in `.github/workflows/`

## Subsystem Layout

```
infra/
├── docker/         # Production and staging Dockerfiles
├── nginx/          # NGINX gateway configuration
├── monitoring/     # Prometheus configs & Grafana dashboards
├── deployment/     # Kubernetes / cloud deployment specs
├── security/       # Security posture & hardening rules
└── README.md
```

## Starting with Docker Compose

From the project root:

```bash
cp .env.example .env
docker compose up --build
```
