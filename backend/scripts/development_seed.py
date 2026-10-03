"""Owned synthetic operational fixtures and password-safe development accounts.

Only the guarded development_data CLI calls these helpers. All operational writes
are transactional and use existing service logic for ledger/state/sync invariants.
"""
from datetime import datetime,timedelta,timezone
from getpass import getpass
from hashlib import sha256
import json
import os
import random
from uuid import UUID

from sqlalchemy import select,func
from app.core.database import AsyncSessionLocal
from app.models import User,Role,Permission,RolePermission,UserRole,Facility,Medicine,AuditLog
from app.models.identity import UserFacility
from app.models.stock import MutationReceipt,StockPolicy
from app.models.operations import StaffRole
from app.models.assets import Equipment
from app.models.supply import PurchaseOrderItem
from app.models.alerts import Alert
from app.security.auth import hasher,verify_password
from app.security.permissions import PERMISSIONS
from app.services import inventory,operations as ops,supply,stock,transfers,assets,alerts
from app.schemas.platform import Receive,Issue
from app.schemas.operations import BedInput,StaffInput,AggregateInput,ShiftInput,AttendanceInput
from app.schemas.assets import EquipmentInput
from app.schemas.supply import SupplierInput,WarehouseInput,OrderInput,OrderAction,OrderReceipt
from app.schemas.stock import PolicyInput
from app.schemas.transfers import TransferCreate,TransferAction
from app.schemas.alerts import RuleInput
from scripts.development_data import guard,actor,ACTOR

READ=('inventory.read','procurement.read','workforce.read','beds.read','equipment.read','alerts.read','reports.read','reports.export','integration.read')
PROFILES={
 'admin':('administrator',set(PERMISSIONS)),
 'operator':('dev_data_operator',set(READ)|{'inventory.write','beds.write','workforce.write','equipment.write','alerts.manage'}),
 'inventory':('dev_data_inventory',{'inventory.read','inventory.write','inventory.transfer','procurement.read','procurement.write','alerts.read','reports.read','reports.export'}),
 'reader':('dev_data_reader',set(READ)),
}


async def create_user(db,profile,password,facility_ids):
    if profile not in PROFILES:raise ValueError('Unknown supported profile')
    username='dev-data-'+profile
    if len(password)<12 or len(password)>1024:raise ValueError('Use a password of 12..1024 characters')
    wanted=set(facility_ids)
    if (profile=='admin' and wanted) or (profile!='admin' and not wanted):
        raise ValueError('Admin is global; restricted profiles require explicit facility IDs')
    for identifier in wanted:
        facility=await db.get(Facility,identifier)
        if not facility or not facility.active or not facility.code.startswith(('FD1-','DEVOPS-')):
            raise ValueError('Scopes must reference active imported or development-seeded facilities')
    name,permissions=PROFILES[profile]
    role=await db.scalar(select(Role).where(Role.name==name))
    if role:
        actual=set(await db.scalars(select(Permission.name).join(RolePermission).where(RolePermission.role_id==role.id)))
        if actual!=permissions:raise ValueError('Existing role differs from requested profile; no permissions changed')
    else:
        role=Role(name=name);db.add(role);await db.flush()
        catalogue={p.name:p.id for p in await db.scalars(select(Permission))}
        if not permissions<=catalogue.keys():raise ValueError('Apply migrations; permission catalogue incomplete')
        db.add_all([RolePermission(role_id=role.id,permission_id=catalogue[n]) for n in permissions])
    existing=await db.scalar(select(User).where(User.username==username))
    if existing:
        owned=await db.scalar(select(AuditLog.id).where(AuditLog.action=='devdata.user.created',AuditLog.actor_id==existing.id))
        assigned=set(await db.scalars(select(UserFacility.facility_id).where(UserFacility.user_id==existing.id)))
        roles=set(await db.scalars(select(UserRole.role_id).where(UserRole.user_id==existing.id)))
        if not owned or assigned!=wanted or roles!={role.id} or not existing.active or existing.scope_mode!=('global' if profile=='admin' else 'restricted'):
            raise ValueError('Existing account differs or is not owned by this seeder; no account changed')
        if not verify_password(password,existing.password_hash):raise ValueError('Existing password differs; seeder never resets passwords')
        return {'username':username,'role':name,'id':str(existing.id),'created':False,'facility_ids':sorted(map(str,wanted))}
    user=User(username=username,password_hash=hasher.hash(password),scope_mode='global' if profile=='admin' else 'restricted')
    db.add(user);await db.flush();db.add(UserRole(user_id=user.id,role_id=role.id))
    db.add_all([UserFacility(user_id=user.id,facility_id=f) for f in wanted])
    inventory.audit(db,user.id,'devdata.user.created',{'profile':profile,'development_only':True,'facility_ids':sorted(map(str,wanted))})
    return {'username':username,'role':name,'id':str(user.id),'created':True,'facility_ids':sorted(map(str,wanted))}


