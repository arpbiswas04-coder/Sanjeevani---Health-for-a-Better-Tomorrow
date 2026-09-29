# Sanjeevani Grid - Optimization Subsystem

This subsystem implements mathematical modeling, linear programming (LP), mixed-integer programming (MIP), constraint satisfaction, and vehicle routing using **Google OR-Tools**.

## Subsystem Modules

- `common/`: Shared base solvers, graph helpers, and distance matrix providers.
- `redistribution/`: Multi-facility inventory balancing and cross-level medical stock transfers.
- `procurement/`: Optimal bulk purchasing schedules under budget, lead-time, and shelf-life constraints.
- `workforce/`: Shift scheduling and doctor/nurse rota balancing under labor regulations.
- `routing/`: Dynamic multi-depot vehicle routing (VRP/VRPTW) for cold-chain medicine delivery.
- `ambulance/`: Dynamic fleet positioning and rapid emergency dispatch dispatching.
- `emergency/`: Surge response disaster load balancing and triage resource allocation.

## Setup and Testing

```bash
cd optimization
pip install -r requirements.txt
pytest tests/
```
