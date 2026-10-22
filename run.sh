#!/usr/bin/env bash
set -euo pipefail

PORT="${1:-8000}"
HOST="${HOST:-127.0.0.1}"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Serving DavaoRoutes at http://localhost:${PORT}/"
if [ "$HOST" != "127.0.0.1" ]; then
  echo "Bound to ${HOST}:${PORT}"
fi
echo "Press Ctrl+C to stop."

exec uv run --no-project python - "$HOST" "$PORT" "$DIR" <<'PY'
import functools
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

host, port, directory = sys.argv[1], int(sys.argv[2]), sys.argv[3]
handler = functools.partial(SimpleHTTPRequestHandler, directory=directory)
server = ThreadingHTTPServer((host, port), handler)
server.serve_forever()
PY