async def users(args):
    password=os.environ.get('DEV_DATA_'+args.profile.upper()+'_PASSWORD') or getpass('Development account password (not echoed): ')
    async with AsyncSessionLocal.begin() as db:
        await guard(db)
        return await create_user(db,args.profile,password,[UUID(v) for v in args.facility_id])


async def seed_operations(db,user,seed,facility_count=3,medicine_count=8):
    if not 2<=facility_count<=10 or not 1<=medicine_count<=20 or not 0<=seed<=2_000_000_000:
        raise ValueError('Use 2..10 facilities, 1..20 medicines and a nonnegative 32-bit seed')
    params={'seed':seed,'facility_count':facility_count,'medicine_count':medicine_count,'version':1}
    key=str(seed);fingerprint=sha256(json.dumps(params,sort_keys=True).encode()).hexdigest()
    previous=await db.scalar(select(MutationReceipt).where(MutationReceipt.actor_id==user.id,
        MutationReceipt.operation=='devdata.operations',MutationReceipt.key==key))
    if previous:
        if previous.request_hash!=fingerprint:raise ValueError('This seed already owns a different configuration; no data changed')
        return {**previous.response,'reused':True}
    facilities=list(await db.scalars(select(Facility).where(Facility.code.like('FD1-%'),Facility.active.is_(True)).order_by(Facility.code).limit(facility_count)))
    medicines=list(await db.scalars(select(Medicine).where(Medicine.code.like('MD1-%')).order_by(Medicine.code).limit(medicine_count)))
    if len(facilities)!=facility_count or len(medicines)!=medicine_count:raise ValueError('Import enough facilities and medicines first')
    rng=random.Random(seed);today=datetime.now(timezone.utc).date();prefix=f'DEVOPS-{seed}'
    # A dedicated, labeled synthetic depot avoids reclassifying a real source hospital.
    depot=Facility(code=prefix+'-DEPOT',name='DEVELOPMENT ONLY synthetic supply depot '+str(seed),
        address='Synthetic development facility; no real-world address',facility_type='warehouse',source_device='devdata:synthetic:v1')
    db.add(depot);await db.flush()
    await supply.warehouse_create(db,user,WarehouseInput(facility_id=depot.id,capacity_units=10000))
    supplier=await supply.supplier_save(db,user,SupplierInput(code=prefix+'-SUP',name='DEVELOPMENT ONLY synthetic supplier '+str(seed)))
    role=await db.scalar(select(StaffRole).where(StaffRole.name=='DEVELOPMENT ONLY nursing team'))
    if not role:role=StaffRole(name='DEVELOPMENT ONLY nursing team');db.add(role);await db.flush()
    batch_ids={};rule_ids=[]
    for fi,facility in enumerate([*facilities,depot]):
        for mi,medicine in enumerate(medicines):
            # Unknown source units remain unknown; these are synthetic generic counts.
            quantity=5 if mi==0 and fi<facility_count else rng.randint(60,120)
            receipt=await inventory.receive(db,Receive(facility_id=facility.id,medicine_id=medicine.id,
                batch_number=f'{prefix}-M{mi}',expires_on=today+timedelta(days=25 if mi==0 else 180),
                quantity=quantity,reference=prefix+' SYNTHETIC receipt',idempotency_key=f'{prefix}-receipt-{fi}-{mi}'),user)
            batch_ids[mi]=receipt['batch_id']
            policy=await db.scalar(select(StockPolicy).where(StockPolicy.facility_id==facility.id,StockPolicy.medicine_id==medicine.id))
            if not policy:await stock.set_policy(db,user,facility.id,medicine.id,PolicyInput(safety_stock=2,expiry_warning_days=30))
            if fi<facility_count:
                await inventory.issue(db,Issue(facility_id=facility.id,medicine_id=medicine.id,quantity=1 if mi==0 else 3,
                    reference=prefix+' SYNTHETIC issue',idempotency_key=f'{prefix}-issue-{fi}-{mi}'),user)
        if facility is depot:continue
        await ops.bed_update(db,user,BedInput(facility_id=facility.id,bed_type=prefix+' SYNTHETIC beds',capacity=20,occupied=18 if fi==0 else rng.randint(4,12)))
        staff=await ops.staff_save(db,user,StaffInput(facility_id=facility.id,staff_role_id=role.id,code=f'{prefix}-STAFF-{fi}',display_name=f'DEVELOPMENT ONLY staff {fi+1}'))
        start=datetime.combine(today,datetime.min.time(),tzinfo=timezone.utc)+timedelta(hours=8)
        await ops.shift_create(db,user,ShiftInput(staff_id=staff['id'],starts_at=start,ends_at=start+timedelta(hours=8)))
        await ops.attendance(db,user,AttendanceInput(staff_id=staff['id'],day=today,status='present'))
        await ops.aggregate(db,user,'footfall',AggregateInput(facility_id=facility.id,day=today,category=prefix+' SYNTHETIC visits',count=rng.randint(10,60),source_device=prefix))
        await assets.save(db,user,Equipment,EquipmentInput(facility_id=facility.id,code=f'{prefix}-EQ-{fi}',equipment_type='DEVELOPMENT ONLY synthetic monitor',next_maintenance=today+timedelta(days=7),notes=prefix+' SYNTHETIC, not a real equipment record'))
        for kind,threshold in [('LOW_STOCK',10),('EXPIRY',30),('HIGH_BED_OCCUPANCY',.85)]:
            rule=await alerts.save_rule(db,user,RuleInput(facility_id=facility.id,kind=kind,threshold=threshold,window_days=30))
            await alerts.evaluate_rule(db,rule['id']);rule_ids.append(rule['id'])
    transfer=await transfers.create(db,user,TransferCreate(source_id=depot.id,destination_id=facilities[1].id,
        reference=prefix+' SYNTHETIC transfer',idempotency_key=prefix+'-transfer',items=[{'batch_id':batch_ids[0],'quantity':3}]))
    for action in ('approve','dispatch','in_transit','receive'):
        await transfers.transition(db,user,transfer['id'],TransferAction(action=action,reason=prefix+' SYNTHETIC workflow'))
    order=await supply.order_create(db,user,OrderInput(reference=prefix+'-PO',supplier_id=supplier['id'],facility_id=facilities[0].id,
        items=[{'medicine_id':medicines[-1].id,'quantity':10,'unit_price':'1.00'}]))
    for action in ('submit','approve','order'):
        await supply.order_action(db,user,order['id'],OrderAction(action=action,note=prefix+' SYNTHETIC price/workflow'))
    item=await db.scalar(select(PurchaseOrderItem).where(PurchaseOrderItem.order_id==order['id']))
    await supply.order_receive(db,user,order['id'],OrderReceipt(item_id=item.id,batch_number=prefix+'-PROC',
        expires_on=today+timedelta(days=180),quantity=10,idempotency_key=prefix+'-procurement'))
    for alert in await db.scalars(select(Alert).where(Alert.rule_id.in_(rule_ids))):
        alert.details={**alert.details,'development_only':True,'seed':seed}
    result={**params,'as_of':str(today),'reused':False,'facility_ids':[str(f.id) for f in facilities],
        'depot_id':str(depot.id),'medicine_ids':[str(m.id) for m in medicines],'transfer_id':str(transfer['id']),'order_id':str(order['id'])}
    db.add(MutationReceipt(actor_id=user.id,operation='devdata.operations',key=key,request_hash=fingerprint,response=result))
    inventory.audit(db,user.id,'devdata.operations.completed',result)
    return result


async def operations(args):
    async with AsyncSessionLocal.begin() as db:
        await guard(db)
        return await seed_operations(db,await actor(db),args.seed,args.facilities,args.medicines)
