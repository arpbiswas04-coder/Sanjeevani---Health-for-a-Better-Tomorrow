"""Explicit DEVELOPMENT-only catalogue imports; never imported by API startup.

Run from backend: python -m scripts.development_data --help
CSV rows are streamed, deduplication is disk-backed, writes commit in bounded batches.
Source fields without a legitimate schema destination are NOT interpreted clinically.
"""
import argparse
import asyncio
from collections import Counter
import csv
from hashlib import sha256
import itertools
import json
from pathlib import Path
import re
import sqlite3
import tempfile
import unicodedata
from uuid import uuid4

from sqlalchemy import select,text,func,or_
from sqlalchemy.engine import make_url
from app.core.config import settings
from app.core.database import AsyncSessionLocal,engine
from app.models import Medicine,Facility,User,AuditLog
from app.models.geography import Country,State
from app.security.auth import require
from app.services.inventory import audit

ROOT=Path(__file__).resolve().parents[2]
ACTOR='dev-data-admin'
MEDICINES=('India_Medicines_part_01.csv','India_Medicines_part_02.csv')
FACILITIES='medindia_hospitals_clinics.csv'
STATES=('Andaman and Nicobar Islands','Andhra Pradesh','Arunachal Pradesh','Assam','Bihar',
 'Chandigarh','Chhattisgarh','Dadra and Nagar Haveli and Daman and Diu','Delhi','Goa','Gujarat',
 'Haryana','Himachal Pradesh','Jammu and Kashmir','Jharkhand','Karnataka','Kerala','Ladakh',
 'Lakshadweep','Madhya Pradesh','Maharashtra','Manipur','Meghalaya','Mizoram','Nagaland',
 'Odisha','Puducherry','Punjab','Rajasthan','Sikkim','Tamil Nadu','Telangana','Tripura',
 'Uttar Pradesh','Uttarakhand','West Bengal')


def clean(value):
    value=' '.join(unicodedata.normalize('NFC',value or '').split())
    return '' if value.casefold() in ('','nan','null','none','n/a','not available') else value


def stable(prefix,value):
    return prefix+sha256(value.encode('utf-8')).hexdigest()[:40]


def validate_target(config):
    url=make_url(config.get_database_url())
    if config.APP_ENV!='development' or url.drivername!='postgresql+asyncpg' or url.host not in ('localhost','127.0.0.1') or url.database!='sanjeevani_dev':
        raise RuntimeError('Development data commands require local PostgreSQL sanjeevani_dev and APP_ENV=development')


async def guard(db):
    validate_target(settings)
    if await db.scalar(text('SELECT current_database()'))!='sanjeevani_dev':
        raise RuntimeError('Connected database is not sanjeevani_dev')


async def actor(db):
    user=await db.scalar(select(User).where(User.username==ACTOR))
    if not user or not user.active or user.scope_mode!='global':
        raise RuntimeError('Create the development admin with the users command first')
    await require('admin.users')(user,db)
    return user


def rows(paths):
    """Round-robin parts: a limited medicine import represents both source files."""
    from contextlib import ExitStack
    with ExitStack() as stack:
        readers=[]
        def tagged(reader,name):
            for n,row in enumerate(reader,2):yield name,n,row
        for path in paths:
            handle=stack.enter_context(Path(path).open(encoding='utf-8-sig',newline=''))
            reader=csv.DictReader(handle)
            readers.append(tagged(reader,Path(path).name))
        yield from (row for group in itertools.zip_longest(*readers) for row in group if row is not None)


def medicine_row(row):
    if 'Medicine Name' not in row:raise ValueError('Missing Medicine Name column')
    name=clean(row['Medicine Name'])
    if not name or len(name)>200:raise ValueError('Invalid medicine name')
    # The scraped type/manufacturer/composition fields are concatenated/unreliable.
    # "unspecified" is an explicit unknown unit, not an inferred tablet/dose/pack.
    return {'name':name,'code':stable('MD1-',name.casefold()),'unit':'unspecified'}


