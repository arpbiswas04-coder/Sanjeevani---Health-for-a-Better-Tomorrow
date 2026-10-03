// Response types transcribed from the actual FastAPI OpenAPI schema. No UI-only telemetry fields.
export interface FacilityView {
  facility_type: string;
  address: string | null;
  block_id: string | null;
  latitude: number | null;
  longitude: number | null;
  contact: string | null;
  version: number;
  source_device: string | null;
  name: string;
  code: string;
  active: boolean;
  id: string;
  created_at: string;
  updated_at: string;
}
export interface MedicineView {
  name: string;
  code: string;
  unit: string;
  id: string;
  created_at: string;
  updated_at: string;
}
export interface MedicineBatchView {
  medicine_id: string;
  batch_number: string;
  expires_on: string;
  recalled: boolean;
  id: string;
  created_at: string;
  updated_at: string;
}
export interface InventoryWithBatch {
  facility_id: string;
  batch_id: string;
  quantity: number;
  reserved: number;
  id: string;
  created_at: string;
  updated_at: string;
  batch: MedicineBatchView;
}
export interface DaysOfStock {
  current_stock: number;
  average_daily_consumption: number | null;
  days_of_stock: number | null;
  history_days: number;
  status: "no_history" | "insufficient_history" | "zero_consumption" | "critical" | "low" | "normal";
  safety_stock: number;
  transferable_stock: number;
  reorder_point: number | null;
  suggested_quantity: number | null;
}
export interface Expiry {
  inventory: InventoryView;
  batch: MedicineBatchView;
  state: "expired" | "upcoming";
}
export interface AlertView {
  facility_id: string;
  rule_id: string;
  kind: string;
  severity: string;
  source: string;
  active_key: string | null;
  status: string;
  details: unknown;
  acknowledged_at: string | null;
  resolved_at: string | null;
  id: string;
  created_at: string;
  updated_at: string;
}
export interface AlertRuleView {
  facility_id: string;
  kind: string;
  threshold: number;
  window_days: number;
  severity: string;
  active: boolean;
  id: string;
  created_at: string;
  updated_at: string;
}
export interface BedsAvailable {
  facility_id: string;
  bed_type: string;
  capacity: number;
  occupied: number;
  id: string;
  created_at: string;
  updated_at: string;
  available: number;
}
export interface EquipmentView {
  facility_id: string;
  code: string;
  equipment_type: string;
  status: string;
  last_maintenance: string | null;
  next_maintenance: string | null;
  notes: string | null;
  id: string;
  created_at: string;
  updated_at: string;
}
export interface AmbulanceView {
  facility_id: string;
  vehicle_id: string;
  status: string;
  operational: boolean;
  latitude: number | null;
  longitude: number | null;
  id: string;
  created_at: string;
  updated_at: string;
}
export interface ReportResult {
  rows: (StockReport | TransferRequestView | PurchaseOrderView | StaffView | BedCapacityView | AlertView)[];
  has_more: boolean;
  offset: number;
  limit: number;
}
export interface StockReport {
  facility_id: string;
  batch_id: string;
  quantity: number;
  reserved: number;
  id: string;
  created_at: string;
  updated_at: string;
  medicine_id: string;
  medicine_name: string;
  medicine_code: string;
  unit: string;
  batch_number: string;
  expires_on: string;
  recalled: boolean;
  facility_name: string;
  facility_code: string;
  available: number;
  expiry_state: "expired" | "upcoming";
}
export interface InventoryView {
  facility_id: string;
  batch_id: string;
  quantity: number;
  reserved: number;
  id: string;
  created_at: string;
  updated_at: string;
}
export interface TransferRequestView {
  source_id: string;
  destination_id: string;
  requested_by: string;
  status: string;
  reference: string;
  id: string;
  created_at: string;
  updated_at: string;
}
export interface PurchaseOrderView {
  reference: string;
  supplier_id: string;
  facility_id: string;
  status: string;
  created_by: string;
  id: string;
  created_at: string;
  updated_at: string;
}
export interface StaffView {
  facility_id: string;
  staff_role_id: string;
  code: string;
  display_name: string;
  active: boolean;
  id: string;
  created_at: string;
  updated_at: string;
}
export interface BedCapacityView {
  facility_id: string;
  bed_type: string;
  capacity: number;
  occupied: number;
  id: string;
  created_at: string;
  updated_at: string;
}
export interface CountryView {
  name: string;
  code: string;
  id: string;
  created_at: string;
  updated_at: string;
}
export interface StateView {
  country_id: string;
  name: string;
  code: string;
  id: string;
  created_at: string;
  updated_at: string;
}
export interface DistrictView {
  state_id: string;
  name: string;
  code: string;
  id: string;
  created_at: string;
  updated_at: string;
}
export interface BlockView {
  district_id: string;
  name: string;
  code: string;
  id: string;
  created_at: string;
  updated_at: string;
}
