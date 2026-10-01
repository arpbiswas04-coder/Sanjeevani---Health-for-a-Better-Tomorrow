# Run your first Member 4 feature

## Requirements

Python 3.11 or newer. The first optimizer uses only Python's standard library:
there is nothing to install to run it from the `infra/` directory.

From the repository root, first enter your implementation directory:

```powershell
cd infra
```

All subsequent commands in this guide run inside `infra/`.

On Windows, use `py` instead of `python` if that is your Python launcher. If no
Python is on PATH, use an installed Python executable by its full path.

On the Windows machine used to build this milestone, Python is not on PATH.
This bundled interpreter was verified successfully. Run this from the repository
root's `infra/` directory in PowerShell (the path is specific to this machine):

```powershell
$member4Python = 'C:\Users\ayank\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $member4Python -m optimization.redistribution --input optimization/redistribution/examples/three_facilities.json
& $member4Python -m unittest discover -s optimization/tests -v
```

For the remaining examples, replace `python` with `& $member4Python` in the same
PowerShell session if needed.

## 1. Run the three-facility example

```powershell
python -m optimization.redistribution --input optimization/redistribution/examples/three_facilities.json
```

Expected allocation:

| Source | Destination | Units | Cost (paise) |
| --- | --- | ---: | ---: |
| fac-11 | fac-10 | 800 | 80000 |
| fac-12 | fac-10 | 400 | 60000 |

Total: 1200 units, 140000 paise (INR 1400), zero unresolved shortage. These are
synthetic costs, not real transport quotations. Inventory is not modified.

## 2. Run insufficient-stock example

```powershell
python -m optimization.redistribution --input optimization/redistribution/examples/partial_shortage.json
```

Expected: 800 recommended units, 400 unresolved, `status: partial`.

## 3. Apply a shelf-life policy

```powershell
python -m optimization.redistribution --input optimization/redistribution/examples/three_facilities.json --policy optimization/redistribution/policy.example.json
```

Change a synthetic candidate's expiry to 3 days and rerun with the example
7-day policy: that candidate is excluded, with a reason in the output.

## 4. Verify the feature

```powershell
python -m unittest discover -s optimization/tests -v
python -m optimization.redistribution --healthcheck
```

Tests include 100 small random cases checked against an exhaustive allocation
oracle, as well as failure cases and command-line integration.

## 5. Integrate with the team

Read `docs/redistribution-contract.md` with Member 2 before wiring real data.
Use `recommend(request, policy)` in the existing backend service. Member 1 can
display transfers, exclusions, costs and unresolved shortage. Approval and stock
reservation remain backend responsibilities.

## Your learning task

Run both examples, inspect their JSON, change synthetic demand and surplus,
and explain why each result changed. Then read `engine.py` and its tests.
Continue with the milestone order in `docs/member4-roadmap.md`.
