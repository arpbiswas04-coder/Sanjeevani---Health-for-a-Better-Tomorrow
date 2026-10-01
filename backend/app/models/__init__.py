from app.models.platform import (
    AuditLog, Facility, Inventory, Medicine, MedicineBatch, Permission,
    Role, RolePermission, StockTransaction, User, UserRole,
)

from app.models.identity import AuthSession, PasswordReset, UserFacility

from app.models.geography import Country, State, District, Block

from app.models.stock import MutationReceipt, StockPolicy, RecallRecord, ExpiryRecord

from app.models.transfers import TransferRequest, TransferItem, TransferApproval, TransferTracking

from app.models.supply import Supplier, Warehouse, WarehouseInventory, PurchaseOrder, PurchaseOrderItem, ProcurementHistory, Shipment, ShipmentHistory

from app.models.operations import TemperatureObservation, BedCapacity, BedOccupancyHistory, StaffRole, Staff, Shift, Attendance, PatientFootfall, DiseaseCount

from app.models.alerts import AlertRule, Alert, NotificationLog, EscalationRule, EscalationHistory

from app.models.assets import Equipment, MaintenanceRecord, Ambulance

from app.models.integrations import Recommendation, PopulationSnapshot, WeatherCache, Barcode, BackupRecord
from app.models.identity import UserDistrict

from app.models.report_jobs import ReportJob, ReportSchedule
from app.models.sync import SyncClock, SyncChange
