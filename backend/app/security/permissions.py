# Explicit capability catalogue. Roles grant only capabilities present here.
PERMISSIONS = (
    'inventory.read', 'inventory.write', 'inventory.transfer', 'inventory.recall',
    'facility.manage', 'procurement.read', 'procurement.write', 'procurement.approve',
    'workforce.read', 'workforce.write', 'beds.read', 'beds.write', 'equipment.read',
    'equipment.write', 'alerts.read', 'alerts.manage', 'reports.read', 'reports.export',
    'integration.read', 'integration.write', 'admin.users', 'admin.config',
    'emergency.activate', 'federation.manage', 'audit.read', 'sync.write',
)
