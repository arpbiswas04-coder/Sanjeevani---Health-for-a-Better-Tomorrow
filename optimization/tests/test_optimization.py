"""Tests for optimization module placeholders."""
from optimization.redistribution.solver import redistributionSolver
from optimization.routing.solver import routingSolver


def test_optimization_solvers():
    r_solver = redistributionSolver()
    r_res = r_solver.solve({})
    assert r_res["status"] == "optimal"

    route_solver = routingSolver()
    route_res = route_solver.solve({})
    assert route_res["status"] == "optimal"
