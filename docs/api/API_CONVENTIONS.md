# Sanjeevani Grid API Conventions

All team members must adhere to these conventions across frontend, backend, AI endpoints, and external integrations.

## 1. Base URL & Versioning

All endpoints must be prefixed with the API version:
```
/api/v1
```

## 2. Standard Success Response Format

Every JSON response returning data must adhere to the wrapper:
```json
{
  "success": true,
  "data": {},
  "message": null
}
```
- `success`: Always `true` for 2xx responses.
- `data`: Object, array, or primitive payload.
- `message`: Optional user-friendly notification message string or `null`.

## 3. Standard Error Response Format

Every non-2xx error response must return:
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Readable error message"
  }
}
```

Standard error codes:
- `UNAUTHORIZED`: 401
- `FORBIDDEN`: 403
- `NOT_FOUND`: 404
- `VALIDATION_ERROR`: 422
- `INTERNAL_SERVER_ERROR`: 500

## 4. Identifiers & Timestamps

- **Identifiers**: All entity IDs must be valid UUID v4 strings (e.g., `3fa85f64-5717-4562-b3fc-2c963f66afa6`).
- **Timestamps**: All dates and timestamps must be ISO 8601 strings in UTC format (e.g., `2026-09-29T15:30:00Z`).

## 5. Shared Risk Levels

All forecasting, clinical triage, and supply-chain risk scoring components use four canonical risk levels:

| Risk Level | Description | Color Code / Status |
| :--- | :--- | :--- |
| `low` | Normal operations, adequate buffer capacity | Green |
| `moderate` | Approaching reorder thresholds or elevated queue | Yellow / Amber |
| `high` | Critical stock levels or imminent ward saturation | Orange |
| `critical` | Stockout, emergency surge, or code red state | Red |

## 6. HTTP Methods

- `GET`: Retrieve resource(s) - Idempotent
- `POST`: Create resource or execute non-idempotent computational action
- `PUT`: Complete update / replace of resource
- `PATCH`: Partial update of specific fields
- `DELETE`: Remove resource
