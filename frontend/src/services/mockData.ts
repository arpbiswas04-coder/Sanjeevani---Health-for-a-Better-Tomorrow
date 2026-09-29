import { RiskLevel } from '@/types';

export interface FacilityMapItem {
  id: string;
  name: string;
  type: 'PHC' | 'CHC' | 'District Hospital' | 'Medical College' | 'Warehouse';
  state: string;
  district: string;
  latitude: number;
  longitude: number;
  risk_level: RiskLevel;
  medicine_availability_pct: number;
  bed_occupancy_pct: number;
  staff_status: string;
  icu_beds_free: number;
  oxygen_supply_hours: number;
}

export interface InventoryItem {
  id: string;
  name: string;
  category: 'Critical Medicine' | 'Oxygen' | 'Antibiotic' | 'Vaccine' | 'Consumables';
  batch_no: string;
  current_stock: number;
  reorder_level: number;
  unit: string;
  expiry_date: string;
  days_until_expiry: number;
  days_of_supply: number;
  facility_name: string;
  risk_level: RiskLevel;
  stockout_probability: number;
}

export interface BedTelemetry {
  type: 'ICU Beds' | 'Ventilator Beds' | 'Oxygen Supported' | 'General Ward';
  total: number;
  occupied: number;
  available: number;
  occupancy_rate: number;
  status: RiskLevel;
}

export interface WorkforceItem {
  department: string;
  doctors_on_duty: number;
  nurses_on_duty: number;
  total_staff: number;
  shift_attendance_pct: number;
  doctor_patient_ratio: string;
  stress_index: RiskLevel;
}

export interface DiseaseSurveillance {
  disease: string;
  cases_this_week: number;
  change_pct: number;
  hotspot_districts: string[];
  severity: RiskLevel;
}

export interface FederatedNode {
  id: string;
  facility_name: string;
  region: string;
  status: 'online' | 'training' | 'offline';
  local_samples: number;
  privacy_epsilon: number;
  last_sync_time: string;
  round_accuracy: number;
}

// 1. Mock Facilities across Indian Health Nodes
export const MOCK_FACILITIES: FacilityMapItem[] = [
  {
    id: 'fac-001',
    name: 'All India Institute of Medical Sciences (AIIMS)',
    type: 'Medical College',
    state: 'Delhi',
    district: 'New Delhi',
    latitude: 28.5672,
    longitude: 77.2100,
    risk_level: 'low',
    medicine_availability_pct: 94,
    bed_occupancy_pct: 91,
    staff_status: 'Optimal (98%)',
    icu_beds_free: 28,
    oxygen_supply_hours: 120,
  },
  {
    id: 'fac-002',
    name: 'Ram Manohar Lohia District Hospital',
    type: 'District Hospital',
    state: 'Uttar Pradesh',
    district: 'Lucknow',
    latitude: 26.8467,
    longitude: 80.9462,
    risk_level: 'high',
    medicine_availability_pct: 58,
    bed_occupancy_pct: 96,
    staff_status: 'Strained (72%)',
    icu_beds_free: 4,
    oxygen_supply_hours: 18,
  },
  {
    id: 'fac-003',
    name: 'Kanpur Central Medical Depot & Warehouse',
    type: 'Warehouse',
    state: 'Uttar Pradesh',
    district: 'Kanpur',
    latitude: 26.4499,
    longitude: 80.3319,
    risk_level: 'low',
    medicine_availability_pct: 98,
    bed_occupancy_pct: 0,
    staff_status: 'Full Roster',
    icu_beds_free: 0,
    oxygen_supply_hours: 240,
  },
  {
    id: 'fac-004',
    name: 'Varanasi Rural Community Health Centre (CHC)',
    type: 'CHC',
    state: 'Uttar Pradesh',
    district: 'Varanasi',
    latitude: 25.3176,
    longitude: 82.9739,
    risk_level: 'moderate',
    medicine_availability_pct: 74,
    bed_occupancy_pct: 78,
    staff_status: 'Normal (84%)',
    icu_beds_free: 6,
    oxygen_supply_hours: 48,
  },
  {
    id: 'fac-005',
    name: 'Patna Sadar Hospital',
    type: 'District Hospital',
    state: 'Bihar',
    district: 'Patna',
    latitude: 25.5941,
    longitude: 85.1376,
    risk_level: 'critical',
    medicine_availability_pct: 42,
    bed_occupancy_pct: 99,
    staff_status: 'Critical Shortage (61%)',
    icu_beds_free: 1,
    oxygen_supply_hours: 9,
  },
  {
    id: 'fac-006',
    name: 'Bhopal Memorial Hospital',
    type: 'Medical College',
    state: 'Madhya Pradesh',
    district: 'Bhopal',
    latitude: 23.2599,
    longitude: 77.4126,
    risk_level: 'low',
    medicine_availability_pct: 88,
    bed_occupancy_pct: 82,
    staff_status: 'Adequate (92%)',
    icu_beds_free: 19,
    oxygen_supply_hours: 72,
  },
  {
    id: 'fac-007',
    name: 'Jaipur SMS Medical Center',
    type: 'Medical College',
    state: 'Rajasthan',
    district: 'Jaipur',
    latitude: 26.9124,
    longitude: 75.7873,
    risk_level: 'moderate',
    medicine_availability_pct: 79,
    bed_occupancy_pct: 87,
    staff_status: 'Normal (88%)',
    icu_beds_free: 12,
    oxygen_supply_hours: 60,
  },
  {
    id: 'fac-008',
    name: 'Primary Health Centre (PHC) Malihabad',
    type: 'PHC',
    state: 'Uttar Pradesh',
    district: 'Lucknow',
    latitude: 26.9200,
    longitude: 80.7100,
    risk_level: 'critical',
    medicine_availability_pct: 38,
    bed_occupancy_pct: 92,
    staff_status: 'Severely Understaffed',
    icu_beds_free: 0,
    oxygen_supply_hours: 6,
  },
];

