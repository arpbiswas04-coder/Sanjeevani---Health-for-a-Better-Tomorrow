from app.schemas import outputs as out
from uuid import UUID
from typing import Literal
from fastapi import APIRouter,Depends,Query,Response
from pydantic import AwareDatetime
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool
from app.core.database import get_db
from app.models import User
from app.security.auth import require
from app.services.reports import report
from app.services.exports import export

router=APIRouter(responses=out.ERROR_RESPONSES, tags=['Reports'])


@router.get('/reports/{kind}', response_model=out.Success[out.ReportResult], response_model_exclude_unset=True, responses={200:{'content':out.BINARY_CONTENT}})
async def reporting(kind:Literal['stock','expiry','transfers','procurement','staff','beds','emergency'],
    format:Literal['json','csv','xlsx','pdf']='json',facility_id:UUID|None=None,medicine_id:UUID|None=None,status:str|None=Query(None,max_length=30),
    start:AwareDatetime|None=None,end:AwareDatetime|None=None,district_id:UUID|None=None,state_id:UUID|None=None,
    offset:int=Query(0,ge=0),limit:int=Query(100,ge=1,le=500),db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('reports.read'))):
    if format!='json':
        await require('reports.export')(user,db)
    # Workforce data also requires its dedicated permission.
    if kind=='staff':
        await require('workforce.read')(user,db)
    result=await report(db,user,kind,offset,limit,facility_id,medicine_id,status,start,end,district_id,state_id)
    if format=='json':
        return {'success':True,'data':result}
    body,media=await run_in_threadpool(export,result['rows'],format)
    return Response(content=body,media_type=media,headers={'Content-Disposition':f'attachment; filename="{kind}.{format}"',
        'X-Has-More':str(result['has_more']).lower(),'X-Next-Offset':str(offset+len(result['rows']))})
