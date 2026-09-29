# Sanjeevani Grid - Federated AI Subsystem

Privacy-preserving collaborative machine learning subsystem for hospitals, clinics, and health departments.

## Purpose

Hospitals cannot share raw Electronic Health Records (EHR) due to HIPAA, GDPR, and national medical privacy regulations. The Federated AI subsystem enables:
- Local training on edge hospital clusters.
- Centralized aggregation of weight updates (gradients) without transmitting raw patient records.
- Differential privacy guarantees and gradient clipping.

## Framework Support

The directory structure is ready for:
- [Flower (flwr)](https://flower.ai/)
- [NVIDIA FLARE](https://github.com/NVIDIA/NVFlare)

## Structure

```
federated/
├── server/          # Aggregation server and coordinator
├── clients/         # Hospital edge client nodes
├── strategies/      # Aggregation logic (FedAvg, FedProx, etc.)
├── privacy/         # Differential privacy and secure aggregation
├── configs/         # YAML configurations for server and client nodes
├── tests/           # Unit tests
├── requirements.txt # Python dependencies
└── README.md
```

## Running Tests

```bash
cd federated
pip install -r requirements.txt
pytest tests/
```