// 2. Mock Inventory Items
export const MOCK_INVENTORY: InventoryItem[] = [
  {
    id: 'inv-001',
    name: 'Liquid Medical Oxygen (Type-D 47L Cylinders)',
    category: 'Oxygen',
    batch_no: 'OXY-2026-B81',
    current_stock: 45,
    reorder_level: 120,
    unit: 'cylinders',
    expiry_date: '2028-12-31',
    days_until_expiry: 820,
    days_of_supply: 2.1,
    facility_name: 'Patna Sadar Hospital',
    risk_level: 'critical',
    stockout_probability: 0.94,
  },
  {
    id: 'inv-002',
    name: 'Insulin Human Regular (100 IU/mL, 10mL)',
    category: 'Critical Medicine',
    batch_no: 'INS-8841-A',
    current_stock: 120,
    reorder_level: 400,
    unit: 'vials',
    expiry_date: '2026-10-18',
    days_until_expiry: 19,
    days_of_supply: 4.8,
    facility_name: 'RML Hospital Lucknow',
    risk_level: 'high',
    stockout_probability: 0.88,
  },
  {
    id: 'inv-003',
    name: 'Ceftriaxone Injection IP 1g',
    category: 'Antibiotic',
    batch_no: 'CEF-9023-K',
    current_stock: 2400,
    reorder_level: 1000,
    unit: 'vials',
    expiry_date: '2027-05-15',
    days_until_expiry: 228,
    days_of_supply: 34.0,
    facility_name: 'AIIMS New Delhi',
    risk_level: 'low',
    stockout_probability: 0.05,
  },
  {
    id: 'inv-004',
    name: 'Paracetamol IV Infusion 1000mg/100mL',
    category: 'Critical Medicine',
    batch_no: 'PCM-1102-D',
    current_stock: 580,
    reorder_level: 800,
    unit: 'bottles',
    expiry_date: '2026-10-08',
    days_until_expiry: 9,
    days_of_supply: 5.5,
    facility_name: 'PHC Malihabad',
    risk_level: 'critical',
    stockout_probability: 0.91,
  },
  {
    id: 'inv-005',
    name: 'Oseltamivir Phosphate Capsules 75mg',
    category: 'Critical Medicine',
    batch_no: 'TAM-4432-Z',
    current_stock: 350,
    reorder_level: 500,
    unit: 'strips',
    expiry_date: '2027-02-28',
    days_until_expiry: 152,
    days_of_supply: 14.2,
    facility_name: 'Varanasi Rural CHC',
    risk_level: 'moderate',
    stockout_probability: 0.42,
  },
  {
    id: 'inv-006',
    name: 'Normal Saline (0.9% NaCl, 500mL)',
    category: 'Consumables',
    batch_no: 'NS-7721-P',
    current_stock: 14200,
    reorder_level: 5000,
    unit: 'units',
    expiry_date: '2027-08-30',
    days_until_expiry: 335,
    days_of_supply: 45.0,
    facility_name: 'Kanpur Central Warehouse',
    risk_level: 'low',
    stockout_probability: 0.02,
  },
];

