# Synthetic operational resilience

Runnable synthetic example from `infra/`:

```powershell
.\.venv-federated\Scripts\python.exe -m optimization.simulation.resilience --input optimization/simulation/resilience-example.json
```

`optimization.simulation.resilience.assess_resilience(comparison, policy)` wraps
the existing shared-snapshot timeline comparison. `comparison` uses the contract
in `timeline-comparison.md`. Policy contains a `version` and `scenario_weights`
mapping covering every scenario ID exactly. Nonnegative weights are normalized;
their finite sum must be positive.

The score is `100 × sum(normalized weight × fulfilled transfer-demand fraction)`.
It measures service in the supplied synthetic scenarios. It is not clinical risk,
a validated health-system resilience index, a probability, or authorization to
dispatch resources. Scenario selection and weights must be agreed by the team.
It reports shortage and fraction deltas alongside the score. Positive-weight
zero-demand scenarios produce an unscored result instead of an invented 100.
Policy version and comparison hash accompany every recommendation-only response.

CLI: `python -m optimization.simulation.resilience --input input.json`, where the
JSON contains `comparison` and `policy`. Existing delay/disruption/stock-loss
scenarios can be used unchanged. Real forecasts and facility state remain upstream
integration requirements; warehouse outages can be represented as source blocking
only within the existing single-active-batch simulation limits.
