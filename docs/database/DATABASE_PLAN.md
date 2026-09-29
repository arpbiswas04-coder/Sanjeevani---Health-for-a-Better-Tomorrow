# Database Schema & Migration Plan

Backend uses PostgreSQL 16 managed through SQLAlchemy 2.0 and Alembic migrations.

## Core Domain Entities (Planned)

1. **Facilities (`facilities`)**: Hospitals, clinics, blood banks, and primary health centers.
2. **Inventory (`inventory_items`, `batches`)**: Medicines, oxygen cylinders, PPE, vaccines, batch numbers, and expiry dates.
3. **Beds & Capacity (`ward_beds`, `occupancy_logs`)**: ICU, ventilator, and general bed telemetry.
4. **Workforce (`staff_members`, `duty_shifts`)**: Doctors, nurses, paramedics, and rota allocations.
5. **Transfers & Logistics (`transfer_requests`, `shipments`)**: Inter-facility redistribution records.
6. **Alerts & Predictions (`risk_alerts`, `forecast_snapshots`)**: AI-generated predictions and early warnings.

## Guidelines for Member 2

- Always create SQLAlchemy models inside `backend/app/models/`.
- Use UUID primary keys for all business tables.
- Generate migrations with `alembic revision --autogenerate -m "description"`.
- Run migrations with `alembic upgrade head`.
