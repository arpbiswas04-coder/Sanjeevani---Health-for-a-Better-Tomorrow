"""Source imports and synthetic operations in disposable test databases only."""
import csv
from types import SimpleNamespace
from uuid import UUID
import pytest
from sqlalchemy import select,func
from app.models import Medicine,Facility,AuditLog,Inventory,StockTransaction,User
from app.models.geography import State,Country,Block,District
from app.models.operations import BedCapacity
from scripts.development_data import import_catalogue,validate_target,medicine_row,facility_row,rows
from scripts.development_seed import create_user,seed_operations


def write_csv(path,records):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    return path


@pytest.mark.parametrize('environment,url',[
 ('production','postgresql+asyncpg://u:p@localhost/sanjeevani_dev'),
 ('development','postgresql+asyncpg://u:p@remote/sanjeevani_dev'),
 ('development','postgresql+asyncpg://u:p@localhost/sanjeevani_test'),
 ('development','sqlite+aiosqlite:///dev.db'),
])
def test_guard_rejects_wrong_environment(environment,url):
    with pytest.raises(RuntimeError):validate_target(SimpleNamespace(APP_ENV=environment,get_database_url=lambda:url))


@pytest.mark.asyncio
async def test_streamed_medicine_parts_conflicts_and_safe_rerun(api,tmp_path):
    _,factory,_=api
    async with factory.begin() as db:await create_user(db,'admin','isolated-test-password',[])
    one=write_csv(tmp_path/'one.csv',[{'Medicine Name':'  Source   Drug  ','Composition':'unknown'},
        {'Medicine Name':'source drug','Composition':'conflicting source text'},{'Medicine Name':'','Composition':''}])
    two=write_csv(tmp_path/'two.csv',[{'Medicine Name':'Other Drug','Composition':''}])
    assert [r[0] for r in rows([one,two])][:2]==['one.csv','two.csv']
    result=await import_catalogue(factory,'medicines',[one,two],None,1,checked=False)
    assert result['inserted']==2 and result['duplicates']==1 and result['invalid']==1
    again=await import_catalogue(factory,'medicines',[one,two],None,2,checked=False)
    assert again['inserted']==0 and again['skipped_existing']==2
    async with factory.begin() as db:
        medicine=await db.scalar(select(Medicine).where(Medicine.name=='Source Drug'))
        assert medicine.unit=='unspecified';medicine.unit='manually-reviewed-unit'
        assert await db.scalar(select(func.count()).select_from(AuditLog).where(AuditLog.action=='devdata.medicines.imported'))==2
    conflict=await import_catalogue(factory,'medicines',[one,two],None,1,checked=False)
    assert conflict['conflicts']==1
    async with factory() as db:assert (await db.get(Medicine,medicine.id)).unit=='manually-reviewed-unit'


@pytest.mark.asyncio
async def test_facility_source_geography_missing_coordinates_and_profile_conflict(api,tmp_path):
    _,factory,_=api
    async with factory.begin() as db:
        await create_user(db,'admin','isolated-test-password',[])
        country=Country(name='India',code='IN');db.add(country);await db.flush()
        db.add(State(name='gujarat',code='GJ',country_id=country.id))
    base={'name':'Source Clinic','city':'Ahmedabad','pincode':'380001','state':'Gujarat','profile_url':'https://example.invalid/source','directory_url':'https://example.invalid/directory'}
    file=write_csv(tmp_path/'f.csv',[base,{**base,'state':' gujarat ','profile_url':'https://example.invalid/duplicate'},
        {**base,'name':''},{**base,'name':'Car Clinic'}])
    result=await import_catalogue(factory,'facilities',[file],None,1,checked=False)
    assert result['inserted']==1 and result['duplicates']==1 and result['invalid']==2
    again=await import_catalogue(factory,'facilities',[file],None,2,checked=False);assert again['skipped_existing']==1
    async with factory() as db:
        facility=await db.scalar(select(Facility));assert facility.latitude is None and facility.longitude is None and facility.block_id is None
        assert facility.facility_type=='other' and 'Ahmedabad' in facility.address
        assert await db.scalar(select(func.count()).select_from(State))==1
        assert await db.scalar(select(func.count()).select_from(District))==0
        assert await db.scalar(select(func.count()).select_from(Block))==0
        details=await db.scalar(select(AuditLog.details).where(AuditLog.action=='devdata.facilities.imported'));assert details['profile_url']==base['profile_url']
    changed=write_csv(tmp_path/'changed.csv',[{**base,'name':'Conflicting changed name'}])
    result=await import_catalogue(factory,'facilities',[changed],None,1,checked=False)
    assert result['conflicts']==1 and result['inserted']==0


@pytest.mark.asyncio
async def test_synthetic_seed_ledger_rbac_and_idempotency(api):
    client,factory,_=api
    async with factory.begin() as db:
        admin=await create_user(db,'admin','isolated-test-password',[])
        for n in range(2):db.add(Facility(name=f'Source facility {n}',code=f'FD1-{n}',facility_type='other'))
        db.add(Medicine(name='Source medicine',code='MD1-0',unit='unspecified'));await db.flush()
        user=await db.get(User,UUID(admin['id']))
        result=await seed_operations(db,user,123,2,1)
    async with factory.begin() as db:
        count=await db.scalar(select(func.count()).select_from(StockTransaction))
        again=await seed_operations(db,await db.get(User,user.id),123,2,1);assert again['reused']
        assert await db.scalar(select(func.count()).select_from(StockTransaction))==count
        for stock in await db.scalars(select(Inventory)):
            balance=await db.scalar(select(func.sum(StockTransaction.quantity)).where(StockTransaction.inventory_id==stock.id))
            assert balance==stock.quantity and stock.reserved==0
        assert await db.scalar(select(func.count()).select_from(BedCapacity))==2
        facility=UUID(result['facility_ids'][0])
        read=await create_user(db,'reader','isolated-reader-password',[facility])
        assert not (await create_user(db,'reader','isolated-reader-password',[facility]))['created']
        with pytest.raises(ValueError):await create_user(db,'reader','different-test-password',[facility])
    login=await client.post('/api/v1/auth/login',data={'username':read['username'],'password':'isolated-reader-password'})
    assert login.status_code==200;client.headers['Authorization']='Bearer '+login.json()['access_token']
    profile=(await client.get('/api/v1/users/me')).json()['data'];assert profile['roles']==['dev_data_reader'] and profile['facility_ids']==[str(facility)]
    assert (await client.put('/api/v1/beds',json={'facility_id':str(facility),'bed_type':'unauthorized','capacity':1,'occupied':0})).status_code==403
    assert (await client.get('/api/v1/inventory',params={'facility_id':result['facility_ids'][1]})).status_code==404
