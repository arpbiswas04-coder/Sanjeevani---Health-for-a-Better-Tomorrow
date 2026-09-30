"""Infra-owned ASGI metrics boundary and bounded read-only dependency probes."""
import asyncio
import hmac
import os
from pathlib import Path
from time import perf_counter
from optimization.common.telemetry import observe, render


def dependencies():
    lines = []
    try:
        import psycopg2
        url = os.environ['DATABASE_URL'].replace('postgresql+asyncpg://','postgresql://',1)
        connection = psycopg2.connect(url, connect_timeout=2, options='-c statement_timeout=1500')
        try:
            connection.set_session(readonly=True, autocommit=True)
            with connection.cursor() as cursor:
                cursor.execute('SELECT count(*) FROM pg_stat_activity WHERE datname=current_database()')
                count = cursor.fetchone()[0]
            lines += ['sanjeevani_dependency_up{service="postgres"} 1', f'sanjeevani_postgres_connections {count}']
        finally: connection.close()
    except Exception:
        lines.append('sanjeevani_dependency_up{service="postgres"} 0')
    try:
        import redis
        with redis.Redis.from_url(os.environ['REDIS_URL'], socket_connect_timeout=1, socket_timeout=1) as client:
            if not client.ping(): raise ValueError('Redis ping failed')
            info = client.info()
        lines += ['sanjeevani_dependency_up{service="redis"} 1',
                  f'sanjeevani_redis_connected_clients {int(info["connected_clients"])}',
                  f'sanjeevani_redis_used_memory_bytes {int(info["used_memory"])}',
                  f'sanjeevani_redis_commands_total {int(info["total_commands_processed"])}']
    except Exception:
        lines.append('sanjeevani_dependency_up{service="redis"} 0')
    return '\n'.join(lines)+'\n'


class MetricsApp:
    def __init__(self, app, token_path, collector=dependencies):
        self.app, self.token_path, self.collector = app, Path(token_path), collector

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http': return await self.app(scope,receive,send)
        path = scope.get('path','')
        if path == '/internal/metrics':
            code, body = 403, b'Forbidden\n'
            try:
                token = self.token_path.read_bytes().strip()
                headers = dict(scope.get('headers',[]))
                if len(token) >= 32 and hmac.compare_digest(headers.get(b'authorization',b''), b'Bearer '+token):
                    if scope.get('method') != 'GET': code, body = 405, b'Method not allowed\n'
                    else:
                        code, body = 200, (render()+await asyncio.to_thread(self.collector)).encode()
            except OSError:
                code, body = 503, b'Metrics credential unavailable\n'
            await send({'type':'http.response.start','status':code,'headers':[
                (b'content-type',b'text/plain; version=0.0.4; charset=utf-8'), (b'cache-control',b'no-store')]})
            await send({'type':'http.response.body','body':body})
            return
        name = 'health' if path == '/api/v1/health' else ('api' if path.startswith('/api/') else 'other')
        start, status = perf_counter(), 500
        async def response(message):
            nonlocal status
            if message['type'] == 'http.response.start':
                status = message['status']
                message = {**message, 'headers': [*message.get('headers',[]), (b'x-content-type-options',b'nosniff')]}
            await send(message)
        try: return await self.app(scope,receive,response)
        except BaseException:
            status = 500
            raise
        finally: observe('http',name,f'{max(1,min(5,status//100))}xx',perf_counter()-start)