def facility_row(row):
    if not {'name','city','pincode','state','profile_url','directory_url'}<=row.keys():
        raise ValueError('Missing facility columns')
    name,city,pincode,state=(clean(row[k]) for k in ('name','city','pincode','state'))
    if not name or len(name)>200 or re.search(r'\bcar clinic\b',name,re.I):
        raise ValueError('Missing/invalid/non-healthcare facility name')
    canonical=next((s for s in STATES if s.casefold()==state.casefold()),None)
    state=canonical or state
    address='; '.join(v for v in [city,('PIN '+pincode) if pincode else '',state] if v)
    if len(address)>500:raise ValueError('Source address exceeds schema limit')
    key=json.dumps([name.casefold(),city.casefold(),pincode,state.casefold()],ensure_ascii=False)
    return {'name':name,'code':stable('FD1-',key),'address':address or None,
            'facility_type':'other','source_device':'dev-import:medindia:v1',
            'latitude':None,'longitude':None,'block_id':None},canonical


async def ensure_states(db,names,owner,counts):
    if not names:return
    countries=list(await db.scalars(select(Country).where(or_(func.lower(Country.name)=='india',Country.code.in_(['IN','IND'])))))
    if len(countries)>1:raise RuntimeError('Ambiguous existing India geography; resolve manually')
    if countries:country=countries[0]
    else:
        country=Country(name='India',code='IN');db.add(country);await db.flush();counts['countries_inserted']+=1
        audit(db,owner.id,'devdata.geography.imported',{'id':str(country.id),'source':'source dataset country context'})
    existing=list(await db.scalars(select(State).where(State.country_id==country.id)))
    for name in sorted(names):
        matching=[s for s in existing if clean(s.name).casefold()==name.casefold()]
        if len(matching)>1:raise RuntimeError('Ambiguous existing state geography; resolve manually')
        if matching:continue
        state=State(name=name,code=stable('S',name)[:8],country_id=country.id)
        db.add(state);await db.flush();existing.append(state);counts['states_inserted']+=1
        audit(db,owner.id,'devdata.geography.imported',{'id':str(state.id),'source':'medindia state label'})


async def import_batch(db,owner,kind,batch,counts):
    model=Medicine if kind=='medicines' else Facility
    # Bounded lookup; do not load an entire existing catalogue into memory.
    codes=[p['code'] for p,_,_ in batch]
    names=[p['name'].lower() for p,_,_ in batch]
    existing=list(await db.scalars(select(model).where(or_(model.code.in_(codes),func.lower(model.name).in_(names)))))
    by_code={r.code:r for r in existing}
    profile_codes={}
    if kind=='facilities':
        profiles=[p.get('profile_url') for _,p,_ in batch if p.get('profile_url')]
        for details in await db.scalars(select(AuditLog.details).where(AuditLog.action=='devdata.facilities.imported',
                AuditLog.details['profile_url'].as_string().in_(profiles))):
            profile_codes[details['profile_url']]=details['code']
    if kind=='facilities':await ensure_states(db,{state for _,_,state in batch if state},owner,counts)
    for payload,provenance,_ in batch:
        if provenance.get('profile_url') in profile_codes and profile_codes[provenance['profile_url']]!=payload['code']:
            counts['conflicts']+=1;continue
        current=by_code.get(payload['code'])
        if current:
            fields=('name','unit') if kind=='medicines' else ('name','address')
            if any(clean(str(getattr(current,k) or '')).casefold()!=clean(str(payload[k] or '')).casefold() for k in fields):
                counts['conflicts']+=1
            else:counts['skipped_existing']+=1
            continue
        matches=[r for r in existing if clean(r.name).casefold()==payload['name'].casefold()
                 and (kind=='medicines' or clean(r.address).casefold()==clean(payload['address']).casefold())]
        if matches:
            # Do not change unowned catalogue entries or arbitrarily pick ambiguous names.
            counts['existing_unowned_or_ambiguous']+=1
            continue
        row=model(id=uuid4(),**payload);db.add(row);existing.append(row);by_code[row.code]=row
        audit(db,owner.id,'devdata.'+kind+'.imported',{'id':str(row.id),'code':row.code,**provenance})
        counts['inserted']+=1
    await db.flush()


