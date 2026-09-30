# Flower/PyTorch regional adapter

Three regional subprocesses now train a synthetic PyTorch linear model through
Flower's NumPyClient callbacks. The existing coordinator validates updates,
computes sample-weighted FedAvg and maintains checkpoint-compatible state.
Held-out synthetic samples stay in each worker; only parameters, counts and
metrics return to the coordinator. The coordinator reports evaluation model
versions, worker failures and whether final evaluation completed.

This is a local subprocess harness, not Flower's network runtime. Processes run
as the same OS user and provide no security boundary. It does not implement
node authentication, secure aggregation, differential privacy or a healthcare
forecasting model. Fresh workers are started for every round and final evaluation;
this startup overhead is acceptable for a small demonstration.

## Environment

Run from `infra/`. Keep this environment separate from the optimizer: Flower
uses an independently managed environment from OR-Tools 9.15.6755. Do not
install the transport and federation extras into the same environment.

```powershell
python -m venv .venv-federated
.\.venv-federated\Scripts\python.exe -m pip install torch==2.14.0 --index-url https://download.pytorch.org/whl/cpu
.\.venv-federated\Scripts\python.exe -m pip install ".[federation]"
```

The local environment is already installed with these versions. No GPU is needed.

## Run and recover

```powershell
.\.venv-federated\Scripts\python.exe -m federated.regional --rounds 1 --checkpoint federated/checkpoints/regional.json
.\.venv-federated\Scripts\python.exe -m federated.regional --rounds 2 --resume federated/checkpoints/regional.json --checkpoint federated/checkpoints/regional.json
```

At least two valid client updates are required. Worker timeouts default to 60
seconds; override with `--timeout` (1–300 seconds). Round status describes
aggregation; inspect `final_evaluation.complete` separately for evaluation success.
Checkpoint durability and trust limitations remain as documented in
[checkpoint recovery](federated-checkpoints.md). Paths must stay inside `infra/`.

The optional focused check is:

```powershell
.\.venv-federated\Scripts\python.exe -m unittest federated.tests.test_regional -v
```

Next: authenticated network execution, then Member 3's model/data contract and
regional evaluation criteria. Real patient data must not be substituted into this
synthetic demo without implementing that integration and its access controls.
