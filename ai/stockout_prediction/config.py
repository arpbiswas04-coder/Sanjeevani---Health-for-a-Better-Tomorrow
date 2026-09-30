"""
Sanjeevani Grid - Stockout Prediction Configuration
ai/stockout_prediction/config.py

Hyperparameters and threshold constants for the deterministic stock-coverage
prediction pipeline.  Centralised here so that predict.py and features.py stay
free of magic numbers, making policy changes auditable in a single file.
"""

# ── Model Identity ──────────────────────────────────────────────────────────
DEFAULT_MODEL_VERSION: str = "stockout_coverage_v1.0.0"

# ── Numeric Safety ──────────────────────────────────────────────────────────
# Daily consumption values at or below this threshold are treated as
# effectively zero to prevent division-by-zero in days_until_stockout.
NEAR_ZERO_CONSUMPTION: float = 1e-8

# ── Risk Level Thresholds (coverage_ratio) ──────────────────────────────────
# coverage_ratio = available_quantity / demand_during_lead_time
#
# The project source-of-truth documents (docs/team/MEMBER_3_AI.md,
# docs/team/INTEGRATION_GUIDE.md, ai/AGENTS.md) specify the four canonical
# risk levels (low / moderate / high / critical) via docs/api/API_CONVENTIONS.md
# but do NOT prescribe any numeric coverage thresholds.
#
# The values below are IMPLEMENTATION-CHOSEN DEFAULTS required to make the
# four-level risk assignment deterministic and configurable.  They are NOT
# derived from any project requirement or external standard.  They should be
# reviewed and adjusted by the team when real operational data is available.
#
#   Stockout predicted (available < demand_during_lead_time):
#       coverage_ratio < COVERAGE_CRITICAL_THRESHOLD  → CRITICAL
#       coverage_ratio >= COVERAGE_CRITICAL_THRESHOLD → HIGH
#
#   No stockout predicted (available >= demand_during_lead_time):
#       coverage_ratio < COVERAGE_MODERATE_THRESHOLD  → MODERATE
#       coverage_ratio >= COVERAGE_MODERATE_THRESHOLD → LOW
#
COVERAGE_CRITICAL_THRESHOLD: float = 0.5   # implementation default — not a project spec value
COVERAGE_MODERATE_THRESHOLD: float = 1.5   # implementation default — not a project spec value


def placeholder() -> dict:
    """Preserve backwards compatibility with early scaffold tests."""
    return {"module": "stockout_prediction.config", "status": "placeholder"}
