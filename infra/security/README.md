# Security & Compliance Architecture

The [CI scanning template](../docs/security-scanning.md) now includes independent
dependency audits and a federation image vulnerability scan. It remains inactive
under `infra/ci-cd/`; no scan results are claimed.

Implemented federation component: [signed update admission](../docs/federated-authentication.md)
with per-node HMAC keys and replay protection. It is an opt-in library boundary;
network deployment and the broader guidelines below remain pending.

Guidelines for securing Sanjeevani Grid infrastructure:
- Principle of Least Privilege (PoLP) across Docker and cloud IAM.
- Zero-trust network segmentation between Edge nodes, AI engines, and Core DB.
- Vault / Secret Manager integration for zero committed credentials.
- OWASP Top 10 API Security compliance.
