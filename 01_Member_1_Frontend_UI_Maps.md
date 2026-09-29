# Member 1 Blueprint — Frontend, UI/UX & Maps

## Mission

Own the complete user-facing experience for **Sanjeevani Grid**.

Your responsibility is to make the platform:

- fast
- responsive
- easy to understand
- role-aware
- map-centric
- accessible
- multilingual
- smoothly integrated with backend APIs

## Main Tech Stack

- React
- TypeScript
- Vite
- Tailwind CSS
- React Router
- TanStack Query
- Zustand
- React Hook Form
- Zod
- Recharts or Apache ECharts
- Leaflet or Mapbox GL
- i18next
- PWA / IndexedDB

## Features You Own

Primary ownership:

- 2. National Health Command Dashboard
- 3. State and District-Level Dashboard
- 4. Interactive Health Resource Map
- 5. PHC/Hospital Management UI
- 7. Real-Time Stock Monitoring UI
- 12. Expiry Tracking UI
- 23. Warehouse Dashboard UI
- 26. Bed Availability UI
- 28. Patient Footfall UI
- 30. Disease Trend UI
- 33. Personnel Management UI
- 34. Attendance UI
- 38. Doctor-to-Patient Ratio UI
- 39. Emergency Command Mode UI
- 48. Federated Model Dashboard UI
- 58. Alert Management UI
- 62. Analytics Dashboard
- 63. Historical Trend Analysis
- 64. Resource Utilization Analytics
- 65. Cost Analytics
- 66. Wastage Reduction Dashboard
- 67. Supply Chain Resilience Score UI
- 68. Health Resource Risk Score UI
- 69. District Comparison
- 70. Performance Dashboard
- 93. Public Health Risk Heatmap
- 97. Multi-Language Support
- 98. Accessibility Features
- 99. Mobile Responsive Interface
- 104. Admin Dashboard UI

## Folder Ownership

```text
frontend/
└── src/
    ├── app/
    ├── assets/
    ├── components/
    ├── layouts/
    ├── pages/
    ├── modules/
    │   ├── auth/
    │   ├── dashboard/
    │   ├── map/
    │   ├── facilities/
    │   ├── inventory/
    │   ├── beds/
    │   ├── workforce/
    │   ├── patients/
    │   ├── disease/
    │   ├── emergency/
    │   ├── federated-ai/
    │   ├── analytics/
    │   ├── equipment/
    │   └── admin/
    ├── hooks/
    ├── services/
    ├── store/
    ├── types/
    ├── utils/
    └── i18n/
```

## Page Build Order

### Phase 1 — Foundation

Build:

- App shell
- Navbar
- Sidebar
- Top bar
- Protected route component
- Loading screen
- Error state
- Toast system
- Modal system

### Phase 2 — Authentication

Pages:

- Login
- Registration
- MFA verification
- Forgot password
- Profile
- Settings

Backend dependency:
- Member 2 provides auth endpoints

### Phase 3 — Main Dashboards

Build:

- National Dashboard
- State Dashboard
- District Dashboard
- Facility Dashboard

Each dashboard should support:

- KPI cards
- alert cards
- charts
- drill-down filters
- last updated time
- export button

### Phase 4 — Resource Map

Build:

- PHC/hospital markers
- warehouse markers
- colored risk markers
- disease heatmap
- emergency heatmap
- facility popup
- district filter
- state filter

Required data contract:

```ts
type FacilityMapItem = {
  id: string;
  name: string;
  type: string;
  latitude: number;
  longitude: number;
  risk_level: "low" | "moderate" | "high" | "critical";
  medicine_availability_pct: number;
  bed_occupancy_pct: number;
  staff_status: string;
};
```

### Phase 5 — Inventory UI

Build:

- Medicine table
- Batch table
- Low-stock page
- Expiry page
- Stock history
- Barcode scan screen
- Transfer request screen

### Phase 6 — Health Resource UI

Build:

- Bed dashboard
- Workforce dashboard
- Attendance dashboard
- Patient footfall
- Disease trends
- Equipment status
- Ambulance status

### Phase 7 — AI UI

Show:

- Demand forecast graph
- Stock-out probability
- Expiry risk
- Bed forecast
- Patient forecast
- Workforce forecast
- Confidence score
- Explainability panel

Example card:

```text
Medicine: Insulin
Predicted stock-out: 5 days
Risk: 91%
Reason:
- demand increased 27%
- current stock covers only 4.8 days
- supplier lead time is 8 days
```

