# 🌿 Sanjeevani Grid — `infra/ayan` Environment & Setup Guide

> **Branch:** `infra/ayan`  
> **Maintainer:** Ayan Kumar Mondal  
> **Role:** Infrastructure, Optimization Engines, Federated Learning Coordinator & Observability (Member 4)  
> **Audience:** Human Teammates & AI Coding Agents (Antigravity, Cursor, VS Code Copilot)

---

## 📑 Table of Contents
1. [Overview & Architecture](#1-overview--architecture)
2. [Prerequisites Checklist](#2-prerequisites-checklist)
3. [🚀 Quickstart (3-Minute Setup)](#3--quickstart-3-minute-setup)
4. [Step-by-Step Setup Guide](#4-step-by-step-setup-guide)
   - [Step 1: Clone & Checkout Branch](#step-1-clone--checkout-branch)
   - [Step 2: Dual Python Virtual Environments](#step-2-dual-python-virtual-environments)
   - [Step 3: Provision Local Credentials & Environment Variables](#step-3-provision-local-credentials--environment-variables)
5. [Running the Optimization & AI Engines](#5-running-the-optimization--ai-engines)
   - [1. Medical Stock Redistribution](#1-medical-stock-redistribution)
   - [2. Multi-Destination Transport Optimization (OR-Tools)](#2-multi-destination-transport-optimization-or-tools)
   - [3. Capacity & Time-Window Vehicle Routing (VRP)](#3-capacity--time-window-vehicle-routing-vrp)
   - [4. Emergency Ambulance Dispatch & ETA Triage](#4-emergency-ambulance-dispatch--eta-triage)
   - [5. Facility Emergency Pressure Scoring](#5-facility-emergency-pressure-scoring)
   - [6. Healthcare Workforce Redistribution](#6-healthcare-workforce-redistribution)
   - [7. Automated Medicine Procurement Planner](#7-automated-medicine-procurement-planner)
   - [8. Multi-Day Timeline & Disruption Simulation](#8-multi-day-timeline--disruption-simulation)
   - [9. Federated Learning Mesh (mTLS + FedAvg)](#9-federated-learning-mesh-mtls--fedavg)
   - [10. Differential Privacy & Secure Aggregation Ledger](#10-differential-privacy--secure-aggregation-ledger)
6. [Docker Compose & Full Stack Orchestration](#6-docker-compose--full-stack-orchestration)
   - [Services & Port Mapping Reference](#services--port-mapping-reference)
   - [Stack Launch Commands](#stack-launch-commands)
7. [Testing & Local CI Verification](#7-testing--local-ci-verification)
8. [Database Recovery & Backup Drill](#8-database-recovery--backup-drill)
9. [🤖 AI Assistant & "Vibe Coding" Agent Guide](#9--ai-assistant--vibe-coding-agent-guide)
10. [Troubleshooting & FAQ](#10-troubleshooting--faq)

---

## 1. Overview & Architecture

The `infra/ayan` branch houses the operational foundation, resource scheduling algorithms, federated learning coordinator, and multi-container runtime for the **Sanjeevani Grid** platform.

```
Sanjeevani-Grid (infra/ayan)
├── infra/
│   ├── optimization/         # 8 algorithmic solvers (Redistribution, VRP, Ambulance, Workforce, etc.)
│   ├── federated/            # mTLS Coordinator, FedAvg strategy, Differential Privacy ledger
│   ├── monitoring/           # Prometheus metrics, Alertmanager, Grafana dashboards
│   ├── deployment/           # Automated secret provisioning, local stack verification, backup drills
│   ├── ci-cd/                # Local CI runner (check-local.ps1) & GitHub Actions template
│   ├── docker/               # Hardened Dockerfiles (Federation, Alertmanager, Backend, Frontend)
│   ├── security/             # Vulnerability audit tooling & PostgreSQL recovery engine
│   ├── compose.yaml          # Core federation & privacy containers
│   ├── compose.team.yaml     # Team scaffold overlay (PostgreSQL 16, Redis 7, Backend, Frontend)
│   ├── compose.monitoring.yaml # Prometheus overlay
│   ├── compose.grafana.yaml  # Grafana dashboard overlay
│   ├── compose.alerts.yaml   # Local Alertmanager & webhook receiver overlay
│   └── delivery.py           # Single-command synthetic acceptance demo
├── backend/                  # FastAPI Application scaffold (:8000)
├── frontend/                 # React 18 + Vite SPA (:8080 or :5173)
└── scripts/                  # Cross-platform helper scripts (setup.ps1, setup.sh)
```

---

## 2. Prerequisites Checklist

Ensure your development machine has the following tools installed:

| Tool | Minimum Version | Recommended Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Python** | 3.11+ | **3.12** | Core engines, optimization solvers, and federated server |
| **Node.js** | 20.0+ | **20 LTS** | Frontend UI build & development server |
| **Docker Desktop** | 24.0+ / Compose v2.20+ | Latest with WSL 2 on Windows | Containerized microservices, PostgreSQL, Redis, Grafana |
| **Git** | 2.30+ | Latest | Version control & branch tracking |
| **PowerShell** (Windows) | 5.1+ | 7+ (pwsh) | Automation scripts & local verification |

> [!TIP]
> **Windows Users:** Ensure **Docker Desktop** is using the **WSL 2 backend** and virtualization is enabled in BIOS/Task Manager. Run PowerShell as Administrator if changing execution policy.

---

## 3. 🚀 Quickstart (3-Minute Setup)

### Option A: Algorithmic Quick Check (No Docker required)
If you only need to run tests, solvers, or federated simulations locally:

```powershell
# 1. Switch to infra folder
cd infra

# 2. Setup optimization virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # On Linux/macOS: source .venv/bin/activate
pip install -e ".[transport]"

# 3. Run all optimization unit tests
python -m unittest discover -s optimization/tests -v

# 4. Run the redistribution solver demo
python -m optimization.redistribution --input optimization/redistribution/examples/three_facilities.json
```

### Option B: Complete Local Stack with Docker & Monitoring
To start the entire microservices stack (PostgreSQL, Redis, Backend, Frontend, Federation, Prometheus, Grafana):

```powershell
cd infra

# 1. Create environments and generate secrets (see Section 4 for details)
.\.venv-federated\Scripts\python.exe -m federated.local provision
.\.venv\Scripts\python.exe deployment/prepare_local_env.py
.\.venv-federated\Scripts\python.exe deployment/prepare_demo_secrets.py

# 2. Launch full stack with one command
.\deployment\start-local.ps1 -Team -Monitoring -Grafana

# 3. Verify health of all services
.\.venv-federated\Scripts\python.exe deployment/verify_local.py --monitoring --grafana
```

---

## 4. Step-by-Step Setup Guide

Follow this guide to set up the entire environment from a clean clone.

### Step 1: Clone & Checkout Branch

```bash
git clone https://github.com/SanjeevaniGrid/Sanjeevani-Grid.git
cd Sanjeevani-Grid
git checkout infra/ayan
git status
```

---

### Step 2: Dual Python Virtual Environments

To avoid package conflicts (e.g. between Google OR-Tools and PyTorch/Flower), this branch is engineered around **two isolated virtual environments** inside the `infra/` folder:

1. **`.venv`** -> Dedicated to **Optimization Solvers** (OR-Tools, Linear Programming).
2. **`.venv-federated`** -> Dedicated to **Federated Learning, Security & Cryptography** (Flower, PyTorch CPU, Cryptography, Prometheus).

#### Setting up Environment 1: `.venv` (Optimization)
```powershell
cd infra
python -m venv .venv

# Activate .venv
.\.venv\Scripts\Activate.ps1
# On Linux/macOS: source .venv/bin/activate

# Install optimization dependencies (includes ortools)
python -m pip install --upgrade pip
python -m pip install -e ".[transport]"
deactivate
```

#### Setting up Environment 2: `.venv-federated` (Federation & Monitoring)
```powershell
python -m venv .venv-federated

# Activate .venv-federated
.\.venv-federated\Scripts\Activate.ps1
# On Linux/macOS: source .venv-federated/bin/activate

python -m pip install --upgrade pip
# Install CPU-only PyTorch first (fast & lightweight)
pip install torch==2.14.0 --index-url https://download.pytorch.org/whl/cpu

# Install federated package dependencies (Flower, Cryptography, Protobuf, etc.)
pip install -e ".[federation]"
deactivate
```

---

### Step 3: Provision Local Credentials & Environment Variables

This branch enforces **zero hardcoded secrets** and uses mutual TLS (mTLS) with cryptographically secure tokens. Run these scripts once to generate local development keys:

```powershell
# From the infra/ directory:

# 1. Generate mTLS CA, certificates, and keys for district edge nodes
.\.venv-federated\Scripts\python.exe -m federated.local provision

# 2. Generate secure random passwords for PostgreSQL & JWTs in infra/.env
.\.venv\Scripts\python.exe deployment/prepare_local_env.py

# 3. Generate Grafana admin password & encrypted backup Fernet keys
.\.venv-federated\Scripts\python.exe deployment/prepare_demo_secrets.py
```

> [!IMPORTANT]
> - `deployment/prepare_local_env.py` creates `infra/.env` with strict operating-system permissions (ACLs on Windows, `0600` on POSIX).
> - Never overwrite `infra/.env` once Docker has initialized the database, otherwise PostgreSQL will refuse connection due to mismatched credentials.
> - Your local Grafana admin password is saved securely in:  
>   `infra/federated/secrets/local-dev/grafana-admin-password`

---

## 5. Running the Optimization & AI Engines

All engines can be run directly via CLI from the `infra/` directory using Python.

### 1. Medical Stock Redistribution
Finds the lowest-cost shipment plan to resolve facility drug shortages while enforcing shelf-life and safety stock.
```powershell
.\.venv\Scripts\python.exe -m optimization.redistribution --input optimization/redistribution/examples/three_facilities.json
```
*Add shelf-life policy:*
```powershell
.\.venv\Scripts\python.exe -m optimization.redistribution --input optimization/redistribution/examples/three_facilities.json --policy optimization/redistribution/policy.example.json
```

### 2. Multi-Destination Transport Optimization (OR-Tools)
Solves fixed dispatch costs, multi-facility destinations, and shared source supply constraints.
```powershell
.\.venv\Scripts\python.exe -m optimization.transport --input optimization/transport/example.json --time-limit 5
```

### 3. Capacity & Time-Window Vehicle Routing (VRP)
Calculates optimal single-depot medical delivery routes with vehicle capacities, service windows, and shift limits.
```powershell
.\.venv\Scripts\python.exe -m optimization.routing --input optimization/routing/example.json --time-limit 5
```

### 4. Emergency Ambulance Dispatch & ETA Triage
Ranks emergency ambulances based on real-time transit distance, road condition ETA, and vehicle capability.
```powershell
.\.venv\Scripts\python.exe -m optimization.ambulance --demo
```

### 5. Facility Emergency Pressure Scoring
Evaluates hospital stress based on bed occupancy, emergency influx, and staff saturation.
```powershell
.\.venv\Scripts\python.exe -m optimization.emergency --demo
# Run with emergency resource recommendations:
.\.venv\Scripts\python.exe -m optimization.emergency --demo --resources
```

### 6. Healthcare Workforce Redistribution
Balances critical doctor/nurse shortages between overloaded hospitals.
```powershell
.\.venv\Scripts\python.exe -m optimization.workforce --demo
```

### 7. Automated Medicine Procurement Planner
Generates bulk supplier replenishment orders before stock falls below safety levels.
```powershell
.\.venv\Scripts\python.exe -m optimization.procurement --demo
```

### 8. Multi-Day Timeline & Disruption Simulation
Simulates sequential daily demand variations, supplier delays, and emergency surges.
```powershell
.\.venv\Scripts\python.exe -m optimization.simulation --compare-timelines --demo
```

### 9. Federated Learning Mesh (mTLS + FedAvg)
Simulates regional edge nodes (District A, B, C) training collaborative models with private data:
```powershell
# Run 3 training rounds across simulated regional hospital clients:
.\.venv-federated\Scripts\python.exe -m federated --rounds 3
```

### 10. Differential Privacy & Secure Aggregation Ledger
Simulates Gaussian noise injection and verifies privacy budget ($\epsilon, \delta$) bounds:
```powershell
.\.venv-federated\Scripts\python.exe -m federated.privacy --samples 100
```

---

### 📦 Master Synthetic Acceptance Demo
Run all 10 engines in sequence and generate a verified JSON evidence bundle:
```powershell
.\.venv\Scripts\python.exe delivery.py --demo
```
The summary report and JSON artifacts will be written to `infra/outputs/delivery-<timestamp>/`.

---

## 6. Docker Compose & Full Stack Orchestration

### Services & Port Mapping Reference

| Service | Container Name | Host Port | Protocol | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Frontend SPA** | `sanjeevani-member4-frontend` | `8080` | HTTP | NGINX serving React production bundle |
| **Backend API** | `sanjeevani-member4-backend` | `8000` | HTTP | FastAPI + Instrumented Metrics |
| **PostgreSQL 16**| `sanjeevani-member4-postgres` | `5432` | TCP | Relational DB (AsyncPG / SQLAlchemy) |
| **Redis 7** | `sanjeevani-member4-redis` | Internal | TCP | Distributed caching |
| **Federation Server**| `sanjeevani-member4-server` | `8443` | HTTPS (mTLS) | Secure FedAvg Coordinator |
| **Prometheus** | `sanjeevani-member4-prometheus` | `9090` | HTTP | Time-series metrics collection |
| **Grafana** | `sanjeevani-member4-grafana` | `3000` | HTTP | Federation & System dashboards |
| **Alertmanager**| `sanjeevani-member4-alertmanager`| `9093` | HTTP | Alert routing engine |
| **Alert Receiver**| `sanjeevani-member4-receiver` | `9094` | HTTP | Local webhook validation receiver |

---

### Stack Launch Commands

Use Docker Compose directly or the provided PowerShell helper script:

#### Method 1: Using the PowerShell Helper (Recommended for Windows)
```powershell
cd infra

# Launch Core Team Stack (Postgres, Redis, Backend, Frontend, Federation):
.\deployment\start-local.ps1 -Team

# Launch with Prometheus and Grafana dashboards:
.\deployment\start-local.ps1 -Team -Monitoring -Grafana

# Launch full observability and alert evaluation stack:
.\deployment\start-local.ps1 -Alerts
```

#### Method 2: Native Docker Compose Commands (Cross-Platform)
```bash
cd infra

# 1. Core Federation Server only
docker compose -f compose.yaml up --build -d

# 2. Team Stack (Backend + Frontend + DB + Cache + Federation)
docker compose -f compose.yaml -f compose.team.yaml up --build -d

# 3. Add Prometheus & Grafana Monitoring
docker compose -f compose.yaml -f compose.team.yaml -f compose.monitoring.yaml -f compose.grafana.yaml up --build -d

# 4. Trigger Federated Multi-Round Client Training in Docker
export FEDERATION_CLIENT_ROUNDS=3    # In PowerShell: $env:FEDERATION_CLIENT_ROUNDS = '3'
docker compose -f compose.yaml -f compose.team.yaml --profile training up -d
```

#### Stopping the Stack:
```bash
# Preserve database volumes and state:
docker compose -f compose.yaml -f compose.team.yaml down

# Complete teardown including volumes:
docker compose -f compose.yaml -f compose.team.yaml down -v
```

---

## 7. Testing & Local CI Verification

Run the entire test suite locally before pushing commits:

### A. One-Command Local CI Runner (Windows PowerShell)
```powershell
cd infra
.\ci-cd\check-local.ps1 -Runtime
```
This executes:
1. Optimization unit tests (`optimization/tests`)
2. Federation & authentication tests (`federated/tests`)
3. Monitoring & recovery tests (`monitoring/tests`)
4. Runtime HTTP & mTLS endpoint assertions (`deployment/verify_local.py`)
5. Local alert firing tests (`deployment/verify_local_alerts.py`)

### B. Manual Component Unittests (Cross-Platform)
```bash
# Optimization Suite (using .venv)
.\.venv\Scripts\python.exe -m unittest discover -s optimization/tests -v

# Federation Suite (using .venv-federated)
.\.venv-federated\Scripts\python.exe -m unittest discover -s federated/tests -v

# Monitoring & Recovery Suite (using .venv-federated)
.\.venv-federated\Scripts\python.exe -m unittest discover -s monitoring/tests -v
```

---

## 8. Database Recovery & Backup Drill

To verify data resiliency and zero-data-loss recovery:

```powershell
cd infra

# 1. Execute synthetic backup & point-in-time recovery drill
.\.venv-federated\Scripts\python.exe deployment/recovery_drill.py

# 2. Run standalone PostgreSQL disaster recovery utility
.\.venv\Scripts\python.exe security/postgres_recovery.py --drill
```

---

## 9. 🤖 AI Assistant & "Vibe Coding" Agent Guide

If you are using **Antigravity**, **Cursor**, **GitHub Copilot**, or **Claude Code** to work in this branch, adhere to the following architecture rules:

### Agent Context Guidelines:
1. **Root Directory Context:** All command execution and Python paths should be executed from `infra/` unless building the top-level frontend or backend.
2. **Environment Separation:**
   - When running OR-Tools, Linear Programming, or simulations: Use `infra/.venv/Scripts/python.exe`.
   - When running Flower, PyTorch, mTLS, Cryptography, or Prometheus scripts: Use `infra/.venv-federated/Scripts/python.exe`.
3. **Configuration & Secrets:** Never hardcode secrets. Always read from `infra/.env` or bind mount paths under `infra/federated/secrets/local-dev/`.
4. **Non-Destructive Testing:** Use `delivery.py --demo` to validate changes across all engines simultaneously.

### Ready-to-Use Agent Prompts:

```markdown
### 📋 Agent Prompt: Run All Local Verifications
"Antigravity, please run the Member 4 local test suites in infra/ using both .venv and .venv-federated, check that all unittests pass, and summarize any failures."
```

```markdown
### 📋 Agent Prompt: Start Docker Environment
"Antigravity, verify that infra/.env and credentials exist, check Docker Desktop availability, and spin up the full team stack with monitoring using infra/deployment/start-local.ps1 -Team -Monitoring -Grafana."
```

```markdown
### 📋 Agent Prompt: Run Simulation Comparison
"Antigravity, execute the disruption simulation comparing baseline vs crisis scenarios using python -m optimization.simulation --compare-timelines --demo and report the difference in shortages and stockouts."
```

---

## 10. Troubleshooting & FAQ

### Q1: PowerShell says `cannot be loaded because running scripts is disabled on this system`
**Fix:** Run this command in your PowerShell terminal to allow local script execution for the current session:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### Q2: `prepare_local_env.py` or `federated.local provision` fails with `FileExistsError`
**Fix:** The provisioning scripts are deliberately designed **never to overwrite existing secrets or certificates**. If you need a completely clean start:
```powershell
# Remove existing local-dev bundle and env (Warning: destroys dev keys):
Remove-Item -Recurse -Force infra/federated/secrets/local-dev
Remove-Item -Force infra/.env
# Then re-run provisioning commands from Step 3.
```

### Q3: `docker compose` fails with `MEMBER4_DB_PASSWORD: required variable not set`
**Fix:** Ensure you ran `deployment/prepare_local_env.py` to generate `infra/.env`. When invoking `docker compose`, always execute from inside the `infra/` folder where `compose.yaml` and `infra/.env` reside.

### Q4: Port conflicts (e.g. `port 5432 or 8000 already in use`)
**Fix:** If you already have a local PostgreSQL or FastAPI instance running on your host machine:
1. Stop the local service: `Stop-Service postgresql*` (Windows) or `sudo systemctl stop postgresql` (Linux).
2. Or change the host port mapping in `infra/compose.team.yaml` (e.g. change `'127.0.0.1:5432:5432'` to `'127.0.0.1:5433:5432'`).

### Q5: How do I access Grafana?
- **URL:** [http://127.0.0.1:3000](http://127.0.0.1:3000)
- **Username:** `admin`
- **Password:** Open `infra/federated/secrets/local-dev/grafana-admin-password` in an editor or view it via PowerShell:
  ```powershell
  Get-Content infra/federated/secrets/local-dev/grafana-admin-password
  ```

---

## 👨‍💻 Maintainer & Support
For questions or issues relating to this branch, reach out to **Ayan Kumar Mondal** or open an issue on the repository. Happy coding! 🚀
