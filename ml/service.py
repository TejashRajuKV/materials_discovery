"""Resident ML service: the engine's commands over local HTTP, with models loaded once.

The per-request CLI pays Python start-up and loads the band-gap bundle (over 1 GB) every time.
This server loads each bundle on first use and keeps it, so later requests skip that cost. It runs
the same functions as the CLI (ml/commands.py) and returns the same JSON documents, so the backend
can use either. Errors come back as {"error": ..., "message": ...} with HTTP 200, as the CLI does.

  python ml/service.py                 # 127.0.0.1:8001 (ML_SERVICE_PORT overrides)

Endpoints:
  GET  /health
  POST /predict   {"formulas": [...], "property": "band_gap"}
  POST /discover  {"spec": {...}, "generate": true, "include_known": true, "top_k": 25}
  POST /explain   {"formula": "MgO"}
"""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml import commands  # noqa: E402

MAX_BODY_BYTES = 1_000_000


def dispatch(path, payload):
    """Run one command and return its result document (or an error document)."""
    try:
        if path == "/predict":
            return commands.predict(payload.get("formulas", []), payload.get("property", "band_gap"))
        if path == "/discover":
            return commands.discover(payload)
        if path == "/explain":
            return commands.explain(payload.get("formula", ""))
        return {"error": "NotFound", "message": f"no such endpoint {path}"}
    except Exception as exc:  # same structured error the CLI prints
        return {"error": type(exc).__name__, "message": str(exc)}


class Handler(BaseHTTPRequestHandler):
    server_version = "materials-ml/1"

    def _send(self, status, document):
        body = json.dumps(document, default=float).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            return self._send(200, {"status": "ok"})
        return self._send(404, {"error": "NotFound", "message": f"no such endpoint {self.path}"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY_BYTES:
            return self._send(413, {"error": "PayloadTooLarge", "message": "request body too large"})
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self._send(400, {"error": "InvalidJSON", "message": "body must be JSON"})
        if not isinstance(payload, dict):
            return self._send(400, {"error": "InvalidJSON", "message": "body must be a JSON object"})
        return self._send(200, dispatch(self.path, payload))

    def log_message(self, fmt, *args):  # keep stdout clean; errors are returned in the response
        sys.stderr.write("ml-service %s\n" % (fmt % args))


def main():
    host = os.environ.get("ML_SERVICE_HOST", "127.0.0.1")
    port = int(os.environ.get("ML_SERVICE_PORT", "8001"))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"ML service on http://{host}:{port}", file=sys.stderr, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
