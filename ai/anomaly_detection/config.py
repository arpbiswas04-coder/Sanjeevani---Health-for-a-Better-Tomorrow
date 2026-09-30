"""
Sanjeevani Grid - Anomaly Detection Configuration
ai/anomaly_detection/config.py

Hyperparameters, thresholds, and target domains for clinical, operational,
and inventory anomaly detection.
"""

from typing import Any, Dict, Tuple

# ── Model Identity ──────────────────────────────────────────────────────────
DEFAULT_MODEL_VERSION: str = "anomaly_detector_v1.0.0"

# ── Documented Anomaly Targets (Member 3 Spec) ──────────────────────────────
TARGET_SUDDEN_INVENTORY_DECREASE: str = "sudden_inventory_decrease"
TARGET_ABNORMAL_CONSUMPTION: str = "abnormal_consumption"
TARGET_UNUSUAL_DISEASE_COUNT: str = "unusual_disease_count"
TARGET_UNEXPECTED_ATTENDANCE_DROP: str = "unexpected_attendance_drop"
TARGET_SUSPICIOUS_MANUAL_STOCK_ADJUSTMENT: str = "suspicious_manual_stock_adjustment"

VALID_ANOMALY_TARGETS: Tuple[str, ...] = (
    TARGET_SUDDEN_INVENTORY_DECREASE,
    TARGET_ABNORMAL_CONSUMPTION,
    TARGET_UNUSUAL_DISEASE_COUNT,
    TARGET_UNEXPECTED_ATTENDANCE_DROP,
    TARGET_SUSPICIOUS_MANUAL_STOCK_ADJUSTMENT,
)

# ── Statistical Detection Parameters ────────────────────────────────────────
# Normal consistency factor: 1 / norm.ppf(0.75) ≈ 1.4826
# Scales Median Absolute Deviation (MAD) to estimate standard deviation sigma
# for Gaussian-distributed baselines.
MAD_NORMAL_SCALE: float = 1.4826
EPSILON: float = 1e-8

# ── Implementation-Chosen Anomaly & Risk Thresholds ────────────────────────
# The project source documents (docs/team/MEMBER_3_AI.md, docs/api/API_CONVENTIONS.md,
# ai/AGENTS.md) mention target domains and statistical approaches (robust z-score,
# Isolation Forest, LOF) but do NOT prescribe specific numeric cutoff values.
#
# The thresholds below are IMPLEMENTATION-CHOSEN DEFAULTS for the robust
# z-score detector:
#   |Z| >= Z_CRITICAL_THRESHOLD (4.5)  → CRITICAL risk
#   |Z| >= Z_HIGH_THRESHOLD (3.0)      → HIGH risk (classified as anomaly)
#   |Z| >= Z_MODERATE_THRESHOLD (2.0)  → MODERATE risk (elevated / warning)
#   |Z| <  Z_MODERATE_THRESHOLD (2.0)  → LOW risk (normal baseline)
#
DEFAULT_Z_THRESHOLD: float = 3.0       # implementation default — not a project spec value
Z_CRITICAL_THRESHOLD: float = 4.5      # implementation default — not a project spec value
Z_HIGH_THRESHOLD: float = 3.0          # implementation default — not a project spec value
Z_MODERATE_THRESHOLD: float = 2.0      # implementation default — not a project spec value


def placeholder() -> Dict[str, Any]:
    """Preserve backwards compatibility with early scaffold tests."""
    return {"module": "anomaly_detection.config", "status": "placeholder"}
