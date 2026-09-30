"""
Sanjeevani Grid - Expiry Prediction Configuration
ai/expiry_prediction/config.py

Hyperparameters, thresholds, and configuration constants for the deterministic
batch expiry and spoilage risk prediction pipeline.
"""

from typing import Any, Dict

# ── Model Identity ──────────────────────────────────────────────────────────
DEFAULT_MODEL_VERSION: str = "expiry_spoilage_v1.0.0"

# ── Numeric Safety ──────────────────────────────────────────────────────────
NEAR_ZERO_CONSUMPTION: float = 1e-8

# ── Wastage Risk Thresholds (wastage_ratio) ─────────────────────────────────
# wastage_ratio = likely_unused_quantity / batch_stock
#
# The project source-of-truth documents (docs/team/MEMBER_3_AI.md,
# docs/api/API_CONVENTIONS.md, ai/AGENTS.md) mandate the four canonical risk
# levels (low / moderate / high / critical) but do NOT prescribe any numeric
# wastage thresholds.
#
# The values below are IMPLEMENTATION-CHOSEN DEFAULTS required to make the
# four-level risk assignment deterministic and configurable. They are NOT
# derived from any project specification or external standard.
#
#   wastage_ratio = likely_unused_quantity / batch_stock
#   - If batch_stock <= 0: LOW (no stock at risk of spoiling)
#   - If days_to_expiry <= 0 and batch_stock > 0: CRITICAL (already expired)
#   - If wastage_ratio >= WASTAGE_CRITICAL_RATIO (0.50): CRITICAL (>= 50% spoilage)
#   - If wastage_ratio >= WASTAGE_HIGH_RATIO (0.20): HIGH (>= 20% spoilage)
#   - If wastage_ratio >= WASTAGE_MODERATE_RATIO (0.05): MODERATE (>= 5% spoilage)
#   - If wastage_ratio < WASTAGE_MODERATE_RATIO: LOW (< 5% spoilage)
#
WASTAGE_CRITICAL_RATIO: float = 0.50   # implementation default — not a project spec value
WASTAGE_HIGH_RATIO: float = 0.20       # implementation default — not a project spec value
WASTAGE_MODERATE_RATIO: float = 0.05   # implementation default — not a project spec value


def placeholder() -> Dict[str, Any]:
    """Preserve backwards compatibility with early scaffold tests."""
    return {"module": "expiry_prediction.config", "status": "placeholder"}
