from app.schemas import outputs as out
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models import User, Inventory
from app.models.supply import Supplier, Warehouse, PurchaseOrder, PurchaseOrderItem, Shipment, ShipmentHistory
from app.schemas.supply import SupplierInput, WarehouseInput, OrderInput, OrderAction, OrderReceipt, ShipmentInput, ShipmentAction
from app.security.auth import require
from app.security.scope import check_facility, facility_filter, global_only
from app.services import supply
from app.repositories.common import serialize, get_record

router = APIRouter(responses=out.ERROR_RESPONSES, tags=['Supply chain'])


def data(value):
    return {'success':True,'data':value}


@router.post('/suppliers',status_code=201, response_model=out.Success[out.SupplierView], response_model_exclude_unset=True)
async def supplier_create(payload:SupplierInput,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('procurement.write'))):
    global_only(user)
    return data(await supply.supplier_save(db,user,payload))


@router.put('/suppliers/{identifier}', response_model=out.Success[out.SupplierView], response_model_exclude_unset=True)
async def supplier_update(identifier:UUID,payload:SupplierInput,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('procurement.write'))):
    global_only(user)
    return data(await supply.supplier_save(db,user,payload,identifier))


@router.get('/suppliers', response_model=out.Success[list[out.SupplierView]], response_model_exclude_unset=True)
async def suppliers(offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=200),db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('procurement.read'))):
    return data([serialize(r) for r in await db.scalars(select(Supplier).order_by(Supplier.id).offset(offset).limit(limit))])


@router.get('/suppliers/{identifier}/metrics', response_model=out.Success[out.SupplierMetrics], response_model_exclude_unset=True)
async def supplier_metrics(identifier:UUID,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('procurement.read'))):
    global_only(user)
    return data(await supply.metrics(db,identifier))


@router.post('/warehouses',status_code=201, response_model=out.Success[out.WarehouseView], response_model_exclude_unset=True)
async def warehouse_create(payload:WarehouseInput,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('facility.manage'))):
    return data(await supply.warehouse_create(db,user,payload))


@router.get('/warehouses', response_model=out.Success[list[out.WarehouseView]], response_model_exclude_unset=True)
async def warehouses(offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=200),db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('inventory.read'))):
    return data([serialize(r) for r in await db.scalars(select(Warehouse).where(facility_filter(user,Warehouse.facility_id)).order_by(Warehouse.id).offset(offset).limit(limit))])


@router.get('/warehouses/{identifier}/inventory', response_model=out.Success[list[out.InventoryView]], response_model_exclude_unset=True)
async def warehouse_stock(identifier:UUID,offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=200),db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('inventory.read'))):
    row=await get_record(db,Warehouse,identifier)
    await check_facility(db,user,row.facility_id)
    return data([serialize(r) for r in await db.scalars(select(Inventory).where(Inventory.facility_id==row.facility_id).order_by(Inventory.id).offset(offset).limit(limit))])


@router.post('/purchase-orders',status_code=201, response_model=out.Success[out.PurchaseOrderView], response_model_exclude_unset=True)
async def order_create(payload:OrderInput,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('procurement.write'))):
    return data(await supply.order_create(db,user,payload))


@router.get('/purchase-orders', response_model=out.Success[list[out.PurchaseOrderView]], response_model_exclude_unset=True)
async def orders(offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=200),db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('procurement.read'))):
    return data([serialize(r) for r in await db.scalars(select(PurchaseOrder).where(facility_filter(user,PurchaseOrder.facility_id)).order_by(PurchaseOrder.id).offset(offset).limit(limit))])


@router.get('/purchase-orders/{identifier}', response_model=out.Success[out.OrderDetail], response_model_exclude_unset=True)
async def order_detail(identifier:UUID,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('procurement.read'))):
    row=await get_record(db,PurchaseOrder,identifier)
    await check_facility(db,user,row.facility_id)
    items=await db.scalars(select(PurchaseOrderItem).where(PurchaseOrderItem.order_id==identifier))
    return data({**serialize(row),'items':[serialize(r) for r in items]})


@router.post('/purchase-orders/{identifier}/actions', response_model=out.Success[out.PurchaseOrderView], response_model_exclude_unset=True)
async def order_action(identifier:UUID,payload:OrderAction,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('procurement.write'))):
    if payload.action=='approve':
        await require('procurement.approve')(user,db)
    return data(await supply.order_action(db,user,identifier,payload))


@router.post('/purchase-orders/{identifier}/receive', response_model=out.Success[out.OrderReceived], response_model_exclude_unset=True)
async def order_receive(identifier:UUID,payload:OrderReceipt,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('procurement.write'))):
    await require('inventory.write')(user,db)
    return data(await supply.order_receive(db,user,identifier,payload))


@router.post('/shipments',status_code=201, response_model=out.Success[out.ShipmentView], response_model_exclude_unset=True)
async def shipment_create(payload:ShipmentInput,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('procurement.write'))):
    return data(await supply.shipment_create(db,user,payload))


@router.get('/shipments', response_model=out.Success[list[out.ShipmentView]], response_model_exclude_unset=True)
async def shipments(offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=200),db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('procurement.read'))):
    return data([serialize(r) for r in await db.scalars(select(Shipment).where(supply.shipment_scope(user)).order_by(Shipment.id).offset(offset).limit(limit))])


@router.get('/shipments/{identifier}/history', response_model=out.Success[list[out.ShipmentHistoryView]], response_model_exclude_unset=True)
async def shipment_history(identifier:UUID,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('procurement.read'))):
    row=await get_record(db,Shipment,identifier)
    await supply.check_shipment_scope(db,user,row)
    return data([serialize(r) for r in await db.scalars(select(ShipmentHistory).where(ShipmentHistory.shipment_id==identifier).order_by(ShipmentHistory.created_at))])


@router.post('/shipments/{identifier}/actions', response_model=out.Success[out.ShipmentView], response_model_exclude_unset=True)
async def shipment_action(identifier:UUID,payload:ShipmentAction,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('procurement.write'))):
    return data(await supply.shipment_action(db,user,identifier,payload))

from app.schemas.supply import WarehouseUpdate

@router.put('/warehouses/{identifier}', response_model=out.Success[out.WarehouseView], response_model_exclude_unset=True)
async def warehouse_update(identifier:UUID,payload:WarehouseUpdate,db:AsyncSession=Depends(get_db,scope='function'),user:User=Depends(require('facility.manage'))):
    return data(await supply.warehouse_update(db,user,identifier,payload))
