# Federated learning — planned

This directory is reserved for the Member 4 federation milestone. No training or
privacy guarantees are implemented yet.

Planned structure: `server/`, `clients/`, `strategies/`, `privacy/`, `configs/`,
and `tests/`.

Before implementation, agree with Member 3 on one model, preprocessing contract,
training data partition, and evaluation metrics. Begin with three simulated
regional clients and FedAvg. Add node authentication, dropout handling, metrics,
and checkpoints before differential privacy and secure aggregation.

