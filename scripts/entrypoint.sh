#!/bin/bash
set -euo pipefail

echo "==> Waiting for database..."
until python -c "
import socket, os, sys, urllib.parse
url = os.environ.get('DATABASE_URL', '')
parsed = urllib.parse.urlparse(url.replace('+asyncpg', '').replace('+psycopg', ''))
host = parsed.hostname or 'localhost'
port = parsed.port or 5432
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(2)
try:
    sock.connect((host, port))
    sock.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; do
    echo "    DB not ready, retrying in 2s..."
    sleep 2
done
echo "==> Database is ready"

echo "==> Running migrations..."
alembic upgrade head
echo "==> Migrations complete"

echo "==> Starting gunicorn..."
exec gunicorn -c gunicorn.conf.py backend.src.main:app
