.PHONY: help init up down restart build logs ps clean test test-backend test-frontend install-frontend install-backend

help:
	@echo "Sanjeevani Grid - Command Reference"
	@echo "==================================="
	@echo "Integrated setup: DEVELOPMENT.md. Root Compose targets below are legacy scaffolding."
	@echo "make init             - Copy .env.example to .env if missing"
	@echo "make up               - Start all services with Docker Compose"
	@echo "make down             - Stop all Docker Compose services"
	@echo "make restart          - Restart all Docker Compose services"
	@echo "make build            - Rebuild all Docker images"
	@echo "make logs             - View logs from all services"
	@echo "make ps               - View status of services"
	@echo "make test             - Run backend and frontend tests"
	@echo "make install-frontend - Install npm packages in frontend"
	@echo "make install-backend  - Install pip requirements in backend"
	@echo "make clean            - Remove cache, node_modules, and temporary files"

init:
	@if [ ! -f .env ]; then cp .env.example .env && echo "Created .env from .env.example"; else echo ".env already exists"; fi

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart

build:
	docker compose build

logs:
	docker compose logs -f

ps:
	docker compose ps

install-frontend:
	cd frontend && npm ci

install-backend:
	cd backend && python -c "import pathlib,sys; assert sys.prefix != sys.base_prefix and pathlib.Path(sys.prefix).resolve() == pathlib.Path('.venv').resolve(), 'Activate backend/.venv first'" && python -m pip install -r requirements.txt

test-backend:
	cd backend && python -c "import pathlib,sys; assert sys.prefix != sys.base_prefix and pathlib.Path(sys.prefix).resolve() == pathlib.Path('.venv').resolve(), 'Activate backend/.venv first'" && python -m pytest -q

test-frontend:
	cd frontend && npm test && npm run build

test: test-backend test-frontend

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf frontend/dist backend/.pytest_cache
