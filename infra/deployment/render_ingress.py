"""Render a reviewed Nginx configuration from a strict public origin and limits."""
import os
from pathlib import Path
import re
from urllib.parse import urlsplit


def render(template, origin, *, auth='5r/m', operations='2r/s', api='20r/s'):
    url = urlsplit(origin)
    if (url.scheme != 'https' or not url.hostname or url.username or url.password or
        url.path or url.query or url.fragment or not re.fullmatch(r'[A-Za-z0-9.-]+', url.hostname)):
        raise ValueError('Use a plain HTTPS origin without path or credentials')
    if url.port is not None and not 1 <= url.port <= 65535:
        raise ValueError('Invalid origin port')
    for rate in (auth, operations, api):
        if not re.fullmatch(r'[1-9][0-9]{0,3}r/[sm]', rate):
            raise ValueError('Invalid Nginx rate')
    return (template.replace('https://localhost:9443', origin)
        .replace('server_name localhost;', f'server_name {url.hostname};')
        .replace('zone=auth:1m rate=5r/m', f'zone=auth:1m rate={auth}')
        .replace('zone=operations:1m rate=2r/s', f'zone=operations:1m rate={operations}')
        .replace('zone=api:1m rate=20r/s', f'zone=api:1m rate={api}'))


def main():
    root = Path(__file__).resolve().parents[1]
    content = render((root/'nginx/member4-tls.conf').read_text(encoding='utf-8'), os.environ['PUBLIC_HTTPS_ORIGIN'],
        auth=os.environ.get('NGINX_AUTH_RATE', '5r/m'), operations=os.environ.get('NGINX_OPERATIONS_RATE', '2r/s'),
        api=os.environ.get('NGINX_API_RATE', '20r/s'))
    target = root/'outputs/nginx.conf'
    target.parent.mkdir(exist_ok=True)
    target.write_text(content, encoding='utf-8')
    print(str(target))


if __name__ == '__main__':
    main()
