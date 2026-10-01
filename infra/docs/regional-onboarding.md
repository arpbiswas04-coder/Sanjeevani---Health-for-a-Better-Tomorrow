# Regional and BRICS onboarding contract

Current demonstrations use synthetic districts, not real BRICS participants.
The coordinator allowlist maps each node ID to its region. Each new partner must
agree on node identity, region, operator, certificate lifecycle/revocation,
network endpoint, model/schema version, public roster and permitted metrics.
Use a distinct client certificate and admission secret for each node; never share
one district identity across organizations. Raw health data stays local.

Member 3 supplies architecture, preprocessing version, safe tensor artifact and
checksum, feature/target schema and eligible local train/evaluation data. Reject
unknown model versions or shapes; never load untrusted pickle artifacts. Model
acceptance criteria and permitted metric summaries require agreement before joining.
Member 4 configures the allowlist and validates a synthetic join, rejected unknown
identity, stale/replayed update, recorded metadata, aggregation and restart recovery.

The existing clear-update HTTPS path is not the masked privacy reference. Real
private training additionally requires authenticated peer-key distribution,
separate client isolation, agreed privacy unit/budget, protected durable accounting
and a reviewed secure aggregation implementation. Current fixed-roster dropout
aborts the entire aggregation; operators cannot bypass that by reducing the roster.

Partner operators own deployment/data eligibility and credentials; Member 3 owns
real models, and the team owns cross-border agreements. These external dependencies
are not satisfied by renaming synthetic districts after countries.
