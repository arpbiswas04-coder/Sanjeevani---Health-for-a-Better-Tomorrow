"""Opt-in, idempotent DEVELOPMENT-ONLY records for real frontend read verification.

Run from backend with .venv Python. Never creates users, changes credentials,
resets data, sends notifications, or advances procurement/transfer workflows.
"""
import asyncio
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from uuid import UUID

import httpx
from sqlalchemy import select, text
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from app.core.config import settings
from app.core.database import AsyncSessionLocal, engine
from app.models import User, Facility
from app.models.stock import StockPolicy
from app.services.alerts import evaluate_rule
from app.services.inventory import audit


async def main():
    url = make_url(settings.get_database_url())
    assert settings.APP_ENV == 'development'
    assert url.database == 'sanjeevani_dev' and url.host in ('localhost', '127.0.0.1')
    assert settings.BACKEND_URL.rstrip('/') in ('http://localhost:8000', 'http://127.0.0.1:8000')
    async with AsyncSessionLocal() as db:
        assert await db.scalar(text('SELECT current_database()')) == 'sanjeevani_dev'
        assert await db.scalar(text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname='postgis')"))
    credentials = json.loads((ROOT / 'tmp/phase2-auth-account.json').read_text())
    created = []
    async with httpx.AsyncClient(base_url=settings.BACKEND_URL.rstrip('/') + '/api/v1', timeout=20) as client:
        response = await client.post('/auth/login', data={**credentials, 'grant_type': 'password'})
        assert response.status_code == 200, f'Login failed: HTTP {response.status_code}'
        client.headers['Authorization'] = 'Bearer ' + response.json()['access_token']

        async def request(method, path, body=None, params=None):
            response = await client.request(method, path, json=body, params=params)
            assert response.status_code < 400, f'{method} {path}: HTTP {response.status_code}'
            return response.json()['data']

        async def listing(path, params=None):
            result = []
            for offset in range(0, 20000, 200):
                rows = await request('GET', path, params={**(params or {}), 'offset': offset, 'limit': 200})
                result.extend(rows)
                if len(rows) < 200:
                    return result
            raise RuntimeError('Narrow the seed lookup; directory exceeds safety limit')

        async def ensure(path, key, value, body, list_path=None, params=None, method='POST'):
            rows = await listing(list_path or path, params)
            existing = [row for row in rows if row[key] == value]
            assert len(existing) <= 1, f'Duplicate development record: {path}'
            if existing:
                return existing[0]
            row = await request(method, path, body)
            created.append({'endpoint': path, 'id': row['id']})
            return row

        me = await request('GET', '/users/me')
        async with AsyncSessionLocal() as db:
            stored = await db.get(User, UUID(me['id']))
            assert stored and stored.username == credentials['username'] and stored.scope_mode == 'global', 'HTTP and PostgreSQL user identity mismatch'
        parent = None
        geography = {}
        for kind, code in [('countries', 'DEV3C'), ('states', 'DEV3S'), ('districts', 'DEV3D'), ('blocks', 'DEV3B')]:
            row = await ensure('/geography/' + kind, 'code', code,
                {'name': 'DEVELOPMENT ONLY Phase 3 ' + kind, 'code': code, 'parent_id': parent})
            parent = row['id']
            geography[kind] = row['id']
        facility = await ensure('/facilities', 'code', 'DEV-PHASE3', {'name': 'DEVELOPMENT ONLY Phase 3 Hospital', 'code': 'DEV-PHASE3'})
        if facility['block_id'] is None:
            facility = await request('PATCH', '/facilities/' + facility['id'], {'facility_type': 'hospital', 'block_id': parent,
                'latitude': 22.5, 'longitude': 88.3, 'address': 'DEVELOPMENT ONLY verification location; not a clinical facility'})
        fid = facility['id']
        medicine = await ensure('/medicines', 'code', 'DEV-PHASE3-MED', {'name': 'DEVELOPMENT ONLY Phase 3 Medicine', 'code': 'DEV-PHASE3-MED', 'unit': 'test-unit'})
        inventory = await listing('/inventory', {'facility_id': fid})
        lot = next((row for row in inventory if row['batch']['batch_number'] == 'DEV-PHASE3-BATCH'), None)
        if lot is None:
            await request('POST', '/inventory/receive', {'facility_id': fid, 'medicine_id': medicine['id'], 'batch_number': 'DEV-PHASE3-BATCH',
                'expires_on': (datetime.now(timezone.utc).date() + timedelta(days=30)).isoformat(), 'quantity': 120,
                'reference': 'DEVELOPMENT ONLY Phase 3 initial stock', 'idempotency_key': 'DEV-PHASE3-INITIAL-STOCK'})
            lot = next(row for row in await listing('/inventory', {'facility_id': fid}) if row['batch']['batch_number'] == 'DEV-PHASE3-BATCH')
            created.append({'endpoint': '/inventory/receive', 'id': lot['id']})
        async with AsyncSessionLocal() as db:
            policy = await db.scalar(select(StockPolicy).where(StockPolicy.facility_id == UUID(fid), StockPolicy.medicine_id == UUID(medicine['id'])))
        if policy is None:
            row = await request('PUT', f"/inventory/policies/{fid}/{medicine['id']}", {'safety_stock': 10, 'expiry_warning_days': 60})
            created.append({'endpoint': '/inventory/policies', 'id': row['id']})
        bed = await ensure('/beds', 'bed_type', 'DEV-PHASE3 ICU', {'facility_id': fid, 'bed_type': 'DEV-PHASE3 ICU', 'capacity': 10, 'occupied': 3}, '/operations/beds', {'facility_id': fid}, 'PUT')
        staff_role = await ensure('/staff-roles', 'name', 'DEVELOPMENT ONLY Phase 3 Role', {'name': 'DEVELOPMENT ONLY Phase 3 Role'})
        staff = await ensure('/staff', 'code', 'DEV-PHASE3-STAFF', {'facility_id': fid, 'staff_role_id': staff_role['id'], 'code': 'DEV-PHASE3-STAFF', 'display_name': 'DEVELOPMENT ONLY Phase 3 Staff'}, '/operations/staff', {'facility_id': fid})
        await ensure('/equipment', 'code', 'DEV-PHASE3-EQUIP', {'facility_id': fid, 'code': 'DEV-PHASE3-EQUIP', 'equipment_type': 'DEVELOPMENT ONLY test device'}, '/assets/equipment', {'facility_id': fid})
        await ensure('/ambulances', 'vehicle_id', 'DEV-PHASE3-AMB', {'facility_id': fid, 'vehicle_id': 'DEV-PHASE3-AMB'}, '/assets/ambulances', {'facility_id': fid})
        for kind, category, count in [('footfall', 'DEV-PHASE3 OPD', 12), ('disease-counts', 'DEV-PHASE3 category', 2)]:
            await ensure('/aggregates/' + kind, 'category', category, {'facility_id': fid, 'day': datetime.now(timezone.utc).date().isoformat(), 'category': category, 'count': count}, '/operations/' + kind, {'facility_id': fid}, 'PUT')
        supplier = await ensure('/suppliers', 'code', 'DEV-PHASE3-SUP', {'name': 'DEVELOPMENT ONLY Phase 3 Supplier', 'code': 'DEV-PHASE3-SUP'})
        await ensure('/purchase-orders', 'reference', 'DEV-PHASE3-ORDER', {'reference': 'DEV-PHASE3-ORDER', 'supplier_id': supplier['id'], 'facility_id': fid,
            'items': [{'medicine_id': medicine['id'], 'quantity': 5, 'unit_price': '0.00'}]})
        rules = await listing('/alert-rules')
        rule = next((r for r in rules if r['facility_id'] == fid and r['kind'] == 'LOW_STOCK'), None)
        if rule is None:
            rule = await request('POST', '/alert-rules', {'facility_id': fid, 'kind': 'LOW_STOCK', 'threshold': 150, 'severity': 'warning'})
            created.append({'endpoint': '/alert-rules', 'id': rule['id']})
        # Evaluate only this development rule using the existing service; no worker or delivery is simulated.
        async with AsyncSessionLocal.begin() as db:
            assert (await db.get(Facility, UUID(fid))).code == 'DEV-PHASE3'
            emitted = await evaluate_rule(db, UUID(rule['id']))
            if emitted:
                audit(db, UUID(me['id']), 'development.phase3_seed', {'facility_id': fid, 'rule_id': rule['id']})
        alerts = [a for a in await listing('/alerts') if a['rule_id'] == rule['id']]
        manifest = {'database': 'sanjeevani_dev', 'facility_id': fid, 'facility_name': facility['name'], 'medicine_id': medicine['id'],
            'medicine_name': medicine['name'], 'batch_id': lot['batch_id'], 'inventory_id': lot['id'], 'bed_id': bed['id'],
            'staff_id': staff['id'], 'rule_id': rule['id'], 'alert_ids': [a['id'] for a in alerts], 'geography': geography}
        (ROOT / 'tmp/phase3-seed.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        print(json.dumps({'database': 'sanjeevani_dev', 'created': created, 'alerts_emitted': emitted, 'manifest': 'tmp/phase3-seed.json'}))
        # Do not log out here: logout revokes all this account's sessions, including an open browser session.
    await engine.dispose()


if __name__ == '__main__':
    asyncio.run(main())
