"""Optimization root package. Authoritative implementation is in infra/optimization."""
import sys
from pathlib import Path

_infra_dir = str(Path(__file__).resolve().parent / "infra")
if _infra_dir not in sys.path or sys.path[0] != _infra_dir:
    sys.path.insert(0, _infra_dir)

_infra_opt = str(Path(__file__).resolve().parent / "infra" / "optimization")
if _infra_opt not in __path__:
    __path__.insert(0, _infra_opt)

