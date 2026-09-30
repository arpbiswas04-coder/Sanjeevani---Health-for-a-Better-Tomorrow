# Member 4 requirement-to-evidence checklist

Scope: local synthetic demo, all implementation under `infra/`. Assignment text is
requirements context; teammate changes and external deployment require separate authority.
Verified means the stated local scope has evidence, not production certification.

| Assignment requirement / feature IDs | Classification | Implementation and evidence / remaining owner |
| --- | --- | --- |
| Redistribution 15–17 | Verified locally | `optimization/redistribution`, transport solver; ten-demo evidence and existing focused checks; Member 2 live stock integration blocked |
| Staff recommendations 37 | Verified locally | `optimization/workforce`; live roster/approval belongs to Member 2 |
| Emergency prioritization 40–42 | Verified locally | `optimization/emergency`; configured EPI/resource orchestration; Member 3 real risk scores pending |
| Simulations 43–44, 95–96 | Verified locally, bounded scope | `optimization/simulation`; stock ledger, arrivals, losses, expiry and disruption comparisons; real predictions pending |
| Federation 45–46, 48–49 | Verified locally | Three district clients, FedAvg, schema checks, metadata, authenticated HTTPS; checkpoint model version 4 confirms upgraded aggregation persisted |
| BRICS network 47 | Blocked by external participants | Configurable region/node metadata exists; no real cross-country nodes, agreements or eligible data supplied |
| Privacy 50–52 | Prototype implemented | Gaussian clipping/noise, accounting and masked aggregate; durable mode and limitations in privacy guide; real-data audit/peer authentication blocked |
| Personalization 53 / FedProx | Optional | Assignment explicitly presents fine-tuning/FedProx as optional next steps |
| Human approval 57 | Contract implemented; blocked by Member 2 | Recommendation-only outputs; backend must authorize, persist and atomically reserve/apply approved actions |
| Resilience orchestration 67 | Verified synthetic contract | Transparent synthetic scenario-service score, separately versioned policy; no clinical validation |
| Ambulance 88 / routing 89 | Verified locally | Eligibility/ETA ranking and OR-Tools routing; live fleet/maps and dispatch belong to integration owners |
| Docker/local startup | Verified locally | Seven persistent services started; six endpoint/monitoring checks passed; no need to add unused Celery/MLflow solely from recommended topology |
| CI/CD | Implemented but inactive | `ci-cd/member4-ci.yml`; activation in root `.github/workflows/` blocked by infra-only scope; cloud target/credentials absent |
| Security / zero trust 100–101 | Partial, release blocked | mTLS, HMAC/replay/rate controls, local secret ACLs; application RBAC belongs to Member 2; unresolved image/crypto findings documented |
| Backup/recovery 102 | Verified synthetic recovery; operations prepared | PostgreSQL encrypted dump/restore matched rows/constraints; real application data, off-host destination and independent key custody pending |
| Monitoring 103 | API/scrape verified; visual check blocked | Six checks + promtool rules passed; browser URL safety guard stopped visual inspection; alert receiver not supplied |
| Production/cloud deployment | Blocked by target/credentials and security gates | No deployment claimed; local target was explicitly selected |

Acceptance paths: `docs/local-demo-acceptance.md`, `outputs/acceptance-ql08940l.json`,
`outputs/backups/drill-0j4yt0nw/report.json`, `outputs/security/`.
Thirty federation checks passed following prior dependency upgrades. New changes
receive focused checks recorded in the completion evidence rather than rerunning unrelated optimizers.