async def import_catalogue(factory,kind,paths,limit=200,batch_size=250,*,checked=True):
    if limit is not None and limit<1:raise ValueError('Limit must be positive')
    if not 1<=batch_size<=1000:raise ValueError('Batch size must be 1..1000')
    counts=Counter({k:0 for k in ('scanned','inserted','skipped_existing','duplicates','invalid','conflicts','existing_unowned_or_ambiguous')})
    with tempfile.TemporaryDirectory(prefix='sanjeevani-import-') as scratch:
        index=sqlite3.connect(str(Path(scratch)/'seen.sqlite'))
        index.execute('CREATE TABLE seen (code TEXT PRIMARY KEY, profile TEXT UNIQUE, fingerprint TEXT)')
        try:
            batch=[];accepted=0
            for filename,line,raw in rows(paths):
                if limit is not None and accepted>=limit:break
                counts['scanned']+=1
                try:
                    if None in raw:raise ValueError('Malformed CSV row')
                    if kind=='medicines':payload,state=medicine_row(raw),None
                    else:payload,state=facility_row(raw)
                except ValueError:
                    counts['invalid']+=1;continue
                profile=clean(raw.get('profile_url')).rstrip('/').casefold() or None
                fingerprint=sha256(json.dumps(raw,sort_keys=True).encode()).hexdigest()
                previous=index.execute('SELECT code,fingerprint FROM seen WHERE code=? OR profile=?',(payload['code'],profile)).fetchone()
                if previous:
                    counts['duplicates' if previous[0]==payload['code'] else 'conflicts']+=1
                    if previous[1]!=fingerprint:counts['source_variants']+=1
                    continue
                index.execute('INSERT INTO seen VALUES (?,?,?)',(payload['code'],profile,fingerprint))
                provenance={'file':filename,'line':line,'source_sha256':fingerprint}
                if kind=='facilities':provenance.update({k:clean(raw[k]) for k in ('city','pincode','state','profile_url','directory_url')})
                batch.append((payload,provenance,state));accepted+=1
                if len(batch)>=batch_size or (limit is not None and accepted>=limit):
                    async with factory.begin() as db:
                        if checked:await guard(db)
                        await import_batch(db,await actor(db),kind,batch,counts)
                    batch=[]
            if batch:
                async with factory.begin() as db:
                    if checked:await guard(db)
                    await import_batch(db,await actor(db),kind,batch,counts)
        finally:index.close()
    return dict(counts)


def parser():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='command',required=True)
    for kind in ('medicines','facilities'):
        q=sub.add_parser(kind);group=q.add_mutually_exclusive_group()
        group.add_argument('--limit',type=int,default=None);group.add_argument('--full',action='store_true')
        q.add_argument('--source-dir',type=Path,default=ROOT);q.add_argument('--batch-size',type=int,default=250)
    q=sub.add_parser('users');q.add_argument('--profile',choices=['admin','operator','inventory','reader'],required=True)
    q.add_argument('--facility-id',action='append',default=[])
    q=sub.add_parser('operations');q.add_argument('--seed',type=int,required=True)
    q.add_argument('--facilities',type=int,default=3);q.add_argument('--medicines',type=int,default=8)
    q=sub.add_parser('enrich');q.add_argument('--seed',type=int,required=True)
    q=sub.add_parser('accounts');q.add_argument('--seed',type=int,required=True)
    q.add_argument('--credentials-file',type=Path)
    return p


async def main(args):
    validate_target(settings)
    # One importer/seeder at a time, across committed chunks. No application locks
    # or production paths are changed. Database connection ownership releases on crash.
    async with engine.connect() as lock:
        await guard(lock)
        if not await lock.scalar(text('SELECT pg_try_advisory_lock(739125801)')):
            raise RuntimeError('Another development data command is running')
        try:
            if args.command in ('medicines','facilities'):
                names=MEDICINES if args.command=='medicines' else (FACILITIES,)
                result=await import_catalogue(AsyncSessionLocal,args.command,[args.source_dir/n for n in names],
                    None if args.full else (args.limit if args.limit is not None else (200 if args.command=='medicines' else 50)),args.batch_size)
            elif args.command=='accounts':
                from scripts.development_accounts import accounts
                result=await accounts(args)
            elif args.command=='enrich':
                from scripts.development_enrichment import enrich
                async with AsyncSessionLocal.begin() as db:
                    await guard(db)
                    result=await enrich(db,await actor(db),args.seed)
            else:
                from scripts.development_seed import users,operations
                result=await (users(args) if args.command=='users' else operations(args))
            print(json.dumps(result,indent=2,default=str))
        finally:await lock.execute(text('SELECT pg_advisory_unlock(739125801)'))
    await engine.dispose()


if __name__=='__main__':
    asyncio.run(main(parser().parse_args()))
