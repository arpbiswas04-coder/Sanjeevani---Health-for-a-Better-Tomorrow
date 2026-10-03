"""Explicit public response contracts. Keep these independent of ORM runtime reflection.

Flexible JSON payload fields are intentional extension points; public records and
computed results have named, typed fields. Credentials and stored export bytes
are never response fields.
"""
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from typing import Any, Generic, Literal, TypeVar
from pydantic import BaseModel, ConfigDict
from app.schemas.response import ErrorDetail
from app.integrations.fhir import Location
from app.integrations.weather import CurrentWeather


class Output(BaseModel):
    model_config=ConfigDict(extra='forbid')


T=TypeVar('T')


class Success(Output,Generic[T]):
    success:Literal[True]
    data:T


class Error(Output):
    success:Literal[False]
    error:ErrorDetail


ERROR_RESPONSES={status:{'model':Error} for status in (400,401,403,404,409,422,429,500,503)}
BINARY_CONTENT={media:{'schema':{'type':'string','format':'binary'}} for media in (
    'text/csv','application/pdf','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}


class UserView(Output):
    username: str
    active: bool
    scope_mode: str
    mfa_required: bool
    id: UUID
    created_at: datetime
    updated_at: datetime


class CurrentUserView(UserView):
    roles: list[str]
    permissions: list[str]
    facility_ids: list[UUID]
    district_ids: list[UUID]


class RoleView(Output):
    name: str
    id: UUID
    created_at: datetime
    updated_at: datetime


class PermissionView(Output):
    name: str
    id: UUID
    created_at: datetime
    updated_at: datetime


class FacilityView(Output):
    facility_type: str
    address: str | None
    block_id: UUID | None
    latitude: float | None
    longitude: float | None
    contact: str | None
    version: int
    source_device: str | None
    name: str
    code: str
    active: bool
    id: UUID
    created_at: datetime
    updated_at: datetime


class MedicineView(Output):
    name: str
    code: str
    unit: str
    id: UUID
    created_at: datetime
    updated_at: datetime


class MedicineBatchView(Output):
    medicine_id: UUID
    batch_number: str
    expires_on: date
    recalled: bool
    id: UUID
    created_at: datetime
    updated_at: datetime


class InventoryView(Output):
    facility_id: UUID
    batch_id: UUID
    quantity: int
    reserved: int
    id: UUID
    created_at: datetime
    updated_at: datetime


class StockTransactionView(Output):
    inventory_id: UUID
    actor_id: UUID
    quantity: int
    kind: str
    reference: str
    id: UUID
    created_at: datetime
    updated_at: datetime


class AuditLogView(Output):
    actor_id: UUID
    action: str
    details: object
    id: UUID
    created_at: datetime
    updated_at: datetime


class CountryView(Output):
    name: str
    code: str
    id: UUID
    created_at: datetime
    updated_at: datetime


class StateView(Output):
    country_id: UUID
    name: str
    code: str
    id: UUID
    created_at: datetime
    updated_at: datetime


class DistrictView(Output):
    state_id: UUID
    name: str
    code: str
    id: UUID
    created_at: datetime
    updated_at: datetime


class BlockView(Output):
    district_id: UUID
    name: str
    code: str
    id: UUID
    created_at: datetime
    updated_at: datetime


class StockPolicyView(Output):
    facility_id: UUID
    medicine_id: UUID
    critical_days: float
    low_days: float
    lead_days: int
    safety_stock: int
    minimum_history_days: int
    expiry_warning_days: int
    id: UUID
    created_at: datetime
    updated_at: datetime


class RecallRecordView(Output):
    batch_id: UUID
    reason: str
    severity: str
    initiated_by: UUID
    status: str
    resolution: str | None
    id: UUID
    created_at: datetime
    updated_at: datetime


class TransferRequestView(Output):
    source_id: UUID
    destination_id: UUID
    requested_by: UUID
    status: str
    reference: str
    id: UUID
    created_at: datetime
    updated_at: datetime


class TransferItemView(Output):
    transfer_id: UUID
    batch_id: UUID
    quantity: int
    id: UUID
    created_at: datetime
    updated_at: datetime


class TransferTrackingView(Output):
    transfer_id: UUID
    actor_id: UUID
    status: str
    note: str
    id: UUID
    created_at: datetime
    updated_at: datetime


class SupplierView(Output):
    name: str
    code: str
    contact: str | None
    address: str | None
    active: bool
    lead_days: int
    id: UUID
    created_at: datetime
    updated_at: datetime


class WarehouseView(Output):
    facility_id: UUID
    capacity: object
    active: bool
    id: UUID
    created_at: datetime
    updated_at: datetime


class PurchaseOrderView(Output):
    reference: str
    supplier_id: UUID
    facility_id: UUID
    status: str
    created_by: UUID
    id: UUID
    created_at: datetime
    updated_at: datetime


class PurchaseOrderItemView(Output):
    order_id: UUID
    medicine_id: UUID
    quantity: int
    received: int
    unit_price: float
    id: UUID
    created_at: datetime
    updated_at: datetime


class ShipmentView(Output):
    reference: str
    order_id: UUID | None
    transfer_id: UUID | None
    supplier_id: UUID | None
    facility_id: UUID
    origin: str
    transport: object
    status: str
    dispatched_at: datetime | None
    expected_at: datetime
    arrived_at: datetime | None
    id: UUID
    created_at: datetime
    updated_at: datetime


class ShipmentHistoryView(Output):
    shipment_id: UUID
    actor_id: UUID
    status: str
    note: str
    id: UUID
    created_at: datetime
    updated_at: datetime


class TemperatureObservationView(Output):
    facility_id: UUID
    shipment_id: UUID | None
    observed_at: datetime
    temperature: float
    minimum: float
    maximum: float
    source: str
    external_id: str
    excursion: bool
    id: UUID
    created_at: datetime
    updated_at: datetime


class BedCapacityView(Output):
    facility_id: UUID
    bed_type: str
    capacity: int
    occupied: int
    id: UUID
    created_at: datetime
    updated_at: datetime


class BedOccupancyHistoryView(Output):
    bed_id: UUID
    capacity: int
    occupied: int
    actor_id: UUID
    id: UUID
    created_at: datetime
    updated_at: datetime


class StaffRoleView(Output):
    name: str
    id: UUID
    created_at: datetime
    updated_at: datetime


class StaffView(Output):
    facility_id: UUID
    staff_role_id: UUID
    code: str
    display_name: str
    active: bool
    id: UUID
    created_at: datetime
    updated_at: datetime


class ShiftView(Output):
    staff_id: UUID
    facility_id: UUID
    starts_at: datetime
    ends_at: datetime
    cancelled: bool
    id: UUID
    created_at: datetime
    updated_at: datetime


class AttendanceView(Output):
    staff_id: UUID
    facility_id: UUID
    day: date
    status: str
    id: UUID
    created_at: datetime
    updated_at: datetime


class PatientFootfallView(Output):
    facility_id: UUID
    day: date
    category: str
    count: int
    version: int
    source_device: str | None
    id: UUID
    created_at: datetime
    updated_at: datetime


class DiseaseCountView(Output):
    facility_id: UUID
    day: date
    category: str
    count: int
    version: int
    source_device: str | None
    id: UUID
    created_at: datetime
    updated_at: datetime


class AlertRuleView(Output):
    facility_id: UUID
    kind: str
    threshold: float
    window_days: int
    severity: str
    active: bool
    id: UUID
    created_at: datetime
    updated_at: datetime


class AlertView(Output):
    facility_id: UUID
    rule_id: UUID
    kind: str
    severity: str
    source: str
    active_key: str | None
    status: str
    details: object
    acknowledged_at: datetime | None
    resolved_at: datetime | None
    id: UUID
    created_at: datetime
    updated_at: datetime


class NotificationLogView(Output):
    dedup_key: str
    recipient_id: UUID
    facility_id: UUID
    channel: str
    template: str
    payload: object
    status: str
    attempts: int
    failure_reason: str | None
    delivered_at: datetime | None
    id: UUID
    created_at: datetime
    updated_at: datetime


class EscalationRuleView(Output):
    rule_id: UUID
    after_minutes: int
    recipient_id: UUID
    channel: str
    active: bool
    id: UUID
    created_at: datetime
    updated_at: datetime


class EscalationHistoryView(Output):
    alert_id: UUID
    escalation_rule_id: UUID
    notification_id: UUID
    id: UUID
    created_at: datetime
    updated_at: datetime


class EquipmentView(Output):
    facility_id: UUID
    code: str
    equipment_type: str
    status: str
    last_maintenance: date | None
    next_maintenance: date | None
    notes: str | None
    id: UUID
    created_at: datetime
    updated_at: datetime


class MaintenanceRecordView(Output):
    equipment_id: UUID
    performed_on: date
    next_due: date
    notes: str
    actor_id: UUID
    id: UUID
    created_at: datetime
    updated_at: datetime


class AmbulanceView(Output):
    facility_id: UUID
    vehicle_id: str
    status: str
    operational: bool
    latitude: float | None
    longitude: float | None
    id: UUID
    created_at: datetime
    updated_at: datetime


class RecommendationView(Output):
    source_id: UUID
    destination_id: UUID
    submitted_by: UUID
    status: str
    payload: object
    model_version: str
    transfer_id: UUID | None
    id: UUID
    created_at: datetime
    updated_at: datetime


class PopulationSnapshotView(Output):
    district_id: UUID
    population: int
    source: str
    source_url: str
    as_of: date
    retrieved_at: datetime
    id: UUID
    created_at: datetime
    updated_at: datetime


class BarcodeView(Output):
    code: str
    medicine_id: UUID | None
    batch_id: UUID | None
    id: UUID
    created_at: datetime
    updated_at: datetime


class BackupRecordView(Output):
    artifact_key: str
    status: str
    checksum: str | None
    size_bytes: int
    started_at: datetime
    completed_at: datetime | None
    verified_at: datetime | None
    id: UUID
    created_at: datetime
    updated_at: datetime


class ReportJobView(Output):
    owner_id: UUID
    facility_id: UUID
    kind: str
    format: str
    status: str
    media_type: str | None
    failure_code: str | None
    expires_at: datetime
    id: UUID
    created_at: datetime
    updated_at: datetime


class ReportScheduleView(Output):
    owner_id: UUID
    facility_id: UUID
    kind: str
    format: str
    interval_minutes: int
    next_run: datetime
    active: bool
    id: UUID
    created_at: datetime
    updated_at: datetime


class TokenPair(Output):
    access_token:str
    refresh_token:str
    token_type:Literal['bearer']
    expires_in:int


class Identity(Output):
    id:UUID
    username:str


class Message(Output):
    message:str


class PublicConfig(Output):
    auth_rate_limit:int
    auth_rate_window_seconds:int
    weather_cache_seconds:int
    backup_retention_days:int
    backup_max_age_hours:int


class RootInfo(Output):
    service:str
    documentation:str
    health:str


class Received(Output):
    inventory_id:UUID
    batch_id:UUID
    quantity:int


class Adjusted(Output):
    inventory_id:UUID
    quantity:int


class Allocation(Output):
    batch_id:UUID
    quantity:int


class Issued(Output):
    allocations:list[Allocation]


class InventoryWithBatch(InventoryView):
    batch:MedicineBatchView


class NearbyFacility(FacilityView):
    distance_km:float


class DaysOfStock(Output):
    current_stock:int
    average_daily_consumption:float|None
    days_of_stock:float|None
    history_days:int
    status:Literal['no_history','insufficient_history','zero_consumption','critical','low','normal']
    safety_stock:int
    transferable_stock:int
    reorder_point:int|None
    suggested_quantity:int|None


class Expiry(Output):
    inventory:InventoryView
    batch:MedicineBatchView
    state:Literal['expired','upcoming']


class Trace(Output):
    batch:MedicineBatchView
    inventory:list[InventoryView]
    transactions:list[StockTransactionView]


class TransferDetail(TransferRequestView):
    items:list[TransferItemView]
    history:list[TransferTrackingView]


class OrderDetail(PurchaseOrderView):
    items:list[PurchaseOrderItemView]


class OrderReceived(Output):
    order:PurchaseOrderView
    stock:Received


class SupplierMetrics(Output):
    order_count:int
    eligible_order_count:int
    fulfilment_rate:float|None
    quantity_fulfilment_rate:float|None
    average_delivery_delay_days:float|None


class BedsAvailable(BedCapacityView):
    available:int


class TaskQueued(Output):
    task_id:str


class RetryResult(Output):
    id:UUID
    status:str


class StockReport(InventoryView):
    medicine_id:UUID
    medicine_name:str
    medicine_code:str
    unit:str
    batch_number:str
    expires_on:date
    recalled:bool
    facility_name:str
    facility_code:str
    available:int
    expiry_state:Literal['expired','upcoming']


ReportRow=StockReport|TransferRequestView|PurchaseOrderView|StaffView|BedCapacityView|AlertView


class ReportResult(Output):
    rows:list[ReportRow]
    has_more:bool
    offset:int
    limit:int


Aggregate=PatientFootfallView|DiseaseCountView
Geography=CountryView|StateView|DistrictView|BlockView
Operation=TemperatureObservationView|BedsAvailable|StaffView|ShiftView|AttendanceView|PatientFootfallView|DiseaseCountView
Asset=EquipmentView|AmbulanceView


class SyncItem(PatientFootfallView):
    change_sequence:int


class SyncCursor(Output):
    after_sequence:int
    until_sequence:int


class SyncPull(Output):
    items:list[SyncItem]
    next_cursor:SyncCursor|None
    watermark:int
    has_more:bool


class SyncPush(Output):
    results:list[Aggregate]


class Consumption(Output):
    day:date
    consumed:int


class OptimizationContext(Output):
    facility:FacilityView
    stock:DaysOfStock
    predicted_demand:None
    transport_metadata:None


class Weather(Output):
    source:Literal['open-meteo']
    current:CurrentWeather
    retrieved_at:datetime
    cached:bool


class BackupStatus(Output):
    latest:BackupRecordView|None
    healthy:bool
    retention_days:int
    storage_name:str|None
    verification_reported:bool
    execution_owner:str


class ColdChainSampleView(Output):
    id:UUID
    observed_at:datetime
    facility_id:UUID
    temperature:float
    minimum:float
    maximum:float
    excursion:bool
    created_at:datetime
    updated_at:datetime