### Phase 8 — Emergency Command UI

Build:

- Emergency dashboard
- district priority table
- crisis map
- resource shortage panel
- emergency recommendations
- scenario simulation form
- what-if comparison

### Phase 9 — Federated AI UI

Build:

- Active nodes
- offline nodes
- current training round
- global model accuracy
- local model accuracy
- privacy status
- last sync

## API Integration Pattern

All API calls must live in:

```text
frontend/src/services/
```

Example:

```ts
export const getFacilities = async () => {
  const response = await api.get("/api/v1/facilities");
  return response.data;
};
```

Never call `fetch()` directly inside random components.

Use TanStack Query:

```ts
const { data, isLoading } = useQuery({
  queryKey: ["facilities"],
  queryFn: getFacilities,
});
```

## Shared API Type Rules

Keep shared frontend interfaces in:

```text
frontend/src/types/
```

Do not invent different property names from backend JSON.

If backend sends:

```json
{
  "medicine_id": "med-101",
  "current_stock": 350
}
```

frontend must use the same fields or one explicit mapper.

## UI State Rules

Use:

- server state → TanStack Query
- global UI/session state → Zustand
- form state → React Hook Form
- validation → Zod

## Responsive Breakpoints

Every page must work at:

- mobile
- tablet
- laptop
- desktop

No dashboard should require horizontal scrolling unless it is a data table.

## Accessibility

Implement:

- semantic HTML
- visible focus states
- keyboard navigation
- aria labels
- sufficient contrast
- chart text alternatives

## Multilingual Architecture

Structure:

```text
src/i18n/
├── en.json
├── hi.json
└── bn.json
```

Never hardcode user-visible text in components when translation is expected.

## Offline Mode

Member 1 owns the browser side:

- PWA
- service worker
- IndexedDB
- offline forms
- local sync queue
- connectivity indicator

Member 2 owns the synchronization API.

## Testing

Use:

- Vitest
- React Testing Library
- Playwright for critical flows

Must test:

- login
- role redirects
- inventory page
- map
- alerts
- emergency dashboard

## Definition of Done

A frontend feature is complete only if:

- UI is responsive
- loading state exists
- empty state exists
- error state exists
- API connected
- permission checks added
- TypeScript has no errors
- no secrets are hardcoded
- mobile view works
- basic tests pass


## GitHub Collaboration Rules

To keep integration smooth:

### Branches

- `main` → production-ready branch
- `develop` → integration branch
- `frontend/member-1`
- `backend/member-2`
- `ai/member-3`
- `infra/member-4`

Never push feature work directly to `main`.

### Daily workflow

```bash
git checkout develop
git pull origin develop

git checkout <your-branch>
git merge develop
```

After your work:

```bash
git add .
git commit -m "feat: clear description"
git push origin <your-branch>
```

Create a Pull Request into `develop`.

### Commit format

Use:

```text
feat: add medicine demand forecast chart
fix: resolve stock API pagination bug
refactor: restructure facility service
docs: update setup instructions
test: add redistribution unit tests
chore: update dependencies
```

### Before every Pull Request

- Pull latest `develop`
- Resolve conflicts locally
- Run project tests
- Run linting
- Confirm `.env` secrets are not committed
- Confirm frontend/backend contracts match
- Add screenshots or API examples where useful

### Shared files: do not change casually

Coordinate before editing:

- `docker-compose.yml`
- `.env.example`
- root `README.md`
- `frontend/src/types/api.ts`
- `backend/app/schemas/`
- API path conventions
- database migrations already used by other members


## Dependency Contract With Other Members

### From Member 2
You need:
- REST endpoints
- OpenAPI schema
- authentication
- pagination contract
- role permissions

### From Member 3
You need prediction response schemas.

Recommended:

```json
{
  "entity_id": "med-001",
  "prediction": 724,
  "confidence": 0.91,
  "horizon_days": 7,
  "explanation": [
    "seasonal demand increase",
    "recent patient growth"
  ]
}
```

### From Member 4
You need:
- federated node status
- optimization recommendations
- monitoring status
- infrastructure environment variables

## Your Final Deliverables

- Complete frontend
- responsive dashboards
- all maps
- all analytics visualizations
- emergency UI
- federated AI UI
- multilingual support
- PWA/offline frontend
- tested frontend build
