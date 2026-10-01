"""Tests for operational recommendation engines."""
import sys
from pathlib import Path

_infra = str(Path(__file__).resolve().parents[2])
if _infra not in sys.path or sys.path[0] != _infra:
    sys.path.insert(0, _infra)