// 3. Bed Telemetry Breakdown
export const MOCK_BEDS: BedTelemetry[] = [
  { type: 'ICU Beds', total: 640, occupied: 588, available: 52, occupancy_rate: 91.8, status: 'high' },
  { type: 'Ventilator Beds', total: 280, occupied: 262, available: 18, occupancy_rate: 93.5, status: 'critical' },
  { type: 'Oxygen Supported', total: 2400, occupied: 1950, available: 450, occupancy_rate: 81.25, status: 'moderate' },
  { type: 'General Ward', total: 8500, occupied: 6380, available: 2120, occupancy_rate: 75.0, status: 'low' },
];

// 4. Workforce Breakdown
export const MOCK_WORKFORCE: WorkforceItem[] = [
  { department: 'Emergency & Trauma', doctors_on_duty: 42, nurses_on_duty: 114, total_staff: 156, shift_attendance_pct: 95, doctor_patient_ratio: '1 : 14', stress_index: 'high' },
  { department: 'Intensive Care (ICU)', doctors_on_duty: 28, nurses_on_duty: 92, total_staff: 120, shift_attendance_pct: 98, doctor_patient_ratio: '1 : 4', stress_index: 'moderate' },
  { department: 'General Medicine / OPD', doctors_on_duty: 68, nurses_on_duty: 140, total_staff: 208, shift_attendance_pct: 89, doctor_patient_ratio: '1 : 42', stress_index: 'critical' },
  { department: 'Pediatrics & Neonatal', doctors_on_duty: 22, nurses_on_duty: 56, total_staff: 78, shift_attendance_pct: 92, doctor_patient_ratio: '1 : 18', stress_index: 'low' },
];

// 5. Disease Trends
export const MOCK_DISEASES: DiseaseSurveillance[] = [
  { disease: 'Dengue Serotype-2', cases_this_week: 1420, change_pct: 28.4, hotspot_districts: ['Lucknow', 'Patna', 'Kanpur'], severity: 'high' },
  { disease: 'Acute Respiratory Infection (ARI)', cases_this_week: 3890, change_pct: 12.1, hotspot_districts: ['New Delhi', 'Jaipur'], severity: 'moderate' },
  { disease: 'Viral Gastroenteritis', cases_this_week: 840, change_pct: -6.5, hotspot_districts: ['Varanasi', 'Bhopal'], severity: 'low' },
  { disease: 'Japanese Encephalitis', cases_this_week: 94, change_pct: 45.0, hotspot_districts: ['Gorakhpur', 'Muzaffarpur'], severity: 'critical' },
];

// 6. Federated Edge Nodes
export const MOCK_FEDERATED_NODES: FederatedNode[] = [
  { id: 'node-aiims-delhi', facility_name: 'AIIMS New Delhi Cluster', region: 'North', status: 'online', local_samples: 148200, privacy_epsilon: 0.85, last_sync_time: '2 mins ago', round_accuracy: 96.8 },
  { id: 'node-rml-lucknow', facility_name: 'RML Lucknow Edge Server', region: 'North-Central', status: 'training', local_samples: 84200, privacy_epsilon: 1.10, last_sync_time: 'Just now', round_accuracy: 94.2 },
  { id: 'node-pmch-patna', facility_name: 'Patna Medical College Mesh', region: 'East', status: 'training', local_samples: 92100, privacy_epsilon: 0.95, last_sync_time: '4 mins ago', round_accuracy: 93.9 },
  { id: 'node-bhopal-edge', facility_name: 'Bhopal Regional Hub', region: 'Central', status: 'online', local_samples: 61400, privacy_epsilon: 1.05, last_sync_time: '8 mins ago', round_accuracy: 95.5 },
  { id: 'node-sms-jaipur', facility_name: 'SMS Jaipur Node', region: 'West', status: 'offline', local_samples: 78000, privacy_epsilon: 1.00, last_sync_time: '38 mins ago', round_accuracy: 91.4 },
];

// 7. Time series trends for Charts
export const MOCK_TRENDS = [
  { day: 'Mon', demand: 2400, supply: 2800, admissions: 310, bedOccupancy: 84 },
  { day: 'Tue', demand: 2750, supply: 2700, admissions: 345, bedOccupancy: 86 },
  { day: 'Wed', demand: 3100, supply: 2650, admissions: 390, bedOccupancy: 89 },
  { day: 'Thu', demand: 3600, supply: 2500, admissions: 420, bedOccupancy: 93 },
  { day: 'Fri', demand: 4100, supply: 2450, admissions: 480, bedOccupancy: 96 },
  { day: 'Sat', demand: 4400, supply: 3200, admissions: 510, bedOccupancy: 94 },
  { day: 'Sun', demand: 3900, supply: 3400, admissions: 460, bedOccupancy: 91 },
];
