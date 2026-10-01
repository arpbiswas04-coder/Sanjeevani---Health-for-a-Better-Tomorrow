import asyncio
from datetime import datetime,timezone
from uuid import UUID
import pytest
from app.models import User
from app.schemas.operations import AggregateInput
from app.services.operations import aggregate
from app.services.sync import pull
from tests.test_platform import seed
from sqlalchemy import select

pytestmark=pytest.mark.asyncio


async def test_delayed_commit_and_concurrent_cursor_order(api):
    client,factory,_=api
    ids=await seed(client)
    async with factory() as db:
        user=await db.scalar(select(User).where(User.username=='admin'))
    payload=AggregateInput(facility_id=ids['facility_id'],day=datetime.now(timezone.utc).date(),category='outpatient',count=1)
    async with factory() as writer:
        await writer.begin()
        await aggregate(writer,user,'footfall',payload)
        async with factory() as reader:
            first=await pull(reader,user,'footfall',0,None,10)
            assert first['watermark']==0 and first['items']==[]
        async def second_writer():
            async with factory.begin() as db:
                return await aggregate(db,user,'footfall',payload.model_copy(update={'expected_version':1,'count':2}))
        task=asyncio.create_task(second_writer())
        await asyncio.sleep(0.05)
        assert not task.done(), 'A later writer must not bypass the uncommitted allocator'
        await writer.commit()
        await asyncio.wait_for(task,5)
    async with factory() as db:
        result=await pull(db,user,'footfall',first['watermark'],None,10)
        assert [r['count'] for r in result['items']]==[1,2]
        assert result['watermark']==2


async def test_sequence_pagination_repeated_pull_and_push(api):
    client,_,_=api
    ids=await seed(client)
    body={'idempotency_key':'sequence-push','items':[{'kind':'footfall','payload':{
        'facility_id':ids['facility_id'],'day':str(datetime.now(timezone.utc).date()),'category':f'category-{i}','count':i}}
        for i in range(3)]}
    first=await client.post('/api/v1/sync/push',json=body)
    assert first.status_code==200,first.text
    assert (await client.post('/api/v1/sync/push',json=body)).json()==first.json()
    page=(await client.get('/api/v1/sync/pull',params={'limit':1})).json()['data']
    assert page['watermark']==3 and page['has_more']
    update={**body['items'][0]['payload'],'expected_version':1,'count':99}
    assert (await client.put('/api/v1/aggregates/footfall',json=update)).status_code==200
    cursor=page['next_cursor']
    second=(await client.get('/api/v1/sync/pull',params={**cursor,'limit':10})).json()['data']
    assert [r['count'] for r in second['items']]==[1,2]
    assert second['watermark']==3 and not second['has_more']
    assert (await client.get('/api/v1/sync/pull',params={**cursor,'limit':10})).json()['data']==second
    changes=(await client.get('/api/v1/sync/pull',params={'after_sequence':3})).json()['data']
    assert changes['watermark']==4 and changes['items'][0]['count']==99
    assert (await client.get('/api/v1/sync/pull',params={'after_sequence':4})).json()['data']['items']==[]
