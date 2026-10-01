import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime,timezone,timedelta
import pytest
from tests.test_platform import seed


@pytest.mark.asyncio
async def test_cold_chain_series_values_dedup_and_scope(api):
    client,_,_=api
    ids=await seed(client)
    now=datetime.now(timezone.utc)
    body={'facility_id':ids['facility_id'],'observed_at':now.isoformat(),'temperature':10,'minimum':2,'maximum':8,'source':'sensor','external_id':'one'}
    assert (await client.post('/api/v1/cold-chain/observations',json=body)).status_code==201
    assert (await client.post('/api/v1/cold-chain/observations',json=body)).status_code==201
    params={'facility_id':ids['facility_id'],'start':(now-timedelta(hours=1)).isoformat(),'end':(now+timedelta(hours=1)).isoformat()}
    response=await client.get('/api/v1/cold-chain/series',params=params)
    assert response.status_code==200,response.text
    rows=response.json()['data']
    assert len(rows)==1 and rows[0]['temperature']==10 and rows[0]['excursion'] is True
    assert (await client.get('/api/v1/cold-chain/series',params={**params,'end':params['start']})).status_code==422
    client.headers.clear()
    assert (await client.get('/api/v1/cold-chain/series',params=params)).status_code==401


def test_timescale_sql_requires_explicit_postgres_opt_in():
    backend=Path(__file__).resolve().parents[1]
    for flag in ('0','1'):
        result=subprocess.run([sys.executable,'-m','alembic','upgrade','head','--sql'],cwd=backend,
            env={**os.environ,'DATABASE_URL':'postgresql+asyncpg://offline@localhost/offline','ENABLE_TIMESCALEDB':flag},capture_output=True,text=True)
        assert result.returncode==0,result.stderr
        assert ('CREATE EXTENSION IF NOT EXISTS timescaledb' in result.stdout)==(flag=='1')
        assert ("create_hypertable('cold_chain_samples'" in result.stdout)==(flag=='1')
        assert 'PRIMARY KEY (id, observed_at)' in result.stdout
