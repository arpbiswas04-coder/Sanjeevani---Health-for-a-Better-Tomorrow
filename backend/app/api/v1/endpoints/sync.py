from app.schemas import outputs as out
from uuid import UUID
from typing import Literal
from fastapi import APIRouter,Depends,Query
from pydantic import AwareDatetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models import User
from app.schemas.sync import SyncPush
from app.security.auth import require
from app.services import sync

router=APIRouter(responses=out.ERROR_RESPONSES, prefix='/sync',tags=['Offline aggregate sync'])


@router.post('/push', response_model=out.Success[out.SyncPush], response_model_exclude_unset=True)
async def push(payload:SyncPush,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('sync.write'))):
    await require('integration.write')(user,db)
    return {'success':True,'data':await sync.push(db,user,payload)}


@router.get('/pull', response_model=out.Success[out.SyncPull], response_model_exclude_unset=True)
async def pull(kind:Literal['footfall','disease-counts']='footfall',after_sequence:int=Query(0,ge=0),
               until_sequence:int|None=Query(None,ge=0),since:AwareDatetime|None=Query(None,deprecated=True),
               limit:int=Query(100,ge=1,le=200),db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('integration.read'))):
    # Legacy timestamp callers receive a safe full bootstrap, never a lossy cursor.
    return {'success':True,'data':await sync.pull(db,user,kind,after_sequence,until_sequence,limit)}
